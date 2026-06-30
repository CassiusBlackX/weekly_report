import { useEffect, useRef } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Image from "@tiptap/extension-image";
import Link from "@tiptap/extension-link";
import Placeholder from "@tiptap/extension-placeholder";
import { Button, Space, Tooltip, Grid, message } from "antd";
import {
  BoldOutlined,
  ItalicOutlined,
  StrikethroughOutlined,
  UnorderedListOutlined,
  OrderedListOutlined,
  PictureOutlined,
  LinkOutlined,
} from "@ant-design/icons";
import { api } from "../api";

const { useBreakpoint } = Grid;

interface Props {
  initialContent: string; // TipTap JSON string, or empty
  onChange: (json: string, html: string) => void;
}

export default function RichTextEditor({ initialContent, onChange }: Props) {
  const fileInput = useRef<HTMLInputElement>(null);
  const screens = useBreakpoint();
  const isMobile = !screens.md;

  const editor = useEditor({
    extensions: [
      StarterKit,
      Image.configure({ inline: false }),
      Link.configure({ openOnClick: false }),
      Placeholder.configure({ placeholder: "在这里填写本周工作内容，可插入图片…" }),
    ],
    content: initialContent ? safeParse(initialContent) : "",
    onUpdate: ({ editor }) => {
      onChange(JSON.stringify(editor.getJSON()), editor.getHTML());
    },
  });

  // Reset content when switching between cycles/users.
  useEffect(() => {
    if (editor && initialContent !== JSON.stringify(editor.getJSON())) {
      editor.commands.setContent(initialContent ? safeParse(initialContent) : "");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialContent, editor]);

  if (!editor) return null;

  const uploadImage = async (file: File) => {
    const hide = message.loading("图片上传中…", 0);
    const form = new FormData();
    form.append("file", file);
    try {
      const { data } = await api.post<{ url: string }>("/uploads", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      editor.chain().focus().setImage({ src: data.url }).run();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || "图片上传失败");
    } finally {
      hide();
    }
  };

  const addLink = () => {
    const url = window.prompt("输入链接地址");
    if (url) editor.chain().focus().setLink({ href: url }).run();
  };

  const btnSize = isMobile ? "middle" : "small";
  const btn = (active: boolean, icon: JSX.Element, onClick: () => void, tip: string) => (
    <Tooltip title={tip}>
      <Button size={btnSize} type={active ? "primary" : "default"} icon={icon} onClick={onClick} />
    </Tooltip>
  );

  return (
    <div style={{ border: "1px solid #d9d9d9", borderRadius: 10, overflow: "hidden" }}>
      <Space
        className="editor-toolbar"
        size={isMobile ? 8 : 4}
        style={{ padding: isMobile ? 10 : 8, borderBottom: "1px solid #f0f0f0", background: "#fafafa", rowGap: 8 }}
        wrap
      >
        {btn(editor.isActive("bold"), <BoldOutlined />, () => editor.chain().focus().toggleBold().run(), "加粗")}
        {btn(editor.isActive("italic"), <ItalicOutlined />, () => editor.chain().focus().toggleItalic().run(), "斜体")}
        {btn(editor.isActive("strike"), <StrikethroughOutlined />, () => editor.chain().focus().toggleStrike().run(), "删除线")}
        {btn(editor.isActive("bulletList"), <UnorderedListOutlined />, () => editor.chain().focus().toggleBulletList().run(), "无序列表")}
        {btn(editor.isActive("orderedList"), <OrderedListOutlined />, () => editor.chain().focus().toggleOrderedList().run(), "有序列表")}
        {btn(editor.isActive("link"), <LinkOutlined />, addLink, "插入链接")}
        {btn(false, <PictureOutlined />, () => fileInput.current?.click(), "插入图片")}
      </Space>
      <input
        ref={fileInput}
        type="file"
        accept="image/*"
        style={{ display: "none" }}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) uploadImage(f);
          e.target.value = "";
        }}
      />
      <EditorContent
        editor={editor}
        className="tiptap-content"
        style={{
          padding: 14,
          minHeight: isMobile ? 200 : 240,
          maxHeight: isMobile ? "52vh" : "none",
          overflowY: "auto",
        }}
      />
    </div>
  );
}

function safeParse(s: string): any {
  try {
    return JSON.parse(s);
  } catch {
    return "";
  }
}

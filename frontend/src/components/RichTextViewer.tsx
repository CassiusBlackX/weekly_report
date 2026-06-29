import DOMPurify from "dompurify";

// Second line of defence (the server already sanitises on save).
export default function RichTextViewer({ html }: { html: string }) {
  if (!html) return <span style={{ color: "#999" }}>（未填写）</span>;
  const clean = DOMPurify.sanitize(html, {
    ADD_ATTR: ["target"],
  });
  return <div className="tiptap-content" dangerouslySetInnerHTML={{ __html: clean }} />;
}

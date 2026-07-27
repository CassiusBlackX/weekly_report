import DOMPurify from "dompurify";

// Second line of defence (the server already sanitises on save).
export default function RichTextViewer({ html }: { html: string }) {
  // Leave it blank rather than labelling it — the card's own title still
  // shows who this is, no need to call out that they haven't written
  // anything yet.
  if (!html) return null;
  const clean = DOMPurify.sanitize(html, {
    ADD_ATTR: ["target"],
  });
  return <div className="tiptap-content" dangerouslySetInnerHTML={{ __html: clean }} />;
}

import { marked } from "marked";
import DOMPurify from "dompurify";

marked.setOptions({
  breaks: true,
  gfm: true,
});

export function useMarkdown() {
  const render = (content) =>
    content ? DOMPurify.sanitize(marked.parse(content)) : "";

  return { render };
}

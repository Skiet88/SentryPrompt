import type { ComponentProps } from "react";
import Markdown, { defaultUrlTransform } from "react-markdown";

/**
 * Renders AI replies as Markdown, safely (SECURITY_RULES.md §1, §5):
 * - raw HTML in the reply is dropped, never rendered;
 * - only a small set of text elements is allowed; images are not, so a
 *   manipulated reply can't load a tracking image or leak data through a URL;
 * - links only work for http(s) and mailto, open in a new tab, and send no referrer.
 */
const ALLOWED = [
  "p", "br", "strong", "em", "del", "a", "ul", "ol", "li", "blockquote",
  "code", "pre", "h1", "h2", "h3", "h4", "h5", "h6", "hr",
  "table", "thead", "tbody", "tr", "th", "td",
];

export function safeUrl(url: string): string {
  const cleaned = defaultUrlTransform(url);
  return /^(https?:|mailto:)/i.test(cleaned) ? cleaned : "";
}

const components: ComponentProps<typeof Markdown>["components"] = {
  a: ({ href, children }) =>
    href ? (
      <a href={href} target="_blank" rel="noopener noreferrer nofollow" className="text-primary underline underline-offset-2">
        {children}
      </a>
    ) : (
      <span>{children}</span>
    ),
};

export function SafeMarkdown({ text }: { text: string }) {
  return (
    <div className="markdown">
      <Markdown skipHtml allowedElements={ALLOWED} unwrapDisallowed urlTransform={safeUrl} components={components}>
        {text}
      </Markdown>
    </div>
  );
}

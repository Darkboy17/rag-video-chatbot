import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import clsx from "clsx";

/**
 * Props for the {@link MessageMarkdown} component.
 * content: The markdown content to render.
 */
type MessageMarkdownProps = {
  content: string;
};

// Centralized markdown renderers keep assistant output consistent across every
// response shape the LLM can produce: links, tables, code, and headings.
const markdownComponents: Components = {

  // A link is an external URL.
  a({ children, href }) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="font-medium text-indigo-700 underline underline-offset-2 hover:text-indigo-900"
      >
        {children}
      </a>
    );
  },

  // A blockquote is a quoted section of text.
  blockquote({ children }) {
    return (
      <blockquote className="my-3 border-l-2 border-slate-300 pl-3 text-slate-600">
        {children}
      </blockquote>
    );
  },

  // A code block is a block of text with a language identifier.
  code({ children, className }) {

    // react-markdown passes a language class for fenced code blocks. Inline
    // code has no className, so it gets the compact pill treatment.
    const isBlockCode = Boolean(className);

    if (isBlockCode) {
      return (
        <code className={clsx("font-mono text-xs", className)}>
          {children}
        </code>
      );
    }

    return (
      <code className="rounded bg-slate-200 px-1 py-0.5 font-mono text-[0.85em] text-slate-900">
        {children}
      </code>
    );
  },

  // A heading is a section of text with a smaller font size.
  h1({ children }) {
    return <h1 className="mb-2 mt-1 text-lg font-semibold">{children}</h1>;
  },
  h2({ children }) {
    return <h2 className="mb-2 mt-4 text-base font-semibold">{children}</h2>;
  },
  h3({ children }) {
    return <h3 className="mb-1.5 mt-3 text-sm font-semibold">{children}</h3>;
  },

  // A horizontal rule is a horizontal line.
  hr() {
    return <hr className="my-4 border-slate-200" />;
  },

  // A list item is a bullet point.
  li({ children }) {
    return <li className="pl-1">{children}</li>;
  },

  // An ordered list is a numbered list.
  ol({ children }) {
    return <ol className="my-3 list-decimal space-y-1 pl-5">{children}</ol>;
  },

  // A paragraph is a block of text.
  p({ children }) {
    return <p className="mb-3 last:mb-0">{children}</p>;
  },

  // A preformatted block of code is a block of text with a monospace font.
  pre({ children }) {
    return (
      <pre className="my-3 max-w-full overflow-x-auto rounded-lg bg-slate-950 p-3 text-slate-50">
        {children}
      </pre>
    );
  },

  // A table is a set of rows and columns.
  table({ children }) {
    return (
      <div className="my-3 max-w-full overflow-x-auto rounded-lg border border-slate-200">
        <table className="w-full border-collapse text-left text-xs">
          {children}
        </table>
      </div>
    );
  },

  // A table row is a set of cells.
  tbody({ children }) {
    return <tbody className="divide-y divide-slate-200">{children}</tbody>;
  },

  // A table cell is a block of text.
  td({ children }) {
    return <td className="px-3 py-2 align-top">{children}</td>;
  },

  // A table header is a block of text.
  th({ children }) {
    return (
      <th className="bg-slate-100 px-3 py-2 font-semibold text-slate-700">
        {children}
      </th>
    );
  },

  // A table header row is a set of table headers.
  thead({ children }) {
    return <thead>{children}</thead>;
  },

  // An unordered list is a list of bullet points.
  ul({ children }) {
    return <ul className="my-3 list-disc space-y-1 pl-5">{children}</ul>;
  },
};

/**
 * Renders assistant markdown with app-specific typography and table/code styles.
 */
export function MessageMarkdown({ content }: MessageMarkdownProps) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
      {content}
    </ReactMarkdown>
  );
}

export function FormattedText({ content }) {
  if (!content) return null;

  const lines = content.split('\n');
  const elements = [];
  let currentList = null;
  let listKey = 0;

  const renderInlineFormatted = (text, keyPrefix = '') => {
    // Regex matches **bold**, `code`, or plain text
    const parts = [];
    const regex = /(\*\*.*?\*\*|`.*?`)/g;
    const splitTokens = text.split(regex);

    splitTokens.forEach((token, idx) => {
      if (!token) return;
      if (token.startsWith('**') && token.endsWith('**')) {
        parts.push(
          <strong key={`${keyPrefix}-b-${idx}`} className="font-semibold text-slate-900 dark:text-slate-100">
            {token.slice(2, -2)}
          </strong>
        );
      } else if (token.startsWith('`') && token.endsWith('`')) {
        parts.push(
          <code
            key={`${keyPrefix}-c-${idx}`}
            className="px-1.5 py-0.5 rounded text-xs font-mono bg-slate-100 dark:bg-slate-800 text-indigo-600 dark:text-indigo-400"
          >
            {token.slice(1, -1)}
          </code>
        );
      } else {
        parts.push(<span key={`${keyPrefix}-t-${idx}`}>{token}</span>);
      }
    });

    return parts;
  };

  const flushList = () => {
    if (currentList) {
      elements.push(
        <ul key={`ul-${listKey++}`} className="my-2 space-y-1 list-disc list-outside ml-5 text-slate-700 dark:text-slate-300">
          {currentList.map((item, idx) => (
            <li key={idx} className="leading-relaxed">
              {renderInlineFormatted(item, `li-${idx}`)}
            </li>
          ))}
        </ul>
      );
      currentList = null;
    }
  };

  lines.forEach((line, lineIdx) => {
    const trimmed = line.trim();

    // Empty line separates paragraphs/lists
    if (!trimmed) {
      flushList();
      return;
    }

    // Bullet point: "* ", "- "
    if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      if (!currentList) currentList = [];
      currentList.push(trimmed.slice(2));
      return;
    }

    // Numbered item: e.g. "1. "
    const numberedMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
    if (numberedMatch) {
      flushList();
      elements.push(
        <div key={`num-${lineIdx}`} className="flex gap-2 my-1 text-slate-700 dark:text-slate-300 leading-relaxed">
          <span className="font-semibold text-indigo-600 dark:text-indigo-400 min-w-[1.25rem]">
            {numberedMatch[1]}.
          </span>
          <div className="flex-1">{renderInlineFormatted(numberedMatch[2], `n-${lineIdx}`)}</div>
        </div>
      );
      return;
    }

    // Regular paragraph
    flushList();
    elements.push(
      <p key={`p-${lineIdx}`} className="my-1.5 text-slate-700 dark:text-slate-300 leading-relaxed">
        {renderInlineFormatted(line, `p-${lineIdx}`)}
      </p>
    );
  });

  flushList();

  return <div className="space-y-0.5">{elements}</div>;
}

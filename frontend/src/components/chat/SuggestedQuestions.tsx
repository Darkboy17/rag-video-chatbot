
// Quick-start prompt menu shown while the chat input is focused.
const QUESTIONS = [
  "What's the engagement rate of each?",
  "Which video got higher engagement, and why?",
  "Compare the hooks in the first 5 seconds.",
  "Who's the creator of Video B and what's their follower count?",
  "Suggest improvements for the lower-performing video.",
];

/**
 * Props for the {@link SuggestedQuestions} component.
 * disabled: A boolean indicating whether the component is disabled.
 * onSelect: A function to call when a suggestion is selected.
 */
type SuggestedQuestionsProps = {
  disabled: boolean;
  onSelect: (question: string) => void;
};

/**
 * Quick-start prompt menu shown while the chat input is focused.
 */
export function SuggestedQuestions({
  disabled,
  onSelect,
}: SuggestedQuestionsProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl shadow-slate-900/10">
      <div className="border-b border-slate-100 px-3 py-2 text-center text-[11px] font-semibold uppercase text-slate-400">
        Suggested questions
      </div>
      {QUESTIONS.map((question) => (
        <button
          key={question}
          type="button"
          disabled={disabled}
          // Keep focus on the textarea long enough for the click handler to run;
          // otherwise the input blur closes this popover before selection.
          onMouseDown={(event) => event.preventDefault()}
          onClick={() => onSelect(question)}
          className="block w-full border-b border-slate-100 px-4 py-2.5 text-left text-sm font-medium text-slate-700 transition last:border-b-0 hover:bg-slate-50 disabled:opacity-45"
        >
          {question}
        </button>
      ))}
    </div>
  );
}

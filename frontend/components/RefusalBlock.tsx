/**
 * Distinct refusal UI when is_refusal === true.
 * Shown even when a low-confidence badge is also present.
 */
import { Gavel } from "lucide-react";

export interface RefusalBlockProps {
  message?: string;
}

const DEFAULT_REFUSAL_NOTE =
  "The system determined that retrieved sources are insufficient to answer reliably. Please consult a licensed lawyer.";

export default function RefusalBlock({
  message = DEFAULT_REFUSAL_NOTE,
}: RefusalBlockProps) {
  return (
    <div
      data-testid="refusal-block"
      className="mt-3 flex items-start gap-3 rounded-lg border border-[#E0C8C8] bg-[var(--confidence-low-bg)] px-3 py-3 text-sm text-[var(--confidence-low-fg)]"
    >
      <Gavel className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <div>
        <p className="font-semibold">Insufficient information to answer</p>
        <p className="mt-1 leading-relaxed opacity-90">{message}</p>
      </div>
    </div>
  );
}

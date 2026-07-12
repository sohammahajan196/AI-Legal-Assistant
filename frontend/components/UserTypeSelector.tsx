/**
 * layperson / law_student / lawyer selector, feeding user_type into
 * outgoing chat requests. See PLAN.md Section 5 and TASKS.md T46.
 */
export type UserType = "layperson" | "law_student" | "lawyer";

/** Default audience on first load, matching backend prompts.py. */
export const DEFAULT_USER_TYPE: UserType = "layperson";

const USER_TYPE_OPTIONS: Array<{ value: UserType; label: string }> = [
  { value: "layperson", label: "Layperson" },
  { value: "law_student", label: "Law student" },
  { value: "lawyer", label: "Lawyer" },
];

export interface UserTypeSelectorProps {
  value: UserType;
  onChange: (value: UserType) => void;
}

export default function UserTypeSelector({
  value,
  onChange,
}: UserTypeSelectorProps) {
  return (
    <div className="mt-4">
      <label
        htmlFor="user-type-select"
        className="block text-sm font-medium text-slate-700"
      >
        I am a
      </label>
      <select
        id="user-type-select"
        value={value}
        onChange={(event) => onChange(event.target.value as UserType)}
        data-testid="user-type-select"
        className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none ring-indigo-500 focus:ring-2 sm:max-w-xs sm:text-base"
      >
        {USER_TYPE_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

/**
 * layperson / law_student / lawyer selector, feeding user_type into
 * outgoing chat requests. See PLAN.md Section 5 and TASKS.md T46.
 */
export type UserType = "layperson" | "law_student" | "lawyer";

export interface UserTypeSelectorProps {
  value: UserType;
  onChange: (value: UserType) => void;
}

export default function UserTypeSelector(props: UserTypeSelectorProps) {
  // TODO: implement selector UI, defaulting to "layperson".
  return null;
}

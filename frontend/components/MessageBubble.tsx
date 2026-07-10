/**
 * Renders a single user or assistant chat message.
 * See TASKS.md T43.
 */
export interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
}

export default function MessageBubble(props: MessageBubbleProps) {
  // TODO: implement bubble styling per role.
  return null;
}

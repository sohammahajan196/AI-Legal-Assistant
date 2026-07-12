/** API types aligned with backend/app/schemas/legal_answer.py and chat.py */

export interface SourceCitation {
  document: string;
  act_year?: number | null;
  section: string;
  domain: string;
  excerpt: string;
  retrieval_score: number;
}

export interface LegalAnswerResponse {
  answer: string;
  confidence_score: number;
  legal_domain: string;
  citations: SourceCitation[];
  is_refusal: boolean;
  disclaimer: string;
}

export interface HistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export interface SessionHistoryResponse {
  session_id: string;
  messages: HistoryMessage[];
}

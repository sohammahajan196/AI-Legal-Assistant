/**
 * Integration-style tests for ChatWindow request wiring. See TASKS.md T45/T46/T47.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ChatWindow from "./ChatWindow";
import {
  ApiClientError,
  fetchBackendHealth,
  fetchSessionHistory,
  sendChatMessage,
} from "@/lib/apiClient";

vi.mock("@/lib/apiClient", async () => {
  const actual = await vi.importActual<typeof import("@/lib/apiClient")>(
    "@/lib/apiClient"
  );
  return {
    ...actual,
    sendChatMessage: vi.fn(),
    fetchSessionHistory: vi.fn(),
    fetchBackendHealth: vi.fn(),
  };
});

vi.mock("@/lib/sessionStorage", () => ({
  getOrCreateSessionId: vi.fn(() => "session-test-id"),
  getStoredSessionId: vi.fn(() => "session-test-id"),
  clearStoredSessionId: vi.fn(),
}));

const SAMPLE_RESPONSE = {
  answer: "Theft is punishable under Section 379 IPC.",
  confidence_score: 0.87,
  legal_domain: "criminal",
  citations: [
    {
      document: "Indian Penal Code",
      act_year: 1860,
      section: "379",
      domain: "criminal",
      excerpt: "Whoever commits theft shall be punished...",
      retrieval_score: 0.91,
    },
  ],
  is_refusal: false,
  disclaimer: "This is not a substitute for licensed legal counsel.",
};

const HEALTHY = {
  status: "ok" as const,
  frontend: "ok" as const,
  backend: "ok" as const,
  backend_token_configured: true,
};

function readLastOutgoingPayload() {
  return JSON.parse(
    screen.getByTestId("last-outgoing-payload").textContent ?? "{}"
  );
}

describe("ChatWindow consent wiring", () => {
  beforeEach(() => {
    vi.mocked(fetchBackendHealth).mockReset();
    vi.mocked(fetchSessionHistory).mockReset();
    vi.mocked(sendChatMessage).mockReset();
    vi.mocked(fetchBackendHealth).mockResolvedValue(HEALTHY);
    vi.mocked(fetchSessionHistory).mockResolvedValue([]);
    vi.mocked(sendChatMessage).mockResolvedValue(SAMPLE_RESPONSE);
  });

  it("reflects unchecked consent in the stub outgoing payload", async () => {
    render(<ChatWindow />);
    await waitFor(() =>
      expect(screen.queryByText("Loading conversation...")).not.toBeInTheDocument()
    );

    fireEvent.click(screen.getByTestId("consent-checkbox"));
    fireEvent.change(screen.getByLabelText("Your message"), {
      target: { value: "What is bail?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => expect(sendChatMessage).toHaveBeenCalled());

    const payload = readLastOutgoingPayload();
    expect(payload.consent_to_log).toBe(false);
    expect(payload.query).toBe("What is bail?");
  });

  it("keeps consent_to_log true by default in the stub outgoing payload", async () => {
    render(<ChatWindow />);
    await waitFor(() =>
      expect(screen.queryByText("Loading conversation...")).not.toBeInTheDocument()
    );

    fireEvent.change(screen.getByLabelText("Your message"), {
      target: { value: "What is theft?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => expect(sendChatMessage).toHaveBeenCalled());

    expect(readLastOutgoingPayload().consent_to_log).toBe(true);
  });
});

describe("ChatWindow user_type wiring", () => {
  beforeEach(() => {
    vi.mocked(fetchBackendHealth).mockReset();
    vi.mocked(fetchSessionHistory).mockReset();
    vi.mocked(sendChatMessage).mockReset();
    vi.mocked(fetchBackendHealth).mockResolvedValue(HEALTHY);
    vi.mocked(fetchSessionHistory).mockResolvedValue([]);
    vi.mocked(sendChatMessage).mockResolvedValue(SAMPLE_RESPONSE);
  });

  it("defaults user_type to layperson in the outgoing payload", async () => {
    render(<ChatWindow />);
    await waitFor(() =>
      expect(screen.queryByText("Loading conversation...")).not.toBeInTheDocument()
    );

    fireEvent.change(screen.getByLabelText("Your message"), {
      target: { value: "What is theft?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => expect(sendChatMessage).toHaveBeenCalled());

    expect(readLastOutgoingPayload().user_type).toBe("layperson");
  });

  it("includes the selected user_type in the outgoing payload", async () => {
    render(<ChatWindow />);
    await waitFor(() =>
      expect(screen.queryByText("Loading conversation...")).not.toBeInTheDocument()
    );

    fireEvent.change(screen.getByTestId("user-type-select"), {
      target: { value: "law_student" },
    });
    fireEvent.change(screen.getByLabelText("Your message"), {
      target: { value: "Explain Section 302 IPC." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => expect(sendChatMessage).toHaveBeenCalled());

    const payload = readLastOutgoingPayload();
    expect(payload.user_type).toBe("law_student");
    expect(payload.query).toBe("Explain Section 302 IPC.");
  });
});

describe("ChatWindow backend wiring", () => {
  beforeEach(() => {
    vi.mocked(fetchBackendHealth).mockReset();
    vi.mocked(fetchSessionHistory).mockReset();
    vi.mocked(sendChatMessage).mockReset();
    vi.mocked(fetchBackendHealth).mockResolvedValue(HEALTHY);
    vi.mocked(fetchSessionHistory).mockResolvedValue([]);
    vi.mocked(sendChatMessage).mockResolvedValue(SAMPLE_RESPONSE);
  });

  it("renders assistant answers with citations, confidence, and disclaimer", async () => {
    render(<ChatWindow />);
    await waitFor(() =>
      expect(screen.queryByText("Loading conversation...")).not.toBeInTheDocument()
    );

    fireEvent.change(screen.getByLabelText("Your message"), {
      target: { value: "What is theft?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() =>
      expect(screen.getByText(SAMPLE_RESPONSE.answer)).toBeInTheDocument()
    );

    expect(screen.getAllByText(/Indian Penal Code/).length).toBeGreaterThan(0);
    expect(
      screen.getAllByLabelText(/High confidence: 87%/i).length
    ).toBeGreaterThan(0);
    expect(screen.getByText(SAMPLE_RESPONSE.disclaimer)).toBeInTheDocument();
  });

  it("loads prior session history on mount", async () => {
    vi.mocked(fetchSessionHistory).mockResolvedValue([
      { role: "user", content: "What is theft?" },
      { role: "assistant", content: "Theft is under Section 379 IPC." },
    ]);

    render(<ChatWindow />);

    await waitFor(() =>
      expect(screen.getByText("What is theft?")).toBeInTheDocument()
    );
    expect(screen.getByText("Theft is under Section 379 IPC.")).toBeInTheDocument();
    expect(fetchBackendHealth).toHaveBeenCalled();
    expect(fetchSessionHistory).toHaveBeenCalledWith("session-test-id");
  });

  it("surfaces backend health failures on mount before chat", async () => {
    vi.mocked(fetchBackendHealth).mockRejectedValue(
      new ApiClientError("Backend unavailable", 502)
    );

    render(<ChatWindow />);

    await waitFor(() =>
      expect(screen.getByTestId("chat-error")).toHaveTextContent(
        "Backend unavailable"
      )
    );
    expect(fetchSessionHistory).not.toHaveBeenCalled();
    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
  });

  it("surfaces backend errors visibly", async () => {
    vi.mocked(sendChatMessage).mockRejectedValue(
      new ApiClientError("Backend unavailable", 502)
    );

    render(<ChatWindow />);
    await waitFor(() =>
      expect(screen.queryByText("Loading conversation...")).not.toBeInTheDocument()
    );

    fireEvent.change(screen.getByLabelText("Your message"), {
      target: { value: "What is theft?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() =>
      expect(screen.getByTestId("chat-error")).toHaveTextContent(
        "Backend unavailable"
      )
    );
  });

  it("leaves the empty desk usable when history fails to load", async () => {
    vi.mocked(fetchSessionHistory).mockRejectedValue(
      new ApiClientError("Backend proxy is not configured", 503)
    );

    render(<ChatWindow />);

    await waitFor(() =>
      expect(screen.queryByText("Loading conversation...")).not.toBeInTheDocument()
    );
    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    expect(screen.getByTestId("chat-error")).toHaveTextContent(
      "Backend proxy is not configured"
    );
  });
});

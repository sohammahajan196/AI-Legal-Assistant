/**
 * Integration-style tests for ChatWindow request wiring. See TASKS.md T45/T46/T47.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ChatWindow from "./ChatWindow";
import {
  ApiClientError,
  fetchBackendHealth,
  sendChatMessage,
} from "@/lib/apiClient";

vi.mock("@/lib/apiClient", async () => {
  const actual = await vi.importActual<typeof import("@/lib/apiClient")>(
    "@/lib/apiClient"
  );
  return {
    ...actual,
    sendChatMessage: vi.fn(),
    fetchBackendHealth: vi.fn(),
  };
});

vi.mock("@/lib/sessionId", () => ({
  createSessionId: vi.fn(() => "session-test-id"),
}));

vi.mock("@/lib/audience", async () => {
  const actual = await vi.importActual<typeof import("@/lib/audience")>(
    "@/lib/audience"
  );
  return {
    ...actual,
    navigateWithAudience: vi.fn(),
  };
});

import { navigateWithAudience } from "@/lib/audience";

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
    vi.mocked(sendChatMessage).mockReset();
    vi.mocked(fetchBackendHealth).mockResolvedValue(HEALTHY);
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
    vi.mocked(sendChatMessage).mockReset();
    vi.mocked(navigateWithAudience).mockReset();
    vi.mocked(fetchBackendHealth).mockResolvedValue(HEALTHY);
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
    render(<ChatWindow initialUserType="law_student" />);
    await waitFor(() =>
      expect(screen.queryByText("Loading conversation...")).not.toBeInTheDocument()
    );

    fireEvent.change(screen.getByLabelText("Your message"), {
      target: { value: "Explain Section 302 IPC." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => expect(sendChatMessage).toHaveBeenCalled());

    const payload = readLastOutgoingPayload();
    expect(payload.user_type).toBe("law_student");
    expect(payload.query).toBe("Explain Section 302 IPC.");
  });

  it("updates the URL when the audience changes without a question", async () => {
    render(<ChatWindow initialUserType="layperson" />);
    await waitFor(() =>
      expect(screen.queryByText("Loading conversation...")).not.toBeInTheDocument()
    );

    fireEvent.change(screen.getByTestId("user-type-select"), {
      target: { value: "lawyer" },
    });

    expect(navigateWithAudience).toHaveBeenCalledWith("lawyer");
    expect(sendChatMessage).not.toHaveBeenCalled();
    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
  });

  it("re-fetches the last question when audience changes after a reply", async () => {
    vi.mocked(sendChatMessage).mockResolvedValueOnce(SAMPLE_RESPONSE);
    vi.mocked(sendChatMessage).mockResolvedValueOnce({
      ...SAMPLE_RESPONSE,
      answer: "Lawyer-focused answer on Section 379 IPC.",
    });

    render(<ChatWindow initialUserType="layperson" />);
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

    fireEvent.change(screen.getByTestId("user-type-select"), {
      target: { value: "lawyer" },
    });

    await waitFor(() => expect(sendChatMessage).toHaveBeenCalledTimes(2));

    expect(sendChatMessage).toHaveBeenLastCalledWith(
      expect.objectContaining({
        query: "What is theft?",
        userType: "lawyer",
      })
    );

    await waitFor(() =>
      expect(
        screen.getByText("Lawyer-focused answer on Section 379 IPC.")
      ).toBeInTheDocument()
    );

    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
    expect(screen.getByText("What is theft?")).toBeInTheDocument();
  });

  it("does not reload when re-selecting the current audience", async () => {
    render(<ChatWindow initialUserType="lawyer" />);
    await waitFor(() =>
      expect(screen.queryByText("Loading conversation...")).not.toBeInTheDocument()
    );

    fireEvent.change(screen.getByTestId("user-type-select"), {
      target: { value: "lawyer" },
    });

    expect(navigateWithAudience).not.toHaveBeenCalled();
  });

  it("shows audience-specific empty-state copy", async () => {
    render(<ChatWindow initialUserType="lawyer" />);
    await waitFor(() =>
      expect(screen.queryByText("Loading conversation...")).not.toBeInTheDocument()
    );

    expect(
      screen.getByText(/Query a provision or issue directly/i)
    ).toBeInTheDocument();
  });
});

describe("ChatWindow backend wiring", () => {
  beforeEach(() => {
    vi.mocked(fetchBackendHealth).mockReset();
    vi.mocked(sendChatMessage).mockReset();
    vi.mocked(fetchBackendHealth).mockResolvedValue(HEALTHY);
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

  it("starts with an empty desk on mount", async () => {
    render(<ChatWindow />);

    await waitFor(() =>
      expect(screen.queryByText("Loading conversation...")).not.toBeInTheDocument()
    );
    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    expect(fetchBackendHealth).toHaveBeenCalled();
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
});

/**
 * Visible error state with 429-aware messaging and optional retry.
 */
"use client";

import { AlertCircle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export interface ErrorAlertProps {
  message: string;
  status?: number;
  onRetry?: () => void;
}

export default function ErrorAlert({
  message,
  status,
  onRetry,
}: ErrorAlertProps) {
  const isRateLimited = status === 429;
  const displayMessage = isRateLimited
    ? "Rate limit reached — please wait before sending another question."
    : message;

  return (
    <Alert
      variant="destructive"
      data-testid="chat-error"
      className="mb-3 shrink-0 border-[#E0C8C8] bg-[var(--confidence-low-bg)] text-[var(--confidence-low-fg)]"
    >
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{isRateLimited ? "Too many requests" : "Something went wrong"}</AlertTitle>
      <AlertDescription className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <span>{displayMessage}</span>
        {onRetry ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="mt-1 w-fit border-current sm:mt-0"
          >
            Retry
          </Button>
        ) : null}
      </AlertDescription>
    </Alert>
  );
}

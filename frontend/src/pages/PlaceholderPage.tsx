/** Holds the place of pages that arrive in the next parts. */
export function PlaceholderPage({ title, text }: { title: string; text: string }) {
  return (
    <div className="mx-auto max-w-2xl px-5 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <p className="mt-2 text-muted">{text}</p>
    </div>
  );
}

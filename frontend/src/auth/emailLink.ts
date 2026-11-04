/** What an email link (verification or password reset) brought with it. */
export interface EmailLink {
  hasCode: boolean;
  errorCode: string | null;
}

export function readEmailLink(url: URL, expectedPath: string): EmailLink {
  if (url.pathname !== expectedPath) return { hasCode: false, errorCode: null };
  const hash = new URLSearchParams(url.hash.replace(/^#/, ""));
  const errorCode =
    url.searchParams.get("error_code") ?? hash.get("error_code") ?? url.searchParams.get("error") ?? hash.get("error");
  return { hasCode: url.searchParams.has("code"), errorCode };
}

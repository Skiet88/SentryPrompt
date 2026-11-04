import { describe, expect, it } from "vitest";

import { ConfigError, readConfig } from "./env";

const VALID = {
  VITE_API_URL: "http://localhost:8000/",
  VITE_SUPABASE_URL: "https://abcd.supabase.co",
  VITE_SUPABASE_PUBLISHABLE_KEY: "sb_publishable_abc",
};

describe("readConfig", () => {
  it("reads the three public settings and trims trailing slashes", () => {
    expect(readConfig(VALID)).toEqual({
      apiUrl: "http://localhost:8000",
      supabaseUrl: "https://abcd.supabase.co",
      supabasePublishableKey: "sb_publishable_abc",
    });
  });

  it.each(["VITE_API_URL", "VITE_SUPABASE_URL", "VITE_SUPABASE_PUBLISHABLE_KEY"])("requires %s", (name) => {
    expect(() => readConfig({ ...VALID, [name]: "" })).toThrow(ConfigError);
  });

  it("refuses a Supabase secret key in the browser", () => {
    expect(() => readConfig({ ...VALID, VITE_SUPABASE_PUBLISHABLE_KEY: "sb_secret_abc" })).toThrow(/SECRET/);
  });

  it("refuses a legacy service_role key in the browser", () => {
    const payload = btoa(JSON.stringify({ role: "service_role" }));
    expect(() => readConfig({ ...VALID, VITE_SUPABASE_PUBLISHABLE_KEY: `x.${payload}.y` })).toThrow(/SECRET/);
  });
});

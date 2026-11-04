import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ApiError } from "@/api/apiClient";
import { AuthFailure } from "@/auth/authGateway";
import { AUTH_MESSAGES } from "@/auth/authMessages";
import { makeServices, renderApp, STUDENT } from "@/test/fakes";

const user = () => userEvent.setup();

describe("protected pages", () => {
  it("send logged-out visitors to the login page", async () => {
    const { services } = makeServices();
    const router = renderApp("/settings", services);
    expect(await screen.findByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/login");
  });

  it("show a retry screen when the login can't be checked (fails closed)", async () => {
    const { services, auth } = makeServices({ profile: new ApiError(503, "auth_unavailable", "Login could not be checked right now.") });
    auth.session = { userId: STUDENT.userId, email: STUDENT.email };
    renderApp("/", services);
    expect(await screen.findByRole("alert")).toHaveTextContent("Login could not be checked right now.");
    expect(screen.queryByText(/What would you like to ask/)).not.toBeInTheDocument();
  });

  it("treat a 401 from the backend as logged out", async () => {
    const { services, auth } = makeServices({ profile: new ApiError(401, "unauthenticated", "x") });
    auth.session = { userId: STUDENT.userId, email: STUDENT.email };
    renderApp("/", services);
    expect(await screen.findByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
  });
});

describe("login", () => {
  it("logs in and returns to the page the user wanted", async () => {
    const { services, auth } = makeServices();
    const router = renderApp("/login", services, { from: "/settings" });
    await user().type(await screen.findByLabelText("Email"), "thabo.m@uni.ac.za");
    await user().type(screen.getByLabelText("Password"), "campus2026");
    await user().click(screen.getByRole("button", { name: "Log in" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/settings"));
    expect(auth.calls).toContain("signIn:thabo.m@uni.ac.za");
  });

  it("ignores an external return address (no open redirect)", async () => {
    const { services } = makeServices();
    const router = renderApp("/login", services, { from: "//evil.example" });
    await user().type(await screen.findByLabelText("Email"), "thabo.m@uni.ac.za");
    await user().type(screen.getByLabelText("Password"), "campus2026");
    await user().click(screen.getByRole("button", { name: "Log in" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
  });

  it("shows one message for a wrong email or password", async () => {
    const { services, auth } = makeServices();
    auth.failWith = new AuthFailure("invalid_credentials");
    renderApp("/login", services);
    await user().type(await screen.findByLabelText("Email"), "someone@uni.ac.za");
    await user().type(screen.getByLabelText("Password"), "wrong");
    await user().click(screen.getByRole("button", { name: "Log in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(AUTH_MESSAGES.invalid_credentials);
  });

  it("checks the email before contacting the server", async () => {
    const { services, auth } = makeServices();
    renderApp("/login", services);
    await user().type(await screen.findByLabelText("Email"), "not-an-email");
    await user().click(screen.getByRole("button", { name: "Log in" }));
    expect(screen.getByLabelText("Email")).toHaveAttribute("aria-invalid", "true");
    expect(auth.calls).toEqual([]);
  });

  it("renders injected text as plain text, never as HTML", async () => {
    const { services } = makeServices();
    renderApp("/login", services, { notice: "<img src=x onerror=alert(1)>" });
    expect(await screen.findByText("<img src=x onerror=alert(1)>")).toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
  });
});

describe("sign up", () => {
  it("validates, signs up and asks the user to check their email", async () => {
    const { services, auth } = makeServices();
    renderApp("/register", services);
    await user().type(await screen.findByLabelText("Email"), "new@uni.ac.za");
    await user().type(screen.getByLabelText("Password"), "short");
    await user().click(screen.getByRole("button", { name: "Create account" }));
    expect(auth.calls).toEqual([]);
    await user().clear(screen.getByLabelText("Password"));
    await user().type(screen.getByLabelText("Password"), "campus2026");
    await user().click(screen.getByRole("button", { name: "Create account" }));
    expect(await screen.findByRole("heading", { name: "Check your email" })).toBeInTheDocument();
    expect(screen.getByText("new@uni.ac.za")).toBeInTheDocument();
    expect(auth.calls).toEqual(["signUp:new@uni.ac.za"]);
  });

  it("lets the user resend the link", async () => {
    const { services, auth } = makeServices();
    renderApp("/check-email", services, { email: "new@uni.ac.za" });
    await user().click(await screen.findByRole("button", { name: "Send the link again" }));
    expect(await screen.findByText("We sent the link again.")).toBeInTheDocument();
    expect(auth.calls).toEqual(["resend:new@uni.ac.za"]);
  });
});

describe("password reset", () => {
  it("gives the same answer whether or not the account exists", async () => {
    const { services, auth } = makeServices();
    renderApp("/forgot-password", services);
    await user().type(await screen.findByLabelText("Email"), "anyone@uni.ac.za");
    await user().click(screen.getByRole("button", { name: "Send reset link" }));
    expect(await screen.findByText(/If an account uses anyone@uni.ac.za/)).toBeInTheDocument();
    expect(auth.calls).toEqual(["reset:anyone@uni.ac.za"]);
  });

  it("shows the form only when opened from a reset link", async () => {
    const { services, auth } = makeServices();
    auth.session = { userId: STUDENT.userId, email: STUDENT.email };
    renderApp("/reset-password", services);
    expect(await screen.findByRole("heading", { name: "This reset link doesn't work" })).toBeInTheDocument();
    expect(screen.queryByLabelText("New password")).not.toBeInTheDocument();
  });

  it("saves the new password and ends every session", async () => {
    const { services, auth } = makeServices({ landingUrl: "http://localhost:5173/reset-password?code=one-time" });
    auth.session = { userId: STUDENT.userId, email: STUDENT.email };
    const router = renderApp("/reset-password", services);
    await user().type(await screen.findByLabelText("New password"), "newcampus2026");
    await user().click(screen.getByRole("button", { name: "Save new password" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    expect(auth.calls).toEqual(["updatePassword", "signOut:global"]);
    expect(await screen.findByText(/Password changed/)).toBeInTheDocument();
  });

  it("shows a fixed message for a broken link, never text from the link", async () => {
    const landing = "http://localhost:5173/reset-password?error_code=otp_expired&error_description=Call+0800+now";
    const { services } = makeServices({ landingUrl: landing });
    renderApp("/reset-password", services);
    expect(await screen.findByRole("alert")).toHaveTextContent("This link has expired.");
    expect(screen.queryByText(/0800/)).not.toBeInTheDocument();
  });
});

describe("email verification link", () => {
  it("opens the app when the link created a session", async () => {
    const { services, auth } = makeServices({ landingUrl: "http://localhost:5173/auth/callback?code=one-time" });
    auth.session = { userId: STUDENT.userId, email: STUDENT.email };
    const router = renderApp("/auth/callback", services);
    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
  });

  it("explains a link that didn't work", async () => {
    const { services } = makeServices({ landingUrl: "http://localhost:5173/auth/callback?code=used" });
    renderApp("/auth/callback", services);
    expect(await screen.findByRole("heading", { name: "We couldn't verify that link" })).toBeInTheDocument();
  });
});

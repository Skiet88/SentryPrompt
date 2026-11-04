import type { RouteObject } from "react-router";

import { PublicOnly, RequireAuth } from "@/auth/guards";
import { AppShell } from "@/layout/AppShell";
import { AuthCallbackPage } from "@/pages/AuthCallbackPage";
import { ChatHomePage } from "@/pages/ChatHomePage";
import { CheckEmailPage } from "@/pages/CheckEmailPage";
import { ForgotPasswordPage } from "@/pages/ForgotPasswordPage";
import { LoginPage } from "@/pages/LoginPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { PlaceholderPage } from "@/pages/PlaceholderPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { ResetPasswordPage } from "@/pages/ResetPasswordPage";

export const routes: RouteObject[] = [
  {
    element: <PublicOnly />,
    children: [
      { path: "/login", element: <LoginPage /> },
      { path: "/register", element: <RegisterPage /> },
      { path: "/forgot-password", element: <ForgotPasswordPage /> },
    ],
  },
  { path: "/check-email", element: <CheckEmailPage /> },
  { path: "/auth/callback", element: <AuthCallbackPage /> },
  { path: "/reset-password", element: <ResetPasswordPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppShell />,
        children: [
          { path: "/", element: <ChatHomePage /> },
          {
            path: "/c/:conversationId",
            element: <PlaceholderPage title="Chat" text="Opening past chats arrives in the next update." />,
          },
          {
            path: "/settings",
            element: <PlaceholderPage title="Settings" text="Your name, and deleting your account, arrive in part 3." />,
          },
          {
            path: "/admin",
            element: <PlaceholderPage title="Admin panel" text="Managing accounts arrives in part 4." />,
          },
        ],
      },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
];

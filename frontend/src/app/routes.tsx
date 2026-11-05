import type { RouteObject } from "react-router";

import { PublicOnly, RequireAuth } from "@/auth/guards";
import { AppShell } from "@/layout/AppShell";
import { AdminPage } from "@/pages/AdminPage";
import { AuthCallbackPage } from "@/pages/AuthCallbackPage";
import { ChatPage } from "@/pages/ChatPage";
import { CheckEmailPage } from "@/pages/CheckEmailPage";
import { ForgotPasswordPage } from "@/pages/ForgotPasswordPage";
import { LoginPage } from "@/pages/LoginPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { SettingsPage } from "@/pages/SettingsPage";
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
          {
            // One parent for both addresses, so the chat stays on screen when a
            // new chat gets its address (see ChatPage).
            element: <ChatPage />,
            children: [
              { path: "/", element: null },
              { path: "/c/:conversationId", element: null },
            ],
          },
          { path: "/settings", element: <SettingsPage /> },
          { path: "/admin", element: <AdminPage /> },
        ],
      },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
];

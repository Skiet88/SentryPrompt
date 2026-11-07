import { useMemo } from "react";
import { createBrowserRouter, RouterProvider } from "react-router";

import { AuthProvider } from "@/auth/AuthProvider";

import { routes } from "./routes";
import { ServicesContext, type Services } from "./services";

export function App({ services }: { services: Services }) {
  const router = useMemo(() => createBrowserRouter(routes), []);
  return (
    <ServicesContext.Provider value={services}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </ServicesContext.Provider>
  );
}

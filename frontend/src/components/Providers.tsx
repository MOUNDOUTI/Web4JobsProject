"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/lib/auth-store";
import { authApi } from "@/lib/api-client";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30000 },
  },
});

function AuthInitializer({ children }: { children: React.ReactNode }) {
  const { login, logout, setLoading } = useAuthStore();

  useEffect(() => {
    // Tenter de renouveler le token au démarrage (via cookie refresh)
    const initAuth = async () => {
      try {
        const refreshRes = await authApi.refresh();
        const newToken = refreshRes.data.access_token;
        useAuthStore.getState().setAccessToken(newToken);
        const meRes = await authApi.me();
        login(newToken, meRes.data);
      } catch {
        logout();
      } finally {
        setLoading(false);
      }
    };
    initAuth();
  }, [login, logout, setLoading]);

  return <>{children}</>;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthInitializer>{children}</AuthInitializer>
    </QueryClientProvider>
  );
}

// =============================================================================
// CyberLearn — Layout racine
// =============================================================================

import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/Providers";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "CyberLearn — Jeu Intelligent",
  description: "Jeu narratif d'apprentissage de la cybersécurité — PEGI 18+",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className="dark">
      <body className="bg-cyber-bg text-cyber-text font-sans antialiased min-h-screen">
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: "#1F2937",
                color: "#E5E7EB",
                border: "1px solid #374151",
              },
              success: { iconTheme: { primary: "#00FF88", secondary: "#0A0E1A" } },
              error: { iconTheme: { primary: "#EF4444", secondary: "#0A0E1A" } },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}

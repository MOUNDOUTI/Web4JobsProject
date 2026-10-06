"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { Shield, Map, Trophy, BarChart2, LogOut, User } from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";
import { authApi } from "@/lib/api-client";
import toast from "react-hot-toast";
import { LEVEL_NAMES } from "@/lib/constants";

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch { /* ignore */ }
    logout();
    router.push("/");
    toast.success("Déconnexion réussie");
  };

  const links = [
    { href: "/dashboard", label: "Tableau de bord", icon: <BarChart2 size={18} /> },
    { href: "/catalogue", label: "Carte du jeu", icon: <Map size={18} /> },
    { href: "/progress", label: "Progression", icon: <Trophy size={18} /> },
  ];

  return (
    <nav className="border-b border-cyber-border bg-cyber-bg2 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-2">
          <Shield className="text-cyber-green" size={24} />
          <span className="font-bold text-cyber-green glow-green text-lg">
            CYBER<span className="text-cyber-cyan">LEARN</span>
          </span>
        </Link>

        {/* Nav links */}
        <div className="hidden md:flex items-center gap-1">
          {links.map((l) => (
            <Link key={l.href} href={l.href}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors
                ${pathname.startsWith(l.href)
                  ? "bg-cyber-green/10 text-cyber-green"
                  : "text-cyber-muted hover:text-cyber-text hover:bg-cyber-bg3"
                }`}>
              {l.icon}{l.label}
            </Link>
          ))}
        </div>

        {/* User info */}
        {user && (
          <div className="flex items-center gap-3">
            <div className="hidden md:block text-right">
              <p className="text-sm font-medium text-cyber-text">{user.pseudo}</p>
              <p className="text-xs text-cyber-green">
                Niv.{user.level} · {user.total_xp} XP
              </p>
            </div>
            <button onClick={handleLogout} title="Déconnexion"
              className="p-2 rounded-lg text-cyber-muted hover:text-cyber-red hover:bg-cyber-red/10 transition-colors">
              <LogOut size={18} />
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}

"use client";

import Link from "next/link";
import { Shield, Terminal, Trophy, Zap } from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function HomePage() {
  const { isAuthenticated, isLoading } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <main className="min-h-screen bg-cyber-bg flex flex-col">
      {/* ── Header ── */}
      <header className="border-b border-cyber-border px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Shield className="text-cyber-green" size={28} />
          <span className="text-xl font-bold text-cyber-green glow-green">
            CYBER<span className="text-cyber-cyan">LEARN</span>
          </span>
        </div>
        <div className="flex gap-3">
          <Link href="/login" className="cyber-btn-secondary text-sm px-4 py-2">
            Connexion
          </Link>
          <Link href="/register" className="cyber-btn-primary text-sm px-4 py-2">
            Inscription 18+
          </Link>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="flex-1 flex flex-col items-center justify-center px-6 py-20 text-center">
        <div className="max-w-3xl mx-auto animate-fade-in">
          <div className="inline-block border border-cyber-green/30 bg-cyber-green/5 text-cyber-green text-xs font-mono px-3 py-1 rounded-full mb-6">
            🔒 PEGI 18+ — Réservé aux adultes
          </div>
          <h1 className="text-5xl md:text-7xl font-bold mb-6">
            <span className="text-cyber-text">Apprenez la</span>{" "}
            <span className="text-cyber-green glow-green">cyber</span>
            <span className="text-cyber-cyan">sécurité</span>
          </h1>
          <p className="text-xl text-cyber-muted mb-4 leading-relaxed">
            Incarnez <span className="text-cyber-gold font-semibold">Alex Chen</span>, agent CSDF,
            et progressez à travers des missions de cybersécurité réelles dans un jeu narratif immersif.
          </p>
          <p className="text-cyber-muted mb-10">
            Terminal simulé · Analyse de logs · Cryptographie · Forensics
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link href="/register" className="cyber-btn-primary text-lg px-8 py-3">
              Commencer l'aventure →
            </Link>
            <Link href="/login" className="cyber-btn-secondary text-lg px-8 py-3">
              Se connecter
            </Link>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="px-6 pb-20">
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { icon: <Terminal size={24} />, title: "Terminal Simulé", desc: "Explorez des systèmes fictifs avec de vraies commandes Linux" },
            { icon: <Shield size={24} />, title: "7 Chapitres", desc: "24+ missions progressives de débutant à expert" },
            { icon: <Trophy size={24} />, title: "Progression & Badges", desc: "XP, niveaux, badges et classement mondial" },
            { icon: <Zap size={24} />, title: "IA Recommandation", desc: "Missions adaptées à votre niveau en temps réel" },
          ].map((f, i) => (
            <div key={i} className="cyber-card hover:border-cyber-green/50 transition-colors">
              <div className="text-cyber-green mb-3">{f.icon}</div>
              <h3 className="font-bold text-cyber-text mb-2">{f.title}</h3>
              <p className="text-sm text-cyber-muted">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-cyber-border px-6 py-4 text-center text-cyber-muted text-sm">
        CyberLearn — Jeu Intelligent · Web4jobs · Stage PFE 2025 · PEGI 18+
      </footer>
    </main>
  );
}

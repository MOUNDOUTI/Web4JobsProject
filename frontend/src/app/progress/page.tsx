"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Trophy, Zap, Clock, Target, Lock } from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";
import { progressApi } from "@/lib/api-client";
import { LEVEL_NAMES, LEVEL_XP } from "@/lib/constants";
import Navbar from "@/components/ui/Navbar";

export default function ProgressPage() {
  const { isAuthenticated, isLoading } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/login");
  }, [isAuthenticated, isLoading, router]);

  const { data: stats } = useQuery({
    queryKey: ["my-progress"],
    queryFn: () => progressApi.getMyProgress().then((r) => r.data),
    enabled: isAuthenticated,
  });

  const { data: badgesData } = useQuery({
    queryKey: ["my-badges"],
    queryFn: () => progressApi.getMyBadges().then((r) => r.data),
    enabled: isAuthenticated,
  });

  const { data: history } = useQuery({
    queryKey: ["my-history"],
    queryFn: () => progressApi.getHistory(10).then((r) => r.data),
    enabled: isAuthenticated,
  });

  if (isLoading) return (
    <div className="min-h-screen bg-cyber-bg flex items-center justify-center">
      <p className="text-cyber-green animate-pulse font-mono">Chargement...</p>
    </div>
  );

  const level = stats?.level || 1;
  const totalXp = stats?.total_xp || 0;
  const nextXp = LEVEL_XP[(level + 1) as keyof typeof LEVEL_XP] || 2000;
  const currentXp = LEVEL_XP[level as keyof typeof LEVEL_XP] || 0;
  const pct = Math.min(100, ((totalXp - currentXp) / (nextXp - currentXp)) * 100);

  return (
    <div className="min-h-screen bg-cyber-bg">
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        <h1 className="text-2xl font-bold text-cyber-text">Ma Progression</h1>

        {/* Niveau et XP */}
        <div className="cyber-card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-xs text-cyber-muted font-mono">AGENT CHEN — CSDF</p>
              <p className="text-2xl font-bold text-cyber-green">{LEVEL_NAMES[level]}</p>
              <p className="text-cyber-muted text-sm">Niveau {level}</p>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold text-cyber-cyan">{totalXp}</p>
              <p className="text-xs text-cyber-muted">XP Total</p>
            </div>
          </div>
          {level < 5 && (
            <>
              <div className="w-full bg-cyber-bg3 rounded-full h-3 mb-2">
                <div className="h-3 rounded-full bg-gradient-to-r from-cyber-green to-cyber-cyan transition-all" style={{ width: `${pct}%` }} />
              </div>
              <p className="text-xs text-cyber-muted">
                {stats?.xp_to_next_level || 0} XP restants pour {LEVEL_NAMES[level + 1]}
              </p>
            </>
          )}
        </div>

        {/* Statistiques */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Missions réussies", value: stats?.missions_completed || 0, icon: <Target size={18} className="text-cyber-green" />, color: "text-cyber-green" },
            { label: "Total sessions", value: stats?.total_sessions || 0, icon: <Zap size={18} className="text-cyber-cyan" />, color: "text-cyber-cyan" },
            { label: "Badges obtenus", value: badgesData?.earned_count || 0, icon: <Trophy size={18} className="text-yellow-400" />, color: "text-yellow-400" },
            {
              label: "Temps de jeu",
              value: stats?.total_play_time_seconds ? `${Math.floor(stats.total_play_time_seconds / 3600)}h` : "0h",
              icon: <Clock size={18} className="text-cyber-muted" />,
              color: "text-cyber-text",
            },
          ].map((s, i) => (
            <div key={i} className="cyber-card text-center">
              <div className="flex justify-center mb-2">{s.icon}</div>
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-xs text-cyber-muted mt-1">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Badges */}
        <div className="cyber-card">
          <h2 className="text-lg font-bold text-cyber-text mb-4 flex items-center gap-2">
            <Trophy size={20} className="text-yellow-400" /> Badges
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {badgesData?.earned_badges?.map((b: { badge_id: number; name: string; description: string; earned_at: string }) => (
              <div key={b.badge_id} className="p-3 bg-cyber-green/5 border border-cyber-green/30 rounded-lg">
                <Trophy size={20} className="text-cyber-green mb-2" />
                <p className="text-sm font-medium text-cyber-green">{b.name}</p>
                <p className="text-xs text-cyber-muted">{b.description}</p>
              </div>
            ))}
            {badgesData?.locked_badges?.map((b: { badge_id: number; name: string; description: string }) => (
              <div key={b.badge_id} className="p-3 bg-cyber-bg3 border border-cyber-border rounded-lg opacity-50">
                <Lock size={20} className="text-cyber-muted mb-2" />
                <p className="text-sm font-medium text-cyber-muted">{b.name}</p>
                <p className="text-xs text-cyber-muted">{b.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Historique */}
        <div className="cyber-card">
          <h2 className="text-lg font-bold text-cyber-text mb-4">Historique récent</h2>
          {history?.history?.length > 0 ? (
            <div className="space-y-2">
              {history.history.map((s: { session_id: number; mission_title: string; chapter_title: string; status: string; score: number; xp_earned: number; started_at: string }) => (
                <div key={s.session_id} className="flex items-center justify-between p-3 bg-cyber-bg3 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-cyber-text">{s.mission_title}</p>
                    <p className="text-xs text-cyber-muted">{s.chapter_title}</p>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-bold ${s.status === "completed" ? "text-cyber-green" : "text-cyber-muted"}`}>
                      {s.status === "completed" ? `${s.score}/100` : s.status}
                    </p>
                    {s.xp_earned > 0 && <p className="text-xs text-cyber-cyan">+{s.xp_earned} XP</p>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-cyber-muted text-sm">Aucune session pour le moment.</p>
          )}
        </div>
      </main>
    </div>
  );
}

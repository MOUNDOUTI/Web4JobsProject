"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Trophy, Map, Zap, Clock, Target, ChevronRight } from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";
import { progressApi, recommendApi } from "@/lib/api-client";
import { LEVEL_NAMES, LEVEL_XP, MISSION_TYPE_LABELS } from "@/lib/constants";
import Navbar from "@/components/ui/Navbar";

export default function DashboardPage() {
  const { isAuthenticated, isLoading, user } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/login");
  }, [isAuthenticated, isLoading, router]);

  const { data: stats } = useQuery({
    queryKey: ["my-progress"],
    queryFn: () => progressApi.getMyProgress().then((r) => r.data),
    enabled: isAuthenticated,
  });

  const { data: recs } = useQuery({
    queryKey: ["recommendations"],
    queryFn: () => recommendApi.getRecommendations(3).then((r) => r.data),
    enabled: isAuthenticated,
  });

  if (isLoading) return (
    <div className="min-h-screen bg-cyber-bg flex items-center justify-center">
      <p className="text-cyber-green animate-pulse font-mono">Chargement...</p>
    </div>
  );

  const level = user?.level || 1;
  const totalXp = user?.total_xp || 0;
  const nextLevelXp = LEVEL_XP[level + 1] || LEVEL_XP[5];
  const currentLevelXp = LEVEL_XP[level] || 0;
  const xpProgress = nextLevelXp > currentLevelXp
    ? ((totalXp - currentLevelXp) / (nextLevelXp - currentLevelXp)) * 100
    : 100;

  return (
    <div className="min-h-screen bg-cyber-bg">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Bienvenue */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-cyber-text">
            Bienvenue, <span className="text-cyber-green">{user?.pseudo}</span>
          </h1>
          <p className="text-cyber-muted mt-1">Agent CSDF — {LEVEL_NAMES[level]}</p>
        </div>

        {/* Stats cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Niveau", value: level, icon: <Trophy size={20} className="text-cyber-gold" />, color: "text-cyber-gold" },
            { label: "XP Total", value: totalXp, icon: <Zap size={20} className="text-cyber-green" />, color: "text-cyber-green" },
            { label: "Missions", value: stats?.missions_completed || 0, icon: <Target size={20} className="text-cyber-cyan" />, color: "text-cyber-cyan" },
            { label: "Badges", value: stats?.badges_count || 0, icon: <Trophy size={20} className="text-yellow-400" />, color: "text-yellow-400" },
          ].map((s, i) => (
            <div key={i} className="cyber-card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-cyber-muted text-sm">{s.label}</span>
                {s.icon}
              </div>
              <p className={`text-3xl font-bold ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Barre XP */}
        <div className="cyber-card mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-cyber-text">
              Niveau {level} — {LEVEL_NAMES[level]}
            </span>
            {level < 5 && (
              <span className="text-xs text-cyber-muted">
                {totalXp} / {nextLevelXp} XP → Niveau {level + 1}
              </span>
            )}
          </div>
          <div className="w-full bg-cyber-bg3 rounded-full h-3">
            <div
              className="h-3 rounded-full bg-gradient-to-r from-cyber-green to-cyber-cyan transition-all duration-500"
              style={{ width: `${Math.min(100, xpProgress)}%` }}
            />
          </div>
          {level < 5 && (
            <p className="text-xs text-cyber-muted mt-1">
              {stats?.xp_to_next_level || 0} XP restants pour le niveau {level + 1}
            </p>
          )}
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Recommandations */}
          <div className="cyber-card">
            <h2 className="text-lg font-bold text-cyber-text mb-4 flex items-center gap-2">
              <Zap size={20} className="text-cyber-green" />
              Recommandé pour vous
            </h2>
            {recs?.recommendations?.length > 0 ? (
              <div className="space-y-3">
                {recs.recommendations.map((rec: { mission_id: number; mission_title: string; chapter_title: string; reason: string }) => (
                  <Link key={rec.mission_id} href={`/catalogue/missions/${rec.mission_id}`}
                    className="flex items-center justify-between p-3 bg-cyber-bg3 rounded-lg hover:border-cyber-green border border-transparent transition-colors group">
                    <div>
                      <p className="text-sm font-medium text-cyber-text group-hover:text-cyber-green transition-colors">
                        {rec.mission_title}
                      </p>
                      <p className="text-xs text-cyber-muted">{rec.chapter_title}</p>
                      <p className="text-xs text-cyber-cyan mt-0.5">{rec.reason}</p>
                    </div>
                    <ChevronRight size={16} className="text-cyber-muted group-hover:text-cyber-green" />
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-cyber-muted text-sm">
                Commencez votre première mission pour obtenir des recommandations !
              </p>
            )}
            <Link href="/catalogue" className="mt-4 block text-center text-cyber-cyan text-sm hover:underline">
              Voir toutes les missions →
            </Link>
          </div>

          {/* Temps de jeu */}
          <div className="cyber-card">
            <h2 className="text-lg font-bold text-cyber-text mb-4 flex items-center gap-2">
              <Clock size={20} className="text-cyber-cyan" />
              Statistiques
            </h2>
            <div className="space-y-3">
              {[
                { label: "Missions complétées", value: stats?.missions_completed || 0, color: "text-cyber-green" },
                { label: "Sessions totales", value: stats?.total_sessions || 0, color: "text-cyber-cyan" },
                { label: "Missions abandonnées", value: stats?.missions_abandoned || 0, color: "text-cyber-muted" },
                {
                  label: "Temps de jeu",
                  value: stats?.total_play_time_seconds
                    ? `${Math.floor(stats.total_play_time_seconds / 3600)}h ${Math.floor((stats.total_play_time_seconds % 3600) / 60)}min`
                    : "0h 0min",
                  color: "text-cyber-gold"
                },
              ].map((s, i) => (
                <div key={i} className="flex justify-between items-center py-2 border-b border-cyber-border last:border-0">
                  <span className="text-sm text-cyber-muted">{s.label}</span>
                  <span className={`font-bold ${s.color}`}>{s.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

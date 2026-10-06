"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Lock, CheckCircle, Play, Clock, Zap } from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";
import { catalogueApi } from "@/lib/api-client";
import { DIFFICULTY_LABELS, MISSION_TYPE_LABELS } from "@/lib/constants";
import Navbar from "@/components/ui/Navbar";
import type { Chapter, Mission } from "@/types";

export default function CataloguePage() {
  const { isAuthenticated, isLoading } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/login");
  }, [isAuthenticated, isLoading, router]);

  const { data, isLoading: chaptersLoading } = useQuery({
    queryKey: ["chapters"],
    queryFn: () => catalogueApi.getChapters().then((r) => r.data),
    enabled: isAuthenticated,
  });

  if (isLoading || chaptersLoading) return (
    <div className="min-h-screen bg-cyber-bg flex items-center justify-center">
      <p className="text-cyber-green animate-pulse font-mono">Chargement de la carte...</p>
    </div>
  );

  return (
    <div className="min-h-screen bg-cyber-bg">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-cyber-text">Carte du jeu</h1>
          <p className="text-cyber-muted mt-1">
            Niveau {data?.player_level} · {data?.total_xp} XP
          </p>
        </div>

        <div className="space-y-6">
          {data?.chapters?.map((chapter: Chapter) => (
            <div key={chapter.id}
              className={`cyber-card transition-all duration-200 ${
                chapter.is_unlocked
                  ? "border-cyber-border hover:border-cyber-green/50"
                  : "opacity-60 border-cyber-border"
              }`}>
              {/* Chapter header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${
                    chapter.is_unlocked ? "bg-cyber-green/10" : "bg-cyber-bg3"
                  }`}>
                    {chapter.is_unlocked
                      ? <Play size={20} className="text-cyber-green" />
                      : <Lock size={20} className="text-cyber-muted" />
                    }
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-cyber-muted">
                        Chapitre {chapter.order_num}
                      </span>
                      {!chapter.is_unlocked && (
                        <span className="text-xs bg-cyber-bg3 text-cyber-muted px-2 py-0.5 rounded-full border border-cyber-border">
                          Niveau {chapter.unlock_level} requis
                        </span>
                      )}
                    </div>
                    <h2 className={`text-lg font-bold mt-0.5 ${
                      chapter.is_unlocked ? "text-cyber-text" : "text-cyber-muted"
                    }`}>
                      {chapter.title}
                    </h2>
                    <p className="text-sm text-cyber-muted mt-1">{chapter.description}</p>
                  </div>
                </div>

                {/* Progress */}
                <div className="text-right min-w-[100px]">
                  <p className="text-sm font-bold text-cyber-green">
                    {chapter.completed_count}/{chapter.missions_count}
                  </p>
                  <p className="text-xs text-cyber-muted">missions</p>
                  <div className="w-24 bg-cyber-bg3 rounded-full h-1.5 mt-2 ml-auto">
                    <div
                      className="h-1.5 rounded-full bg-cyber-green transition-all"
                      style={{ width: `${chapter.completion_percentage}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Missions list */}
              {chapter.is_unlocked && chapter.missions?.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-4 pt-4 border-t border-cyber-border">
                  {chapter.missions.map((mission: Mission) => (
                    <Link
                      key={mission.id}
                      href={`/catalogue/missions/${mission.id}`}
                      className={`p-3 rounded-lg border transition-all group ${
                        mission.is_completed
                          ? "border-cyber-green/30 bg-cyber-green/5"
                          : "border-cyber-border bg-cyber-bg3 hover:border-cyber-cyan/50"
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="text-xs font-mono text-cyber-muted">
                          {String(chapter.order_num)}.{mission.order_num}
                        </span>
                        {mission.is_completed && (
                          <CheckCircle size={14} className="text-cyber-green flex-shrink-0" />
                        )}
                      </div>
                      <p className={`text-sm font-medium mb-2 ${
                        mission.is_completed
                          ? "text-cyber-green"
                          : "text-cyber-text group-hover:text-cyber-cyan"
                      }`}>
                        {mission.title}
                      </p>
                      <div className="flex items-center gap-3 text-xs text-cyber-muted">
                        <span className="flex items-center gap-1">
                          <Zap size={10} className="text-cyber-green" />
                          {mission.xp_reward} XP
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock size={10} />
                          {Math.floor(mission.time_limit_seconds / 60)} min
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-2">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          mission.difficulty === "beginner"
                            ? "difficulty-beginner"
                            : mission.difficulty === "intermediate"
                            ? "difficulty-intermediate"
                            : mission.difficulty === "advanced"
                            ? "difficulty-advanced"
                            : "difficulty-expert"
                        }`}>
                          {DIFFICULTY_LABELS[mission.difficulty]}
                        </span>
                        <span className="text-xs text-cyber-muted">
                          {MISSION_TYPE_LABELS[mission.mission_type]}
                        </span>
                      </div>
                      {mission.best_score !== null && (
                        <p className="text-xs text-cyber-green mt-2">
                          Meilleur score : {mission.best_score}/100
                        </p>
                      )}
                    </Link>
                  ))}
                </div>
              )}

              {/* Locked message */}
              {!chapter.is_unlocked && (
                <div className="mt-3 pt-3 border-t border-cyber-border text-center">
                  <p className="text-xs text-cyber-muted">
                    🔒 Atteignez le niveau {chapter.unlock_level} pour débloquer ce chapitre
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

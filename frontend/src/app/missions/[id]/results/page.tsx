"use client";

import { useEffect } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Trophy, Zap, Star, ArrowRight, RotateCcw } from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";
import { sessionsApi } from "@/lib/api-client";
import Navbar from "@/components/ui/Navbar";
import type { SessionResult } from "@/types";

export default function MissionResultsPage() {
  const { id } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session");
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuthStore();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.replace("/login");
    if (!sessionId) router.replace("/catalogue");
  }, [isAuthenticated, authLoading, sessionId, router]);

  const { data: result, isLoading } = useQuery({
    queryKey: ["session-results", sessionId],
    queryFn: () => sessionsApi.getResults(Number(sessionId)).then((r) => r.data as SessionResult),
    enabled: !!sessionId && isAuthenticated,
  });

  if (authLoading || isLoading) return (
    <div className="min-h-screen bg-cyber-bg flex items-center justify-center">
      <p className="text-cyber-green animate-pulse font-mono">Chargement des résultats...</p>
    </div>
  );

  if (!result) return null;

  const isCompleted = result.status === "completed";
  const scoreColor = result.score >= 80 ? "text-cyber-green" : result.score >= 50 ? "text-yellow-400" : "text-cyber-red";

  return (
    <div className="min-h-screen bg-cyber-bg">
      <Navbar />
      <main className="max-w-2xl mx-auto px-4 py-12">
        {/* Header résultat */}
        <div className="text-center mb-8 animate-fade-in">
          <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 ${
            isCompleted ? "bg-cyber-green/20 border-2 border-cyber-green" : "bg-cyber-red/20 border-2 border-cyber-red"
          }`}>
            {isCompleted
              ? <Trophy size={36} className="text-cyber-green" />
              : <span className="text-3xl">🏳️</span>
            }
          </div>
          <h1 className="text-2xl font-bold text-cyber-text mb-1">
            {isCompleted ? "Mission accomplie !" : "Mission terminée"}
          </h1>
          <p className="text-cyber-muted">{result.mission_title}</p>
        </div>

        {/* Score principal */}
        <div className="cyber-card text-center mb-6">
          <p className="text-cyber-muted text-sm mb-2">Score final</p>
          <p className={`text-6xl font-bold ${scoreColor}`}>
            {result.score}<span className="text-2xl text-cyber-muted">/100</span>
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="cyber-card text-center">
            <Zap size={20} className="text-cyber-green mx-auto mb-1" />
            <p className="text-2xl font-bold text-cyber-green">+{result.xp_earned}</p>
            <p className="text-xs text-cyber-muted">XP gagnés</p>
          </div>
          <div className="cyber-card text-center">
            <Star size={20} className="text-yellow-400 mx-auto mb-1" />
            <p className="text-2xl font-bold text-yellow-400">{result.hints_used}</p>
            <p className="text-xs text-cyber-muted">Indices utilisés</p>
          </div>
          <div className="cyber-card text-center">
            <p className="text-2xl font-bold text-cyber-cyan">{result.attempts}</p>
            <p className="text-xs text-cyber-muted">Tentatives</p>
          </div>
          <div className="cyber-card text-center">
            <p className="text-2xl font-bold text-cyber-text">
              {result.duration_seconds ? `${Math.floor(result.duration_seconds / 60)}min` : "—"}
            </p>
            <p className="text-xs text-cyber-muted">Durée</p>
          </div>
        </div>

        {/* Level up */}
        {result.level_up && (
          <div className="cyber-card border border-cyber-gold/50 bg-cyber-gold/5 text-center mb-6">
            <p className="text-2xl mb-1">🎉</p>
            <p className="font-bold text-cyber-gold">Niveau {result.level_up} atteint !</p>
          </div>
        )}

        {/* Nouveaux badges */}
        {result.new_badges?.length > 0 && (
          <div className="cyber-card mb-6">
            <p className="text-xs font-mono text-cyber-green mb-3">🏆 NOUVEAUX BADGES</p>
            <div className="space-y-2">
              {result.new_badges.map((badge) => (
                <div key={badge.badge_id} className="flex items-center gap-3 p-2 bg-cyber-bg3 rounded-lg">
                  <div className="w-8 h-8 bg-cyber-green/10 rounded-full flex items-center justify-center">
                    <Trophy size={16} className="text-cyber-green" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-cyber-text">{badge.name}</p>
                    <p className="text-xs text-cyber-muted">{badge.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Narration post-mission */}
        {result.narrative_outro && (
          <div className="cyber-card border-l-4 border-l-cyber-gold mb-6">
            <p className="text-xs text-cyber-gold font-mono mb-2">📖 SUITE DE L'HISTOIRE</p>
            <p className="text-sm text-cyber-text italic leading-relaxed">
              {result.narrative_outro}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <Link href="/catalogue" className="cyber-btn-secondary flex-1 text-center flex items-center justify-center gap-2">
            <RotateCcw size={16} /> Retour au catalogue
          </Link>
          <Link href="/dashboard" className="cyber-btn-primary flex-1 text-center flex items-center justify-center gap-2">
            Suite <ArrowRight size={16} />
          </Link>
        </div>
      </main>
    </div>
  );
}

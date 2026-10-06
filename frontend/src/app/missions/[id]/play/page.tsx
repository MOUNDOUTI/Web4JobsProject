"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Clock, Lightbulb, Flag, AlertTriangle } from "lucide-react";
import toast from "react-hot-toast";
import { useAuthStore } from "@/lib/auth-store";
import { sessionsApi, catalogueApi } from "@/lib/api-client";
import TerminalGame from "@/components/game/TerminalGame";
import QuizGame from "@/components/game/QuizGame";
import Navbar from "@/components/ui/Navbar";
import type { SessionStartResponse, HintResponse, SubmitSolutionResponse, QuizQuestion } from "@/types";

export default function MissionPlayPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuthStore();

  const [session, setSession] = useState<SessionStartResponse | null>(null);
  const [answer, setAnswer] = useState("");
  const [hints, setHints] = useState<string[]>([]);
  const [hintsUsed, setHintsUsed] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);
  const [result, setResult] = useState<SubmitSolutionResponse | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.replace("/login");
  }, [isAuthenticated, authLoading, router]);

  // Récupérer la fiche mission
  const { data: missionData } = useQuery({
    queryKey: ["mission", id],
    queryFn: () => catalogueApi.getMission(Number(id)).then((r) => r.data),
    enabled: !!id && isAuthenticated,
  });

  // Démarrer la session
  useEffect(() => {
    if (missionData && !session && !isStarting) {
      setIsStarting(true);
      sessionsApi.startMission(Number(id))
        .then((res) => {
          setSession(res.data);
          setTimeLeft(res.data.time_limit_seconds);
          toast.success("Mission démarrée !");
        })
        .catch((err) => {
          const msg = err?.response?.data?.message || "Impossible de démarrer la mission";
          toast.error(msg);
          router.back();
        });
    }
  }, [missionData, session, id, isStarting, router]);

  // Timer
  useEffect(() => {
    if (!session || timeLeft <= 0 || result) return;
    const interval = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearInterval(interval);
          toast.error("Temps écoulé !");
          router.replace(`/missions/${id}/results?session=${session.session_id}`);
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [session, result]);

  // Soumettre solution
  const submitMutation = useMutation({
    mutationFn: () => sessionsApi.submitSolution(session!.session_id, answer),
    onSuccess: (res) => {
      const data: SubmitSolutionResponse = res.data;
      setResult(data);
      if (data.correct) {
        toast.success("🎉 Correct ! Mission accomplie !");
        setTimeout(() => {
          router.replace(`/missions/${id}/results?session=${session!.session_id}`);
        }, 1500);
      } else {
        toast.error(`Incorrect (tentative ${data.attempts})`);
        setResult(null);
      }
    },
    onError: (err: unknown) => {
      const error = err as { response?: { data?: { message?: string } } };
      toast.error(error?.response?.data?.message || "Erreur lors de la soumission");
    },
  });

  // Demander un indice
  const hintMutation = useMutation({
    mutationFn: () => sessionsApi.getHint(session!.session_id),
    onSuccess: (res) => {
      const data: HintResponse = res.data;
      setHints((prev) => [...prev, data.hint]);
      setHintsUsed(data.hint_index + 1);
      toast(`💡 Indice ${data.hint_index + 1} (-${data.score_penalty} pts)`, { icon: "💡" });
    },
    onError: () => toast.error("Plus d'indices disponibles"),
  });

  // Abandonner
  const abandonMutation = useMutation({
    mutationFn: () => sessionsApi.abandon(session!.session_id),
    onSuccess: () => {
      toast("Session abandonnée", { icon: "🏳️" });
      router.replace("/catalogue");
    },
  });

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  if (authLoading || !missionData) return (
    <div className="min-h-screen bg-cyber-bg flex items-center justify-center">
      <p className="text-cyber-green animate-pulse font-mono">Initialisation...</p>
    </div>
  );

  const maxHints = session?.max_hints || 0;
  const questions = missionData.public_config?.questions as QuizQuestion[] || [];

  return (
    <div className="min-h-screen bg-cyber-bg">
      <Navbar />

      {/* Mission bar */}
      <div className="border-b border-cyber-border bg-cyber-bg2 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <div>
            <p className="text-xs text-cyber-muted font-mono">{missionData.chapter_title}</p>
            <h1 className="font-bold text-cyber-text">{missionData.title}</h1>
          </div>
          <div className="flex items-center gap-6">
            {/* Timer */}
            <div className={`flex items-center gap-1.5 font-mono text-sm ${
              timeLeft <= 60 ? "text-cyber-red animate-pulse" : "text-cyber-cyan"
            }`}>
              <Clock size={16} />
              {formatTime(timeLeft)}
            </div>
            {/* Hints */}
            <div className="flex items-center gap-1.5 text-sm text-cyber-muted">
              <Lightbulb size={16} />
              {hintsUsed}/{maxHints} indices
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Colonne gauche : interface de jeu */}
        <div className="lg:col-span-2 space-y-4">
          {/* Briefing narratif */}
          {session?.narrative_intro && (
            <div className="cyber-card border-l-4 border-l-cyber-gold">
              <p className="text-xs text-cyber-gold font-mono mb-1">📨 BRIEFING</p>
              <p className="text-sm text-cyber-text leading-relaxed italic">
                {session.narrative_intro}
              </p>
            </div>
          )}

          {/* Interface selon le type */}
          {session && missionData.mission_type === "terminal" && (
            <TerminalGame sessionId={session.session_id} />
          )}

          {session && missionData.mission_type === "quiz" && questions.length > 0 && (
            <QuizGame
              questions={questions}
              timePerQuestion={missionData.public_config?.time_per_question as number || 30}
              onAnswer={(qId, idx) => console.log("Réponse", qId, idx)}
              onComplete={(ans) => setAnswer(ans)}
            />
          )}

          {/* Indices affichés */}
          {hints.length > 0 && (
            <div className="space-y-2">
              {hints.map((hint, i) => (
                <div key={i} className="cyber-card border-l-4 border-l-cyber-cyan text-sm">
                  <p className="text-cyber-cyan font-mono text-xs mb-1">💡 Indice {i + 1}</p>
                  <p className="text-cyber-text">{hint}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Colonne droite : soumission */}
        <div className="space-y-4">
          {/* Objectif */}
          <div className="cyber-card">
            <p className="text-xs text-cyber-green font-mono mb-2">🎯 OBJECTIF</p>
            <p className="text-sm text-cyber-text leading-relaxed">{missionData.description}</p>
            <div className="flex flex-wrap gap-2 mt-3">
              {missionData.skills_targeted?.map((s: string) => (
                <span key={s} className="text-xs bg-cyber-bg3 text-cyber-cyan border border-cyber-border px-2 py-0.5 rounded-full">
                  {s}
                </span>
              ))}
            </div>
          </div>

          {/* Soumission */}
          {missionData.mission_type !== "quiz" && (
            <div className="cyber-card">
              <p className="text-xs text-cyber-green font-mono mb-3">🚩 SOUMISSION</p>
              <input
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && session && submitMutation.mutate()}
                placeholder="FLAG{votre_réponse}"
                className="cyber-input font-mono text-sm mb-3"
              />
              <button
                onClick={() => session && submitMutation.mutate()}
                disabled={!answer || submitMutation.isPending || !session}
                className="cyber-btn-primary w-full flex items-center justify-center gap-2"
              >
                <Flag size={16} />
                {submitMutation.isPending ? "Validation..." : "Soumettre"}
              </button>
            </div>
          )}

          {missionData.mission_type === "quiz" && answer === "completed" && (
            <div className="cyber-card">
              <p className="text-xs text-cyber-green font-mono mb-3">🚩 VALIDATION</p>
              <button
                onClick={() => session && submitMutation.mutate()}
                disabled={submitMutation.isPending}
                className="cyber-btn-primary w-full"
              >
                {submitMutation.isPending ? "Validation..." : "Valider le quiz →"}
              </button>
            </div>
          )}

          {/* Actions */}
          <div className="space-y-2">
            {hintsUsed < maxHints && (
              <button
                onClick={() => hintMutation.mutate()}
                disabled={hintMutation.isPending || !session}
                className="cyber-btn-secondary w-full flex items-center justify-center gap-2 text-sm"
              >
                <Lightbulb size={16} />
                Indice ({maxHints - hintsUsed} restants) — {10 * (hintsUsed + 1)} pts
              </button>
            )}
            <button
              onClick={() => {
                if (confirm("Abandonner cette mission ?")) abandonMutation.mutate();
              }}
              className="w-full flex items-center justify-center gap-2 text-sm text-cyber-muted hover:text-cyber-red transition-colors py-2"
            >
              <AlertTriangle size={16} />
              Abandonner
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

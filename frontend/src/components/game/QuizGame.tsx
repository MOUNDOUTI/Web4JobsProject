"use client";

import { useState, useEffect } from "react";
import { CheckCircle, XCircle, Clock } from "lucide-react";
import type { QuizQuestion } from "@/types";

interface QuizGameProps {
  questions: QuizQuestion[];
  timePerQuestion?: number;
  onAnswer: (questionId: number, answerIndex: number) => void;
  onComplete: (answer: string) => void;
}

export default function QuizGame({
  questions,
  timePerQuestion = 30,
  onAnswer,
  onComplete,
}: QuizGameProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [answered, setAnswered] = useState<{ correct: boolean; index: number }[]>([]);
  const [timeLeft, setTimeLeft] = useState(timePerQuestion);
  const [isComplete, setIsComplete] = useState(false);

  const currentQuestion = questions[currentIndex];
  const totalQuestions = questions.length;

  useEffect(() => {
    if (selected !== null || isComplete) return;
    const interval = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearInterval(interval);
          handleSelect(-1); // Temps écoulé
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [currentIndex, selected, isComplete]);

  const handleSelect = (index: number) => {
    if (selected !== null) return;
    setSelected(index);
    onAnswer(currentQuestion.id, index);
    setAnswered((prev) => [...prev, { correct: false, index }]);

    setTimeout(() => {
      if (currentIndex + 1 >= totalQuestions) {
        setIsComplete(true);
        onComplete("completed");
      } else {
        setCurrentIndex((i) => i + 1);
        setSelected(null);
        setTimeLeft(timePerQuestion);
      }
    }, 1200);
  };

  if (isComplete) {
    return (
      <div className="cyber-card text-center py-12">
        <CheckCircle size={48} className="text-cyber-green mx-auto mb-4" />
        <h3 className="text-xl font-bold text-cyber-text mb-2">Quiz terminé !</h3>
        <p className="text-cyber-muted">Soumettez votre réponse pour valider la mission.</p>
      </div>
    );
  }

  if (!currentQuestion) return null;

  const timerPercent = (timeLeft / timePerQuestion) * 100;

  return (
    <div className="space-y-4">
      {/* Progression */}
      <div className="flex items-center justify-between text-sm">
        <span className="text-cyber-muted">
          Question {currentIndex + 1} / {totalQuestions}
        </span>
        <span className={`flex items-center gap-1 font-mono ${
          timeLeft <= 10 ? "text-cyber-red animate-pulse" : "text-cyber-cyan"
        }`}>
          <Clock size={14} /> {timeLeft}s
        </span>
      </div>

      {/* Timer bar */}
      <div className="w-full bg-cyber-bg3 rounded-full h-1.5">
        <div
          className={`h-1.5 rounded-full transition-all ${
            timeLeft <= 10 ? "bg-cyber-red" : "bg-cyber-cyan"
          }`}
          style={{ width: `${timerPercent}%` }}
        />
      </div>

      {/* Question */}
      <div className="cyber-card">
        <p className="text-cyber-text font-medium leading-relaxed">
          {currentQuestion.text}
        </p>
      </div>

      {/* Options */}
      <div className="grid grid-cols-1 gap-3">
        {currentQuestion.options.map((option, i) => (
          <button
            key={i}
            onClick={() => handleSelect(i)}
            disabled={selected !== null}
            className={`w-full text-left p-4 rounded-lg border transition-all font-mono text-sm
              ${selected === null
                ? "border-cyber-border bg-cyber-bg3 hover:border-cyber-cyan hover:bg-cyber-cyan/5 text-cyber-text cursor-pointer"
                : selected === i
                  ? "border-cyber-cyan bg-cyber-cyan/10 text-cyber-cyan"
                  : "border-cyber-border bg-cyber-bg3 text-cyber-muted cursor-not-allowed"
              }
            `}
          >
            <span className="text-cyber-muted mr-3">{String.fromCharCode(65 + i)}.</span>
            {option}
          </button>
        ))}
      </div>

      {/* Points dots */}
      <div className="flex justify-center gap-2 pt-2">
        {questions.map((_, i) => (
          <div key={i} className={`w-2 h-2 rounded-full transition-colors ${
            i < currentIndex ? "bg-cyber-green"
            : i === currentIndex ? "bg-cyber-cyan"
            : "bg-cyber-border"
          }`} />
        ))}
      </div>
    </div>
  );
}

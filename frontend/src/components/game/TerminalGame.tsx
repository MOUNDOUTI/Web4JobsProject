"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { sessionsApi } from "@/lib/api-client";
import toast from "react-hot-toast";

interface TerminalGameProps {
  sessionId: number;
  onSolutionFound?: (answer: string) => void;
}

interface TerminalLine {
  type: "command" | "output" | "system" | "error";
  content: string;
}

export default function TerminalGame({ sessionId, onSolutionFound }: TerminalGameProps) {
  const [history, setHistory] = useState<TerminalLine[]>([
    { type: "system", content: "CSDF Terminal v2.1 — Connexion sécurisée établie" },
    { type: "system", content: "Tapez 'help' pour voir les commandes disponibles." },
    { type: "system", content: "" },
  ]);
  const [input, setInput] = useState("");
  const [cmdHistory, setCmdHistory] = useState<string[]>([]);
  const [cmdIndex, setCmdIndex] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const addLines = (lines: TerminalLine[]) => {
    setHistory((prev) => [...prev, ...lines]);
  };

  const handleCommand = async () => {
    const cmd = input.trim();
    if (!cmd) return;

    addLines([{ type: "command", content: `$ ${cmd}` }]);
    setCmdHistory((prev) => [cmd, ...prev]);
    setCmdIndex(-1);
    setInput("");
    setIsLoading(true);

    try {
      const res = await sessionsApi.sendCommand(sessionId, cmd);
      const output = res.data.output;

      if (output === "") {
        addLines([{ type: "output", content: "" }]);
      } else {
        const lines = output.split("\n").map((line: string) => ({
          type: "output" as const,
          content: line,
        }));
        addLines(lines);
      }
    } catch {
      addLines([{ type: "error", content: "Erreur de connexion au serveur." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleCommand();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const newIndex = Math.min(cmdIndex + 1, cmdHistory.length - 1);
      setCmdIndex(newIndex);
      setInput(cmdHistory[newIndex] || "");
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      const newIndex = Math.max(cmdIndex - 1, -1);
      setCmdIndex(newIndex);
      setInput(newIndex === -1 ? "" : cmdHistory[newIndex]);
    } else if (e.key === "Tab") {
      e.preventDefault();
    }
  };

  const getLineColor = (type: TerminalLine["type"]) => {
    switch (type) {
      case "command": return "text-cyber-green font-bold";
      case "output":  return "text-cyber-text";
      case "system":  return "text-cyber-cyan";
      case "error":   return "text-cyber-red";
    }
  };

  return (
    <div
      className="bg-cyber-terminal border border-cyber-border rounded-lg h-[450px] flex flex-col font-mono text-sm"
      onClick={() => inputRef.current?.focus()}
    >
      {/* Terminal header */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-cyber-border bg-cyber-bg2 rounded-t-lg">
        <div className="w-3 h-3 rounded-full bg-cyber-red" />
        <div className="w-3 h-3 rounded-full bg-yellow-400" />
        <div className="w-3 h-3 rounded-full bg-cyber-green" />
        <span className="ml-2 text-xs text-cyber-muted">agent_chen@csdf — terminal</span>
      </div>

      {/* Output area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-0.5">
        {history.map((line, i) => (
          <div key={i} className={`leading-5 whitespace-pre-wrap ${getLineColor(line.type)}`}>
            {line.content}
          </div>
        ))}
        {isLoading && (
          <div className="text-cyber-muted animate-pulse">Traitement...</div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="flex items-center gap-2 px-4 py-3 border-t border-cyber-border">
        <span className="text-cyber-green font-bold flex-shrink-0">$</span>
        <input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          className="flex-1 bg-transparent text-cyber-text outline-none caret-cyber-green placeholder-cyber-border"
          placeholder={isLoading ? "..." : "tapez une commande..."}
          autoComplete="off"
          spellCheck={false}
        />
        <span className="text-cyber-green animate-[blink_1s_step-end_infinite]">█</span>
      </div>
    </div>
  );
}

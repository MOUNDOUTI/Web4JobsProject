export const LEVEL_NAMES: Record<number, string> = {
  1: "Recrue",
  2: "Analyste Junior",
  3: "Investigateur Cyber",
  4: "Expert en Sécurité",
  5: "Agent Élite CSDF",
};

export const LEVEL_XP: Record<number, number> = {
  1: 0,
  2: 200,
  3: 500,
  4: 1000,
  5: 2000,
};

export const DIFFICULTY_LABELS: Record<string, string> = {
  beginner: "Débutant",
  intermediate: "Intermédiaire",
  advanced: "Avancé",
  expert: "Expert",
};

export const MISSION_TYPE_LABELS: Record<string, string> = {
  terminal: "Terminal",
  log_analysis: "Analyse de logs",
  quiz: "Quiz",
  network_config: "Config réseau",
  code_review: "Analyse de code",
  cryptography: "Cryptographie",
  incident_report: "Rapport d'incident",
};

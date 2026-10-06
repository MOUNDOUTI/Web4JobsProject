// =============================================================================
// CyberLearn — Types TypeScript globaux
// =============================================================================

// ── Auth ──────────────────────────────────────────────────────────────────────
export interface User {
  id: number;
  email: string;
  pseudo: string;
  level: number;
  total_xp: number;
  role: "user" | "admin";
  is_verified_18: boolean;
  avatar_url: string | null;
  bio: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  pseudo: string;
  role: string;
  level: number;
  total_xp: number;
}

export interface RegisterRequest {
  email: string;
  pseudo: string;
  password: string;
  password_confirm: string;
  birth_date: string;
  accept_terms: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

// ── Chapitres et Missions ─────────────────────────────────────────────────────
export interface Mission {
  id: number;
  title: string;
  order_num: number;
  mission_type: MissionType;
  difficulty: DifficultyLevel;
  description: string;
  narrative_intro: string | null;
  skills_targeted: string[] | null;
  xp_reward: number;
  time_limit_seconds: number;
  max_hints: number;
  chapter_id: number;
  chapter_title: string;
  is_unlocked: boolean;
  is_completed: boolean;
  best_score: number | null;
  public_config: Record<string, unknown>;
}

export interface Chapter {
  id: number;
  title: string;
  order_num: number;
  description: string;
  narrative_context: string | null;
  unlock_level: number;
  cover_image_url: string | null;
  is_unlocked: boolean;
  missions_count: number;
  completed_count: number;
  completion_percentage: number;
  missions: Mission[];
}

export type MissionType =
  | "terminal"
  | "log_analysis"
  | "quiz"
  | "network_config"
  | "code_review"
  | "cryptography"
  | "incident_report";

export type DifficultyLevel = "beginner" | "intermediate" | "advanced" | "expert";

// ── Sessions de jeu ───────────────────────────────────────────────────────────
export interface SessionStartResponse {
  session_id: number;
  mission_id: number;
  mission_title: string;
  mission_type: MissionType;
  narrative_intro: string;
  time_limit_seconds: number;
  max_hints: number;
  started_at: string;
}

export interface TerminalCommandResponse {
  command: string;
  output: string;
  session_id: number;
}

export interface SubmitSolutionResponse {
  correct: boolean;
  message: string;
  explanation: string | null;
  score: number;
  attempts: number;
  session_completed: boolean;
  xp_earned?: number;
  new_badges?: Badge[];
  level_up?: number | null;
}

export interface HintResponse {
  hint: string;
  hint_index: number;
  hints_remaining: number;
  score_penalty: number;
}

export interface SessionResult {
  session_id: number;
  mission_id: number;
  mission_title: string;
  status: string;
  score: number;
  max_score: number;
  score_percentage: number;
  xp_earned: number;
  hints_used: number;
  attempts: number;
  duration_seconds: number | null;
  narrative_outro: string | null;
  new_badges: Badge[];
  level_up: number | null;
}

// ── Progression ───────────────────────────────────────────────────────────────
export interface Badge {
  badge_id: number;
  name: string;
  description: string;
  icon_url: string | null;
  earned_at?: string;
}

export interface PlayerStats {
  user_id: number;
  pseudo: string;
  level: number;
  total_xp: number;
  xp_to_next_level: number;
  missions_completed: number;
  missions_abandoned: number;
  total_sessions: number;
  total_play_time_seconds: number;
  badges_count: number;
  current_level_name: string;
  next_level: number | null;
  next_level_name: string | null;
}

export interface Recommendation {
  mission_id: number;
  mission_title: string;
  chapter_title: string;
  reason: string;
  priority: number;
  session_id: number | null;
}

// ── Quiz ──────────────────────────────────────────────────────────────────────
export interface QuizQuestion {
  id: number;
  text: string;
  options: string[];
}

// ── API Error ─────────────────────────────────────────────────────────────────
export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

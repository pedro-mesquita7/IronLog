export interface Equipment {
  equipment_id: string;
  name: string;
  equipment_type: 'bar' | 'plate' | 'machine';
  weight_kg: number;
  quantity?: number;
  settings_schema?: Record<string, unknown> | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface Exercise {
  exercise_id: string;
  name: string;
  muscle_group: 'chest' | 'back' | 'legs' | 'shoulders' | 'arms' | 'core' | 'full_body';
  default_bar_id?: string | null;
  has_plate_calculator: boolean;
  is_unilateral: boolean;
  weak_side: 'left' | 'right' | null;
  rest_timer_seconds: 60 | 120 | 180;
  machine_settings?: Record<string, unknown> | null;
  replacement_exercise_ids: string[];
  notes?: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface Plan {
  plan_id: string;
  name: string;
  split_type?: string | null;
  is_active: boolean;
  days?: PlanDay[];
  created_at: string;
  updated_at: string;
}

export interface PlanDay {
  day_number: number;
  day_name: string;
  exercises: PlanExercise[];
}

export interface PlanExercise {
  exercise_id: string;
  order: number;
  target_sets: number;
  target_reps: string;
  set_type: 'working' | 'backoff';
}

export interface Session {
  session_id: string;
  plan_id: string;
  plan_day_number: number;
  date: string;
  status: 'in_progress' | 'completed';
  started_at: string;
  completed_at: string | null;
  notes: string | null;
  created_at: string;
}

export interface SessionExercise {
  exercise_id: string;
  name: string;
  order: number;
  target_sets: number;
  target_reps: string;
  set_type: string;
  is_unilateral: boolean;
  weak_side: string | null;
  has_plate_calculator: boolean;
  rest_timer_seconds: number;
  notes: string | null;
  warmup: {
    warmup_50?: { weight_kg: number; reps: string };
    warmup_75?: { weight_kg: number; reps: string };
  } | null;
  last_working_weight_kg: number | null;
  machine_settings: Record<string, unknown> | null;
  replacement_exercise_ids?: string[];
}

export interface WorkoutSet {
  set_id: string;
  session_id: string;
  exercise_id: string;
  original_exercise_id: string | null;
  set_type: 'warmup_50' | 'warmup_75' | 'working' | 'backoff';
  set_order: number;
  weight_kg: number;
  reps: number;
  rir: number;
  is_weight_pr: boolean;
  is_e1rm_pr: boolean;
  estimated_1rm: number;
  timestamp: string;
}

export interface SessionExerciseNote {
  session_id: string;
  exercise_id: string;
  note_text: string;
  created_at: string;
}

export interface Correction {
  correction_id: string;
  set_id: string;
  session_id: string;
  field: 'weight_kg' | 'reps' | 'rir';
  old_value: unknown;
  new_value: unknown;
  reason: string | null;
  created_at: string;
}

export interface StartSessionResponse {
  session_id: string;
  status: string;
  exercises: SessionExercise[];
}

export interface SeedResponse {
  seeded: boolean;
  equipment_count?: number;
  exercise_count?: number;
  plan_id?: string;
  message: string;
}

export interface ProgressionPoint {
  week_start: string;
  max_weight_kg: string;
  avg_weight_kg: string;
  weekly_total_load: string;
  max_estimated_1rm: string;
  total_sets: string;
  weight_prs: string;
  e1rm_prs: string;
}

export interface RecoveryCorrelationPoint {
  date: string;
  recovery_score: string;
  hrv_rmssd: string;
  resting_heart_rate: string;
  session_total_load: string;
  total_sets: string;
  weight_prs: string;
  duration_minutes: string;
}

export interface PRRecord {
  timestamp: string;
  exercise_id: string;
  exercise_name: string;
  weight_kg: string;
  estimated_1rm: string;
  reps: string;
  is_weight_pr: string;
  is_e1rm_pr: string;
}

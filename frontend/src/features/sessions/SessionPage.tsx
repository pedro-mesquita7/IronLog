import { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { apiFetch } from '../../shared/api';
import type { SessionExercise, WorkoutSet, Session, Equipment, Exercise } from '../../shared/types';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { ExercisePanel } from './ExercisePanel';
import styles from './SessionPage.module.css';

export function SessionPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<Session | null>(null);
  const [exercises, setExercises] = useState<SessionExercise[]>([]);
  const [sets, setSets] = useState<WorkoutSet[]>([]);
  const [activeIdx, setActiveIdx] = useState(0);
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [allExercises, setAllExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [showComplete, setShowComplete] = useState(false);

  const loadSession = useCallback(async () => {
    const [sessionRes, eqRes, exRes] = await Promise.all([
      apiFetch<{ session: Session & { sets?: WorkoutSet[]; exercise_notes?: unknown[] } }>(`/sessions/${id}`),
      apiFetch<{ equipment: Equipment[] }>('/equipment'),
      apiFetch<{ exercises: Exercise[] }>('/exercises'),
    ]);

    setSession(sessionRes.session);
    // Sets are nested inside the session object from GET /api/sessions/{id}
    setSets(sessionRes.session.sets || []);
    setEquipment(eqRes.equipment);
    setAllExercises(exRes.exercises);
  }, [id]);

  useEffect(() => {
    // Restore exercises from sessionStorage (saved by SessionStartPage or this component)
    const stored = sessionStorage.getItem(`ironlog_session_${id}`);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (parsed.exercises?.length > 0) {
          setExercises(parsed.exercises);
        }
      } catch { /* ignore */ }
    }

    loadSession()
      .then(() => {
        // If exercises still empty after load, rebuild from plan
        setExercises((prev) => {
          if (prev.length > 0) return prev;
          // Fallback: no sessionStorage and no exercises in GET response
          // This happens on page refresh — we need to re-fetch from plan
          return prev;
        });
      })
      .finally(() => setLoading(false));
  }, [loadSession, id]);

  // If exercises are empty after loading, rebuild from plan data
  useEffect(() => {
    if (loading || exercises.length > 0 || !session || allExercises.length === 0) return;

    // Rebuild exercise list from plan
    apiFetch<{ plan: { days?: Array<{ day_number: number; exercises: Array<{ exercise_id: string; order: number; target_sets: number; target_reps: string; set_type: string }> }> } }>(`/plans/${session.plan_id}`)
      .then((res) => {
        const day = res.plan.days?.find((d) => d.day_number === session.plan_day_number);
        if (!day) return;
        const rebuilt: SessionExercise[] = day.exercises.map((pe) => {
          const ex = allExercises.find((e) => e.exercise_id === pe.exercise_id);
          return {
            exercise_id: pe.exercise_id,
            name: ex?.name || pe.exercise_id,
            order: pe.order,
            target_sets: pe.target_sets,
            target_reps: pe.target_reps,
            set_type: pe.set_type,
            is_unilateral: ex?.is_unilateral || false,
            weak_side: ex?.weak_side || null,
            has_plate_calculator: ex?.has_plate_calculator || false,
            rest_timer_seconds: ex?.rest_timer_seconds || 120,
            notes: ex?.notes || null,
            warmup: null,
            last_working_weight_kg: null,
            machine_settings: ex?.machine_settings || null,
            replacement_exercise_ids: ex?.replacement_exercise_ids,
          };
        });
        setExercises(rebuilt);
      });
  }, [loading, exercises.length, session, allExercises]);

  // Store exercise data in sessionStorage so we don't lose it on refresh
  useEffect(() => {
    if (exercises.length > 0 && id) {
      sessionStorage.setItem(`ironlog_session_${id}`, JSON.stringify({ exercises }));
    }
  }, [exercises, id]);

  const handleSetAdded = (newSet: WorkoutSet) => {
    setSets((prev) => [...prev, newSet]);
  };

  const handleSetUpdated = (updated: WorkoutSet) => {
    setSets((prev) => prev.map((s) => (s.set_id === updated.set_id ? updated : s)));
  };

  const handleSetDeleted = (setId: string) => {
    setSets((prev) => prev.filter((s) => s.set_id !== setId));
  };

  const handleComplete = async () => {
    await apiFetch(`/sessions/${id}/complete`, { method: 'PUT' });
    sessionStorage.removeItem(`ironlog_session_${id}`);
    navigate('/sessions', { replace: true });
  };

  const handleSwapExercise = (exIdx: number, newExerciseId: string) => {
    const newEx = allExercises.find((e) => e.exercise_id === newExerciseId);
    if (!newEx) return;
    setExercises((prev) => {
      const updated = [...prev];
      const old = updated[exIdx];
      updated[exIdx] = {
        ...old,
        exercise_id: newExerciseId,
        name: newEx.name,
        is_unilateral: newEx.is_unilateral,
        weak_side: newEx.weak_side,
        has_plate_calculator: newEx.has_plate_calculator,
        rest_timer_seconds: newEx.rest_timer_seconds,
        notes: newEx.notes || null,
        replacement_exercise_ids: newEx.replacement_exercise_ids,
      };
      return updated;
    });
  };

  if (loading) return <LoadingSpinner />;
  if (!session) return <p>Session not found</p>;

  const isCompleted = session.status === 'completed';
  const activeExercise = exercises[activeIdx];

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>{isCompleted ? 'Session' : 'Workout'}</h1>
        <span className={styles.date}>{session.date}</span>
      </div>

      {/* Exercise tabs */}
      <div className={styles.tabs}>
        {exercises.map((ex, i) => {
          const exSets = sets.filter((s) => s.exercise_id === ex.exercise_id);
          return (
            <button
              key={`${ex.exercise_id}-${i}`}
              onClick={() => setActiveIdx(i)}
              className={`${styles.tab} ${i === activeIdx ? styles.activeTab : ''}`}
            >
              <span className={styles.tabNum}>{ex.order}</span>
              <span className={styles.tabName}>{ex.name}</span>
              {exSets.length > 0 && (
                <span className={styles.tabSets}>{exSets.length}/{ex.target_sets}</span>
              )}
            </button>
          );
        })}
      </div>

      {/* Active exercise panel */}
      {activeExercise && (
        <ExercisePanel
          sessionId={id!}
          exercise={activeExercise}
          exerciseIndex={activeIdx}
          sets={sets.filter((s) => s.exercise_id === activeExercise.exercise_id)}
          equipment={equipment}
          allExercises={allExercises}
          isCompleted={isCompleted}
          onSetAdded={handleSetAdded}
          onSetUpdated={handleSetUpdated}
          onSetDeleted={handleSetDeleted}
          onSwap={(newId) => handleSwapExercise(activeIdx, newId)}
          originalExerciseId={exercises[activeIdx]?.exercise_id}
        />
      )}

      {/* Navigation */}
      <div className={styles.nav}>
        <button
          onClick={() => setActiveIdx(Math.max(0, activeIdx - 1))}
          disabled={activeIdx === 0}
          className={styles.navBtn}
        >Prev</button>

        {!isCompleted && (
          <button onClick={() => setShowComplete(true)} className={styles.completeBtn}>
            Complete Session
          </button>
        )}

        <button
          onClick={() => setActiveIdx(Math.min(exercises.length - 1, activeIdx + 1))}
          disabled={activeIdx === exercises.length - 1}
          className={styles.navBtn}
        >Next</button>
      </div>

      {showComplete && (
        <ConfirmDialog
          message="Complete this session? It will become read-only."
          onConfirm={handleComplete}
          onCancel={() => setShowComplete(false)}
        />
      )}
    </div>
  );
}

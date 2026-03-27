import { useEffect, useState, useCallback, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { apiFetch } from '../../shared/api';
import type { SessionExercise, WorkoutSet, Session, Equipment, Exercise, SessionExerciseNote } from '../../shared/types';
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
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [allExercises, setAllExercises] = useState<Exercise[]>([]);
  const [exerciseNotes, setExerciseNotes] = useState<SessionExerciseNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [showComplete, setShowComplete] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [planDayName, setPlanDayName] = useState<string | null>(null);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  const loadSession = useCallback(async () => {
    const [sessionRes, eqRes, exRes] = await Promise.all([
      apiFetch<{ session: Session & { sets?: WorkoutSet[]; exercise_notes?: SessionExerciseNote[] } }>(`/sessions/${id}`),
      apiFetch<{ equipment: Equipment[] }>('/equipment'),
      apiFetch<{ exercises: Exercise[] }>('/exercises'),
    ]);

    setSession(sessionRes.session);
    setSets(sessionRes.session.sets || []);
    setEquipment(eqRes.equipment);
    setAllExercises(exRes.exercises);
    setExerciseNotes(sessionRes.session.exercise_notes || []);

    // Fetch plan name
    if (sessionRes.session.plan_id) {
      try {
        const planRes = await apiFetch<{ plan: { name: string; days?: Array<{ day_number: number; day_name: string }> } }>(`/plans/${sessionRes.session.plan_id}`);
        const day = planRes.plan.days?.find((d) => d.day_number === sessionRes.session.plan_day_number);
        setPlanDayName(day?.day_name || planRes.plan.name);
      } catch { /* ignore */ }
    }
  }, [id]);

  useEffect(() => {
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
        setExercises((prev) => prev);
      })
      .finally(() => setLoading(false));
  }, [loadSession, id]);

  // Rebuild exercises from plan if empty
  useEffect(() => {
    if (loading || exercises.length > 0 || !session || allExercises.length === 0) return;

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
            suggested_weight_kg: null,
            suggested_reps: null,
            machine_settings: ex?.machine_settings || null,
            replacement_exercise_ids: ex?.replacement_exercise_ids,
          };
        });
        setExercises(rebuilt);
      });
  }, [loading, exercises.length, session, allExercises]);

  // Persist exercises to sessionStorage
  useEffect(() => {
    if (exercises.length > 0 && id) {
      sessionStorage.setItem(`ironlog_session_${id}`, JSON.stringify({ exercises }));
    }
  }, [exercises, id]);

  // Auto-expand first unfinished exercise
  useEffect(() => {
    if (expandedIdx !== null || exercises.length === 0) return;
    const idx = exercises.findIndex((ex) => {
      const exSets = sets.filter((s) => s.exercise_id === ex.exercise_id);
      return exSets.length < ex.target_sets;
    });
    setExpandedIdx(idx >= 0 ? idx : 0);
  }, [exercises, sets, expandedIdx]);

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

  const handleDelete = async () => {
    await apiFetch(`/sessions/${id}`, { method: 'DELETE' });
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

  const handleNoteAdded = (note: SessionExerciseNote) => {
    setExerciseNotes((prev) => {
      const filtered = prev.filter((n) => !(n.exercise_id === note.exercise_id));
      return [...filtered, note];
    });
  };

  const setsByExercise = useMemo(() => {
    const map = new Map<string, WorkoutSet[]>();
    for (const s of sets) {
      const arr = map.get(s.exercise_id);
      if (arr) arr.push(s);
      else map.set(s.exercise_id, [s]);
    }
    return map;
  }, [sets]);

  if (loading) return <LoadingSpinner />;
  if (!session) return <p>Session not found</p>;

  const isCompleted = session.status === 'completed';

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1>{planDayName || (isCompleted ? 'Session' : 'Workout')}</h1>
          <span className={styles.date}>{session.date}</span>
        </div>
        {isCompleted && (
          <button onClick={() => setShowDelete(true)} className={styles.deleteBtn} title="Delete session">
            &#128465;
          </button>
        )}
      </div>

      {/* All exercises in vertical scroll */}
      {exercises.map((ex, i) => {
        const exSets = setsByExercise.get(ex.exercise_id) || [];
        const isExpanded = expandedIdx === i;
        const exNote = exerciseNotes.find((n) => n.exercise_id === ex.exercise_id);

        return (
          <div key={`${ex.exercise_id}-${i}`} className={styles.section}>
            <button
              className={`${styles.sectionHeader} ${isExpanded ? styles.expanded : ''}`}
              onClick={() => setExpandedIdx(isExpanded ? null : i)}
            >
              <span className={styles.sectionOrder}>{ex.order}</span>
              <span className={styles.sectionName}>{ex.name}</span>
              <span className={styles.sectionProgress}>
                {exSets.length}/{ex.target_sets}
              </span>
              <span className={styles.chevron}>{isExpanded ? '\u25B2' : '\u25BC'}</span>
            </button>

            {isExpanded && (
              <ExercisePanel
                sessionId={id!}
                exercise={ex}
                exerciseIndex={i}
                sets={exSets}
                equipment={equipment}
                allExercises={allExercises}
                isCompleted={isCompleted}
                onSetAdded={handleSetAdded}
                onSetUpdated={handleSetUpdated}
                onSetDeleted={handleSetDeleted}
                onSwap={(newId) => handleSwapExercise(i, newId)}
                originalExerciseId={exercises[i]?.exercise_id}
                sessionNote={exNote?.note_text || null}
                onNoteAdded={handleNoteAdded}
              />
            )}
          </div>
        );
      })}

      {/* Complete Session button */}
      {!isCompleted && (
        <button onClick={() => setShowComplete(true)} className={styles.completeBtn}>
          Complete Session
        </button>
      )}

      {showComplete && (
        <ConfirmDialog
          message="Complete this session? It will become read-only."
          onConfirm={handleComplete}
          onCancel={() => setShowComplete(false)}
        />
      )}

      {showDelete && (
        <ConfirmDialog
          message="Delete this session? It will be removed from history and won't count toward PRs."
          onConfirm={handleDelete}
          onCancel={() => setShowDelete(false)}
        />
      )}
    </div>
  );
}

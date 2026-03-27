import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { apiFetch } from '../../shared/api';
import { useTimer } from '../../context/TimerContext';
import type { SessionExercise, WorkoutSet, Equipment, Exercise, SessionExerciseNote, ExerciseHistoryEntry } from '../../shared/types';
import { PRCelebration } from '../../components/PRCelebration';
import { PlateCalculatorModal } from '../../components/PlateCalculator';
import { SetRow } from './SetRow';
import styles from './ExercisePanel.module.css';

interface Props {
  sessionId: string;
  exercise: SessionExercise;
  exerciseIndex: number;
  sets: WorkoutSet[];
  equipment: Equipment[];
  allExercises: Exercise[];
  isCompleted: boolean;
  onSetAdded: (s: WorkoutSet) => void;
  onSetUpdated: (s: WorkoutSet) => void;
  onSetDeleted: (id: string) => void;
  onSwap: (newExerciseId: string) => void;
  originalExerciseId: string;
  sessionNote: string | null;
  onNoteAdded: (note: SessionExerciseNote) => void;
}

interface PlannedRow {
  order: number;
  type: 'working' | 'backoff';
  hintKg: number | null;
  hintReps: string;
  logged: WorkoutSet | null;
}

export function ExercisePanel({
  sessionId, exercise, sets, equipment, allExercises, isCompleted,
  onSetAdded, onSetUpdated, onSetDeleted, onSwap, originalExerciseId,
  sessionNote, onNoteAdded,
}: Props) {
  const { startTimer } = useTimer();
  const [saving, setSaving] = useState(false);
  const [prData, setPrData] = useState<{ isWeightPR: boolean; isE1rmPR: boolean; weightKg: number; estimated1rm: number } | null>(null);
  const [showPlateCalc, setShowPlateCalc] = useState(false);
  const [showSwap, setShowSwap] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<ExerciseHistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [plateCalcWeight, setPlateCalcWeight] = useState(0);
  const [showNoteInput, setShowNoteInput] = useState(false);
  const [noteText, setNoteText] = useState(sessionNote || '');

  const barFromAll = allExercises.find((e) => e.exercise_id === exercise.exercise_id);
  const defaultBar = equipment.find((e) => e.equipment_id === barFromAll?.default_bar_id);

  const suggestedKg = exercise.suggested_weight_kg ?? exercise.last_working_weight_kg ?? 0;

  // Build planned rows: only working/backoff sets (no warmups)
  const plannedRows: PlannedRow[] = useMemo(() => {
    const rows: PlannedRow[] = [];
    // Warmup rows are now shown as hints above, not in the table
    for (let i = 0; i < exercise.target_sets; i++) {
      rows.push({
        order: i + 1,
        type: exercise.set_type as PlannedRow['type'],
        hintKg: suggestedKg || null,
        hintReps: exercise.suggested_reps || exercise.target_reps,
        logged: null,
      });
    }

    // Match logged sets to planned rows by order
    const sortedSets = [...sets].sort((a, b) => a.set_order - b.set_order);
    for (const s of sortedSets) {
      const match = rows.find((r) => r.order === s.set_order && !r.logged);
      if (match) {
        match.logged = s;
      }
    }

    return rows;
  }, [exercise, sets, suggestedKg]);

  // Extra logged sets beyond planned rows
  const extraSets = sets.filter(
    (s) => !plannedRows.some((r) => r.logged?.set_id === s.set_id)
  ).sort((a, b) => a.set_order - b.set_order);

  const handleLogSet = useCallback(async (
    rowOrder: number,
    type: string,
    weightKg: number,
    reps: number,
    rir: number,
  ) => {
    setSaving(true);
    try {
      const body: Record<string, unknown> = {
        exercise_id: exercise.exercise_id,
        set_type: type,
        set_order: rowOrder,
        weight_kg: weightKg,
        reps,
        rir,
      };
      if (originalExerciseId !== exercise.exercise_id) {
        body.original_exercise_id = originalExerciseId;
      }

      const res = await apiFetch<WorkoutSet>(`/sessions/${sessionId}/sets`, {
        method: 'POST',
        body: JSON.stringify(body),
      });

      onSetAdded(res);

      if (res.is_weight_pr || res.is_e1rm_pr) {
        setPrData({
          isWeightPR: res.is_weight_pr,
          isE1rmPR: res.is_e1rm_pr,
          weightKg: res.weight_kg,
          estimated1rm: res.estimated_1rm,
        });
      }

      startTimer(exercise.exercise_id, exercise.rest_timer_seconds);
    } finally {
      setSaving(false);
    }
  }, [exercise, sessionId, originalExerciseId, onSetAdded, startTimer]);

  const handleLoadHistory = async () => {
    if (showHistory) {
      setShowHistory(false);
      return;
    }
    setHistoryLoading(true);
    try {
      const res = await apiFetch<{ history: ExerciseHistoryEntry[] }>(`/exercises/${exercise.exercise_id}/history`);
      setHistory(res.history);
      setShowHistory(true);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleSaveNote = async () => {
    if (!noteText.trim()) return;
    try {
      const res = await apiFetch<{ note: SessionExerciseNote }>(`/sessions/${sessionId}/notes`, {
        method: 'POST',
        body: JSON.stringify({ exercise_id: exercise.exercise_id, note_text: noteText.trim() }),
      });
      onNoteAdded(res.note);
      setShowNoteInput(false);
    } catch { /* ignore */ }
  };

  const replacements = exercise.replacement_exercise_ids || barFromAll?.replacement_exercise_ids || [];

  return (
    <div className={styles.panel}>
      {/* Exercise header */}
      <div className={styles.exHeader}>
        <h2 className={styles.exName}>{exercise.name}</h2>
        <div className={styles.badges}>
          {exercise.is_unilateral && <span className={styles.badge}>UNI{exercise.weak_side ? ` (${exercise.weak_side})` : ''}</span>}
          <span className={styles.target}>{exercise.target_sets}x{exercise.target_reps}</span>
        </div>
      </div>

      {/* Exercise-level notes (permanent) */}
      {exercise.notes && <p className={styles.notes}>{exercise.notes}</p>}

      {/* Session-specific note */}
      {sessionNote && !showNoteInput && (
        <p className={styles.sessionNote} onClick={() => !isCompleted && setShowNoteInput(true)}>
          {sessionNote}
        </p>
      )}

      {/* Actions row */}
      <div className={styles.actions}>
        {exercise.has_plate_calculator && defaultBar && (
          <button onClick={() => { setPlateCalcWeight(suggestedKg); setShowPlateCalc(true); }} className={styles.actionBtn}>Plates</button>
        )}
        {replacements.length > 0 && !isCompleted && (
          <button onClick={() => setShowSwap(!showSwap)} className={styles.actionBtn}>Swap</button>
        )}
        <button onClick={handleLoadHistory} className={styles.actionBtn} disabled={historyLoading}>
          {historyLoading ? '...' : 'History'}
        </button>
        {!isCompleted && !showNoteInput && (
          <button onClick={() => setShowNoteInput(true)} className={styles.actionBtn}>Note</button>
        )}
      </div>

      {/* Note input */}
      {showNoteInput && !isCompleted && (
        <div className={styles.noteInput}>
          <textarea
            className={styles.noteTextarea}
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="Session note for this exercise..."
            rows={2}
          />
          <div className={styles.noteActions}>
            <button onClick={handleSaveNote} className={styles.noteSave} disabled={!noteText.trim()}>Save</button>
            <button onClick={() => setShowNoteInput(false)} className={styles.noteCancel}>Cancel</button>
          </div>
        </div>
      )}

      {/* Swap dropdown */}
      {showSwap && (
        <div className={styles.swapList}>
          {replacements.map((rid) => {
            const rex = allExercises.find((e) => e.exercise_id === rid);
            return rex ? (
              <button key={rid} onClick={() => { onSwap(rid); setShowSwap(false); }} className={styles.swapItem}>
                {rex.name}
              </button>
            ) : null;
          })}
        </div>
      )}

      {/* Exercise history modal */}
      {showHistory && (
        <div className={styles.historyPanel}>
          <div className={styles.historyHeader}>
            <span>Recent History</span>
            <button onClick={() => setShowHistory(false)} className={styles.historyClose}>x</button>
          </div>
          {history.length === 0 && <p className={styles.historyEmpty}>No history yet</p>}
          {history.map((h) => (
            <div key={h.set_id} className={`${styles.historyRow} ${h.is_weight_pr || h.is_e1rm_pr ? styles.historyPr : ''}`}>
              <span className={styles.historyDate}>{new Date(h.timestamp).toLocaleDateString()}</span>
              <span>{h.weight_kg}kg</span>
              <span>{h.reps} reps</span>
              <span>RIR {h.rir}</span>
              {(h.is_weight_pr || h.is_e1rm_pr) && <span className={styles.historyPrBadge}>PR</span>}
            </div>
          ))}
        </div>
      )}

      {/* Warmup hint */}
      {exercise.warmup && (
        <p className={styles.warmupHint}>
          Warmup: 50% @ {exercise.warmup.warmup_50?.weight_kg}kg &times; {exercise.warmup.warmup_50?.reps}
          {exercise.warmup.warmup_75 && <> &rarr; 75% @ {exercise.warmup.warmup_75.weight_kg}kg &times; {exercise.warmup.warmup_75.reps}</>}
        </p>
      )}

      {/* Sets table */}
      <div className={styles.setsTable}>
        <div className={styles.setsHeader}>
          <span>#</span>
          <span>KG</span>
          <span>Reps</span>
          <span>RIR</span>
          <span></span>
        </div>

        {plannedRows.map((row) =>
          row.logged ? (
            <SetRow
              key={row.logged.set_id}
              set={row.logged}
              sessionId={sessionId}
              isCompleted={isCompleted}
              onUpdated={onSetUpdated}
              onDeleted={onSetDeleted}
            />
          ) : (
            <PlannedSetRow
              key={`planned-${row.order}`}
              row={row}
              disabled={isCompleted || saving}
              onLog={(kg, reps, rir) => handleLogSet(row.order, row.type, kg, reps, rir)}
            />
          )
        )}

        {extraSets.map((s) => (
          <SetRow
            key={s.set_id}
            set={s}
            sessionId={sessionId}
            isCompleted={isCompleted}
            onUpdated={onSetUpdated}
            onDeleted={onSetDeleted}
          />
        ))}
      </div>

      {/* Add extra set beyond plan */}
      {!isCompleted && (
        <AddExtraSetRow
          disabled={saving}
          defaultWeight={suggestedKg}
          onLog={(type, kg, reps, rir) =>
            handleLogSet(sets.length + 1, type, kg, reps, rir)
          }
        />
      )}

      {/* Plate calculator modal */}
      {showPlateCalc && defaultBar && (
        <PlateCalculatorModal
          targetWeight={plateCalcWeight}
          barWeight={defaultBar.weight_kg}
          equipment={equipment}
          isUnilateral={exercise.is_unilateral}
          onClose={() => setShowPlateCalc(false)}
        />
      )}

      {/* PR celebration */}
      {prData && (
        <PRCelebration
          isWeightPR={prData.isWeightPR}
          isE1rmPR={prData.isE1rmPR}
          weightKg={prData.weightKg}
          estimated1rm={prData.estimated1rm}
          onDone={() => setPrData(null)}
        />
      )}
    </div>
  );
}


/* --- Planned set row: auto-saves on reps entry --- */

function PlannedSetRow({ row, disabled, onLog }: {
  row: PlannedRow;
  disabled: boolean;
  onLog: (kg: number, reps: number, rir: number) => void;
}) {
  const [kg, setKg] = useState(row.hintKg ? String(row.hintKg) : '');
  const [reps, setReps] = useState('');
  const [rir, setRir] = useState('2');
  const [saved, setSaved] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  // Auto-save when reps is entered (debounced 500ms)
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const repsNum = parseInt(reps);
    if (!reps || isNaN(repsNum) || repsNum <= 0 || disabled || saved) return;

    debounceRef.current = setTimeout(() => {
      const weightKg = parseFloat(kg) || row.hintKg || 0;
      const rirNum = parseInt(rir) || 0;
      setSaved(true);
      onLog(weightKg, repsNum, rirNum);
    }, 500);

    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [reps, kg, rir, disabled, saved, row.hintKg, onLog]);

  const stripNonNumeric = (value: string, allowDot: boolean) => {
    return allowDot ? value.replace(/[^0-9.]/g, '') : value.replace(/[^0-9]/g, '');
  };

  if (saved) {
    return (
      <div className={styles.plannedRow}>
        <span className={styles.plannedNum}>{row.order}</span>
        <span className={styles.savedValue}>{parseFloat(kg) || row.hintKg || 0}</span>
        <span className={styles.savedValue}>{reps}</span>
        <span className={styles.savedValue}>{rir || '0'}</span>
        <span className={styles.savedCheck}>&#10003;</span>
      </div>
    );
  }

  return (
    <div className={styles.plannedRow}>
      <span className={styles.plannedNum}>{row.order}</span>
      <input
        type="text"
        inputMode="decimal"
        pattern="[0-9.]*"
        className={styles.plannedInput}
        value={kg}
        onChange={(e) => setKg(stripNonNumeric(e.target.value, true))}
        placeholder={row.hintKg ? String(row.hintKg) : 'kg'}
      />
      <input
        type="text"
        inputMode="numeric"
        pattern="[0-9]*"
        className={styles.plannedInput}
        value={reps}
        onChange={(e) => setReps(stripNonNumeric(e.target.value, false))}
        placeholder={row.hintReps}
      />
      <input
        type="text"
        inputMode="numeric"
        pattern="[0-9]*"
        className={styles.plannedInput}
        value={rir}
        onChange={(e) => setRir(stripNonNumeric(e.target.value, false))}
        placeholder="2"
      />
      <span></span>
    </div>
  );
}


/* --- Add extra set row (collapsed, for sets beyond the plan) --- */

function AddExtraSetRow({ disabled, defaultWeight, onLog }: {
  disabled: boolean;
  defaultWeight: number;
  onLog: (type: string, kg: number, reps: number, rir: number) => void;
}) {
  const [open, setOpen] = useState(false);
  const [type, setType] = useState('working');
  const [kg, setKg] = useState(String(defaultWeight || ''));
  const [reps, setReps] = useState('');
  const [rir, setRir] = useState('2');

  const stripNonNumeric = (value: string, allowDot: boolean) => {
    return allowDot ? value.replace(/[^0-9.]/g, '') : value.replace(/[^0-9]/g, '');
  };

  if (!open) {
    return (
      <button className={styles.addExtraBtn} onClick={() => setOpen(true)}>
        + Extra set
      </button>
    );
  }

  return (
    <div className={styles.addForm}>
      <select value={type} onChange={(e) => setType(e.target.value)} className={styles.typeSelect}>
        <option value="working">Work</option>
        <option value="backoff">Back</option>
        <option value="warmup_50">W50%</option>
        <option value="warmup_75">W75%</option>
      </select>
      <input type="text" inputMode="decimal" pattern="[0-9.]*" value={kg} onChange={(e) => setKg(stripNonNumeric(e.target.value, true))} placeholder="kg" className={styles.formInput} />
      <input type="text" inputMode="numeric" pattern="[0-9]*" value={reps} onChange={(e) => setReps(stripNonNumeric(e.target.value, false))} placeholder="reps" className={styles.formInput} />
      <input type="text" inputMode="numeric" pattern="[0-9]*" value={rir} onChange={(e) => setRir(stripNonNumeric(e.target.value, false))} placeholder="rir" className={styles.formInput} />
      <button
        className={styles.addBtn}
        disabled={disabled || !reps}
        onClick={() => {
          onLog(type, parseFloat(kg) || 0, parseInt(reps), parseInt(rir) || 0);
          setReps('');
        }}
      >+</button>
    </div>
  );
}

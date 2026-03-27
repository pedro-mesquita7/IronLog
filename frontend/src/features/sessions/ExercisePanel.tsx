import { useState, useCallback, useMemo } from 'react';
import { apiFetch } from '../../shared/api';
import { useTimer } from '../../context/TimerContext';
import type { SessionExercise, WorkoutSet, Equipment, Exercise } from '../../shared/types';
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
}

interface PlannedRow {
  order: number;
  type: 'warmup_50' | 'warmup_75' | 'working' | 'backoff';
  hintKg: number | null;
  hintReps: string;
  logged: WorkoutSet | null;
}

export function ExercisePanel({
  sessionId, exercise, sets, equipment, allExercises, isCompleted,
  onSetAdded, onSetUpdated, onSetDeleted, onSwap, originalExerciseId,
}: Props) {
  const { startTimer } = useTimer();
  const [saving, setSaving] = useState(false);
  const [prData, setPrData] = useState<{ isWeightPR: boolean; isE1rmPR: boolean; weightKg: number; estimated1rm: number } | null>(null);
  const [showPlateCalc, setShowPlateCalc] = useState(false);
  const [showSwap, setShowSwap] = useState(false);
  const [plateCalcWeight, setPlateCalcWeight] = useState(0);

  const barFromAll = allExercises.find((e) => e.exercise_id === exercise.exercise_id);
  const defaultBar = equipment.find((e) => e.equipment_id === barFromAll?.default_bar_id);

  const lastWeight = exercise.last_working_weight_kg ?? 0;

  // Build the planned rows: warmups (if history exists) + working sets from plan
  const plannedRows: PlannedRow[] = useMemo(() => {
    const rows: PlannedRow[] = [];
    let order = 1;

    // Warmup rows (only if we have last working weight)
    if (exercise.warmup) {
      if (exercise.warmup.warmup_50) {
        rows.push({
          order: order++,
          type: 'warmup_50',
          hintKg: exercise.warmup.warmup_50.weight_kg,
          hintReps: exercise.warmup.warmup_50.reps,
          logged: null,
        });
      }
      if (exercise.warmup.warmup_75) {
        rows.push({
          order: order++,
          type: 'warmup_75',
          hintKg: exercise.warmup.warmup_75.weight_kg,
          hintReps: exercise.warmup.warmup_75.reps,
          logged: null,
        });
      }
    }

    // Working/backoff sets from plan target
    for (let i = 0; i < exercise.target_sets; i++) {
      // First set is working (top set), remaining could be backoff if target_sets > 1
      // But spec says set_type comes from plan, so use the plan's set_type for all
      rows.push({
        order: order++,
        type: exercise.set_type as PlannedRow['type'],
        hintKg: lastWeight || null,
        hintReps: exercise.target_reps,
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
  }, [exercise, sets, lastWeight]);

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

  const replacements = exercise.replacement_exercise_ids || barFromAll?.replacement_exercise_ids || [];

  const typeLabel = (t: string) =>
    t === 'warmup_50' ? 'W50%' : t === 'warmup_75' ? 'W75%' : t === 'backoff' ? 'Back' : 'Work';

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

      {/* Notes */}
      {exercise.notes && <p className={styles.notes}>{exercise.notes}</p>}

      {/* Actions row */}
      <div className={styles.actions}>
        {exercise.has_plate_calculator && defaultBar && (
          <button onClick={() => { setPlateCalcWeight(lastWeight); setShowPlateCalc(true); }} className={styles.actionBtn}>Plates</button>
        )}
        {replacements.length > 0 && !isCompleted && (
          <button onClick={() => setShowSwap(!showSwap)} className={styles.actionBtn}>Swap</button>
        )}
      </div>

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

      {/* Sets table with planned rows */}
      <div className={styles.setsTable}>
        <div className={styles.setsHeader}>
          <span>#</span>
          <span>Type</span>
          <span>kg</span>
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
              typeLabel={typeLabel(row.type)}
              disabled={isCompleted || saving}
              onLog={(kg, reps, rir) => handleLogSet(row.order, row.type, kg, reps, rir)}
            />
          )
        )}

        {/* Any extra sets logged beyond the plan */}
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
          defaultWeight={lastWeight}
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


/* --- Planned set row: shows hint, lets user fill in and log --- */

function PlannedSetRow({ row, typeLabel, disabled, onLog }: {
  row: PlannedRow;
  typeLabel: string;
  disabled: boolean;
  onLog: (kg: number, reps: number, rir: number) => void;
}) {
  const [kg, setKg] = useState(row.hintKg ? String(row.hintKg) : '');
  const [reps, setReps] = useState('');
  const [rir, setRir] = useState('2');

  return (
    <div className={styles.plannedRow}>
      <span className={styles.plannedNum}>{row.order}</span>
      <span className={styles.plannedType}>{typeLabel}</span>
      <input
        type="number"
        step="0.5"
        className={styles.plannedInput}
        value={kg}
        onChange={(e) => setKg(e.target.value)}
        placeholder={row.hintKg ? String(row.hintKg) : 'kg'}
      />
      <input
        type="number"
        className={styles.plannedInput}
        value={reps}
        onChange={(e) => setReps(e.target.value)}
        placeholder={row.hintReps}
      />
      <input
        type="number"
        className={styles.plannedInput}
        value={rir}
        onChange={(e) => setRir(e.target.value)}
        placeholder="2"
      />
      <button
        className={styles.logBtn}
        disabled={disabled || !reps}
        onClick={() => onLog(parseFloat(kg) || row.hintKg || 0, parseInt(reps), parseInt(rir) || 0)}
      >
        Log
      </button>
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
      <input type="number" step="0.5" value={kg} onChange={(e) => setKg(e.target.value)} placeholder="kg" className={styles.formInput} />
      <input type="number" value={reps} onChange={(e) => setReps(e.target.value)} placeholder="reps" className={styles.formInput} />
      <input type="number" value={rir} onChange={(e) => setRir(e.target.value)} placeholder="rir" className={styles.formInput} />
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

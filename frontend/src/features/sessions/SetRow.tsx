import { useState } from 'react';
import { apiFetch } from '../../shared/api';
import type { WorkoutSet } from '../../shared/types';
import styles from './SetRow.module.css';

interface Props {
  set: WorkoutSet;
  sessionId: string;
  isCompleted: boolean;
  onUpdated: (s: WorkoutSet) => void;
  onDeleted: (id: string) => void;
}

const stripNonNumeric = (value: string, allowDot: boolean) => {
  return allowDot ? value.replace(/[^0-9.]/g, '') : value.replace(/[^0-9]/g, '');
};

export function SetRow({ set, sessionId, isCompleted, onUpdated, onDeleted }: Props) {
  const [editing, setEditing] = useState(false);
  const [weightKg, setWeightKg] = useState(String(set.weight_kg));
  const [reps, setReps] = useState(String(set.reps));
  const [rir, setRir] = useState(String(set.rir));

  const handleSave = async () => {
    const res = await apiFetch<{ set: WorkoutSet }>(`/sessions/${sessionId}/sets/${set.set_id}`, {
      method: 'PUT',
      body: JSON.stringify({
        weight_kg: parseFloat(weightKg),
        reps: parseInt(reps),
        rir: parseInt(rir),
      }),
    });
    onUpdated(res.set);
    setEditing(false);
  };

  const handleDelete = async () => {
    await apiFetch(`/sessions/${sessionId}/sets/${set.set_id}`, { method: 'DELETE' });
    onDeleted(set.set_id);
  };

  if (editing && !isCompleted) {
    return (
      <div className={styles.row}>
        <span className={styles.num}>{set.set_order}</span>
        <input className={styles.editInput} value={weightKg} onChange={(e) => setWeightKg(stripNonNumeric(e.target.value, true))} type="text" inputMode="decimal" pattern="[0-9.]*" />
        <input className={styles.editInput} value={reps} onChange={(e) => setReps(stripNonNumeric(e.target.value, false))} type="text" inputMode="numeric" pattern="[0-9]*" />
        <input className={styles.editInput} value={rir} onChange={(e) => setRir(stripNonNumeric(e.target.value, false))} type="text" inputMode="numeric" pattern="[0-9]*" />
        <div className={styles.editActions}>
          <button onClick={handleSave} className={styles.saveBtn}>ok</button>
          <button onClick={() => setEditing(false)} className={styles.cancelBtn}>x</button>
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.row} ${set.is_weight_pr || set.is_e1rm_pr ? styles.prRow : ''}`} onClick={() => !isCompleted && setEditing(true)}>
      <span className={styles.num}>{set.set_order}</span>
      <span className={styles.weight}>{set.weight_kg}</span>
      <span className={styles.reps}>{set.reps}</span>
      <span className={styles.rir}>{set.rir}</span>
      {!isCompleted ? (
        <button onClick={(e) => { e.stopPropagation(); handleDelete(); }} className={styles.delBtn}>x</button>
      ) : (
        <span className={styles.prBadge}>
          {set.is_weight_pr && 'W'}
          {set.is_e1rm_pr && 'E'}
        </span>
      )}
    </div>
  );
}

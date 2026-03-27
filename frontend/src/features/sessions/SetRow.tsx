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

export function SetRow({ set, sessionId, isCompleted, onUpdated, onDeleted }: Props) {
  const [editing, setEditing] = useState(false);
  const [weightKg, setWeightKg] = useState(String(set.weight_kg));
  const [reps, setReps] = useState(String(set.reps));
  const [rir, setRir] = useState(String(set.rir));

  const typeLabel = set.set_type === 'warmup_50' ? 'W50' : set.set_type === 'warmup_75' ? 'W75' : set.set_type === 'backoff' ? 'Back' : 'Work';

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
        <span className={styles.type}>{typeLabel}</span>
        <input className={styles.editInput} value={weightKg} onChange={(e) => setWeightKg(e.target.value)} type="number" step="0.5" />
        <input className={styles.editInput} value={reps} onChange={(e) => setReps(e.target.value)} type="number" />
        <input className={styles.editInput} value={rir} onChange={(e) => setRir(e.target.value)} type="number" />
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
      <span className={styles.type}>{typeLabel}</span>
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

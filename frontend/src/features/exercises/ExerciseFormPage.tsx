import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { apiFetch, ApiError } from '../../shared/api';
import type { Exercise, Equipment } from '../../shared/types';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import styles from './ExerciseFormPage.module.css';

const MUSCLE_GROUPS = ['chest', 'back', 'legs', 'shoulders', 'arms', 'core', 'full_body'];
const REST_OPTIONS = [60, 120, 180];

export function ExerciseFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = !!id;

  const [name, setName] = useState('');
  const [muscleGroup, setMuscleGroup] = useState('chest');
  const [restTimer, setRestTimer] = useState(60);
  const [hasPlateCalc, setHasPlateCalc] = useState(false);
  const [isUnilateral, setIsUnilateral] = useState(false);
  const [weakSide, setWeakSide] = useState<string>('');
  const [defaultBarId, setDefaultBarId] = useState('');
  const [notes, setNotes] = useState('');
  const [bars, setBars] = useState<Equipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [showDelete, setShowDelete] = useState(false);

  useEffect(() => {
    const promises: Promise<void>[] = [
      apiFetch<{ equipment: Equipment[] }>('/equipment').then((r) => {
        setBars(r.equipment.filter((e) => e.equipment_type === 'bar'));
      }),
    ];

    if (id) {
      promises.push(
        apiFetch<{ exercises: Exercise[] }>('/exercises').then((r) => {
          const ex = r.exercises.find((e) => e.exercise_id === id);
          if (ex) {
            setName(ex.name);
            setMuscleGroup(ex.muscle_group);
            setRestTimer(ex.rest_timer_seconds);
            setHasPlateCalc(ex.has_plate_calculator);
            setIsUnilateral(ex.is_unilateral);
            setWeakSide(ex.weak_side || '');
            setDefaultBarId(ex.default_bar_id || '');
            setNotes(ex.notes || '');
          }
        })
      );
    }

    Promise.all(promises).finally(() => setLoading(false));
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');

    const body: Record<string, unknown> = {
      name,
      muscle_group: muscleGroup,
      rest_timer_seconds: restTimer,
      has_plate_calculator: hasPlateCalc,
      is_unilateral: isUnilateral,
      weak_side: weakSide || null,
      default_bar_id: defaultBarId || null,
      notes: notes || null,
    };

    try {
      if (isEdit) {
        await apiFetch(`/exercises/${id}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await apiFetch('/exercises', { method: 'POST', body: JSON.stringify(body) });
      }
      navigate('/exercises', { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    await apiFetch(`/exercises/${id}`, { method: 'DELETE' });
    navigate('/exercises', { replace: true });
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className={styles.page}>
      <h1>{isEdit ? 'Edit Exercise' : 'New Exercise'}</h1>
      <form onSubmit={handleSubmit} className={styles.form}>
        <label>Name</label>
        <input value={name} onChange={(e) => setName(e.target.value)} required className={styles.input} />

        <label>Muscle Group</label>
        <select value={muscleGroup} onChange={(e) => setMuscleGroup(e.target.value)} className={styles.input}>
          {MUSCLE_GROUPS.map((g) => <option key={g} value={g}>{g}</option>)}
        </select>

        <label>Rest Timer</label>
        <select value={restTimer} onChange={(e) => setRestTimer(Number(e.target.value))} className={styles.input}>
          {REST_OPTIONS.map((s) => <option key={s} value={s}>{s}s</option>)}
        </select>

        <label>Default Bar</label>
        <select value={defaultBarId} onChange={(e) => setDefaultBarId(e.target.value)} className={styles.input}>
          <option value="">None</option>
          {bars.map((b) => <option key={b.equipment_id} value={b.equipment_id}>{b.name}</option>)}
        </select>

        <div className={styles.checkRow}>
          <label><input type="checkbox" checked={hasPlateCalc} onChange={(e) => setHasPlateCalc(e.target.checked)} /> Plate Calculator</label>
          <label><input type="checkbox" checked={isUnilateral} onChange={(e) => setIsUnilateral(e.target.checked)} /> Unilateral</label>
        </div>

        {isUnilateral && (
          <>
            <label>Weak Side</label>
            <select value={weakSide} onChange={(e) => setWeakSide(e.target.value)} className={styles.input}>
              <option value="">None</option>
              <option value="left">Left</option>
              <option value="right">Right</option>
            </select>
          </>
        )}

        <label>Notes</label>
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} className={styles.input} />

        {error && <p className={styles.error}>{error}</p>}

        <button type="submit" disabled={saving} className={styles.saveBtn}>
          {saving ? 'Saving...' : 'Save'}
        </button>

        {isEdit && (
          <button type="button" onClick={() => setShowDelete(true)} className={styles.deleteBtn}>
            Archive
          </button>
        )}
      </form>

      <button onClick={() => navigate(-1)} className={styles.backBtn}>Back</button>

      {showDelete && (
        <ConfirmDialog
          message={`Archive ${name}?`}
          onConfirm={handleDelete}
          onCancel={() => setShowDelete(false)}
        />
      )}
    </div>
  );
}

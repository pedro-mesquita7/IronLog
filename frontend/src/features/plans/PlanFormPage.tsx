import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { apiFetch, ApiError } from '../../shared/api';
import type { Plan, Exercise } from '../../shared/types';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import styles from './PlanFormPage.module.css';

interface DayForm {
  day_name: string;
  exercises: { exercise_id: string; target_sets: number; target_reps: string; set_type: string }[];
}

export function PlanFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = !!id;

  const [name, setName] = useState('');
  const [splitType, setSplitType] = useState('');
  const [days, setDays] = useState<DayForm[]>([{ day_name: 'Day 1', exercises: [] }]);
  const [allExercises, setAllExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const promises: Promise<void>[] = [
      apiFetch<{ exercises: Exercise[] }>('/exercises').then((r) => setAllExercises(r.exercises)),
    ];

    if (id) {
      promises.push(
        apiFetch<{ plan: Plan }>(`/plans/${id}`).then((r) => {
          const p = r.plan;
          setName(p.name);
          setSplitType(p.split_type || '');
          if (p.days && p.days.length > 0) {
            setDays(p.days.map((d) => ({
              day_name: d.day_name,
              exercises: d.exercises.map((e) => ({
                exercise_id: e.exercise_id,
                target_sets: e.target_sets,
                target_reps: e.target_reps,
                set_type: e.set_type,
              })),
            })));
          }
        })
      );
    }

    Promise.all(promises).finally(() => setLoading(false));
  }, [id]);

  const addDay = () => setDays([...days, { day_name: `Day ${days.length + 1}`, exercises: [] }]);

  const removeDay = (i: number) => setDays(days.filter((_, idx) => idx !== i));

  const addExercise = (dayIdx: number) => {
    const updated = [...days];
    updated[dayIdx].exercises.push({ exercise_id: '', target_sets: 2, target_reps: '6-8', set_type: 'working' });
    setDays(updated);
  };

  const removeExercise = (dayIdx: number, exIdx: number) => {
    const updated = [...days];
    updated[dayIdx].exercises = updated[dayIdx].exercises.filter((_, i) => i !== exIdx);
    setDays(updated);
  };

  const updateDay = (dayIdx: number, field: string, value: string) => {
    const updated = [...days];
    (updated[dayIdx] as unknown as Record<string, unknown>)[field] = value;
    setDays(updated);
  };

  const updateExercise = (dayIdx: number, exIdx: number, field: string, value: string | number) => {
    const updated = [...days];
    (updated[dayIdx].exercises[exIdx] as Record<string, unknown>)[field] = value;
    setDays(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');

    const body = {
      name,
      split_type: splitType || null,
      days: days.map((d) => ({
        day_name: d.day_name,
        exercises: d.exercises
          .filter((ex) => ex.exercise_id)
          .map((ex, i) => ({ ...ex, order: i + 1, target_sets: Number(ex.target_sets) })),
      })),
    };

    try {
      if (isEdit) {
        await apiFetch(`/plans/${id}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await apiFetch('/plans', { method: 'POST', body: JSON.stringify(body) });
      }
      navigate('/plans', { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className={styles.page}>
      <h1>{isEdit ? 'Edit Plan' : 'New Plan'}</h1>
      <form onSubmit={handleSubmit} className={styles.form}>
        <label>Name</label>
        <input value={name} onChange={(e) => setName(e.target.value)} required className={styles.input} />

        <label>Split Type</label>
        <input value={splitType} onChange={(e) => setSplitType(e.target.value)} placeholder="e.g. Upper/Lower" className={styles.input} />

        {days.map((day, di) => (
          <div key={di} className={styles.dayBlock}>
            <div className={styles.dayHeader}>
              <input
                value={day.day_name}
                onChange={(e) => updateDay(di, 'day_name', e.target.value)}
                className={styles.dayInput}
              />
              {days.length > 1 && (
                <button type="button" onClick={() => removeDay(di)} className={styles.removeBtn}>x</button>
              )}
            </div>

            {day.exercises.map((ex, ei) => (
              <div key={ei} className={styles.exRow}>
                <select
                  value={ex.exercise_id}
                  onChange={(e) => updateExercise(di, ei, 'exercise_id', e.target.value)}
                  className={styles.exSelect}
                >
                  <option value="">Select...</option>
                  {allExercises.map((ae) => (
                    <option key={ae.exercise_id} value={ae.exercise_id}>{ae.name}</option>
                  ))}
                </select>
                <input
                  type="number"
                  value={ex.target_sets}
                  onChange={(e) => updateExercise(di, ei, 'target_sets', e.target.value)}
                  className={styles.setsInput}
                  min={1}
                />
                <input
                  value={ex.target_reps}
                  onChange={(e) => updateExercise(di, ei, 'target_reps', e.target.value)}
                  className={styles.repsInput}
                  placeholder="reps"
                />
                <button type="button" onClick={() => removeExercise(di, ei)} className={styles.removeBtn}>x</button>
              </div>
            ))}
            <button type="button" onClick={() => addExercise(di)} className={styles.addExBtn}>+ Exercise</button>
          </div>
        ))}

        <button type="button" onClick={addDay} className={styles.addDayBtn}>+ Add Day</button>

        {error && <p className={styles.error}>{error}</p>}

        <button type="submit" disabled={saving} className={styles.saveBtn}>
          {saving ? 'Saving...' : 'Save'}
        </button>
      </form>

      <button onClick={() => navigate(-1)} className={styles.backBtn}>Back</button>
    </div>
  );
}

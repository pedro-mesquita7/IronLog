import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { apiFetch } from '../../shared/api';
import type { Plan, Exercise } from '../../shared/types';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import styles from './PlanDetailPage.module.css';

export function PlanDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [plan, setPlan] = useState<Plan | null>(null);
  const [exercises, setExercises] = useState<Record<string, Exercise>>({});
  const [loading, setLoading] = useState(true);
  const [showDelete, setShowDelete] = useState(false);

  useEffect(() => {
    Promise.all([
      apiFetch<{ plan: Plan }>(`/plans/${id}`).then((r) => setPlan(r.plan)),
      apiFetch<{ exercises: Exercise[] }>('/exercises').then((r) => {
        const map: Record<string, Exercise> = {};
        r.exercises.forEach((e) => (map[e.exercise_id] = e));
        setExercises(map);
      }),
    ]).finally(() => setLoading(false));
  }, [id]);

  const handleDelete = async () => {
    await apiFetch(`/plans/${id}`, { method: 'DELETE' });
    navigate('/plans', { replace: true });
  };

  if (loading || !plan) return <LoadingSpinner />;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1>{plan.name}</h1>
          {plan.split_type && <p className={styles.split}>{plan.split_type}</p>}
        </div>
        <div className={styles.actions}>
          <button onClick={() => navigate(`/plans/${id}/edit`)} className={styles.editBtn}>Edit</button>
          <button onClick={() => setShowDelete(true)} className={styles.deleteBtn}>Delete</button>
        </div>
      </div>

      {plan.days?.map((day) => (
        <section key={day.day_number} className={styles.day}>
          <h2>Day {day.day_number}: {day.day_name}</h2>
          {day.exercises.map((pe) => {
            const ex = exercises[pe.exercise_id];
            return (
              <div key={`${pe.exercise_id}-${pe.order}`} className={styles.exercise}>
                <span className={styles.order}>{pe.order}</span>
                <div className={styles.exInfo}>
                  <span className={styles.exName}>{ex?.name || pe.exercise_id}</span>
                  <span className={styles.exMeta}>{pe.target_sets}x{pe.target_reps} {pe.set_type}</span>
                </div>
              </div>
            );
          })}
        </section>
      ))}

      <button onClick={() => navigate(-1)} className={styles.backBtn}>Back</button>

      {showDelete && (
        <ConfirmDialog
          message={`Delete plan "${plan.name}"? This cannot be undone.`}
          onConfirm={handleDelete}
          onCancel={() => setShowDelete(false)}
        />
      )}
    </div>
  );
}

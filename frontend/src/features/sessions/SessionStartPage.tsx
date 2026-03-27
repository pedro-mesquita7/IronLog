import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../../shared/api';
import type { Plan, StartSessionResponse } from '../../shared/types';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import styles from './SessionStartPage.module.css';

export function SessionStartPage() {
  const navigate = useNavigate();
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState<number | null>(null);

  useEffect(() => {
    apiFetch<{ plans: Plan[] }>('/plans')
      .then((r) => {
        if (r.plans.length === 0) {
          // No data at all — redirect to guided setup
          navigate('/setup', { replace: true });
          return;
        }
        const active = r.plans.find((p) => p.is_active);
        if (active) {
          return apiFetch<{ plan: Plan }>(`/plans/${active.plan_id}`).then((pr) => setPlan(pr.plan));
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const handleStart = async (dayNumber: number) => {
    if (!plan) return;
    setStarting(dayNumber);
    try {
      const res = await apiFetch<StartSessionResponse>('/sessions', {
        method: 'POST',
        body: JSON.stringify({ plan_id: plan.plan_id, plan_day_number: dayNumber }),
      });
      // Store exercises from POST response so SessionPage can use them
      sessionStorage.setItem(
        `ironlog_session_${res.session_id}`,
        JSON.stringify({ exercises: res.exercises })
      );
      navigate(`/sessions/${res.session_id}`, { replace: true });
    } finally {
      setStarting(null);
    }
  };

  if (loading) return <LoadingSpinner />;

  if (!plan) {
    return (
      <div className={styles.page}>
        <h1>Start Session</h1>
        <p className={styles.empty}>No active plan. Go to Plans to activate one.</p>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <h1>Start Session</h1>
      <p className={styles.plan}>{plan.name}</p>
      <div className={styles.days}>
        {plan.days?.map((day) => (
          <button
            key={day.day_number}
            onClick={() => handleStart(day.day_number)}
            disabled={starting !== null}
            className={styles.dayBtn}
          >
            <span className={styles.dayName}>{day.day_name}</span>
            <span className={styles.dayExCount}>{day.exercises.length} exercises</span>
            {starting === day.day_number && <span className={styles.starting}>Starting...</span>}
          </button>
        ))}
      </div>
    </div>
  );
}

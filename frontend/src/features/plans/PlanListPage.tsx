import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../../shared/api';
import type { Plan } from '../../shared/types';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import styles from './PlanListPage.module.css';

export function PlanListPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    apiFetch<{ plans: Plan[] }>('/plans')
      .then((r) => setPlans(r.plans))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleActivate = async (planId: string) => {
    await apiFetch(`/plans/${planId}/activate`, { method: 'PUT' });
    load();
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Plans</h1>
        <Link to="/plans/new" className={styles.addBtn}>+ Add</Link>
      </div>

      {plans.length === 0 && <p className={styles.empty}>No plans yet.</p>}

      {plans.map((p) => (
        <div key={p.plan_id} className={styles.item}>
          <Link to={`/plans/${p.plan_id}`} className={styles.info}>
            <span className={styles.name}>
              {p.name}
              {p.is_active && <span className={styles.activeBadge}>Active</span>}
            </span>
            <span className={styles.split}>{p.split_type || ''}</span>
          </Link>
          {!p.is_active && (
            <button onClick={() => handleActivate(p.plan_id)} className={styles.activateBtn}>
              Activate
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

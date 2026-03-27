import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../../shared/api';
import type { Exercise } from '../../shared/types';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import styles from './ExerciseListPage.module.css';

const GROUPS = ['chest', 'back', 'legs', 'shoulders', 'arms', 'core', 'full_body'] as const;

export function ExerciseListPage() {
  const [items, setItems] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    apiFetch<{ exercises: Exercise[] }>('/exercises')
      .then((r) => setItems(r.exercises))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  const filtered = filter === 'all' ? items : items.filter((e) => e.muscle_group === filter);

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Exercises</h1>
        <Link to="/exercises/new" className={styles.addBtn}>+ Add</Link>
      </div>

      <div className={styles.filters}>
        <button
          className={`${styles.filterBtn} ${filter === 'all' ? styles.active : ''}`}
          onClick={() => setFilter('all')}
        >All</button>
        {GROUPS.map((g) => (
          <button
            key={g}
            className={`${styles.filterBtn} ${filter === g ? styles.active : ''}`}
            onClick={() => setFilter(g)}
          >{g}</button>
        ))}
      </div>

      {filtered.length === 0 && <p className={styles.empty}>No exercises found.</p>}

      {filtered.map((ex) => (
        <Link key={ex.exercise_id} to={`/exercises/${ex.exercise_id}/edit`} className={styles.item}>
          <div>
            <span className={styles.name}>{ex.name}</span>
            {ex.is_unilateral && <span className={styles.badge}>UNI</span>}
          </div>
          <span className={styles.group}>{ex.muscle_group}</span>
        </Link>
      ))}
    </div>
  );
}

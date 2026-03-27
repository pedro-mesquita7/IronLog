import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../../shared/api';
import type { SeedResponse } from '../../shared/types';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import styles from './GuidedSetupPage.module.css';

export function GuidedSetupPage() {
  const navigate = useNavigate();
  const [checking, setChecking] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    apiFetch<{ equipment: unknown[] }>('/equipment')
      .then((res) => {
        if (res.equipment.length > 0) navigate('/', { replace: true });
        else setChecking(false);
      })
      .catch(() => setChecking(false));
  }, [navigate]);

  const handleSeed = async () => {
    setSeeding(true);
    setError('');
    try {
      const res = await apiFetch<SeedResponse>('/seed', { method: 'POST' });
      if (res.seeded || !res.seeded) navigate('/', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Seed failed');
    } finally {
      setSeeding(false);
    }
  };

  if (checking) return <LoadingSpinner />;

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Welcome to IronLog</h1>
      <p className={styles.desc}>
        No data found. Seed default equipment, exercises, and a 4-day Upper/Lower plan?
      </p>
      {error && <p className={styles.error}>{error}</p>}
      <button onClick={handleSeed} disabled={seeding} className={styles.seedBtn}>
        {seeding ? 'Seeding...' : 'Seed Default Data'}
      </button>
      <button onClick={() => navigate('/', { replace: true })} className={styles.skipBtn}>
        Skip — I'll add my own
      </button>
    </div>
  );
}

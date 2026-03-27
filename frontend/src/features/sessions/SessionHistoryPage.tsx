import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../../shared/api';
import type { Session } from '../../shared/types';
import { formatDate, todayISO } from '../../shared/dateUtils';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import styles from './SessionHistoryPage.module.css';

export function SessionHistoryPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [from, setFrom] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().slice(0, 10);
  });
  const [to, setTo] = useState(todayISO);

  useEffect(() => {
    setLoading(true);
    apiFetch<{ sessions: Session[] }>(`/sessions?from=${from}&to=${to}`)
      .then((r) => setSessions(r.sessions))
      .finally(() => setLoading(false));
  }, [from, to]);

  return (
    <div className={styles.page}>
      <h1>Session History</h1>
      <div className={styles.filters}>
        <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} className={styles.dateInput} />
        <span className={styles.sep}>to</span>
        <input type="date" value={to} onChange={(e) => setTo(e.target.value)} className={styles.dateInput} />
      </div>

      {loading && <LoadingSpinner />}

      {!loading && sessions.length === 0 && <p className={styles.empty}>No sessions found.</p>}

      {!loading &&
        sessions.map((s) => (
          <Link key={s.session_id} to={`/sessions/${s.session_id}`} className={styles.item}>
            <div>
              <span className={styles.date}>{formatDate(s.date)}</span>
              <span className={`${styles.status} ${s.status === 'completed' ? styles.completed : styles.inProgress}`}>
                {s.status === 'completed' ? 'Completed' : 'In Progress'}
              </span>
            </div>
            <span className={styles.time}>{formatDate(s.started_at)}</span>
          </Link>
        ))}
    </div>
  );
}

import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import styles from './MorePage.module.css';

const links = [
  { to: '/equipment', label: 'Equipment', icon: '🏋️' },
  { to: '/exercises', label: 'Exercises', icon: '💪' },
  { to: '/plans', label: 'Training Plans', icon: '📝' },
];

export function MorePage() {
  const { logout } = useAuth();

  return (
    <div className={styles.page}>
      <h1>More</h1>

      <div className={styles.group}>
        {links.map((l) => (
          <Link key={l.to} to={l.to} className={styles.row}>
            <span className={styles.rowIcon}>{l.icon}</span>
            <span className={styles.rowLabel}>{l.label}</span>
            <span className={styles.chevron}>›</span>
          </Link>
        ))}
      </div>

      <div className={styles.group}>
        <button className={styles.logoutBtn} onClick={logout}>
          Log Out
        </button>
      </div>
    </div>
  );
}

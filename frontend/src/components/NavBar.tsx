import { NavLink } from 'react-router-dom';
import styles from './NavBar.module.css';

const tabs = [
  { to: '/', label: 'Home' },
  { to: '/equipment', label: 'Equip' },
  { to: '/exercises', label: 'Exercises' },
  { to: '/plans', label: 'Plans' },
  { to: '/sessions', label: 'History' },
  { to: '/analytics', label: 'Stats' },
];

export function NavBar() {
  return (
    <nav className={styles.nav}>
      {tabs.map((t) => (
        <NavLink
          key={t.to}
          to={t.to}
          end={t.to === '/'}
          className={({ isActive }) => `${styles.tab} ${isActive ? styles.active : ''}`}
        >
          {t.label}
        </NavLink>
      ))}
    </nav>
  );
}

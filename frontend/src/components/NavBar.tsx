import { memo } from 'react';
import { NavLink } from 'react-router-dom';
import styles from './NavBar.module.css';

const tabs = [
  { to: '/', label: 'Home', icon: '🏠' },
  { to: '/sessions', label: 'History', icon: '📋' },
  { to: '/analytics', label: 'Stats', icon: '📊' },
  { to: '/more', label: 'More', icon: '⋯' },
];

export const NavBar = memo(function NavBar() {
  return (
    <nav className={styles.nav}>
      {tabs.map((t) => (
        <NavLink
          key={t.to}
          to={t.to}
          end={t.to === '/'}
          className={({ isActive }) => `${styles.tab} ${isActive ? styles.active : ''}`}
        >
          <span className={styles.icon}>{t.icon}</span>
          <span className={styles.label}>{t.label}</span>
        </NavLink>
      ))}
    </nav>
  );
});

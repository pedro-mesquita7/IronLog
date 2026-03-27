import { useTimer } from '../context/TimerContext';
import styles from './RestTimerOverlay.module.css';

export function RestTimerOverlay() {
  const { isRunning, remaining, duration, stopTimer } = useTimer();

  if (!isRunning) return null;

  const mins = Math.floor(remaining / 60);
  const secs = remaining % 60;
  const pct = ((duration - remaining) / duration) * 100;

  return (
    <div className={styles.overlay} onClick={stopTimer}>
      <div className={styles.bar} style={{ width: `${pct}%` }} />
      <span className={styles.time}>
        {mins}:{secs.toString().padStart(2, '0')}
      </span>
      <span className={styles.label}>Rest</span>
    </div>
  );
}

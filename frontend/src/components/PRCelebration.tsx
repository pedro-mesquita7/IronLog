import { useEffect, useState } from 'react';
import styles from './PRCelebration.module.css';

interface Props {
  isWeightPR: boolean;
  isE1rmPR: boolean;
  weightKg: number;
  estimated1rm: number;
  onDone: () => void;
}

export function PRCelebration({ isWeightPR, isE1rmPR, weightKg, estimated1rm, onDone }: Props) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => { setVisible(false); onDone(); }, 3000);
    return () => clearTimeout(t);
  }, [onDone]);

  if (!visible) return null;

  return (
    <div className={styles.overlay} onClick={() => { setVisible(false); onDone(); }}>
      <div className={styles.content}>
        <div className={styles.title}>NEW PR!</div>
        {isWeightPR && <div className={styles.detail}>Weight PR: {weightKg}kg</div>}
        {isE1rmPR && <div className={styles.detail}>e1RM PR: {estimated1rm.toFixed(1)}kg</div>}
      </div>
    </div>
  );
}

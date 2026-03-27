import { calculatePlates } from '../shared/plateCalculator';
import type { Equipment } from '../shared/types';
import styles from './PlateCalculator.module.css';

interface Props {
  targetWeight: number;
  barWeight: number;
  equipment: Equipment[];
  isUnilateral: boolean;
  onClose: () => void;
}

export function PlateCalculatorModal({ targetWeight, barWeight, equipment, isUnilateral, onClose }: Props) {
  const plates = equipment
    .filter((e) => e.equipment_type === 'plate' && !e.is_archived)
    .map((e) => ({ weight_kg: e.weight_kg, quantity: e.quantity || 0 }));

  const result = calculatePlates(targetWeight, barWeight, plates);

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h3>Plate Calculator</h3>
        <p className={styles.target}>Target: {targetWeight}kg (bar: {barWeight}kg)</p>
        {result.perSide.length === 0 ? (
          <p className={styles.empty}>Bar only</p>
        ) : (
          <>
            <p className={styles.label}>{isUnilateral ? 'Each side:' : 'Per side:'}</p>
            <div className={styles.plates}>
              {result.perSide.map((w, i) => (
                <span key={i} className={styles.plate}>{w}kg</span>
              ))}
            </div>
          </>
        )}
        {result.remainder > 0 && (
          <p className={styles.remainder}>Cannot load {result.remainder}kg per side</p>
        )}
        <button className={styles.close} onClick={onClose}>Close</button>
      </div>
    </div>
  );
}

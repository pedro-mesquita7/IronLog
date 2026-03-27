import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../../shared/api';
import type { Equipment } from '../../shared/types';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import styles from './EquipmentListPage.module.css';

export function EquipmentListPage() {
  const [items, setItems] = useState<Equipment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<{ equipment: Equipment[] }>('/equipment')
      .then((r) => setItems(r.equipment))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  const bars = items.filter((e) => e.equipment_type === 'bar');
  const plates = items.filter((e) => e.equipment_type === 'plate');
  const machines = items.filter((e) => e.equipment_type === 'machine');

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Equipment</h1>
        <Link to="/equipment/new" className={styles.addBtn}>+ Add</Link>
      </div>

      {items.length === 0 && <p className={styles.empty}>No equipment yet.</p>}

      {bars.length > 0 && (
        <section>
          <h2 className={styles.section}>Bars</h2>
          {bars.map((e) => (
            <Link key={e.equipment_id} to={`/equipment/${e.equipment_id}/edit`} className={styles.item}>
              <span>{e.name}</span>
              <span className={styles.weight}>{e.weight_kg}kg</span>
            </Link>
          ))}
        </section>
      )}

      {plates.length > 0 && (
        <section>
          <h2 className={styles.section}>Plates</h2>
          {plates.map((e) => (
            <Link key={e.equipment_id} to={`/equipment/${e.equipment_id}/edit`} className={styles.item}>
              <span>{e.name}</span>
              <span className={styles.weight}>{e.weight_kg}kg x{e.quantity}</span>
            </Link>
          ))}
        </section>
      )}

      {machines.length > 0 && (
        <section>
          <h2 className={styles.section}>Machines</h2>
          {machines.map((e) => (
            <Link key={e.equipment_id} to={`/equipment/${e.equipment_id}/edit`} className={styles.item}>
              <span>{e.name}</span>
            </Link>
          ))}
        </section>
      )}
    </div>
  );
}

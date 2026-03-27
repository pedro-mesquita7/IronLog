import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { apiFetch, ApiError } from '../../shared/api';
import type { Equipment } from '../../shared/types';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import styles from './EquipmentFormPage.module.css';

export function EquipmentFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = !!id;

  const [name, setName] = useState('');
  const [type, setType] = useState<'bar' | 'plate' | 'machine'>('bar');
  const [weightKg, setWeightKg] = useState('');
  const [quantity, setQuantity] = useState('');
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [showDelete, setShowDelete] = useState(false);

  useEffect(() => {
    if (!id) return;
    apiFetch<{ equipment: Equipment[] }>('/equipment')
      .then((r) => {
        const eq = r.equipment.find((e) => e.equipment_id === id);
        if (eq) {
          setName(eq.name);
          setType(eq.equipment_type);
          setWeightKg(String(eq.weight_kg || ''));
          setQuantity(String(eq.quantity || ''));
        }
      })
      .finally(() => setLoading(false));
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    const body: Record<string, unknown> = { name, equipment_type: type };
    if (weightKg) body.weight_kg = parseFloat(weightKg);
    if (type === 'plate' && quantity) body.quantity = parseInt(quantity);

    try {
      if (isEdit) {
        await apiFetch(`/equipment/${id}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await apiFetch('/equipment', { method: 'POST', body: JSON.stringify(body) });
      }
      navigate('/equipment', { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    await apiFetch(`/equipment/${id}`, { method: 'DELETE' });
    navigate('/equipment', { replace: true });
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className={styles.page}>
      <h1>{isEdit ? 'Edit Equipment' : 'New Equipment'}</h1>
      <form onSubmit={handleSubmit} className={styles.form}>
        <label>Name</label>
        <input value={name} onChange={(e) => setName(e.target.value)} required className={styles.input} />

        <label>Type</label>
        <select value={type} onChange={(e) => setType(e.target.value as typeof type)} className={styles.input}>
          <option value="bar">Bar</option>
          <option value="plate">Plate</option>
          <option value="machine">Machine</option>
        </select>

        <label>Weight (kg)</label>
        <input type="number" step="0.5" value={weightKg} onChange={(e) => setWeightKg(e.target.value)} className={styles.input} />

        {type === 'plate' && (
          <>
            <label>Quantity</label>
            <input type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} className={styles.input} />
          </>
        )}

        {error && <p className={styles.error}>{error}</p>}

        <button type="submit" disabled={saving} className={styles.saveBtn}>
          {saving ? 'Saving...' : 'Save'}
        </button>

        {isEdit && (
          <button type="button" onClick={() => setShowDelete(true)} className={styles.deleteBtn}>
            Archive
          </button>
        )}
      </form>

      <button onClick={() => navigate(-1)} className={styles.backBtn}>Back</button>

      {showDelete && (
        <ConfirmDialog
          message={`Archive ${name}?`}
          onConfirm={handleDelete}
          onCancel={() => setShowDelete(false)}
        />
      )}
    </div>
  );
}

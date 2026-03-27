import { useEffect, useState } from 'react';
import {
  LineChart, Line, BarChart, Bar, ScatterChart, Scatter,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import { apiFetch } from '../../shared/api';
import type { Exercise, ProgressionPoint, RecoveryCorrelationPoint, PRRecord } from '../../shared/types';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import styles from './AnalyticsDashboardPage.module.css';

function toNum(v: string | undefined): number {
  return v ? parseFloat(v) : 0;
}

export function AnalyticsDashboardPage() {
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [selectedExId, setSelectedExId] = useState('');
  const [progression, setProgression] = useState<ProgressionPoint[]>([]);
  const [correlation, setCorrelation] = useState<RecoveryCorrelationPoint[]>([]);
  const [prs, setPrs] = useState<PRRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [exportFrom, setExportFrom] = useState(() => {
    const d = new Date(); d.setDate(d.getDate() - 90);
    return d.toISOString().slice(0, 10);
  });
  const [exportTo, setExportTo] = useState(() => new Date().toISOString().slice(0, 10));
  const [exporting, setExporting] = useState(false);

  // Load exercises + recovery + PRs on mount
  useEffect(() => {
    Promise.all([
      apiFetch<{ exercises: Exercise[] }>('/exercises'),
      apiFetch<{ correlation: RecoveryCorrelationPoint[] }>('/analytics/recovery-correlation'),
      apiFetch<{ prs: PRRecord[] }>('/analytics/prs'),
    ])
      .then(([exRes, corrRes, prRes]) => {
        const active = exRes.exercises.filter((e) => !e.is_archived);
        setExercises(active);
        if (active.length > 0) setSelectedExId(active[0].exercise_id);
        setCorrelation(corrRes.correlation);
        setPrs(prRes.prs);
      })
      .finally(() => setLoading(false));
  }, []);

  // Load progression when exercise changes
  useEffect(() => {
    if (!selectedExId) return;
    apiFetch<{ progression: ProgressionPoint[] }>(`/analytics/progression?exercise_id=${selectedExId}`)
      .then((r) => setProgression(r.progression))
      .catch(() => setProgression([]));
  }, [selectedExId]);

  const handleExport = () => {
    setExporting(true);
    apiFetch<{ export: unknown }>(`/export?from=${exportFrom}&to=${exportTo}`)
      .then((r) => {
        const blob = new Blob([JSON.stringify(r.export, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ironlog-export-${exportFrom}-${exportTo}.json`;
        a.click();
        URL.revokeObjectURL(url);
      })
      .finally(() => setExporting(false));
  };

  if (loading) return <div className={styles.page}><LoadingSpinner /></div>;

  // Chart data transforms
  const progData = progression.map((p) => ({
    week: p.week_start.slice(5),
    maxWeight: toNum(p.max_weight_kg),
    e1rm: toNum(p.max_estimated_1rm),
    volume: toNum(p.weekly_total_load),
    sets: toNum(p.total_sets),
  }));

  const corrData = correlation.map((c) => ({
    recovery: toNum(c.recovery_score),
    load: toNum(c.session_total_load),
    hrv: toNum(c.hrv_rmssd),
    date: c.date,
  }));

  // Muscle group frequency from PR data
  const muscleFreq: Record<string, number> = {};
  prs.forEach((pr) => {
    const ex = exercises.find((e) => e.exercise_id === pr.exercise_id);
    if (ex) muscleFreq[ex.muscle_group] = (muscleFreq[ex.muscle_group] || 0) + 1;
  });
  const freqData = Object.entries(muscleFreq)
    .map(([group, count]) => ({ group, count }))
    .sort((a, b) => b.count - a.count);

  return (
    <div className={styles.page}>
      <h1>Analytics</h1>

      {/* Exercise selector */}
      <div className={styles.selector}>
        <select
          className={styles.select}
          value={selectedExId}
          onChange={(e) => setSelectedExId(e.target.value)}
        >
          {exercises.map((ex) => (
            <option key={ex.exercise_id} value={ex.exercise_id}>{ex.name}</option>
          ))}
        </select>
      </div>

      {/* Weight / e1RM Progression */}
      <div className={styles.section}>
        <h2>Weight & e1RM Progression</h2>
        <div className={styles.chartWrap}>
          {progData.length === 0 ? (
            <p className={styles.empty}>No progression data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={progData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#38383a" />
                <XAxis dataKey="week" stroke="#98989d" fontSize={11} />
                <YAxis yAxisId="left" stroke="#5ac8fa" fontSize={11} />
                <YAxis yAxisId="right" orientation="right" stroke="#0a84ff" fontSize={11} />
                <Tooltip contentStyle={{ background: '#1c1c1e', border: '1px solid #38383a', color: '#fff' }} />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="maxWeight" name="Max Weight" stroke="#5ac8fa" dot={{ r: 3 }} />
                <Line yAxisId="right" type="monotone" dataKey="e1rm" name="Est. 1RM" stroke="#0a84ff" dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Volume Trends */}
      <div className={styles.section}>
        <h2>Weekly Volume</h2>
        <div className={styles.chartWrap}>
          {progData.length === 0 ? (
            <p className={styles.empty}>No volume data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={progData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#38383a" />
                <XAxis dataKey="week" stroke="#98989d" fontSize={11} />
                <YAxis stroke="#98989d" fontSize={11} />
                <Tooltip contentStyle={{ background: '#1c1c1e', border: '1px solid #38383a', color: '#fff' }} />
                <Bar dataKey="volume" name="Total Load" fill="#5ac8fa" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Recovery Correlation */}
      <div className={styles.section}>
        <h2>Recovery vs Training Load</h2>
        <div className={styles.chartWrap}>
          {corrData.length === 0 ? (
            <p className={styles.empty}>No recovery data yet. WHOOP sync required.</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#38383a" />
                <XAxis dataKey="recovery" name="Recovery %" stroke="#98989d" fontSize={11} type="number" domain={[0, 100]} />
                <YAxis dataKey="load" name="Training Load" stroke="#98989d" fontSize={11} />
                <Tooltip
                  contentStyle={{ background: '#1c1c1e', border: '1px solid #38383a', color: '#fff' }}
                  formatter={(val: number, name: string) => [val, name]}
                />
                <Scatter data={corrData} fill="#0a84ff" />
              </ScatterChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* PR Timeline */}
      <div className={styles.section}>
        <h2>PR Timeline</h2>
        {prs.length === 0 ? (
          <p className={styles.empty}>No PRs recorded yet.</p>
        ) : (
          prs.slice(-20).reverse().map((pr, i) => (
            <div key={i} className={styles.prItem}>
              <div>
                <span className={styles.prName}>{pr.exercise_name}</span>
                {pr.is_weight_pr === 'true' && <span className={`${styles.prBadge} ${styles.weightPr}`}>Weight PR</span>}
                {pr.is_e1rm_pr === 'true' && <span className={`${styles.prBadge} ${styles.e1rmPr}`}>e1RM PR</span>}
              </div>
              <span className={styles.prDetail}>
                {pr.weight_kg}kg x {pr.reps} &middot; {pr.timestamp.slice(0, 10)}
              </span>
            </div>
          ))
        )}
      </div>

      {/* Exercise Frequency by Muscle Group */}
      <div className={styles.section}>
        <h2>PR Frequency by Muscle Group</h2>
        <div className={styles.chartWrap}>
          {freqData.length === 0 ? (
            <p className={styles.empty}>No data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={freqData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#38383a" />
                <XAxis type="number" stroke="#98989d" fontSize={11} />
                <YAxis dataKey="group" type="category" stroke="#98989d" fontSize={11} width={80} />
                <Tooltip contentStyle={{ background: '#1c1c1e', border: '1px solid #38383a', color: '#fff' }} />
                <Bar dataKey="count" name="PRs" fill="#0a84ff" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Export */}
      <div className={styles.section}>
        <h2>Export Data</h2>
        <div className={styles.exportBar}>
          <input type="date" value={exportFrom} onChange={(e) => setExportFrom(e.target.value)} className={styles.dateInput} />
          <span className={styles.sep}>to</span>
          <input type="date" value={exportTo} onChange={(e) => setExportTo(e.target.value)} className={styles.dateInput} />
          <button onClick={handleExport} disabled={exporting} className={styles.exportBtn}>
            {exporting ? '...' : 'Export'}
          </button>
        </div>
      </div>
    </div>
  );
}

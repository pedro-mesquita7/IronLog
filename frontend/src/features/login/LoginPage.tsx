import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import styles from './LoginPage.module.css';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) return;
    setError('');
    setLoading(true);
    try {
      await login(token.trim());
      navigate('/', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>IronLog</h1>
      <p className={styles.subtitle}>Gym Session Tracker</p>
      <form onSubmit={handleSubmit} className={styles.form}>
        <input
          type="password"
          placeholder="Auth token"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          className={styles.input}
          autoFocus
        />
        {error && <p className={styles.error}>{error}</p>}
        <button type="submit" disabled={loading || !token.trim()} className={styles.button}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
}

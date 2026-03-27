import { useEffect, useState } from 'react';
import { useOnlineStatus } from '../shared/useOnlineStatus';
import { getQueueLength, replayQueue } from '../shared/offlineQueue';
import styles from './OfflineIndicator.module.css';

export function OfflineIndicator() {
  const online = useOnlineStatus();
  const [queueLen, setQueueLen] = useState(getQueueLength);

  useEffect(() => {
    const id = setInterval(() => setQueueLen(getQueueLength()), 2000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (online && queueLen > 0) {
      replayQueue().then(() => setQueueLen(getQueueLength()));
    }
  }, [online, queueLen]);

  if (online && queueLen === 0) return null;

  return (
    <div className={styles.banner}>
      {!online ? 'Offline' : `Syncing ${queueLen} pending change${queueLen !== 1 ? 's' : ''}...`}
    </div>
  );
}

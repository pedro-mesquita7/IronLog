import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';

interface TimerState {
  exerciseId: string | null;
  endTime: number | null;
  duration: number;
  remaining: number;
  isRunning: boolean;
  startTimer: (exerciseId: string, durationSeconds: number) => void;
  stopTimer: () => void;
}

const TimerContext = createContext<TimerState | null>(null);

function loadFromStorage(): { exerciseId: string | null; endTime: number | null; duration: number } {
  try {
    const data = sessionStorage.getItem('ironlog_timer');
    if (data) {
      const parsed = JSON.parse(data);
      if (parsed.endTime && parsed.endTime > Date.now()) return parsed;
    }
  } catch { /* ignore */ }
  return { exerciseId: null, endTime: null, duration: 0 };
}

export function TimerProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState(loadFromStorage);
  const [remaining, setRemaining] = useState(0);

  const startTimer = useCallback((exerciseId: string, durationSeconds: number) => {
    const endTime = Date.now() + durationSeconds * 1000;
    const newState = { exerciseId, endTime, duration: durationSeconds };
    setState(newState);
    sessionStorage.setItem('ironlog_timer', JSON.stringify(newState));
  }, []);

  const stopTimer = useCallback(() => {
    setState({ exerciseId: null, endTime: null, duration: 0 });
    sessionStorage.removeItem('ironlog_timer');
  }, []);

  useEffect(() => {
    if (!state.endTime) {
      setRemaining(0);
      return;
    }
    const tick = () => {
      const left = Math.max(0, Math.ceil((state.endTime! - Date.now()) / 1000));
      setRemaining(left);
      if (left <= 0) {
        try { navigator.vibrate?.(200); } catch { /* best-effort */ }
        stopTimer();
      }
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [state.endTime, stopTimer]);

  return (
    <TimerContext.Provider
      value={{
        exerciseId: state.exerciseId,
        endTime: state.endTime,
        duration: state.duration,
        remaining,
        isRunning: remaining > 0,
        startTimer,
        stopTimer,
      }}
    >
      {children}
    </TimerContext.Provider>
  );
}

export function useTimer() {
  const ctx = useContext(TimerContext);
  if (!ctx) throw new Error('useTimer must be used within TimerProvider');
  return ctx;
}

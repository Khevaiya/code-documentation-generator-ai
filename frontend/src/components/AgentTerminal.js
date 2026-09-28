import React, { useEffect, useRef } from 'react';
import styles from './AgentTerminal.module.css';
import { Terminal, Activity } from 'lucide-react';

export function AgentTerminal({ logs = [], isRunning = false }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  if (!logs || logs.length === 0) {
    return null;
  }

  return (
    <div className={styles.terminal}>
      <div className={styles.terminalHeader}>
        <div className={styles.terminalDots}>
          <span className={`${styles.dot} ${styles.dotRed}`} />
          <span className={`${styles.dot} ${styles.dotYellow}`} />
          <span className={`${styles.dot} ${styles.dotGreen}`} />
        </div>
        <div className={styles.terminalTitle}>
          <Terminal size={14} />
          Agent Telemetry & Execution Log
        </div>
        {isRunning && <span className={styles.pulseDot} title="Processing..." />}
      </div>
      <div className={styles.terminalBody}>
        {logs.map((log, idx) => (
          <div key={idx} className={styles.logRow}>
            <span className={styles.time}>{log.timestamp}</span>
            <span className={`${styles.badge} ${styles['badge' + (log.level || 'INFO')]}`}>
              {log.level || 'INFO'}
            </span>
            <span className={styles.logMsg}>{log.message}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

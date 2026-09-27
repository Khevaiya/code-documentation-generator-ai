import React from 'react';
import styles from './ProgressTracker.module.css';
import { CheckCircle2, XCircle, Loader2, Clock, Cpu, Sparkles, FileOutput } from 'lucide-react';

const STATUS_STEPS = [
  { key: 'ingesting',   label: 'Ingesting Source',      icon: Cpu },
  { key: 'analyzing',   label: 'Static Analysis',        icon: Cpu },
  { key: 'generating',  label: 'CodeLens Engine Analysis',   icon: Sparkles },
  { key: 'rendering',   label: 'Rendering Outputs',      icon: FileOutput },
  { key: 'completed',   label: 'Complete',               icon: CheckCircle2 },
];

const STATUS_ORDER = ['pending', 'ingesting', 'analyzing', 'generating', 'rendering', 'completed', 'failed'];

function getStepState(stepKey, currentStatus) {
  if (currentStatus === 'failed') return 'idle';
  const currentIdx = STATUS_ORDER.indexOf(currentStatus);
  const stepIdx = STATUS_ORDER.indexOf(stepKey);
  if (stepIdx < currentIdx) return 'done';
  if (stepIdx === currentIdx) return 'active';
  return 'idle';
}

export function ProgressTracker({ job }) {
  const isFailed = job.status === 'failed';
  const isCompleted = job.status === 'completed';

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <div className={styles.statusBadge} data-status={job.status}>
          {isFailed ? <XCircle size={14} /> : isCompleted ? <CheckCircle2 size={14} /> : <Loader2 size={14} className={styles.spin} />}
          {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
        </div>
        <span className={styles.message}>{job.message || 'Processing...'}</span>
      </div>

      {/* Progress bar */}
      <div className={styles.progressBar}>
        <div
          className={`${styles.progressFill} ${isFailed ? styles.failed : ''} ${isCompleted ? styles.done : ''}`}
          style={{ width: `${job.progress}%` }}
        />
      </div>
      <div className={styles.progressPct}>{job.progress}%</div>

      {/* Step indicators */}
      <div className={styles.steps}>
        {STATUS_STEPS.map(({ key, label, icon: Icon }) => {
          const state = getStepState(key, job.status);
          return (
            <div key={key} className={`${styles.step} ${styles[state]}`}>
              <div className={styles.stepIcon}>
                {state === 'done' ? (
                  <CheckCircle2 size={16} />
                ) : state === 'active' ? (
                  <Loader2 size={16} className={styles.spin} />
                ) : (
                  <Clock size={16} />
                )}
              </div>
              <span className={styles.stepLabel}>{label}</span>
            </div>
          );
        })}
      </div>

      {isFailed && (
        <div className={styles.errorBox}>
          <XCircle size={16} />
          <span>{job.error || 'Analysis failed. Please try again.'}</span>
        </div>
      )}
    </div>
  );
}

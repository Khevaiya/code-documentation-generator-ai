import React from 'react';
import styles from './ResultsPanel.module.css';
import { Download, FileText, FileType, Globe, Presentation, FileCode, CheckCircle2, RefreshCw } from 'lucide-react';

const FORMAT_META = {
  markdown: { label: 'Markdown',    icon: FileCode,     color: '#6366F1', ext: '.md' },
  docx:     { label: 'Word Doc',    icon: FileType,     color: '#2563EB', ext: '.docx' },
  pdf:      { label: 'PDF',         icon: FileText,     color: '#DC2626', ext: '.pdf' },
  html:     { label: 'Interactive', icon: Globe,        color: '#059669', ext: '.html' },
  pptx:     { label: 'Slides',      icon: Presentation, color: '#D97706', ext: '.pptx' },
};

const API_BASE = process.env.REACT_APP_API_URL || '';

export function ResultsPanel({ job, onReset }) {
  const outputs = job?.output_files || {};
  const hasOutputs = Object.keys(outputs).length > 0;

  const handleDownload = async (fmt, path) => {
    const url = `${API_BASE}${path}`;
    const res = await fetch(url);
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = path.split('/').pop();
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(blobUrl);
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.successBanner}>
        <CheckCircle2 size={24} color="#10B981" />
        <div>
          <h3 className={styles.successTitle}>Analysis Complete</h3>
          <p className={styles.successSub}>{Object.keys(outputs).length} output file{Object.keys(outputs).length !== 1 ? 's' : ''} ready for download</p>
        </div>
      </div>

      {hasOutputs && (
        <div className={styles.grid}>
          {Object.entries(outputs).map(([fmt, path]) => {
            const meta = FORMAT_META[fmt] || { label: fmt, icon: FileText, color: '#6B7280', ext: '' };
            const Icon = meta.icon;
            return (
              <button
                key={fmt}
                className={styles.downloadCard}
                onClick={() => handleDownload(fmt, path)}
                style={{ '--card-color': meta.color }}
              >
                <div className={styles.cardIconWrap} style={{ background: `${meta.color}20`, color: meta.color }}>
                  <Icon size={24} />
                </div>
                <div className={styles.cardInfo}>
                  <span className={styles.cardLabel}>{meta.label}</span>
                  <span className={styles.cardExt}>{meta.ext}</span>
                </div>
                <div className={styles.downloadIcon}>
                  <Download size={16} />
                </div>
              </button>
            );
          })}
        </div>
      )}

      <button className={styles.resetBtn} onClick={onReset}>
        <RefreshCw size={16} />
        Analyze Another Project
      </button>
    </div>
  );
}

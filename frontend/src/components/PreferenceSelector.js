import React from 'react';
import styles from './PreferenceSelector.module.css';
import {
  Building2, Shield, BookOpen, ClipboardCheck,
  DollarSign, Wrench, Code2, BarChart3,
  FileText, FileType, Globe, Presentation, FileCode
} from 'lucide-react';

export const LENSES = [
  { id: 'architecture',     label: 'Architecture',        icon: Building2,     desc: 'System design, patterns, data flow' },
  { id: 'security',         label: 'Security',            icon: Shield,        desc: 'Vulnerabilities, CVEs, auth gaps' },
  { id: 'onboarding',       label: 'Onboarding',          icon: BookOpen,      desc: 'Dev guide, setup, key concepts' },
  { id: 'compliance',       label: 'Compliance',          icon: ClipboardCheck,desc: 'SOC2, GDPR, OWASP mapping' },
  { id: 'cost_optimization',label: 'Cost Optimization',   icon: DollarSign,    desc: 'N+1 queries, caching, scaling costs' },
  { id: 'technical_debt',   label: 'Technical Debt',      icon: Wrench,        desc: 'TODOs, dead code, outdated deps' },
  { id: 'api_consumer',     label: 'API Consumer',        icon: Code2,         desc: 'Endpoint docs, schemas, examples' },
  { id: 'executive_summary',label: 'Executive Summary',   icon: BarChart3,     desc: 'Business risk & health score' },
];

export const FORMATS = [
  { id: 'markdown', label: 'Markdown',    icon: FileCode,     desc: '.md — GitHub-ready' },
  { id: 'docx',     label: 'Word Doc',    icon: FileType,     desc: '.docx — Professional report' },
  { id: 'pdf',      label: 'PDF',         icon: FileText,     desc: '.pdf — Print-ready' },
  { id: 'html',     label: 'Interactive', icon: Globe,        desc: '.html — Searchable web doc' },
  { id: 'pptx',     label: 'Slides',      icon: Presentation, desc: '.pptx — Stakeholder deck' },
];

export const ROLES = [
  { id: '',                 label: 'No specific role' },
  { id: 'cto',             label: 'CTO / VP Engineering' },
  { id: 'engineer',        label: 'Software Engineer' },
  { id: 'auditor',         label: 'Security Auditor' },
  { id: 'product_manager', label: 'Product Manager' },
];

export function PreferenceSelector({ selectedLenses, selectedFormats, audienceRole, onChange }) {
  const toggleLens = (id) => {
    const next = selectedLenses.includes(id)
      ? selectedLenses.filter(l => l !== id)
      : [...selectedLenses, id];
    onChange({ selectedLenses: next, selectedFormats, audienceRole });
  };

  const toggleFormat = (id) => {
    const next = selectedFormats.includes(id)
      ? selectedFormats.filter(f => f !== id)
      : [...selectedFormats, id];
    onChange({ selectedLenses, selectedFormats: next, audienceRole });
  };

  const selectAllLenses = () => onChange({ selectedLenses: LENSES.map(l => l.id), selectedFormats, audienceRole });
  const clearLenses = () => onChange({ selectedLenses: [], selectedFormats, audienceRole });

  return (
    <div className={styles.wrapper}>
      {/* Analysis Lenses */}
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div>
            <h3 className={styles.sectionTitle}>Analysis Lenses</h3>
            <p className={styles.sectionDesc}>Choose what angle to analyze the codebase from</p>
          </div>
          <div className={styles.bulkActions}>
            <button className={styles.bulkBtn} onClick={selectAllLenses}>All</button>
            <button className={styles.bulkBtn} onClick={clearLenses}>Clear</button>
          </div>
        </div>
        <div className={styles.grid}>
          {LENSES.map(({ id, label, icon: Icon, desc }) => {
            const selected = selectedLenses.includes(id);
            return (
              <button
                key={id}
                className={`${styles.card} ${selected ? styles.selected : ''}`}
                onClick={() => toggleLens(id)}
              >
                <div className={styles.cardIcon}>
                  <Icon size={18} />
                </div>
                <div className={styles.cardContent}>
                  <span className={styles.cardLabel}>{label}</span>
                  <span className={styles.cardDesc}>{desc}</span>
                </div>
                <div className={`${styles.check} ${selected ? styles.checkActive : ''}`}>
                  {selected && <span>✓</span>}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Output Formats */}
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <div>
            <h3 className={styles.sectionTitle}>Output Formats</h3>
            <p className={styles.sectionDesc}>All selected formats are generated in one pass</p>
          </div>
        </div>
        <div className={styles.formatsGrid}>
          {FORMATS.map(({ id, label, icon: Icon, desc }) => {
            const selected = selectedFormats.includes(id);
            return (
              <button
                key={id}
                className={`${styles.formatCard} ${selected ? styles.selected : ''}`}
                onClick={() => toggleFormat(id)}
              >
                <Icon size={20} />
                <span className={styles.formatLabel}>{label}</span>
                <span className={styles.formatDesc}>{desc}</span>
                {selected && <div className={styles.formatCheck}>✓</div>}
              </button>
            );
          })}
        </div>
      </div>

      {/* Audience Role */}
      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Audience Role</h3>
        <p className={styles.sectionDesc}>Tailors the tone and framing of the output</p>
        <div className={styles.rolesGrid}>
          {ROLES.map(({ id, label }) => (
            <button
              key={id}
              className={`${styles.roleBtn} ${audienceRole === id ? styles.selected : ''}`}
              onClick={() => onChange({ selectedLenses, selectedFormats, audienceRole: id })}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

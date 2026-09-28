import React, { useState } from 'react';
import styles from './HealthDashboard.module.css';
import { ShieldCheck, Activity, AlertTriangle, CheckCircle2, Wrench, Shield, Cpu, Gauge, GitBranch, Terminal } from 'lucide-react';

function SvgRadarChart({ data }) {
  const size = 190;
  const center = size / 2;
  const radius = size * 0.38;
  const totalAxes = data.length;

  if (totalAxes < 3) return null;

  // Compute vertices for 100% boundary and actual data polygon
  const angleStep = (2 * Math.PI) / totalAxes;

  const getCoordinates = (index, value) => {
    const angle = index * angleStep - Math.PI / 2;
    const r = (value / 100) * radius;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  };

  const points = data.map((d, i) => {
    const coords = getCoordinates(i, d.score);
    return `${coords.x},${coords.y}`;
  }).join(' ');

  // Grid rings (25%, 50%, 75%, 100%)
  const gridRings = [0.25, 0.5, 0.75, 1.0].map(pct => {
    return data.map((_, i) => {
      const coords = getCoordinates(i, pct * 100);
      return `${coords.x},${coords.y}`;
    }).join(' ');
  });

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* Background Grid Rings */}
      {gridRings.map((ringPoints, idx) => (
        <polygon
          key={idx}
          points={ringPoints}
          fill="transparent"
          stroke="rgba(99, 102, 241, 0.15)"
          strokeWidth="1"
        />
      ))}

      {/* Axis Spokes */}
      {data.map((d, i) => {
        const outer = getCoordinates(i, 100);
        return (
          <line
            key={i}
            x1={center}
            y1={center}
            x2={outer.x}
            y2={outer.y}
            stroke="rgba(99, 102, 241, 0.2)"
            strokeWidth="1"
          />
        );
      })}

      {/* Data Polygon */}
      <polygon
        points={points}
        fill="rgba(6, 182, 212, 0.25)"
        stroke="#06B6D4"
        strokeWidth="2"
      />

      {/* Data Points */}
      {data.map((d, i) => {
        const coords = getCoordinates(i, d.score);
        return (
          <circle
            key={i}
            cx={coords.x}
            cy={coords.y}
            r="3.5"
            fill="#38BDF8"
            stroke="#050811"
            strokeWidth="1.5"
          />
        );
      })}

      {/* Labels */}
      {data.map((d, i) => {
        const coords = getCoordinates(i, 118);
        return (
          <text
            key={i}
            x={coords.x}
            y={coords.y + 3}
            fill="#94A3B8"
            fontSize="8.5"
            fontWeight="500"
            textAnchor="middle"
          >
            {d.subject}
          </text>
        );
      })}
    </svg>
  );
}

export function HealthDashboard({ healthData }) {
  const [severityFilter, setSeverityFilter] = useState('ALL');

  if (!healthData) return null;

  const remediations = healthData.remediations || [];
  const filteredRemediations = severityFilter === 'ALL'
    ? remediations
    : remediations.filter(r => r.severity === severityFilter);

  const pillars = [
    { name: 'Security Posture', score: healthData.security_score, icon: Shield, color: '#EF4444' },
    { name: 'Architecture Modularity', score: healthData.architecture_score, icon: Cpu, color: '#6366F1' },
    { name: 'Performance & Scale', score: healthData.performance_score, icon: Gauge, color: '#06B6D4' },
    { name: 'Maintainability', score: healthData.maintainability_score, icon: GitBranch, color: '#F59E0B' },
    { name: 'Testing & Reliability', score: healthData.reliability_score, icon: CheckCircle2, color: '#10B981' },
  ];

  const gradeClass = `grade${healthData.grade?.replace('+', '_plus') || 'A'}`;

  return (
    <div className={styles.wrapper}>
      {/* Top Section: Grade + Radar */}
      <div className={styles.topSection}>
        {/* Overall Grade Card */}
        <div className={styles.gradeCard}>
          <div className={styles.scoreCircle}>
            <span className={`${styles.gradeLetter} ${styles[gradeClass]}`}>
              {healthData.grade || 'A'}
            </span>
            <span className={styles.scoreNum}>{healthData.overall_score || 0} / 100</span>
          </div>
          <h3 className={styles.gradeTitle}>Executive Codebase Health</h3>
          <p className={styles.gradeSub}>{healthData.summary_text}</p>
        </div>

        {/* Radar Chart Card */}
        <div className={styles.radarCard}>
          <div className={styles.cardHeader}>
            <h4 className={styles.cardTitle}>
              <Activity size={16} color="#06B6D4" />
              5-Pillar Architectural Balance
            </h4>
            <span style={{ fontSize: '0.75rem', color: '#64748B' }}>Weighted AI Evaluation</span>
          </div>
          <div className={styles.radarContainer}>
            <SvgRadarChart data={healthData.radar_data || []} />
          </div>
        </div>
      </div>

      {/* 5 Pillar Breakdown Cards */}
      <div className={styles.pillarGrid}>
        {pillars.map(p => {
          const Icon = p.icon;
          return (
            <div key={p.name} className={styles.pillarCard}>
              <div className={styles.pillarTop}>
                <span className={styles.pillarName}>{p.name}</span>
                <Icon size={16} color={p.color} />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                <span className={styles.pillarScore}>{p.score}%</span>
                <span style={{ fontSize: '0.72rem', color: p.score >= 80 ? '#10B981' : (p.score >= 60 ? '#F59E0B' : '#EF4444') }}>
                  {p.score >= 80 ? 'Optimal' : (p.score >= 60 ? 'Moderate' : 'Action Req.')}
                </span>
              </div>
              <div className={styles.meterBg}>
                <div
                  className={styles.meterFill}
                  style={{ width: `${p.score}%`, background: p.color }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Actionable Remediation Items */}
      <div className={styles.remediationsSection}>
        <div className={styles.remHeader}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Wrench size={18} color="#818CF8" />
            <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text)' }}>
              Prioritized Remediation Roadmap ({remediations.length})
            </h4>
          </div>

          <div className={styles.filterChips}>
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(sev => (
              <button
                key={sev}
                className={`${styles.filterChip} ${severityFilter === sev ? styles.active : ''}`}
                onClick={() => setSeverityFilter(sev)}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.remList}>
          {filteredRemediations.map((item, idx) => (
            <div key={item.id || idx} className={styles.remCard}>
              <div className={styles.remCardTop}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className={`${styles.sevBadge} ${styles['sev' + item.severity]}`}>
                    {item.severity}
                  </span>
                  <span className={styles.remTitle}>{item.title}</span>
                </div>
                {item.file_path && (
                  <span style={{ fontSize: '0.72rem', color: '#64748B', fontFamily: 'var(--font-mono)' }}>
                    {item.file_path}
                  </span>
                )}
              </div>
              <p className={styles.remDesc}>{item.description}</p>
              {item.suggested_fix && (
                <div className={styles.fixBox}>
                  <CheckCircle2 size={14} style={{ minWidth: 14, marginTop: 2 }} />
                  <span><strong>Fix:</strong> {item.suggested_fix}</span>
                </div>
              )}
            </div>
          ))}

          {filteredRemediations.length === 0 && (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#64748B', fontSize: '0.85rem' }}>
              ✓ No {severityFilter !== 'ALL' ? severityFilter : ''} issues found in this category!
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

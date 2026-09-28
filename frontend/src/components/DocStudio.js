import React, { useState } from 'react';
import styles from './DocStudio.module.css';
import {
  Layers, Shield, UserCheck, CheckSquare, DollarSign, Wrench,
  Globe, FileText, Code2, Download, Copy, Check, Eye, Maximize2, ZoomIn, ZoomOut
} from 'lucide-react';

const LENS_META = {
  architecture:      { label: 'Architecture',        icon: Layers,        color: '#6366F1' },
  security:          { label: 'Security Audit',      icon: Shield,        color: '#EF4444' },
  onboarding:        { label: 'Developer Onboard',   icon: UserCheck,     color: '#06B6D4' },
  compliance:        { label: 'Compliance & SOC2',   icon: CheckSquare,   color: '#8B5CF6' },
  cost_optimization: { label: 'Cost & Scalability',  icon: DollarSign,    color: '#10B981' },
  technical_debt:    { label: 'Technical Debt',      icon: Wrench,        color: '#F59E0B' },
  api_consumer:      { label: 'API Reference',       icon: Globe,         color: '#3B82F6' },
  executive_summary: { label: 'Executive Summary',   icon: FileText,      color: '#EC4899' },
};

export function DocStudio({ docModel }) {
  const lenses = docModel?.lens_results || [];
  const [activeLensIdx, setActiveLensIdx] = useState(0);
  const [viewMode, setViewMode] = useState('rich'); // 'rich' | 'raw'
  const [copiedDiag, setCopiedDiag] = useState(null);
  const [copiedRaw, setCopiedRaw] = useState(false);
  const [diagramScale, setDiagramScale] = useState(1);

  if (lenses.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: '#94A3B8' }}>
        No documentation lenses generated.
      </div>
    );
  }

  const activeLens = lenses[activeLensIdx] || lenses[0];
  const meta = LENS_META[activeLens.lens_type] || { label: activeLens.lens_type, icon: FileText, color: '#6366F1' };
  const LensIcon = meta.icon;

  const handleCopyCode = (code, id) => {
    navigator.clipboard.writeText(code);
    setCopiedDiag(id);
    setTimeout(() => setCopiedDiag(null), 2000);
  };

  const handleCopyRawMarkdown = () => {
    const text = `# ${activeLens.title || meta.label}\n\n${activeLens.summary}\n\n` +
      activeLens.findings.map(f => `### ${f.title}\n${f.description}\n`).join('\n');
    navigator.clipboard.writeText(text);
    setCopiedRaw(true);
    setTimeout(() => setCopiedRaw(false), 2000);
  };

  const handleDownloadSvg = (svgContent, title) => {
    if (!svgContent) return;
    const blob = new Blob([svgContent], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/\s+/g, '_').toLowerCase()}.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className={styles.studio}>
      {/* Left Sidebar: Lens Switcher */}
      <div className={styles.sidebar}>
        <div className={styles.sidebarTitle}>Generated Lenses ({lenses.length})</div>
        <div className={styles.lensNavList}>
          {lenses.map((lens, idx) => {
            const lMeta = LENS_META[lens.lens_type] || { label: lens.lens_type, icon: FileText, color: '#6366F1' };
            const Icon = lMeta.icon;
            const isActive = idx === activeLensIdx;
            return (
              <button
                key={lens.lens_type}
                className={`${styles.lensNavBtn} ${isActive ? styles.active : ''}`}
                onClick={() => { setActiveLensIdx(idx); setDiagramScale(1); }}
              >
                <div className={styles.lensNavLeft}>
                  <Icon size={16} color={isActive ? '#818CF8' : lMeta.color} />
                  <span>{lMeta.label}</span>
                </div>
                {lens.findings?.length > 0 && (
                  <span className={styles.lensFindingCount}>{lens.findings.length}</span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Reading & Diagram Panel */}
      <div className={styles.mainPanel}>
        {/* Header */}
        <div className={styles.headerRow}>
          <div className={styles.lensTitle}>
            <LensIcon size={22} color={meta.color} />
            <span>{activeLens.title || meta.label}</span>
          </div>

          <div className={styles.viewModeTabs}>
            <button
              className={`${styles.viewModeBtn} ${viewMode === 'rich' ? styles.active : ''}`}
              onClick={() => setViewMode('rich')}
            >
              <Eye size={12} style={{ display: 'inline', marginRight: 4 }} />
              Rich View
            </button>
            <button
              className={`${styles.viewModeBtn} ${viewMode === 'raw' ? styles.active : ''}`}
              onClick={() => setViewMode('raw')}
            >
              <Code2 size={12} style={{ display: 'inline', marginRight: 4 }} />
              Raw Markdown
            </button>
          </div>
        </div>

        {/* Rich View Mode */}
        {viewMode === 'rich' ? (
          <>
            {/* Executive Summary Box */}
            <div className={styles.summaryBox}>
              <p>{activeLens.summary}</p>
            </div>

            {/* Diagrams Section */}
            {activeLens.diagrams && activeLens.diagrams.length > 0 && (
              <div>
                <h4 className={styles.sectionHeading}>
                  <Layers size={16} color="#818CF8" />
                  Interactive Architecture Diagrams ({activeLens.diagrams.length})
                </h4>

                {activeLens.diagrams.map((diag, dIdx) => (
                  <div key={dIdx} className={styles.diagramCard}>
                    <div className={styles.diagramHeader}>
                      <span className={styles.diagramTitle}>{diag.title}</span>
                      <div className={styles.diagramControls}>
                        <button
                          className={styles.toolBtn}
                          onClick={() => setDiagramScale(s => Math.min(2.5, s + 0.2))}
                          title="Zoom In"
                        >
                          <ZoomIn size={13} />
                        </button>
                        <button
                          className={styles.toolBtn}
                          onClick={() => setDiagramScale(s => Math.max(0.5, s - 0.2))}
                          title="Zoom Out"
                        >
                          <ZoomOut size={13} />
                        </button>
                        <button
                          className={styles.toolBtn}
                          onClick={() => handleCopyCode(diag.mermaid_code, dIdx)}
                        >
                          {copiedDiag === dIdx ? <Check size={13} color="#10B981" /> : <Copy size={13} />}
                          <span>{copiedDiag === dIdx ? 'Copied' : 'Copy Mermaid'}</span>
                        </button>
                        {diag.svg && (
                          <button
                            className={styles.toolBtn}
                            onClick={() => handleDownloadSvg(diag.svg, diag.title)}
                          >
                            <Download size={13} />
                            <span>SVG</span>
                          </button>
                        )}
                      </div>
                    </div>

                    <div className={styles.diagramCanvas}>
                      {diag.svg ? (
                        <div
                          style={{
                            transform: `scale(${diagramScale})`,
                            transformOrigin: 'center center',
                            transition: 'transform 0.2s',
                            maxWidth: '100%'
                          }}
                          dangerouslySetInnerHTML={{ __html: diag.svg }}
                        />
                      ) : (
                        <pre style={{ color: '#818CF8', fontSize: '0.8rem', padding: '1rem', overflowX: 'auto' }}>
                          {diag.mermaid_code}
                        </pre>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Findings Section */}
            {activeLens.findings && activeLens.findings.length > 0 && (
              <div>
                <h4 className={styles.sectionHeading}>
                  <Shield size={16} color="#06B6D4" />
                  Key Findings & Citations ({activeLens.findings.length})
                </h4>

                {activeLens.findings.map((f, fIdx) => (
                  <div key={fIdx} className={styles.findingCard}>
                    <div className={styles.findingTop}>
                      <span className={styles.findingTitle}>{f.title}</span>
                      {f.severity && (
                        <span style={{ fontSize: '0.7rem', color: '#F87171', fontWeight: 600, textTransform: 'uppercase' }}>
                          [{f.severity}]
                        </span>
                      )}
                    </div>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      {f.description}
                    </p>

                    {/* Citations */}
                    {f.citations && f.citations.length > 0 && (
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: 4 }}>
                        {f.citations.map((c, cIdx) => (
                          <span key={cIdx} className={styles.citationPill}>
                            📄 {c.file_path}{c.line_start ? `:${c.line_start}` : ''}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Recommendation */}
                    {f.recommendation && (
                      <div className={styles.recommendBox}>
                        <strong>Action:</strong> {f.recommendation}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Gaps Section */}
            {activeLens.gaps && activeLens.gaps.length > 0 && (
              <div style={{ marginTop: '1rem' }}>
                <h4 className={styles.sectionHeading} style={{ color: '#F59E0B' }}>
                  ⚠️ Gap Detection & Missing Components ({activeLens.gaps.length})
                </h4>
                {activeLens.gaps.map((g, gIdx) => (
                  <div key={gIdx} className={styles.findingCard} style={{ borderLeft: '3px solid #F59E0B' }}>
                    <strong>{g.area}:</strong> {g.description}
                    {g.recommendation && (
                      <span style={{ fontSize: '0.8rem', color: '#34D399', marginTop: 4 }}>
                        ↳ Recommendation: {g.recommendation}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          /* Raw Markdown View Mode */
          <div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.5rem' }}>
              <button className={styles.toolBtn} onClick={handleCopyRawMarkdown}>
                {copiedRaw ? <Check size={13} color="#10B981" /> : <Copy size={13} />}
                <span>{copiedRaw ? 'Copied Full Markdown' : 'Copy Markdown'}</span>
              </button>
            </div>
            <pre className={styles.rawCodeBlock}>
              {`# ${activeLens.title || meta.label}\n\n${activeLens.summary}\n\n` +
                activeLens.findings.map(f => `### ${f.title}\n${f.description}\n`).join('\n')}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

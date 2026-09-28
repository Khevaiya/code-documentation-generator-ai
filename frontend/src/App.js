import React, { useState } from 'react';
import styles from './App.module.css';
import { InputPanel } from './components/InputPanel';
import { PreferenceSelector } from './components/PreferenceSelector';
import { ProgressTracker } from './components/ProgressTracker';
import { ResultsPanel } from './components/ResultsPanel';
import { AgentTerminal } from './components/AgentTerminal';
import { DocStudio } from './components/DocStudio';
import { KnowledgeGraphViewer } from './components/KnowledgeGraphViewer';
import { HealthDashboard } from './components/HealthDashboard';
import { ArchitectureCopilot } from './components/ArchitectureCopilot';
import { ExportModal } from './components/ExportModal';
import { useAnalysis } from './hooks/useAnalysis';
import {
  Cpu, ChevronRight, AlertCircle, Zap, FileText, Network,
  Activity, Download, Share2, Bot, Sparkles, RefreshCw
} from 'lucide-react';

const DEFAULT_LENSES = ['architecture', 'security', 'onboarding', 'api_consumer', 'executive_summary'];
const DEFAULT_FORMATS = ['markdown', 'html', 'pdf', 'docx', 'pptx'];

export default function App() {
  const [input, setInput] = useState(null);
  const [prefs, setPrefs] = useState({
    selectedLenses: DEFAULT_LENSES,
    selectedFormats: DEFAULT_FORMATS,
    audienceRole: '',
  });

  // Active view tab when analysis completes: 'studio' | 'graph' | 'health' | 'downloads'
  const [activeTab, setActiveTab] = useState('studio');
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);

  const { job, error, isSubmitting, submitGithub, submitZip, reset } = useAnalysis();

  const isRunning = job && !['completed', 'failed'].includes(job.status);
  const isCompleted = job?.status === 'completed';
  const showForm = !job || job.status === 'failed';

  const handleSubmit = () => {
    if (!input) return;
    if (prefs.selectedLenses.length === 0) return;
    if (prefs.selectedFormats.length === 0) return;

    const params = {
      lenses: prefs.selectedLenses,
      output_formats: prefs.selectedFormats,
      audience_role: prefs.audienceRole || undefined,
      project_name: input.projectName || undefined,
    };

    if (input.type === 'github') {
      submitGithub({ ...params, github_url: input.github_url });
    } else {
      submitZip({ ...params, file: input.file });
    }
  };

  const canSubmit = input && prefs.selectedLenses.length > 0 && prefs.selectedFormats.length > 0 && !isSubmitting && !isRunning;

  const handleReset = () => {
    reset();
    setInput(null);
    setPrefs({ selectedLenses: DEFAULT_LENSES, selectedFormats: DEFAULT_FORMATS, audienceRole: '' });
    setActiveTab('studio');
  };

  return (
    <div className={styles.app}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.logo} onClick={handleReset}>
            <div className={styles.logoIcon}><Cpu size={22} /></div>
            <div>
              <div className={styles.logoTitle}>CodeLens AI</div>
              <div className={styles.logoSub}>Codebase Intelligence & Documentation Agent</div>
            </div>
          </div>

          {/* Navigation Tabs (Available when completed) */}
          {isCompleted && (
            <div className={styles.headerTabs}>
              <button
                className={`${styles.tabBtn} ${activeTab === 'studio' ? styles.active : ''}`}
                onClick={() => setActiveTab('studio')}
              >
                <FileText size={15} />
                Doc Studio
              </button>
              <button
                className={`${styles.tabBtn} ${activeTab === 'graph' ? styles.active : ''}`}
                onClick={() => setActiveTab('graph')}
              >
                <Network size={15} />
                Knowledge Graph
              </button>
              <button
                className={`${styles.tabBtn} ${activeTab === 'health' ? styles.active : ''}`}
                onClick={() => setActiveTab('health')}
              >
                <Activity size={15} />
                Health Scorecard
              </button>
              <button
                className={`${styles.tabBtn} ${activeTab === 'downloads' ? styles.active : ''}`}
                onClick={() => setActiveTab('downloads')}
              >
                <Download size={15} />
                Downloads
              </button>
            </div>
          )}

          {/* Header Action Buttons */}
          <div className={styles.headerActions}>
            {isCompleted && (
              <>
                <button
                  className={styles.exportTriggerBtn}
                  onClick={() => setIsExportOpen(true)}
                  title="1-Click Ecosystem Exports"
                >
                  <Share2 size={15} />
                  Export
                </button>
                <button
                  className={styles.copilotTriggerBtn}
                  onClick={() => setIsCopilotOpen(true)}
                >
                  <Bot size={16} />
                  Ask Copilot
                </button>
              </>
            )}
            {!isCompleted && (
              <div className={styles.headerBadge}>
                <Zap size={13} />
                Powered by Gemini 2.5 Flash
              </div>
            )}
          </div>
        </div>
      </header>

      <main className={styles.main}>
        {/* If Completed: Tab Views */}
        {isCompleted ? (
          <div>
            {/* Top Toolbar */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <div>
                <h2 style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--text)' }}>
                  {job.doc_model?.project_name || 'Codebase'} Intelligence Hub
                </h2>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  Generated across {job.doc_model?.lens_results?.length || 0} lenses &bull; Knowledge Graph mapped
                </p>
              </div>

              <button
                onClick={handleReset}
                style={{
                  background: 'rgba(19, 30, 54, 0.7)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-secondary)',
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-sm)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  fontSize: '0.82rem'
                }}
              >
                <RefreshCw size={13} />
                Analyze Another Codebase
              </button>
            </div>

            {/* Tab 1: Doc Studio */}
            {activeTab === 'studio' && (
              <DocStudio docModel={job.doc_model} />
            )}

            {/* Tab 2: Knowledge Graph */}
            {activeTab === 'graph' && (
              <KnowledgeGraphViewer
                graphData={job.knowledge_graph}
                onAskCopilotAboutNode={(node) => setIsCopilotOpen(true)}
              />
            )}

            {/* Tab 3: Health Dashboard */}
            {activeTab === 'health' && (
              <HealthDashboard healthData={job.health_score} />
            )}

            {/* Tab 4: Downloads */}
            {activeTab === 'downloads' && (
              <ResultsPanel job={job} onReset={handleReset} />
            )}
          </div>
        ) : (
          /* Form & Analysis State */
          <>
            {/* Hero */}
            <div className={styles.hero}>
              <div className={styles.heroGlow} />
              <h1 className={styles.heroTitle}>
                Turn any codebase into<br />
                <span className={styles.heroAccent}>interactive architecture & intelligence</span>
              </h1>
              <p className={styles.heroSub}>
                Upload a repository or enter a GitHub URL. Generate multi-lens documentation,
                interactive Code Knowledge Graphs, security scorecards, and consult with your AI Architecture Copilot.
              </p>
              <div className={styles.heroBadges}>
                {['8 Analysis Lenses', 'Interactive CodeKG', 'Executive Scorecard', 'AI Architecture Copilot', '1-Click Docusaurus Export'].map(b => (
                  <span key={b} className={styles.heroBadge}>{b}</span>
                ))}
              </div>
            </div>

            {/* Main Configuration Card */}
            <div className={styles.card}>
              {/* Step 1: Input */}
              <div className={styles.step}>
                <div className={styles.stepNum}>1</div>
                <div className={styles.stepContent}>
                  <h2 className={styles.stepTitle}>Source Code Ingestion</h2>
                  <p className={styles.stepDesc}>Enter a public GitHub URL or upload a project ZIP archive</p>
                </div>
              </div>
              <div className={styles.stepBody}>
                <InputPanel onInputChange={setInput} />
              </div>

              <div className={styles.divider} />

              {/* Step 2: Preferences */}
              <div className={styles.step}>
                <div className={styles.stepNum}>2</div>
                <div className={styles.stepContent}>
                  <h2 className={styles.stepTitle}>Analysis & Synthesis Lenses</h2>
                  <p className={styles.stepDesc}>
                    {prefs.selectedLenses.length} lens{prefs.selectedLenses.length !== 1 ? 'es' : ''} &bull; {prefs.selectedFormats.length} format{prefs.selectedFormats.length !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
              <div className={styles.stepBody}>
                <PreferenceSelector
                  selectedLenses={prefs.selectedLenses}
                  selectedFormats={prefs.selectedFormats}
                  audienceRole={prefs.audienceRole}
                  onChange={setPrefs}
                />
              </div>

              {/* Error Display */}
              {error && (
                <div className={styles.errorBanner}>
                  <AlertCircle size={16} />
                  <span>{error}</span>
                </div>
              )}

              {/* Job progress & Live Terminal Stream */}
              {job && (
                <div className={styles.stepBody}>
                  <ProgressTracker job={job} />
                  <AgentTerminal logs={job.terminal_logs || []} isRunning={isRunning} />
                </div>
              )}

              {/* Submit Row */}
              {showForm && (
                <div className={styles.submitRow}>
                  <div className={styles.submitMeta}>
                    {prefs.selectedLenses.length > 0 && prefs.selectedFormats.length > 0 ? (
                      <span className={styles.submitInfo}>
                        Generating {prefs.selectedLenses.length} lenses, Code Knowledge Graph, and Health Scorecard
                      </span>
                    ) : (
                      <span className={styles.submitWarning}>Select at least one lens and format to continue</span>
                    )}
                  </div>
                  <button
                    className={`${styles.submitBtn} ${!canSubmit ? styles.disabled : ''}`}
                    onClick={handleSubmit}
                    disabled={!canSubmit}
                  >
                    {isSubmitting ? 'Starting Agent...' : 'Analyze & Map Codebase'}
                    <ChevronRight size={18} />
                  </button>
                </div>
              )}
            </div>

            {/* Features Strip */}
            <div className={styles.features}>
              {[
                { title: '🌐 Code Knowledge Graph', desc: 'Auto-constructs an in-memory 2D graph of all files, functions, routes, and call links.' },
                { title: '💬 Architecture Copilot', desc: 'Chat directly with your codebase with verified citations, blast radius analysis, and dynamic diagrams.' },
                { title: '📊 Executive Scorecard', desc: '0–100 letter grades across Security, Modularity, Performance, and Testing with remediation guides.' },
                { title: '⚡ 1-Click Ecosystem Export', desc: 'Export full Docusaurus websites, GitHub Wikis, or GitHub PR review comments in 1 click.' },
              ].map(f => (
                <div key={f.title} className={styles.feature}>
                  <h4 className={styles.featureTitle}>{f.title}</h4>
                  <p className={styles.featureDesc}>{f.desc}</p>
                </div>
              ))}
            </div>
          </>
        )}
      </main>

      {/* Slide-out Architecture Copilot Drawer */}
      {isCompleted && (
        <ArchitectureCopilot
          jobId={job.job_id}
          isOpen={isCopilotOpen}
          onClose={() => setIsCopilotOpen(false)}
        />
      )}

      {/* 1-Click Ecosystem Export Modal */}
      {isCompleted && (
        <ExportModal
          jobId={job.job_id}
          isOpen={isExportOpen}
          onClose={() => setIsExportOpen(false)}
        />
      )}

      <footer className={styles.footer}>
        <span>CodeLens AI · Codebase Intelligence & Documentation Agent · Powered by Google Gemini</span>
      </footer>
    </div>
  );
}

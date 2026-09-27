import React, { useState } from 'react';
import styles from './App.module.css';
import { InputPanel } from './components/InputPanel';
import { PreferenceSelector } from './components/PreferenceSelector';
import { ProgressTracker } from './components/ProgressTracker';
import { ResultsPanel } from './components/ResultsPanel';
import { useAnalysis } from './hooks/useAnalysis';
import { Cpu, ChevronRight, AlertCircle, Zap } from 'lucide-react';

const DEFAULT_LENSES = ['architecture', 'security', 'onboarding'];
const DEFAULT_FORMATS = ['markdown', 'html'];

export default function App() {
  const [input, setInput] = useState(null);
  const [prefs, setPrefs] = useState({
    selectedLenses: DEFAULT_LENSES,
    selectedFormats: DEFAULT_FORMATS,
    audienceRole: '',
  });

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
  };

  return (
    <div className={styles.app}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.logo}>
            <div className={styles.logoIcon}><Cpu size={20} /></div>
            <div>
              <div className={styles.logoTitle}>CodeLens AI</div>
              <div className={styles.logoSub}>Codebase Analysis Agent</div>
            </div>
          </div>
          <div className={styles.headerBadge}>
            <Zap size={12} />
             Powered by CodeLens Engine
          </div>
        </div>
      </header>

      <main className={styles.main}>
        {/* Hero */}
        <div className={styles.hero}>
          <div className={styles.heroGlow} />
          <h1 className={styles.heroTitle}>
            Turn any codebase into<br />
            <span className={styles.heroAccent}>enterprise-grade documentation</span>
          </h1>
          <p className={styles.heroSub}>
            Upload a repo or paste a GitHub URL. Select your analysis lenses and output formats.
            <br />Get architecture diagrams, security audits, onboarding guides and more 
          </p>
          <div className={styles.heroBadges}>
            {['8 Analysis Lenses', '5 Output Formats', 'Diagrams', 'Gap Detection', 'Confidence Scores'].map(b => (
              <span key={b} className={styles.heroBadge}>{b}</span>
            ))}
          </div>
        </div>

        {/* Main Card */}
        <div className={styles.card}>
          {isCompleted ? (
            <ResultsPanel job={job} onReset={handleReset} />
          ) : (
            <>
              {/* Step 1: Input */}
              <div className={styles.step}>
                <div className={styles.stepNum}>1</div>
                <div className={styles.stepContent}>
                  <h2 className={styles.stepTitle}>Source Code</h2>
                  <p className={styles.stepDesc}>GitHub URL or ZIP archive</p>
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
                  <h2 className={styles.stepTitle}>Analysis Preferences</h2>
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

              <div className={styles.divider} />

              {/* Error */}
              {error && (
                <div className={styles.errorBanner}>
                  <AlertCircle size={16} />
                  <span>{error}</span>
                </div>
              )}

              {/* Job progress */}
              {job && (
                <div className={styles.stepBody}>
                  <ProgressTracker job={job} />
                </div>
              )}

              {/* Submit */}
              {showForm && (
                <div className={styles.submitRow}>
                  <div className={styles.submitMeta}>
                    {prefs.selectedLenses.length > 0 && prefs.selectedFormats.length > 0 ? (
                      <span className={styles.submitInfo}>
                        Running {prefs.selectedLenses.length} lenses → generating {prefs.selectedFormats.length} output files
                      </span>
                    ) : (
                      <span className={styles.submitWarning}>Select at least one lens and one format</span>
                    )}
                  </div>
                  <button
                    className={`${styles.submitBtn} ${!canSubmit ? styles.disabled : ''}`}
                    onClick={handleSubmit}
                    disabled={!canSubmit}
                  >
                    {isSubmitting ? 'Starting...' : 'Analyze Codebase'}
                    <ChevronRight size={18} />
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        {/* Features strip */}
        <div className={styles.features}>
          {[
            { title: 'Multi-pass Analysis', desc: 'Not one-shot — The agent understands your project before generating documentation.' },
            { title: 'Diagrams Included', desc: 'Auto-generated architecture, sequence, and ER diagrams in every report.' },
            { title: 'Confidence Citations', desc: 'Every claim links to the exact file and line it was inferred from.' },
            { title: 'Gap Detection', desc: 'Flags missing tests, undocumented APIs, absent error handling, and more.' },
          ].map(f => (
            <div key={f.title} className={styles.feature}>
              <h4 className={styles.featureTitle}>{f.title}</h4>
              <p className={styles.featureDesc}>{f.desc}</p>
            </div>
          ))}
        </div>
      </main>

      <footer className={styles.footer}>
        <span>Codebase Analysis Agent · Powered by CodeLens Engine</span>
      </footer>
    </div>
  );
}

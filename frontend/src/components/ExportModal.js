import React, { useState } from 'react';
import axios from 'axios';
import styles from './ExportModal.module.css';
import { Share2, Globe, BookOpen, GitPullRequest, Download, Copy, Check, X, Loader2 } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || '';

export function ExportModal({ jobId, isOpen, onClose }) {
  const [copiedPR, setCopiedPR] = useState(false);
  const [prPreview, setPrPreview] = useState(null);
  const [loadingPR, setLoadingPR] = useState(false);

  if (!isOpen) return null;

  const handleDownloadZip = (type, filename) => {
    const url = `${API_BASE}/download/${jobId}/export/${type}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleFetchPR = async () => {
    if (prPreview) {
      navigator.clipboard.writeText(prPreview);
      setCopiedPR(true);
      setTimeout(() => setCopiedPR(false), 2000);
      return;
    }

    setLoadingPR(true);
    try {
      const res = await axios.get(`${API_BASE}/download/${jobId}/export/pr_review`);
      setPrPreview(res.data);
      navigator.clipboard.writeText(res.data);
      setCopiedPR(true);
      setTimeout(() => setCopiedPR(false), 2000);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingPR(false);
    }
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.titleArea}>
            <Share2 size={20} color="#818CF8" />
            <h3 className={styles.title}>1-Click Ecosystem Exports</h3>
          </div>
          <button className={styles.closeBtn} onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Body Options */}
        <div className={styles.body}>
          {/* Option 1: Docusaurus Site */}
          <div className={styles.exportCard}>
            <div className={styles.cardLeft}>
              <div className={styles.iconWrap} style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818CF8' }}>
                <Globe size={20} />
              </div>
              <div>
                <h4 className={styles.cardTitle}>Docusaurus / VitePress Site</h4>
                <p className={styles.cardDesc}>Ready-to-deploy static documentation website bundle</p>
              </div>
            </div>
            <button
              className={styles.actionBtn}
              onClick={() => handleDownloadZip('docusaurus', 'docusaurus_site.zip')}
            >
              <Download size={14} />
              Download .zip
            </button>
          </div>

          {/* Option 2: GitHub Wiki */}
          <div className={styles.exportCard}>
            <div className={styles.cardLeft}>
              <div className={styles.iconWrap} style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10B981' }}>
                <BookOpen size={20} />
              </div>
              <div>
                <h4 className={styles.cardTitle}>GitHub Wiki Repository</h4>
                <p className={styles.cardDesc}>Pre-structured wiki pages with sidebar and cross-links</p>
              </div>
            </div>
            <button
              className={styles.actionBtn}
              style={{ background: '#059669' }}
              onClick={() => handleDownloadZip('github_wiki', 'github_wiki.zip')}
            >
              <Download size={14} />
              Download .zip
            </button>
          </div>

          {/* Option 3: GitHub PR Review Bot Comment */}
          <div className={styles.exportCard}>
            <div className={styles.cardLeft}>
              <div className={styles.iconWrap} style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#F59E0B' }}>
                <GitPullRequest size={20} />
              </div>
              <div>
                <h4 className={styles.cardTitle}>GitHub PR Review Markdown</h4>
                <p className={styles.cardDesc}>Collapsible summary formatted for GitHub Actions or PRs</p>
              </div>
            </div>
            <button
              className={styles.actionBtn}
              style={{ background: '#D97706' }}
              onClick={handleFetchPR}
              disabled={loadingPR}
            >
              {loadingPR ? (
                <Loader2 size={14} className="spin" style={{ animation: 'spin 1s linear infinite' }} />
              ) : copiedPR ? (
                <Check size={14} color="#FFF" />
              ) : (
                <Copy size={14} />
              )}
              {copiedPR ? 'Copied to Clipboard' : 'Copy PR Markdown'}
            </button>
          </div>

          {/* PR Preview snippet */}
          {prPreview && (
            <div className={styles.previewArea}>
              {prPreview}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

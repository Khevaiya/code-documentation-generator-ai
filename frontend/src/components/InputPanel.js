import React, { useState, useRef } from 'react';
import styles from './InputPanel.module.css';
import { Github, Upload, FolderOpen, X } from 'lucide-react';

export function InputPanel({ onInputChange }) {
  const [mode, setMode] = useState('github'); // 'github' | 'zip'
  const [githubUrl, setGithubUrl] = useState('');
  const [file, setFile] = useState(null);
  const [projectName, setProjectName] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef();

  const handleFileChange = (f) => {
    if (f && f.name.endsWith('.zip')) {
      setFile(f);
      const name = f.name.replace('.zip', '');
      setProjectName(name);
      onInputChange({ type: 'zip', file: f, projectName: name });
    }
  };

  const handleGithubChange = (url) => {
    setGithubUrl(url);
    const match = url.match(/github\.com\/[^/]+\/([^/?\s]+)/);
    const name = match ? match[1] : '';
    setProjectName(name);
    onInputChange({ type: 'github', github_url: url, projectName: name });
  };

  const handleProjectNameChange = (name) => {
    setProjectName(name);
    if (mode === 'github') onInputChange({ type: 'github', github_url: githubUrl, projectName: name });
    else onInputChange({ type: 'zip', file, projectName: name });
  };

  return (
    <div className={styles.panel}>
      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${mode === 'github' ? styles.active : ''}`}
          onClick={() => setMode('github')}
        >
          <Github size={16} /> GitHub URL
        </button>
        <button
          className={`${styles.tab} ${mode === 'zip' ? styles.active : ''}`}
          onClick={() => setMode('zip')}
        >
          <Upload size={16} /> ZIP Upload
        </button>
      </div>

      {mode === 'github' ? (
        <div className={styles.field}>
          <label className={styles.label}>GitHub Repository URL</label>
          <input
            className={styles.input}
            type="url"
            placeholder="https://github.com/owner/repo"
            value={githubUrl}
            onChange={(e) => handleGithubChange(e.target.value)}
          />
          <span className={styles.hint}>Public repos only.</span>
        </div>
      ) : (
        <div
          className={`${styles.dropzone} ${dragOver ? styles.dragOver : ''} ${file ? styles.hasFile : ''}`}
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFileChange(e.dataTransfer.files[0]); }}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".zip"
            style={{ display: 'none' }}
            onChange={(e) => handleFileChange(e.target.files[0])}
          />
          {file ? (
            <div className={styles.fileInfo}>
              <FolderOpen size={20} color="#3B82F6" />
              <span className={styles.fileName}>{file.name}</span>
              <span className={styles.fileSize}>({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
              <button className={styles.removeFile} onClick={(e) => { e.stopPropagation(); setFile(null); setProjectName(''); onInputChange(null); }}>
                <X size={14} />
              </button>
            </div>
          ) : (
            <div className={styles.dropContent}>
              <Upload size={32} color="#3B82F6" />
              <p>Drop your ZIP here or <span className={styles.browse}>browse</span></p>
              <span className={styles.hint}>Max 50MB · .zip archives only</span>
            </div>
          )}
        </div>
      )}

      <div className={styles.field}>
        <label className={styles.label}>Project Name <span className={styles.optional}>(auto-detected)</span></label>
        <input
          className={styles.input}
          type="text"
          placeholder="My Awesome Project"
          value={projectName}
          onChange={(e) => handleProjectNameChange(e.target.value)}
        />
      </div>
    </div>
  );
}

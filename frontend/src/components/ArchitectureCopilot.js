import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import styles from './ArchitectureCopilot.module.css';
import { Bot, Send, X, Sparkles, MessageSquare, ChevronRight, Loader2, ArrowRight } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || '';

export function ArchitectureCopilot({ jobId, isOpen, onClose, initialQuery }) {
  const [messages, setMessages] = useState([]);
  const [inputVal, setInputVal] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    if (initialQuery && isOpen) {
      sendMessage(initialQuery);
    }
  }, [initialQuery, isOpen]);

  const sendMessage = async (text) => {
    const q = text || inputVal;
    if (!q.trim() || isLoading) return;

    const userMsg = { role: 'user', content: q };
    setMessages(prev => [...prev, userMsg]);
    setInputVal('');
    setIsLoading(true);

    try {
      const historyPayload = messages.map(m => ({ role: m.role, content: m.content }));
      const res = await axios.post(`${API_BASE}/jobs/${jobId}/chat`, {
        message: q,
        history: historyPayload,
      });

      const botMsg = {
        role: 'assistant',
        content: res.data.response,
        diagrams: res.data.diagrams || [],
        citations: res.data.citations || [],
        followups: res.data.suggested_followups || [],
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Failed to get response: ${err.response?.data?.detail || err.message}`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  const starterPrompts = [
    "Explain the end-to-end request lifecycle and architecture flow.",
    "What is the blast radius if I modify the main ingestion handler?",
    "Where are the top security risks and how do I patch them?",
    "Generate a step-by-step refactoring plan to improve modularity.",
  ];

  return (
    <div className={styles.copilotDrawer}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.titleArea}>
          <div className={styles.botIconWrap}>
            <Bot size={18} color="#FFF" />
          </div>
          <div>
            <h3 className={styles.title}>Architecture Copilot</h3>
            <span className={styles.sub}>Knowledge Graph & Context Grounded</span>
          </div>
        </div>
        <button className={styles.closeBtn} onClick={onClose}>
          <X size={18} />
        </button>
      </div>

      {/* Chat Messages */}
      <div className={styles.chatBody}>
        {messages.length === 0 && (
          <div className={styles.starterSection}>
            <div className={styles.starterTitle}>
              <Sparkles size={14} style={{ display: 'inline', marginRight: 4 }} />
              Quick Architectural Inquiries
            </div>
            <div className={styles.chipsGrid}>
              {starterPrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  className={styles.starterChip}
                  onClick={() => sendMessage(prompt)}
                >
                  <span>{prompt}</span>
                  <ChevronRight size={14} color="#818CF8" />
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, idx) => (
          <div key={idx} className={styles.msgRow}>
            {m.role === 'user' ? (
              <div className={styles.userMsg}>{m.content}</div>
            ) : (
              <div className={styles.botMsg}>
                <div style={{ whiteSpace: 'pre-wrap' }}>{m.content}</div>

                {/* Diagrams */}
                {m.diagrams && m.diagrams.map((d, dIdx) => (
                  <div key={dIdx} className={styles.diagBox}>
                    <pre>{d}</pre>
                  </div>
                ))}

                {/* Citations */}
                {m.citations && m.citations.length > 0 && (
                  <div className={styles.citationWrap}>
                    {m.citations.map((c, cIdx) => (
                      <span key={cIdx} className={styles.citationTag}>
                        📄 {c.file_path}{c.line ? `:${c.line}` : ''}
                      </span>
                    ))}
                  </div>
                )}

                {/* Followups */}
                {m.followups && m.followups.length > 0 && (
                  <div className={styles.followupsWrap}>
                    <span style={{ fontSize: '0.72rem', color: '#64748B' }}>Suggested follow-ups:</span>
                    {m.followups.map((f, fIdx) => (
                      <button
                        key={fIdx}
                        className={styles.followupBtn}
                        onClick={() => sendMessage(f)}
                      >
                        ↳ {f}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className={styles.botMsg} style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#818CF8' }}>
            <Loader2 size={16} className="spin" style={{ animation: 'spin 1s linear infinite' }} />
            <span>Analyzing Knowledge Graph and formulating answer...</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input Section */}
      <div className={styles.inputSection}>
        <input
          type="text"
          placeholder="Ask anything about architecture, flow, or risks..."
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          className={styles.chatInput}
          disabled={isLoading}
        />
        <button
          className={`${styles.sendBtn} ${isLoading || !inputVal.trim() ? styles.disabled : ''}`}
          onClick={() => sendMessage()}
          disabled={isLoading || !inputVal.trim()}
        >
          <Send size={15} />
        </button>
      </div>
    </div>
  );
}

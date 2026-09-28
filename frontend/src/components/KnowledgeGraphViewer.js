import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import styles from './KnowledgeGraphViewer.module.css';
import { Network, Search, ZoomIn, ZoomOut, RotateCcw, ShieldAlert, Layers, Play, Pause, X, Zap } from 'lucide-react';

const LAYER_COLORS = {
  api:      { bg: '#06B6D4', glow: 'rgba(6, 182, 212, 0.4)', label: 'API Routes' },
  logic:    { bg: '#6366F1', glow: 'rgba(99, 102, 241, 0.4)', label: 'Core Logic' },
  data:     { bg: '#10B981', glow: 'rgba(16, 185, 129, 0.4)', label: 'Data Models' },
  library:  { bg: '#F59E0B', glow: 'rgba(245, 158, 11, 0.4)', label: 'External Libs' },
  security: { bg: '#EF4444', glow: 'rgba(239, 68, 68, 0.4)', label: 'Security' },
  frontend: { bg: '#EC4899', glow: 'rgba(236, 72, 153, 0.4)', label: 'Frontend' },
  config:   { bg: '#8B5CF6', glow: 'rgba(139, 92, 246, 0.4)', label: 'Configs' },
  test:     { bg: '#3B82F6', glow: 'rgba(59, 130, 246, 0.4)', label: 'Tests' },
};

export function KnowledgeGraphViewer({ graphData, onAskCopilotAboutNode }) {
  const canvasRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [blastNode, setBlastNode] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeLayers, setActiveLayers] = useState({
    api: true, logic: true, data: true, library: true, security: true, frontend: true, config: true, test: true
  });
  const [isSimulating, setIsSimulating] = useState(true);

  // Transform raw data into graph simulation nodes & edges
  const nodes = useMemo(() => {
    if (!graphData?.nodes) return [];
    return graphData.nodes.map((n, i) => {
      const angle = (i / graphData.nodes.length) * 2 * Math.PI;
      const radius = 180 + (i % 3) * 60;
      return {
        ...n,
        x: (canvasRef.current?.width || 800) / 2 + Math.cos(angle) * radius + (Math.random() - 0.5) * 40,
        y: (canvasRef.current?.height || 600) / 2 + Math.sin(angle) * radius + (Math.random() - 0.5) * 40,
        vx: 0,
        vy: 0,
        radius: n.is_hub ? 14 : Math.max(6, Math.min(12, 6 + (n.degree || 1) * 1.5)),
      };
    });
  }, [graphData]);

  const edges = useMemo(() => graphData?.edges || [], [graphData]);

  // Transform view matrix
  const transformRef = useRef({ x: 0, y: 0, k: 1 });
  const isDraggingRef = useRef(false);
  const dragNodeRef = useRef(null);
  const lastMouseRef = useRef({ x: 0, y: 0 });

  // Calculate blast radius set
  const blastRadiusSets = useMemo(() => {
    if (!blastNode) return { upstream: new Set(), downstream: new Set() };
    const forward = {};
    const backward = {};
    edges.forEach(e => {
      forward[e.source] = forward[e.source] || [];
      forward[e.source].push(e.target);
      backward[e.target] = backward[e.target] || [];
      backward[e.target].push(e.source);
    });

    const upstream = new Set();
    const q1 = [blastNode.id];
    while (q1.length) {
      const curr = q1.pop();
      (backward[curr] || []).forEach(p => {
        if (!upstream.has(p)) { upstream.add(p); q1.push(p); }
      });
    }

    const downstream = new Set();
    const q2 = [blastNode.id];
    while (q2.length) {
      const curr = q2.pop();
      (forward[curr] || []).forEach(n => {
        if (!downstream.has(n)) { downstream.add(n); q2.push(n); }
      });
    }

    return { upstream, downstream };
  }, [blastNode, edges]);

  // Main rendering loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;

    const resize = () => {
      canvas.width = canvas.parentElement.clientWidth;
      canvas.height = canvas.parentElement.clientHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const tick = () => {
      // 1. Simple force-directed physics
      if (isSimulating) {
        const k = 0.05;
        const repulse = 800;
        const centerGravity = 0.005;
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;

        for (let i = 0; i < nodes.length; i++) {
          const n1 = nodes[i];
          if (!activeLayers[n1.layer]) continue;

          // Center gravity
          n1.vx += (cx - n1.x) * centerGravity;
          n1.vy += (cy - n1.y) * centerGravity;

          // Repulsion
          for (let j = i + 1; j < nodes.length; j++) {
            const n2 = nodes[j];
            if (!activeLayers[n2.layer]) continue;
            const dx = n2.x - n1.x;
            const dy = n2.y - n1.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            if (dist < 280) {
              const f = repulse / (dist * dist);
              n1.vx -= (dx / dist) * f;
              n1.vy -= (dy / dist) * f;
              n2.vx += (dx / dist) * f;
              n2.vy += (dy / dist) * f;
            }
          }
        }

        // Link attraction
        const nodeMap = {};
        nodes.forEach(n => { nodeMap[n.id] = n; });
        edges.forEach(e => {
          const s = nodeMap[e.source];
          const t = nodeMap[e.target];
          if (s && t && activeLayers[s.layer] && activeLayers[t.layer]) {
            const dx = t.x - s.x;
            const dy = t.y - s.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const targetDist = 90;
            const force = (dist - targetDist) * k;
            s.vx += (dx / dist) * force;
            s.vy += (dy / dist) * force;
            t.vx -= (dx / dist) * force;
            t.vy -= (dy / dist) * force;
          }
        });

        // Apply velocities with damping
        nodes.forEach(n => {
          if (n !== dragNodeRef.current) {
            n.vx *= 0.85;
            n.vy *= 0.85;
            n.x += n.vx;
            n.y += n.vy;
          }
        });
      }

      // 2. Draw canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      const t = transformRef.current;
      ctx.translate(t.x, t.y);
      ctx.scale(t.k, t.k);

      const nodeMap = {};
      nodes.forEach(n => { nodeMap[n.id] = n; });

      // Draw edges
      edges.forEach(e => {
        const s = nodeMap[e.source];
        const tg = nodeMap[e.target];
        if (!s || !tg || !activeLayers[s.layer] || !activeLayers[tg.layer]) return;

        let strokeColor = 'rgba(99, 102, 241, 0.18)';
        let lineWidth = 1;

        if (blastNode) {
          if (blastRadiusSets.upstream.has(s.id) || blastRadiusSets.downstream.has(tg.id)) {
            strokeColor = 'rgba(239, 68, 68, 0.8)';
            lineWidth = 2;
          } else {
            strokeColor = 'rgba(255, 255, 255, 0.04)';
          }
        } else if (selectedNode && (selectedNode.id === s.id || selectedNode.id === tg.id)) {
          strokeColor = 'rgba(6, 182, 212, 0.9)';
          lineWidth = 2;
        }

        ctx.beginPath();
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = lineWidth;
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(tg.x, tg.y);
        ctx.stroke();
      });

      // Draw nodes
      nodes.forEach(n => {
        if (!activeLayers[n.layer]) return;
        const meta = LAYER_COLORS[n.layer] || { bg: '#94A3B8', glow: 'rgba(148, 163, 184, 0.4)' };
        const isMatched = searchQuery && n.label.toLowerCase().includes(searchQuery.toLowerCase());
        const isSelected = selectedNode?.id === n.id;
        const isBlast = blastNode?.id === n.id;
        const isUpstream = blastRadiusSets.upstream.has(n.id);
        const isDownstream = blastRadiusSets.downstream.has(n.id);

        let color = meta.bg;
        let radius = n.radius;

        if (isBlast) {
          color = '#EF4444';
          radius += 6;
        } else if (isUpstream) {
          color = '#F43F5E';
          radius += 3;
        } else if (isDownstream) {
          color = '#06B6D4';
          radius += 3;
        } else if (isSelected || isMatched) {
          color = '#38BDF8';
          radius += 4;
        }

        // Glow
        ctx.beginPath();
        ctx.arc(n.x, n.y, radius + 4, 0, 2 * Math.PI);
        ctx.fillStyle = isBlast ? 'rgba(239, 68, 68, 0.4)' : meta.glow;
        ctx.fill();

        // Core circle
        ctx.beginPath();
        ctx.arc(n.x, n.y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = '#FFFFFF';
        ctx.lineWidth = isSelected || isBlast ? 2.5 : 1;
        ctx.stroke();

        // Label
        if (t.k > 0.6 || isSelected || isBlast || isMatched || n.is_hub) {
          ctx.font = `${isSelected || n.is_hub ? 'bold 11px' : '9px'} -apple-system, sans-serif`;
          ctx.fillStyle = isSelected || isBlast ? '#FFFFFF' : 'rgba(241, 245, 249, 0.85)';
          ctx.textAlign = 'center';
          ctx.fillText(n.label, n.x, n.y + radius + 12);
        }
      });

      ctx.restore();
      animId = requestAnimationFrame(tick);
    };

    animId = requestAnimationFrame(tick);
    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animId);
    };
  }, [nodes, edges, activeLayers, isSimulating, selectedNode, blastNode, blastRadiusSets, searchQuery]);

  // Canvas Mouse Controls (Pan & Zoom & Drag)
  const handleMouseDown = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const t = transformRef.current;
    const worldX = (mouseX - t.x) / t.k;
    const worldY = (mouseY - t.y) / t.k;

    // Hit test nodes
    let clickedNode = null;
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      if (!activeLayers[n.layer]) continue;
      const dx = n.x - worldX;
      const dy = n.y - worldY;
      if (Math.sqrt(dx * dx + dy * dy) <= n.radius + 4) {
        clickedNode = n;
        break;
      }
    }

    if (clickedNode) {
      dragNodeRef.current = clickedNode;
      setSelectedNode(clickedNode);
    } else {
      isDraggingRef.current = true;
      lastMouseRef.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleMouseMove = (e) => {
    if (dragNodeRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      const t = transformRef.current;
      dragNodeRef.current.x = (e.clientX - rect.left - t.x) / t.k;
      dragNodeRef.current.y = (e.clientY - rect.top - t.y) / t.k;
      dragNodeRef.current.vx = 0;
      dragNodeRef.current.vy = 0;
    } else if (isDraggingRef.current) {
      const dx = e.clientX - lastMouseRef.current.x;
      const dy = e.clientY - lastMouseRef.current.y;
      transformRef.current.x += dx;
      transformRef.current.y += dy;
      lastMouseRef.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
    dragNodeRef.current = null;
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.1 : 0.9;
    const newK = Math.max(0.2, Math.min(3, transformRef.current.k * factor));
    transformRef.current.k = newK;
  };

  const handleZoom = (delta) => {
    transformRef.current.k = Math.max(0.2, Math.min(3, transformRef.current.k + delta));
  };

  const handleReset = () => {
    transformRef.current = { x: 0, y: 0, k: 1 };
    setBlastNode(null);
    setSelectedNode(null);
  };

  const toggleLayer = (layer) => {
    setActiveLayers(prev => ({ ...prev, [layer]: !prev[layer] }));
  };

  return (
    <div className={styles.container}>
      {/* Top Controls Bar */}
      <div className={styles.topBar}>
        <div className={styles.titleArea}>
          <Network size={18} color="#818CF8" />
          <span>Code Knowledge Graph (CodeKG)</span>
          <span className={styles.badge}>{graphData?.metrics?.total_nodes || 0} Nodes</span>
          <span className={styles.badge}>{graphData?.metrics?.total_edges || 0} Edges</span>
        </div>

        <div className={styles.controls}>
          <div className={styles.searchBox}>
            <Search size={14} color="#64748B" />
            <input
              type="text"
              placeholder="Search symbol/file..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={styles.searchInput}
            />
          </div>

          <button className={styles.btn} onClick={() => handleZoom(0.2)} title="Zoom In">
            <ZoomIn size={14} />
          </button>
          <button className={styles.btn} onClick={() => handleZoom(-0.2)} title="Zoom Out">
            <ZoomOut size={14} />
          </button>
          <button className={styles.btn} onClick={handleReset} title="Reset View">
            <RotateCcw size={14} />
          </button>
          <button
            className={`${styles.btn} ${isSimulating ? styles.btnActive : ''}`}
            onClick={() => setIsSimulating(!isSimulating)}
            title={isSimulating ? 'Pause Physics' : 'Resume Physics'}
          >
            {isSimulating ? <Pause size={14} /> : <Play size={14} />}
          </button>
        </div>
      </div>

      {/* Layer Filter Pills */}
      <div className={styles.layerPills}>
        {Object.entries(LAYER_COLORS).map(([layerKey, meta]) => (
          <button
            key={layerKey}
            className={`${styles.layerPill} ${activeLayers[layerKey] ? styles.active : ''}`}
            onClick={() => toggleLayer(layerKey)}
            style={{
              borderColor: activeLayers[layerKey] ? meta.bg : 'transparent',
              background: activeLayers[layerKey] ? `${meta.bg}22` : 'rgba(19, 30, 54, 0.4)'
            }}
          >
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: meta.bg }} />
            {meta.label}
          </button>
        ))}
      </div>

      {/* Canvas Area */}
      <div className={styles.canvasWrapper}>
        <canvas
          ref={canvasRef}
          className={styles.canvas}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onWheel={handleWheel}
        />

        {/* Node Inspector Drawer */}
        {selectedNode && (
          <div className={styles.inspectorDrawer}>
            <div className={styles.drawerHeader}>
              <div>
                <h4 className={styles.nodeTitle}>{selectedNode.label}</h4>
                <span
                  className={styles.nodeTypeBadge}
                  style={{
                    background: `${LAYER_COLORS[selectedNode.layer]?.bg || '#6366F1'}25`,
                    color: LAYER_COLORS[selectedNode.layer]?.bg || '#6366F1'
                  }}
                >
                  {selectedNode.type} &bull; {selectedNode.layer}
                </span>
              </div>
              <button className={styles.closeBtn} onClick={() => setSelectedNode(null)}>
                <X size={16} />
              </button>
            </div>

            {selectedNode.path && (
              <div className={styles.statCard}>
                <span className={styles.statLabel}>File Path</span>
                <p className={styles.statVal} style={{ fontSize: '0.8rem', wordBreak: 'break-all' }}>
                  {selectedNode.path}
                </p>
              </div>
            )}

            <div className={styles.statGrid}>
              <div className={styles.statCard}>
                <span className={styles.statLabel}>Centrality Rank</span>
                <p className={styles.statVal}>{(selectedNode.centrality * 100).toFixed(0)}%</p>
              </div>
              <div className={styles.statCard}>
                <span className={styles.statLabel}>Total Connections</span>
                <p className={styles.statVal}>{selectedNode.degree || 0}</p>
              </div>
            </div>

            <div>
              <h5 className={styles.sectionTitle}>Incoming Callers (In-Degree)</h5>
              <div className={styles.linkList}>
                {edges.filter(e => e.target === selectedNode.id).map((e, idx) => (
                  <div key={idx} className={styles.linkItem}>
                    ← {nodes.find(n => n.id === e.source)?.label || e.source} ({e.type})
                  </div>
                ))}
                {edges.filter(e => e.target === selectedNode.id).length === 0 && (
                  <span style={{ fontSize: '0.75rem', color: '#64748B' }}>No direct incoming callers</span>
                )}
              </div>
            </div>

            <div>
              <h5 className={styles.sectionTitle}>Dependencies (Out-Degree)</h5>
              <div className={styles.linkList}>
                {edges.filter(e => e.source === selectedNode.id).map((e, idx) => (
                  <div key={idx} className={styles.linkItem}>
                    → {nodes.find(n => n.id === e.target)?.label || e.target} ({e.type})
                  </div>
                ))}
                {edges.filter(e => e.source === selectedNode.id).length === 0 && (
                  <span style={{ fontSize: '0.75rem', color: '#64748B' }}>No outgoing dependencies</span>
                )}
              </div>
            </div>

            {/* Blast Radius Trigger */}
            <button
              className={styles.blastBtn}
              onClick={() => {
                if (blastNode?.id === selectedNode.id) {
                  setBlastNode(null);
                } else {
                  setBlastNode(selectedNode);
                }
              }}
            >
              <Zap size={14} />
              {blastNode?.id === selectedNode.id ? 'Clear Blast Highlight' : 'Calculate Blast Radius'}
            </button>
          </div>
        )}
      </div>

      {/* Footer Metrics */}
      <div className={styles.footerMetrics}>
        <span>
          Critical Hubs: {graphData?.metrics?.hub_nodes?.slice(0, 4).join(', ') || 'None detected'}
        </span>
        <span>
          {graphData?.metrics?.has_cycles ? (
            <strong style={{ color: '#EF4444' }}>⚠️ Circular Imports Detected</strong>
          ) : (
            <span style={{ color: '#10B981' }}>✓ Clean Directed Topology</span>
          )}
        </span>
      </div>
    </div>
  );
}

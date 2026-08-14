import { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import CFGGraph from './components/CFGGraph';
import './App.css';

const API = 'http://localhost:3001/api';

export default function App() {
  const [analysis, setAnalysis] = useState(null);
  const [analysisVersion, setAnalysisVersion] = useState(0);
  const [activeFn, setActiveFn] = useState(null);
  const [highlightRange, setHighlightRange] = useState(null);
  const [highlightedNodeId, setHighlightedNodeId] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetch(`${API}/sample`)
      .then((r) => r.json())
      .then((d) => {
        setAnalysis(d);
        setActiveFn(d.functions[0].name);
        setAnalysisVersion((v) => v + 1);
        setLoading(false);
      })
      .catch(() => { setError('Could not reach the backend at ' + API + '. Is it running?'); setLoading(false); });
  }, []);

  const cfg = useMemo(
    () => analysis?.functions.find((f) => f.name === activeFn),
    [analysis, activeFn]
  );

  const sourceLines = useMemo(() => (analysis ? analysis.source.split('\n') : []), [analysis]);

  const handleUpload = useCallback((e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    const form = new FormData();
    form.append('file', file);
    fetch(`${API}/analyze`, { method: 'POST', body: form })
      .then(async (r) => {
        const d = await r.json();
        if (!r.ok) throw new Error(d.error || 'analysis failed');
        return d;
      })
      .then((d) => {
        setAnalysis(d);
        setActiveFn(d.functions[0]?.name ?? null);
        setHighlightRange(null);
        setHighlightedNodeId(null);
        setAnalysisVersion((v) => v + 1);
        setLoading(false);
      })
      .catch((err) => { setError(err.message); setLoading(false); })
      .finally(() => { e.target.value = ''; });
  }, []);

  const handleSelectFromGraph = useCallback((start, end, nodeId) => {
    setHighlightRange([start, end]);
    setHighlightedNodeId(nodeId);
  }, []);

  const handleSelectFromSource = useCallback((lineNum) => {
    if (!cfg) return;
    const node = cfg.nodes.find((n) => n.line_start > 0 && lineNum >= n.line_start && lineNum <= n.line_end);
    if (node) {
      setHighlightRange([node.line_start, node.line_end]);
      setHighlightedNodeId(node.id);
    }
  }, [cfg]);

  const complexityColor = (c) => (c <= 5 ? 'var(--teal)' : c <= 10 ? 'var(--slate)' : 'var(--sienna)');

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand__mark">CFG</span>
          <span className="brand__name">cflow-analyzer</span>
        </div>
        {error && <div className="topbar__error">{error}</div>}
        <button className="upload-btn" onClick={() => fileInputRef.current?.click()} disabled={loading}>
          {loading ? 'Analyzing…' : 'Upload .c file'}
        </button>
        <input ref={fileInputRef} type="file" accept=".c" hidden onChange={handleUpload} />
      </header>

      <div className="workbench">
        <nav className="panel func-list">
          <div className="func-list__label">Functions</div>
          {analysis?.functions.map((f) => (
            <button
              key={f.name}
              className={`func-item ${f.name === activeFn ? 'func-item--active' : ''}`}
              onClick={() => { setActiveFn(f.name); setHighlightRange(null); setHighlightedNodeId(null); }}
            >
              <span className="func-item__name">{f.name}()</span>
              <span className="func-item__meta">
                <span className="func-item__dot" style={{ background: complexityColor(f.complexity) }} />
                M={f.complexity} · {f.num_nodes} nodes
              </span>
            </button>
          ))}
        </nav>

        <main className="panel graph-panel">
          {cfg && (
            <ReactFlowProvider key={`${cfg.name}-${analysisVersion}`}>
              <CFGGraph cfg={cfg} onSelectLine={handleSelectFromGraph} highlightedNodeId={highlightedNodeId} />
            </ReactFlowProvider>
          )}
          <div className="legend">
            <span className="legend__item"><span className="legend__swatch" style={{ background: 'var(--teal)' }} />true</span>
            <span className="legend__item"><span className="legend__swatch" style={{ background: 'var(--sienna)' }} />false</span>
            <span className="legend__item"><span className="legend__swatch" style={{ background: 'var(--slate)' }} />uncond / case</span>
            <span className="legend__item legend__hint">drag nodes to rearrange</span>
          </div>
        </main>

        <aside className="panel source-panel">
          <div className="source-panel__header">Source — click a line to locate its block</div>
          <pre className="source-code">
            {sourceLines.map((line, i) => {
              const lineNum = i + 1;
              const isHighlighted = highlightRange && lineNum >= highlightRange[0] && lineNum <= highlightRange[1];
              return (
                <div
                  key={i}
                  className={`source-line ${isHighlighted ? 'source-line--highlight' : ''}`}
                  onClick={() => handleSelectFromSource(lineNum)}
                >
                  <span className="source-line__num">{lineNum}</span>
                  <span>{line}</span>
                </div>
              );
            })}
          </pre>

          {cfg && (
            <div className="metrics">
              <div className="metrics__label">Cyclomatic complexity</div>
              <div className="metrics__row">
                <span>Nodes (N)</span><span className="metrics__value">{cfg.num_nodes}</span>
              </div>
              <div className="metrics__row">
                <span>Edges (E)</span><span className="metrics__value">{cfg.num_edges}</span>
              </div>
              <div className="metrics__row">
                <span>Connected components (P)</span><span className="metrics__value">1</span>
              </div>
              <div className="metrics__formula">
                M = E − N + 2P = {cfg.num_edges} − {cfg.num_nodes} + 2 = <strong>{cfg.complexity}</strong>
              </div>
              <div className="metrics__result" style={{ borderColor: complexityColor(cfg.complexity) }}>
                <span className="metrics__result-num" style={{ color: complexityColor(cfg.complexity) }}>{cfg.complexity}</span>
                <span className="metrics__result-label">complexity for {cfg.name}()</span>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

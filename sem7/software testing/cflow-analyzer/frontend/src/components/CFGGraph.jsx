import { useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  BackgroundVariant,
  MarkerType,
  useNodesState,
  useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';

const EDGE_COLOR = {
  true: 'var(--teal)',
  false: 'var(--sienna)',
  uncond: 'var(--slate)',
  case: 'var(--slate)',
};

function BlockNode({ id, data }) {
  const lines = data.label ? data.label.split('\n').filter(Boolean) : [];
  const kind = data.isEntry ? 'entry' : data.isExit ? 'exit' : 'block';
  const selected = id === data.highlightedId;
  return (
    <div className={`cfg-node cfg-node--${kind} ${selected ? 'cfg-node--selected' : ''}`}>
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <div className="cfg-node__tag">{data.id}</div>
      <div className="cfg-node__body">
        {lines.length === 0 ? (
          <span className="cfg-node__empty">—</span>
        ) : (
          lines.map((l, i) => <div key={i} className="cfg-node__line">{l}</div>)
        )}
      </div>
      {data.lineStart > 0 && (
        <div className="cfg-node__meta">L{data.lineStart}{data.lineEnd !== data.lineStart ? `–${data.lineEnd}` : ''}</div>
      )}
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}

const nodeTypes = { block: BlockNode };

function layoutPositions(nodes, edges) {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'TB', nodesep: 48, ranksep: 64 });
  nodes.forEach((n) => g.setNode(n.id, { width: 200, height: 84 }));
  edges.forEach((e) => g.setEdge(e.source, e.target));
  dagre.layout(g);
  return nodes.map((n) => {
    const pos = g.node(n.id);
    return { ...n, position: { x: pos.x - 100, y: pos.y - 42 } };
  });
}

export default function CFGGraph({ cfg, onSelectLine, highlightedNodeId }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges] = useEdgesState([]);

  // Recompute layout only when the function being viewed actually changes -
  // this is what makes dragging "stick": position updates from onNodesChange
  // are never overwritten by an unrelated re-render (e.g. clicking a line).
  useEffect(() => {
    if (!cfg) { setNodes([]); setEdges([]); return; }

    const rfNodesRaw = cfg.nodes.map((n) => ({
      id: n.id,
      type: 'block',
      data: {
        id: n.id,
        label: n.label,
        isEntry: n.is_entry,
        isExit: n.is_exit,
        lineStart: n.line_start,
        lineEnd: n.line_end,
        highlightedId: null,
      },
      position: { x: 0, y: 0 },
    }));

    const rfEdges = cfg.edges.map((e, i) => ({
      id: `e${i}-${e.from}-${e.to}`,
      source: e.from,
      target: e.to,
      type: 'smoothstep',
      label: e.type === 'true' ? 'T' : e.type === 'false' ? 'F' : e.label || undefined,
      style: { stroke: EDGE_COLOR[e.type] || 'var(--slate)', strokeWidth: 1.75 },
      labelStyle: { fill: EDGE_COLOR[e.type] || 'var(--slate)', fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 600 },
      labelBgStyle: { fill: 'var(--paper)', fillOpacity: 0.9 },
      markerEnd: { type: MarkerType.ArrowClosed, color: EDGE_COLOR[e.type] || 'var(--slate)', width: 16, height: 16 },
    }));

    setNodes(layoutPositions(rfNodesRaw, rfEdges));
    setEdges(rfEdges);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cfg]);

  // Highlighting only touches `data`, never `position`, so a drag survives it.
  useEffect(() => {
    setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, highlightedId: highlightedNodeId } })));
  }, [highlightedNodeId, setNodes]);

  const handleNodeClick = (_, node) => {
    if (onSelectLine && node.data.lineStart > 0) onSelectLine(node.data.lineStart, node.data.lineEnd, node.id);
  };

  if (!cfg) return null;

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      nodeTypes={nodeTypes}
      onNodeClick={handleNodeClick}
      fitView
      fitViewOptions={{ padding: 0.15 }}
      proOptions={{ hideAttribution: true }}
      minZoom={0.3}
    >
      <Background variant={BackgroundVariant.Lines} gap={24} size={1} color="var(--hairline)" />
      <Controls showInteractive={false} />
    </ReactFlow>
  );
}

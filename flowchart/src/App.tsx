import { useCallback, useState, useRef } from 'react';
import type { Node, Edge, NodeChange, EdgeChange, NodeProps } from '@xyflow/react';
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  MarkerType,
  applyNodeChanges,
  applyEdgeChanges,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './App.css';

const nodeWidth = 260;
const nodeHeight = 86;

type Phase = 'setup' | 'loop' | 'decision' | 'done';

const phaseColors: Record<Phase, { bg: string; border: string }> = {
  setup: { bg: '#f0f7ff', border: '#4a90d9' },
  loop: { bg: '#f5f5f5', border: '#666666' },
  decision: { bg: '#fff8e6', border: '#c9a227' },
  done: { bg: '#f0fff4', border: '#38a169' },
};

const allSteps: { id: string; label: string; description: string; phase: Phase }[] = [
  {
    id: '1',
    label: 'PRD + Beads issues',
    description:
      'generate-prd → tasks/prd-*.md; prd-to-beads → bd epics/tasks + deps (or hand-roll bd create)',
    phase: 'setup',
  },
  {
    id: '2',
    label: 'Epics + branch metadata',
    description: 'Project + phase epics; bd update … --notes "branch: ralph/…" (required for Ralph)',
    phase: 'setup',
  },
  {
    id: '3',
    label: 'Run ralph.py',
    description:
      'Portable: python3 <ralph-cursor>/bin/ralph.py run --project REPO — bundled ralph.py, cwd=REPO, .beads/; legacy: python3 scripts/ralph/ralph.py in-repo; needs cursor-agent|agent',
    phase: 'setup',
  },
  {
    id: '4',
    label: 'Worker: CLI + task',
    description:
      'Cursor w/ prompt.cursor.md; bd list/show → phase branch; bd ready → read task + comments (newest first)',
    phase: 'loop',
  },
  {
    id: '5',
    label: 'Ship + Beads + git',
    description:
      'Meet AC; OK → comments add + bd close, else factual comment; commit/push when clean (per prompt)',
    phase: 'loop',
  },
  {
    id: '6',
    label: 'Ralph: saw COMPLETE?',
    description: 'Worker prints <promise>COMPLETE</promise> when phase/project done; else normal end',
    phase: 'decision',
  },
  {
    id: '7',
    label: 'Ralph exits 0',
    description: 'Driver finds <promise>COMPLETE</promise> in worker stdout → clean exit',
    phase: 'done',
  },
];

const notes = [
  {
    id: 'note-prd',
    appearsWithStep: 1,
    position: { x: 400, y: 48 },
    color: { bg: '#e8f4fc', border: '#2b6cb0' },
    content: `generate-prd (IDE)
.cursor/commands/generate-prd.md

→ tasks/prd-<feature>.md
Iterate + read before Beads.`,
  },
  {
    id: 'note-1',
    appearsWithStep: 2,
    position: { x: 400, y: 300 },
    color: { bg: '#f5f0ff', border: '#8b5cf6' },
    content: `bd update $EPIC_ID --notes "branch: ralph/my-feature"

Ralph reads branch from
top-level project epic`,
  },
  {
    id: 'note-2',
    appearsWithStep: 5,
    position: { x: 1060, y: 520 },
    color: { bg: '#fdf4f0', border: '#c97a50' },
    content: `Before bd close (success):
bd comments add <id> "Completed…"

Stuck: comments add, facts only`,
  },
];

/** Which handles each step id needs (edges only — no interactive wiring). */
const nodeHandles: Record<string, Partial<Record<'top' | 'bottom' | 'left' | 'right', 'source' | 'target'>>> = {
  '1': { bottom: 'source' },
  '2': { top: 'target', bottom: 'source' },
  '3': { top: 'target', right: 'source' },
  '4': { left: 'target', right: 'target', bottom: 'source' },
  '5': { top: 'target', bottom: 'source' },
  '6': { top: 'target', bottom: 'source', left: 'source' },
  '7': { top: 'target' },
};

function CustomNode({ id, data }: NodeProps<{ title: string; description: string; phase: Phase }>) {
  const colors = phaseColors[data.phase];
  const h = nodeHandles[id] ?? {};

  const handle = (side: 'top' | 'bottom' | 'left' | 'right', kind: 'source' | 'target') => {
    const pos =
      side === 'top'
        ? Position.Top
        : side === 'bottom'
          ? Position.Bottom
          : side === 'left'
            ? Position.Left
            : Position.Right;
    return <Handle key={`${id}-${side}-${kind}`} type={kind} position={pos} id={`${side}-${kind}`} />;
  };

  return (
    <div
      className="custom-node"
      style={{
        backgroundColor: colors.bg,
        borderColor: colors.border,
        width: nodeWidth,
        minHeight: nodeHeight,
      }}
    >
      {(Object.entries(h) as [keyof typeof h, 'source' | 'target'][]).map(([side, kind]) => handle(side, kind))}
      <div className="node-content">
        <div className="node-title">{data.title}</div>
        {data.description && <div className="node-description">{data.description}</div>}
      </div>
    </div>
  );
}

function NoteNode({ data }: { data: { content: string; color: { bg: string; border: string } } }) {
  return (
    <div
      className="note-node"
      style={{
        backgroundColor: data.color.bg,
        borderColor: data.color.border,
      }}
    >
      <pre>{data.content}</pre>
    </div>
  );
}

const nodeTypes = { custom: CustomNode, note: NoteNode };

const positions: { [key: string]: { x: number; y: number } } = {
  '1': { x: 80, y: 48 },
  '2': { x: 80, y: 200 },
  '3': { x: 80, y: 352 },
  '4': { x: 780, y: 48 },
  '5': { x: 780, y: 220 },
  '6': { x: 780, y: 392 },
  '7': { x: 780, y: 564 },
  ...Object.fromEntries(notes.map((n) => [n.id, n.position])),
};

const edgeConnections: {
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  label?: string;
}[] = [
  { source: '1', target: '2', sourceHandle: 'bottom-source', targetHandle: 'top-target' },
  { source: '2', target: '3', sourceHandle: 'bottom-source', targetHandle: 'top-target' },
  { source: '3', target: '4', sourceHandle: 'right-source', targetHandle: 'left-target' },
  { source: '4', target: '5', sourceHandle: 'bottom-source', targetHandle: 'top-target' },
  { source: '5', target: '6', sourceHandle: 'bottom-source', targetHandle: 'top-target' },
  { source: '6', target: '7', sourceHandle: 'bottom-source', targetHandle: 'top-target', label: 'Yes' },
  {
    source: '6',
    target: '4',
    sourceHandle: 'left-source',
    targetHandle: 'right-target',
    label: 'No',
  },
];

function createNode(step: (typeof allSteps)[0], visible: boolean, position?: { x: number; y: number }): Node {
  return {
    id: step.id,
    type: 'custom',
    position: position || positions[step.id],
    data: {
      title: step.label,
      description: step.description,
      phase: step.phase,
    },
    style: {
      width: nodeWidth,
      height: nodeHeight,
      opacity: visible ? 1 : 0,
      transition: 'opacity 0.5s ease-in-out',
      pointerEvents: visible ? 'auto' : 'none',
    },
  };
}

function createEdge(conn: (typeof edgeConnections)[0], visible: boolean): Edge {
  return {
    id: `e${conn.source}-${conn.target}${conn.label ?? ''}`,
    source: conn.source,
    target: conn.target,
    sourceHandle: conn.sourceHandle,
    targetHandle: conn.targetHandle,
    label: visible ? conn.label : undefined,
    animated: visible,
    style: {
      stroke: '#222',
      strokeWidth: 2,
      opacity: visible ? 1 : 0,
      transition: 'opacity 0.5s ease-in-out',
    },
    labelStyle: {
      fill: '#222',
      fontWeight: 600,
      fontSize: 13,
    },
    labelShowBg: true,
    labelBgPadding: [8, 4] as [number, number],
    labelBgStyle: {
      fill: '#fff',
      stroke: '#222',
      strokeWidth: 1,
    },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#222',
    },
  };
}

function createNoteNode(note: (typeof notes)[0], visible: boolean, position?: { x: number; y: number }): Node {
  return {
    id: note.id,
    type: 'note',
    position: position || positions[note.id],
    data: { content: note.content, color: note.color },
    style: {
      opacity: visible ? 1 : 0,
      transition: 'opacity 0.5s ease-in-out',
      pointerEvents: visible ? 'auto' : 'none',
    },
    draggable: true,
    selectable: false,
    connectable: false,
  };
}

function App() {
  const [visibleCount, setVisibleCount] = useState(1);
  const nodePositions = useRef<{ [key: string]: { x: number; y: number } }>({ ...positions });

  const getNodes = (count: number) => {
    const stepNodes = allSteps.map((step, index) =>
      createNode(step, index < count, nodePositions.current[step.id])
    );
    const noteNodes = notes.map((note) => {
      const noteVisible = count >= note.appearsWithStep;
      return createNoteNode(note, noteVisible, nodePositions.current[note.id]);
    });
    return [...stepNodes, ...noteNodes];
  };

  const initialNodes = getNodes(1);
  const initialEdges = edgeConnections.map((conn) => createEdge(conn, false));

  const [nodes, setNodes] = useNodesState(initialNodes);
  const [edges, setEdges] = useEdgesState(initialEdges);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      changes.forEach((change) => {
        if (change.type === 'position' && change.position) {
          nodePositions.current[change.id] = change.position;
        }
      });
      setNodes((nds) => applyNodeChanges(changes, nds));
    },
    [setNodes]
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      setEdges((eds) => applyEdgeChanges(changes, eds));
    },
    [setEdges]
  );

  const getEdgeVisibility = (conn: (typeof edgeConnections)[0], visibleStepCount: number) => {
    const sourceIndex = allSteps.findIndex((s) => s.id === conn.source);
    const targetIndex = allSteps.findIndex((s) => s.id === conn.target);
    return sourceIndex < visibleStepCount && targetIndex < visibleStepCount;
  };

  const handleNext = useCallback(() => {
    if (visibleCount < allSteps.length) {
      const newCount = visibleCount + 1;
      setVisibleCount(newCount);

      setNodes(getNodes(newCount));
      setEdges(
        edgeConnections.map((conn) => createEdge(conn, getEdgeVisibility(conn, newCount)))
      );
    }
  }, [visibleCount, setNodes, setEdges]);

  const handlePrev = useCallback(() => {
    if (visibleCount > 1) {
      const newCount = visibleCount - 1;
      setVisibleCount(newCount);

      setNodes(getNodes(newCount));
      setEdges(
        edgeConnections.map((conn) => createEdge(conn, getEdgeVisibility(conn, newCount)))
      );
    }
  }, [visibleCount, setNodes, setEdges]);

  const handleReset = useCallback(() => {
    setVisibleCount(1);
    nodePositions.current = { ...positions };
    setNodes(getNodes(1));
    setEdges(edgeConnections.map((conn) => createEdge(conn, false)));
  }, [setNodes, setEdges]);

  return (
    <div className="app-container">
      <div className="header">
        <h1>How Ralph loops (this repo)</h1>
        <p>
          PRD → Beads → <code>ralph.py</code> drives Cursor (<code>prompt.cursor.md</code>); tracker ={' '}
          <strong>Beads</strong> (<code>bd</code>).
        </p>
      </div>
      <div className="flow-container">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          fitViewOptions={{ padding: 0.12 }}
          minZoom={0.22}
          maxZoom={1.25}
          nodesDraggable={true}
          nodesConnectable={false}
          edgesReconnectable={false}
          elementsSelectable={true}
          deleteKeyCode={null}
          panOnDrag={true}
          panOnScroll={true}
          zoomOnScroll={true}
          zoomOnPinch={true}
          zoomOnDoubleClick={true}
          selectNodesOnDrag={false}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#ddd" />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
      <div className="controls">
        <button type="button" onClick={handlePrev} disabled={visibleCount <= 1}>
          Previous
        </button>
        <span className="step-counter">
          Step {visibleCount} of {allSteps.length}
        </span>
        <button type="button" onClick={handleNext} disabled={visibleCount >= allSteps.length}>
          Next
        </button>
        <button type="button" onClick={handleReset} className="reset-btn">
          Reset
        </button>
      </div>
      <div className="instructions">
        Click Next to reveal each step. No token after <code>max_iterations</code> → <code>ralph.py</code> exits 1
        (check <code>bd list --status open</code>).
      </div>
    </div>
  );
}

export default App;

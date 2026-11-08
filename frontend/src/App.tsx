
import { useEffect, useRef, useState, type CSSProperties, type FormEvent } from 'react'
import cytoscape, { type Core, type ElementDefinition } from 'cytoscape'
import './App.css'

type NodeData = {
  id: string
  label: string
  type: string
  size?: number
}

type EdgeData = {
  id: string
  source: string
  target: string
  label: string
  memory_id: string
  subject: string
  predicate: string
  object_value: string
  context: string | null
  status: string
  confidence: number
  source_id: string
  recorded_at: string | null
  valid_from: string | null
  valid_to: string | null
}

type GraphData = {
  nodes: { data: NodeData }[]
  edges: { data: EdgeData }[]
}

type SelectedItem = NodeData | EdgeData

type MemoryRecord = {
  memory_id: string
  subject: string
  predicate: string
  object_value: string
  context: string | null
  source_id: string
  status: 'ACTIVE' | 'SUPERSEDED' | 'UNRESOLVED' | string
  confidence: number
  valid_from: string | null
  valid_to: string | null
  recorded_at: string | null
}

type MemoryEditForm = {
  subject: string
  predicate: string
  object_value: string
  context: string
  valid_from: string
  valid_to: string
}

const databaseInputStyle: CSSProperties = {
  width: '100%',
  minWidth: '125px',
  boxSizing: 'border-box',
  padding: '8px 9px',
  border: '1px solid #40536B',
  borderRadius: '6px',
  background: '#101B2A',
  color: '#E8EEF7',
  fontSize: '12px',
  fontFamily: 'inherit',
}

const databaseCellStyle: CSSProperties = {
  padding: '12px 10px',
  borderBottom: '1px solid #26364A',
  color: '#D5DFEC',
  fontSize: '12px',
  verticalAlign: 'top',
  whiteSpace: 'nowrap',
}

type ChatSource = {
  memory_id: string
  subject: string
  predicate: string
  object_value: string
  context: string | null
  status: string
  similarity: number
}

type ChatMessage = {
  id: number
  role: 'user' | 'assistant'
  content: string
  sources?: ChatSource[]
}

const graphLayout = {
  name: 'cose' as const,
  animate: false,
  fit: true,
  padding: 65,
  nodeRepulsion: () => 450000,
  idealEdgeLength: () => 150,
  edgeElasticity: () => 100,
  nestingFactor: 1.2,
  gravity: 0.25,
  numIter: 1000,
  initialTemp: 200,
  coolingFactor: 0.95,
  minTemp: 1,
}

function App() {
  const graphRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)
  const chatMessagesRef = useRef<HTMLDivElement>(null)

  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [selected, setSelected] = useState<SelectedItem | null>(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [showSuperseded, setShowSuperseded] = useState(false)
  const [showUnresolved, setShowUnresolved] = useState(true)

  const [view, setView] = useState<'explorer' | 'database' | 'chat'>('explorer')
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])

  const [deletingNode, setDeletingNode] = useState(false)
  const [deletingEdge, setDeletingEdge] = useState(false)
  const [deleteError, setDeleteError] = useState('')

  const [memories, setMemories] = useState<MemoryRecord[]>([])
  const [databaseLoading, setDatabaseLoading] = useState(false)
  const [databaseError, setDatabaseError] = useState('')
  const [databaseSearch, setDatabaseSearch] = useState('')
  const [databaseStatus, setDatabaseStatus] = useState('ALL')
  const [editingMemoryId, setEditingMemoryId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<MemoryEditForm | null>(null)
  const [savingMemory, setSavingMemory] = useState(false)
  const [databaseMessage, setDatabaseMessage] = useState('')

  // Fetch graph data.
  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/graph')
      .then((response) => {
        if (!response.ok) throw new Error('Could not load graph')
        return response.json()
      })
      .then((data: GraphData) => {
        setGraphData(data)
        setError('')
      })
      .catch(() => {
        setError('Unable to connect to MemoryMesh API.')
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  // Load the complete database table from the existing SQLite-backed API.
  useEffect(() => {
    void refreshMemories()
  }, [])

  // Initialize Cytoscape.
  useEffect(() => {
    if (!graphData || !graphRef.current) return

    const degree = new Map<string, number>()

    graphData.nodes.forEach(({ data }) => degree.set(data.id, 0))

    graphData.edges.forEach(({ data }) => {
      degree.set(data.source, (degree.get(data.source) ?? 0) + 1)
      degree.set(data.target, (degree.get(data.target) ?? 0) + 1)
    })

    const getNodeSize = (connections: number) => {
      if (connections <= 1) return 42
      if (connections <= 3) return 62
      if (connections <= 5) return 82
      return 104
    }

    const elements: ElementDefinition[] = [
      ...graphData.nodes.map(({ data }) => ({
        data: {
          ...data,
          size: getNodeSize(degree.get(data.id) ?? 0),
        },
      })),
      ...graphData.edges.map((edge) => ({
        ...edge,
        classes: edge.data.status.toLowerCase(),
      })),
    ]

    const cy = cytoscape({
      container: graphRef.current,
      elements,
      layout: graphLayout,
      minZoom: 0.2,
      maxZoom: 3,
      wheelSensitivity: 0.2,
      style: [
        {
          selector: 'node',
          style: {
            shape: 'ellipse',
            width: 'data(size)',
            height: 'data(size)',
            'background-color': '#29496F',
            'border-color': '#A8CFFF',
            'border-width': 3,
            label: 'data(label)',
            color: '#FFFFFF',
            'font-size': 18,
            'min-zoomed-font-size': 14,
            'font-weight': 'bold',
            'font-family': 'Arial, sans-serif',
            'text-wrap': 'wrap',
            'text-max-width': '130px',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 12,
            'text-background-color': '#080E18',
            'text-background-opacity': 0.98,
            'text-background-padding': '4px',
            'overlay-opacity': 0,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 3,
            'line-color': '#91A4BE',
            'target-arrow-color': '#91A4BE',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 1.15,
            'curve-style': 'bezier',
            label: '',
            color: '#FFFFFF',
            'font-size': 13,
            'font-weight': 'bold',
            'text-background-color': '#080E18',
            'text-background-opacity': 0.98,
            'text-background-padding': '4px',
            'overlay-opacity': 0,
          },
        },
        {
          selector: '.active',
          style: {
            'line-color': '#45E0B0',
            'target-arrow-color': '#45E0B0',
            'line-style': 'solid',
            width: 3,
          },
        },
        {
          selector: '.unresolved',
          style: {
            'line-color': '#FFC15C',
            'target-arrow-color': '#FFC15C',
            'line-style': 'dotted',
            width: 3.5,
          },
        },
        {
          selector: '.superseded',
          style: {
            'line-color': '#8998AD',
            'target-arrow-color': '#8998AD',
            'line-style': 'solid',
            opacity: 0.55,
            width: 2.5,
          },
        },
        {
          selector: '.selected',
          style: {
            'border-color': '#FFFFFF',
            'border-width': 4,
            'background-color': '#3D6592',
          },
        },
        {
          selector: '.dimmed',
          style: {
            opacity: 0.15,
          },
        },
        {
          selector: 'node.focused',
          style: {
            'border-color': '#FFFFFF',
            'border-width': 4,
            opacity: 1,
          },
        },
        {
          selector: 'edge.focused',
          style: {
            width: 3.5,
            opacity: 1,
          },
        },
        {
          selector: 'edge.inspected',
          style: {
            label: 'data(label)',
            'font-size': 13,
            color: '#FFFFFF',
            'text-background-color': '#172638',
            'text-background-opacity': 1,
            'text-background-padding': '5px',
            width: 4,
            opacity: 1,
            'line-color': '#FFFFFF',
            'target-arrow-color': '#FFFFFF',
          },
        },
      ],
    })

    cyRef.current = cy

    cy.on('tap', 'edge', (event) => {
      const edge = event.target
      const neighborhood = edge.union(edge.source()).union(edge.target())

      cy.elements().removeClass('focused dimmed inspected')
      cy.elements().difference(neighborhood).addClass('dimmed')
      neighborhood.addClass('focused')
      edge.addClass('inspected')

      setDeleteError('')
      setSelected(edge.data() as EdgeData)
    })

    cy.on('tap', 'node', (event) => {
      const node = event.target
      const neighborhood = node.closedNeighborhood()

      cy.elements().removeClass('focused dimmed inspected')
      cy.elements().difference(neighborhood).addClass('dimmed')
      neighborhood.addClass('focused')

      setDeleteError('')
      setSelected(node.data() as NodeData)
    })

    cy.on('tap', (event) => {
      if (event.target === cy) {
        cy.elements().removeClass('focused dimmed inspected')
        setSelected(null)
        setDeleteError('')
      }
    })

    return () => {
      cy.destroy()
      cyRef.current = null
    }
  }, [graphData])

  // Filter memories by status.
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return

    cy.edges().forEach((edge) => {
      const status = edge.data('status')
      const visible =
        status === 'ACTIVE' ||
        (status === 'UNRESOLVED' && showUnresolved) ||
        (status === 'SUPERSEDED' && showSuperseded)

      edge.style('display', visible ? 'element' : 'none')
    })

    cy.nodes().forEach((node) => {
      const connected = node.connectedEdges().some(
        (edge) => edge.style('display') !== 'none',
      )
      node.style('display', connected ? 'element' : 'none')
    })
  }, [showSuperseded, showUnresolved, graphData])

  // Search entities.
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return

    const term = search.toLowerCase().trim()
    cy.elements().removeClass('selected')

    if (!term) return

    const matches = cy.nodes().filter((node) =>
      String(node.data('label')).toLowerCase().includes(term),
    )

    matches.addClass('selected')

    if (matches.length) {
      cy.animate({
        fit: { eles: matches, padding: 100 },
        duration: 350,
      })
    }
  }, [search])

  // Keep the latest chat message visible.
  useEffect(() => {
    const container = chatMessagesRef.current
    if (container) {
      container.scrollTo({
        top: container.scrollHeight,
        behavior: 'smooth',
      })
    }
  }, [messages, chatLoading])

  // Graph navigation controls.
  function fitGraph() {
    const cy = cyRef.current
    if (!cy) return

    const visibleElements = cy.elements(':visible')
    if (visibleElements.length > 0) cy.fit(visibleElements, 70)
  }

  function zoomGraph(direction: 'in' | 'out') {
    const cy = cyRef.current
    if (!cy) return

    const factor = direction === 'in' ? 1.25 : 0.8
    const nextZoom = Math.max(
      cy.minZoom(),
      Math.min(cy.maxZoom(), cy.zoom() * factor),
    )

    cy.zoom({
      level: nextZoom,
      renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 },
    })
  }

  function resetGraphLayout() {
    const cy = cyRef.current
    if (!cy) return

    cy.elements().removeClass('focused dimmed inspected selected')
    setSelected(null)
    setDeleteError('')
    setSearch('')
    cy.layout(graphLayout).run()
  }

  // Refresh graph after a memory has been added, updated, or deleted.
  async function refreshGraph(): Promise<boolean> {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/graph')

      if (!response.ok) {
        throw new Error('Could not refresh graph')
      }

      const data: GraphData = await response.json()

      setGraphData(data)
      setSelected(null)
      setDeleteError('')
      setError('')

      return true
    } catch {
      setError('The graph could not be refreshed.')
      return false
    }
  }

  async function refreshMemories(): Promise<boolean> {
    setDatabaseLoading(true)
    try {
      const response = await fetch('http://127.0.0.1:8000/api/memories')
      if (!response.ok) throw new Error('Could not load memory records.')
      const data: MemoryRecord[] = await response.json()
      setMemories(data)
      setDatabaseError('')
      return true
    } catch (err) {
      setDatabaseError(
        err instanceof Error ? err.message : 'Unable to load memory records.',
      )
      return false
    } finally {
      setDatabaseLoading(false)
    }
  }

  function startEditingMemory(memory: MemoryRecord) {
    setDatabaseMessage('')
    setDatabaseError('')
    setEditingMemoryId(memory.memory_id)
    setEditForm({
      subject: memory.subject,
      predicate: memory.predicate,
      object_value: memory.object_value,
      context: memory.context ?? '',
      // The API stores timezone-aware timestamps. The editor displays UTC.
      valid_from: memory.valid_from ? memory.valid_from.slice(0, 16) : '',
      valid_to: memory.valid_to ? memory.valid_to.slice(0, 16) : '',
    })
  }

  function cancelEditingMemory() {
    setEditingMemoryId(null)
    setEditForm(null)
    setDatabaseError('')
  }

  async function saveMemoryEdit(memoryId: string) {
    if (!editForm || savingMemory) return

    if (
      !editForm.subject.trim() ||
      !editForm.predicate.trim() ||
      !editForm.object_value.trim()
    ) {
      setDatabaseError('Subject, predicate, and object value cannot be empty.')
      return
    }

    const toUtcIso = (value: string) =>
      value ? `${value}:00+00:00` : null

    const payload = {
      subject: editForm.subject.trim(),
      predicate: editForm.predicate.trim(),
      object_value: editForm.object_value.trim(),
      context: editForm.context.trim() || null,
      valid_from: toUtcIso(editForm.valid_from),
      valid_to: toUtcIso(editForm.valid_to),
    }

    setSavingMemory(true)
    setDatabaseError('')
    setDatabaseMessage('')

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/memories/${memoryId}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        },
      )

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Could not update this memory.')
      }

      setEditingMemoryId(null)
      setEditForm(null)
      setDatabaseMessage('Memory updated successfully.')

      const [tableRefreshed, graphRefreshed] = await Promise.all([
        refreshMemories(),
        refreshGraph(),
      ])

      if (!tableRefreshed || !graphRefreshed) {
        setDatabaseError('Memory was saved, but one of the views could not refresh. Reload the page.')
        setDatabaseMessage('')
      }
    } catch (err) {
      setDatabaseError(
        err instanceof Error ? err.message : 'Unable to update this memory.',
      )
    } finally {
      setSavingMemory(false)
    }
  }

  // Delete the selected entity and every memory connected to it.
  async function deleteSelectedNode() {
    if (!selected || 'memory_id' in selected || deletingNode) return

    const node = selected

    const connectedCount =
      graphData?.edges.filter(
        ({ data }) =>
          data.source === node.id || data.target === node.id,
      ).length ?? 0

    if (connectedCount === 0) {
      setDeleteError('No connected memories found for this entity.')
      return
    }

    const confirmed = window.confirm(
      `Permanently delete "${node.label}"?\n\n` +
        `${connectedCount} connected memories will be deleted, ` +
        `including superseded and unresolved memories.\n\n` +
        `This action cannot be undone.`,
    )

    if (!confirmed) return

    setDeletingNode(true)
    setDeleteError('')

    try {
      const response = await fetch(
        'http://127.0.0.1:8000/api/graph/node',
        {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            node_id: node.id,
          }),
        },
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.detail || 'Could not delete this entity.',
        )
      }

      const refreshed = await refreshGraph()

      if (refreshed) {
        window.alert(
          `Entity "${node.label}" deleted successfully.\n` +
            `${data.deleted_memories} memories permanently deleted.`,
        )
      } else {
        window.alert(
          `${data.deleted_memories} memories were deleted, ` +
            `but the graph could not refresh. Reload the page.`,
        )
      }
    } catch (err) {
      setDeleteError(
        err instanceof Error
          ? err.message
          : 'Unable to delete this entity.',
      )
    } finally {
      setDeletingNode(false)
    }
  }

  // Delete only the selected relationship.
  async function deleteSelectedEdge() {
    if (!selected || !('memory_id' in selected) || deletingEdge) return

    const edge = selected

    const confirmed = window.confirm(
      `Permanently delete this relationship?\n\n` +
        `${edge.subject} → ${edge.predicate} → ${edge.object_value}\n\n` +
        `Only this memory will be deleted. Other relationships will remain.\n\n` +
        `This action cannot be undone.`,
    )

    if (!confirmed) return

    setDeletingEdge(true)
    setDeleteError('')

    try {
      const response = await fetch(
        'http://127.0.0.1:8000/api/graph/edge',
        {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            memory_id: edge.memory_id,
          }),
        },
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.detail || 'Could not delete this relationship.',
        )
      }

      const refreshed = await refreshGraph()

      if (refreshed) {
        window.alert('Relationship deleted successfully.')
      } else {
        window.alert(
          'The relationship was deleted, but the graph could not refresh. Reload the page.',
        )
      }
    } catch (err) {
      setDeleteError(
        err instanceof Error
          ? err.message
          : 'Unable to delete this relationship.',
      )
    } finally {
      setDeletingEdge(false)
    }
  }

  // Send a question or /remember command to the MemoryMesh API.
  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const question = chatInput.trim()
    if (!question || chatLoading) return

    const userMessage: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content: question,
    }

    setMessages((previous) => [...previous, userMessage])
    setChatInput('')
    setChatError('')
    setChatLoading(true)

    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: question }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.detail || 'Something went wrong while processing your message.',
        )
      }

      const assistantMessage: ChatMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.answer,
        sources: data.sources ?? [],
      }

      setMessages((previous) => [...previous, assistantMessage])

      if (
        data.type === 'memory' &&
        (data.action === 'ADDED' || data.action === 'ADDED_UNRESOLVED')
      ) {
        await refreshGraph()
      }
    } catch (err) {
      setChatError(
        err instanceof Error
          ? err.message
          : 'Unable to connect to MemoryMesh API.',
      )
    } finally {
      setChatLoading(false)
    }
  }

  function clearChat() {
    if (chatLoading) return
    setMessages([])
    setChatError('')
  }

  // Memory counts.
  const counts = {
    total: graphData?.edges.length ?? 0,
    active:
      graphData?.edges.filter((edge) => edge.data.status === 'ACTIVE').length ??
      0,
    unresolved:
      graphData?.edges.filter((edge) => edge.data.status === 'UNRESOLVED')
        .length ?? 0,
    superseded:
      graphData?.edges.filter((edge) => edge.data.status === 'SUPERSEDED')
        .length ?? 0,
  }

  const filteredMemories = memories.filter((memory) => {
    const matchesStatus = databaseStatus === 'ALL' || memory.status === databaseStatus
    const term = databaseSearch.trim().toLowerCase()
    const matchesSearch =
      !term ||
      [memory.subject, memory.predicate, memory.object_value, memory.context ?? '', memory.memory_id]
        .some((value) => value.toLowerCase().includes(term))
    return matchesStatus && matchesSearch
  })

  return (
    <main className={`app-shell ${view === 'chat' ? 'chat-mode' : view === 'database' ? 'database-mode' : ''}`}>
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">M</div>
          <div>
            <h1>MemoryMesh</h1>
            <span>PERSONAL KNOWLEDGE ENGINE</span>
          </div>
        </div>

        <div className="sidebar-section">
          <p className="section-label">WORKSPACE</p>

          <button
            className={`nav-button ${view === 'chat' ? 'active' : ''}`}
            onClick={() => setView('chat')}
          >
            <span>◉</span>
            Chat
          </button>

          <button
            className={`nav-button ${view === 'explorer' ? 'active' : ''}`}
            onClick={() => setView('explorer')}
          >
            <span>◇</span>
            Knowledge Graph
          </button>
          <button
            className={`nav-button ${view === 'database' ? 'active' : ''}`}
            onClick={() => {
              setView('database')
              void refreshMemories()
            }}
          >
            <span>▦</span>
            Database
          </button>
        </div>

        {view === 'explorer' && (
          <>
            <div className="sidebar-section">
              <p className="section-label">EXPLORER</p>
              <input
                className="search-input"
                placeholder="Search entities..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <div className="sidebar-section">
              <p className="section-label">MEMORY STATUS</p>

              <label className="filter-row">
                <span>
                  <i className="status-dot active-dot" />
                  Active
                </span>
                <strong>{counts.active}</strong>
              </label>

              <label className="filter-row">
                <span>
                  <i className="status-dot unresolved-dot" />
                  Unresolved
                </span>
                <input
                  type="checkbox"
                  checked={showUnresolved}
                  onChange={(e) => setShowUnresolved(e.target.checked)}
                />
              </label>

              <label className="filter-row">
                <span>
                  <i className="status-dot superseded-dot" />
                  Superseded
                </span>
                <input
                  type="checkbox"
                  checked={showSuperseded}
                  onChange={(e) => setShowSuperseded(e.target.checked)}
                />
              </label>
            </div>
          </>
        )}

        <div className="sidebar-bottom">
          <div className="connection-indicator">
            <i
              className={`status-dot ${
                error ? 'superseded-dot' : 'active-dot'
              }`}
            />
            {error
              ? 'API disconnected'
              : loading
                ? 'Connecting...'
                : 'Memory engine connected'}
          </div>
          <span>MEMORYMESH · V0.1</span>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="breadcrumb">
              KNOWLEDGE BASE / {view === 'chat' ? 'CHAT' : view === 'database' ? 'DATABASE' : 'EXPLORER'}
            </p>
            <h2>
              {view === 'chat' ? 'Chat with MemoryMesh' : view === 'database' ? 'Memory Database' : 'Knowledge Graph'}
            </h2>
          </div>

          {view === 'explorer' && (
            <div className="topbar-stats">
              <div>
                <strong>{counts.total}</strong>
                <span>Memories</span>
              </div>
              <div>
                <strong>{graphData?.nodes.length ?? 0}</strong>
                <span>Entities</span>
              </div>
            </div>
          )}

          {view === 'database' && (
            <div className="topbar-stats">
              <div>
                <strong>{memories.length}</strong>
                <span>Records</span>
              </div>
              <div>
                <strong>{memories.filter((memory) => memory.status === 'ACTIVE').length}</strong>
                <span>Active</span>
              </div>
            </div>
          )}

          {view === 'chat' && (
            <button
              className="clear-chat-button"
              onClick={clearChat}
              disabled={messages.length === 0 || chatLoading}
            >
              Clear chat
            </button>
          )}
        </header>

        {/* Keep the graph mounted when switching views. */}
        <div className={`graph-area ${view !== 'explorer' ? 'view-hidden' : ''}`}>
          {loading && (
            <div className="graph-message">Loading knowledge graph...</div>
          )}

          {error && (
            <div className="graph-message error-message">{error}</div>
          )}

          <div ref={graphRef} className="graph-canvas" />

          <div className="graph-controls">
            <button onClick={fitGraph} title="Fit graph to screen">
              <span>⛶</span>
              Fit
            </button>
            <button onClick={() => zoomGraph('in')} title="Zoom in">
              +
            </button>
            <button onClick={() => zoomGraph('out')} title="Zoom out">
              −
            </button>
            <button onClick={resetGraphLayout} title="Reset graph layout">
              <span>↻</span>
              Reset
            </button>
          </div>

          <div className="graph-legend">
            <p className="legend-title">GRAPH LEGEND</p>

            <div className="legend-row">
              <i className="legend-entity" />
              <span>Entity</span>
            </div>

            <div className="legend-row">
              <i className="legend-line active" />
              <span>Active memory · solid line</span>
            </div>

            <div className="legend-row">
              <i className="legend-line unresolved" />
              <span>Unresolved memory · dotted line</span>
            </div>

            <div className="legend-row">
              <i
                className="legend-line superseded"
                style={{
                  borderTop: '3px solid #8998AD',
                  borderBottom: 'none',
                  background: 'none',
                  opacity: 1,
                }}
              />
              <span>Superseded memory · solid grey line</span>
            </div>

            <p className="legend-note">Arrow points from subject to object.</p>
          </div>

          <div className="graph-hint">
            Drag to move · Scroll to zoom · Select an edge to inspect
          </div>
        </div>

        {/* Database view */}
        <div
          className={`database-area ${view === 'database' ? '' : 'view-hidden'}`}
        >
          <div className="database-toolbar">
            <input
              value={databaseSearch}
              onChange={(event) => setDatabaseSearch(event.target.value)}
              placeholder="Search memories..."
              style={{ ...databaseInputStyle, maxWidth: '360px', minWidth: '220px', padding: '10px 12px' }}
            />
            <select
              value={databaseStatus}
              onChange={(event) => setDatabaseStatus(event.target.value)}
              style={{ ...databaseInputStyle, width: '170px', minWidth: '150px', padding: '10px 12px' }}
            >
              <option value="ALL">All statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="UNRESOLVED">Unresolved</option>
              <option value="SUPERSEDED">Superseded</option>
            </select>
            <button
              type="button"
              onClick={() => void refreshMemories()}
              disabled={databaseLoading}
              className="database-refresh-button" 
            >
              {databaseLoading ? 'Refreshing...' : 'Refresh'}
            </button>
            <span style={{ color: '#91A4BE', fontSize: '12px' }}>
              {filteredMemories.length} of {memories.length} records
            </span>
          </div>

          {databaseError && (
            <p style={{ margin: 0, color: '#FF8585', fontSize: '13px' }}>{databaseError}</p>
          )}
          {databaseMessage && (
            <p style={{ margin: 0, color: '#45E0B0', fontSize: '13px' }}>{databaseMessage}</p>
          )}

          <div className="database-table-viewport">
            <table className="database-table" style={{ width: '100%', minWidth: '1650px', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead style={{ position: 'sticky', top: 0, zIndex: 2, background: '#172638' }}>
                <tr>
                  {['Subject', 'Predicate', 'Object value', 'Context', 'Valid from (UTC)', 'Valid to (UTC)', 'Status', 'Confidence', 'Source', 'Recorded at', 'Memory ID', 'Actions'].map((heading) => (
                    <th key={heading} style={{ ...databaseCellStyle, color: '#AFC1D8', fontWeight: 700, background: '#172638' }}>{heading}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredMemories.map((memory) => {
                  const rowEditForm = editingMemoryId === memory.memory_id ? editForm : null
                  const isEditing = rowEditForm !== null
                  return (
                    <tr key={memory.memory_id} style={{ background: isEditing ? '#142338' : 'transparent' }}>
                      <td style={databaseCellStyle}>{isEditing ? <input aria-label="Subject" style={databaseInputStyle} value={rowEditForm.subject} onChange={(event) => setEditForm({ ...rowEditForm, subject: event.target.value })} /> : memory.subject}</td>
                      <td style={databaseCellStyle}>{isEditing ? <input aria-label="Predicate" style={databaseInputStyle} value={rowEditForm.predicate} onChange={(event) => setEditForm({ ...rowEditForm, predicate: event.target.value })} /> : memory.predicate}</td>
                      <td style={databaseCellStyle}>{isEditing ? <input aria-label="Object value" style={databaseInputStyle} value={rowEditForm.object_value} onChange={(event) => setEditForm({ ...rowEditForm, object_value: event.target.value })} /> : memory.object_value}</td>
                      <td style={{ ...databaseCellStyle, whiteSpace: isEditing ? 'normal' : 'nowrap' }}>{isEditing ? <input aria-label="Context" style={databaseInputStyle} value={rowEditForm.context} onChange={(event) => setEditForm({ ...rowEditForm, context: event.target.value })} /> : memory.context || '—'}</td>
                      <td style={databaseCellStyle}>{isEditing ? <input aria-label="Valid from" type="datetime-local" style={databaseInputStyle} value={rowEditForm.valid_from} onChange={(event) => setEditForm({ ...rowEditForm, valid_from: event.target.value })} /> : memory.valid_from || '—'}</td>
                      <td style={databaseCellStyle}>{isEditing ? <input aria-label="Valid to" type="datetime-local" style={databaseInputStyle} value={rowEditForm.valid_to} onChange={(event) => setEditForm({ ...rowEditForm, valid_to: event.target.value })} /> : memory.valid_to || '—'}</td>
                      <td style={databaseCellStyle}><span className={`status-badge ${memory.status.toLowerCase()}`}>{memory.status}</span></td>
                      <td style={databaseCellStyle}>{(memory.confidence * 100).toFixed(1)}%</td>
                      <td style={databaseCellStyle}>{memory.source_id}</td>
                      <td style={databaseCellStyle}>{memory.recorded_at || '—'}</td>
                      <td style={{ ...databaseCellStyle, fontFamily: 'monospace', fontSize: '11px' }}>{memory.memory_id}</td>
                      <td style={databaseCellStyle}>
                        {isEditing ? (
                          <div style={{ display: 'flex', gap: '6px' }}>
                            <button type="button" onClick={() => void saveMemoryEdit(memory.memory_id)} disabled={savingMemory} style={{ padding: '7px 10px', border: '1px solid #267D65', borderRadius: '5px', background: '#174D40', color: '#C9FFF0', cursor: savingMemory ? 'wait' : 'pointer' }}>{savingMemory ? 'Saving...' : 'Save'}</button>
                            <button type="button" onClick={cancelEditingMemory} disabled={savingMemory} style={{ padding: '7px 10px', border: '1px solid #40536B', borderRadius: '5px', background: '#243449', color: '#D5DFEC', cursor: 'pointer' }}>Cancel</button>
                          </div>
                        ) : (
                          <button type="button" onClick={() => startEditingMemory(memory)} disabled={editingMemoryId !== null} style={{ padding: '7px 10px', border: '1px solid #40536B', borderRadius: '5px', background: '#1B2B40', color: '#D5DFEC', cursor: editingMemoryId !== null ? 'not-allowed' : 'pointer', opacity: editingMemoryId !== null ? 0.5 : 1 }}>Edit</button>
                        )}
                      </td>
                    </tr>
                  )
                })}
                {!databaseLoading && filteredMemories.length === 0 && (
                  <tr>
                    <td colSpan={12} style={{ ...databaseCellStyle, padding: '30px', textAlign: 'center', color: '#91A4BE' }}>
                      {databaseError ? 'Could not load memory records.' : 'No memory records match this filter.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <p style={{ margin: 0, color: '#8295AD', fontSize: '11px' }}>
            Only subject, predicate, object value, context, valid from, and valid to can be edited. Status and metadata are read-only. Dates are displayed and edited in UTC.
          </p>
        </div>

        {/* Chat view */}
        <div className={`chat-area ${view !== 'chat' ? 'view-hidden' : ''}`}>
          <div className="chat-messages" ref={chatMessagesRef}>
            {messages.length === 0 && (
              <div className="chat-welcome">
                <div className="chat-welcome-icon">M</div>
                <h3>Ask or tell MemoryMesh something.</h3>
                <p>
                  Ask questions about your stored memories, or use{' '}
                  <strong>/remember</strong> followed by information you want
                  to add to your knowledge graph.
                </p>

                <div className="suggested-questions">
                  <button
                    onClick={() =>
                      setChatInput(
                        'What programming language does my backend use?',
                      )
                    }
                  >
                    What programming language does my backend use?
                  </button>
                  <button
                    onClick={() =>
                      setChatInput(
                        '/remember The MemoryMesh frontend uses React with TypeScript.',
                      )
                    }
                  >
                    /remember The MemoryMesh frontend uses React with TypeScript.
                  </button>
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div
                className={`message-row ${message.role}`}
                key={message.id}
              >
                {message.role === 'assistant' && (
                  <div className="message-avatar">M</div>
                )}

                <div className="message-content">
                  <div className="message-bubble">{message.content}</div>

                  {message.role === 'assistant' &&
                    message.sources &&
                    message.sources.length > 0 && (
                      <div className="message-sources">
                        <p className="sources-heading">
                          SOURCES · {message.sources.length}
                        </p>

                        {message.sources.map((source) => (
                          <details
                            className="source-card"
                            key={source.memory_id}
                          >
                            <summary>
                              <span>
                                {source.subject} → {source.object_value}
                              </span>
                              <span className="source-chevron">⌄</span>
                            </summary>

                            <div className="source-details">
                              <p>
                                <strong>Predicate:</strong> {source.predicate}
                              </p>
                              <p>
                                <strong>Status:</strong> {source.status}
                              </p>
                              <p>
                                <strong>Similarity:</strong>{' '}
                                {(source.similarity * 100).toFixed(1)}%
                              </p>
                              {source.context && (
                                <p>
                                  <strong>Context:</strong> {source.context}
                                </p>
                              )}
                              <p className="source-id">{source.memory_id}</p>
                            </div>
                          </details>
                        ))}
                      </div>
                    )}
                </div>

                {message.role === 'user' && (
                  <div className="user-avatar">You</div>
                )}
              </div>
            ))}

            {chatLoading && (
              <div className="message-row assistant">
                <div className="message-avatar">M</div>
                <div className="typing-indicator">
                  Processing your message...
                </div>
              </div>
            )}

            {chatError && <div className="chat-error">{chatError}</div>}
          </div>

          <form className="chat-input-area" onSubmit={sendMessage}>
            <input
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask a question or use /remember to add a memory..."
              disabled={chatLoading}
            />
            <button
              type="submit"
              disabled={!chatInput.trim() || chatLoading}
            >
              {chatLoading ? '...' : 'Send'}
            </button>
          </form>

          <p className="chat-disclaimer">
            Use /remember before information you want to store. Other messages
            are treated as questions.
          </p>
        </div>
      </section>

      <aside className={`inspector ${view !== 'explorer' ? 'view-hidden' : ''}`}>
        <div className="inspector-header">
          <p className="section-label">INSPECTOR</p>
          <h3>{selected ? 'Selected item' : 'No selection'}</h3>
        </div>

        {selected ? (
          <div className="inspector-content">
            {'memory_id' in selected ? (
              <>
                <span
                  className={`status-badge ${selected.status.toLowerCase()}`}
                >
                  {selected.status}
                </span>
                <h4>{selected.subject}</h4>
                <p className="relation-label">{selected.predicate}</p>
                <h4>{selected.object_value}</h4>

                <div className="detail-divider" />

                <p className="detail-label">CONTEXT</p>
                <p className="detail-value">
                  {selected.context || 'No context provided'}
                </p>

                <p className="detail-label">CONFIDENCE</p>
                <p className="detail-value">
                  {(selected.confidence * 100).toFixed(1)}%
                </p>

                <p className="detail-label">SOURCE</p>
                <p className="detail-value">{selected.source_id}</p>

                <p className="detail-label">RECORDED AT</p>
                <p className="detail-value">
                  {selected.recorded_at || 'Unknown'}
                </p>

                <p className="detail-label">VALID FROM</p>
                <p className="detail-value">
                  {selected.valid_from || 'Not specified'}
                </p>

                <p className="detail-label">VALID TO</p>
                <p className="detail-value">
                  {selected.valid_to || 'Not specified'}
                </p>

                <p className="detail-label">MEMORY ID</p>
                <p className="detail-value id-value">
                  {selected.memory_id}
                </p>

                {deleteError && (
                  <p
                    className="detail-value"
                    style={{
                      color: '#FF8585',
                      marginTop: '14px',
                    }}
                  >
                    {deleteError}
                  </p>
                )}

                <button
                  type="button"
                  onClick={deleteSelectedEdge}
                  disabled={deletingEdge}
                  style={{
                    width: 'fit-content',
                    marginTop: '16px',
                    padding: '8px 12px',
                    border: '1px solid #A94747',
                    borderRadius: '6px',
                    background: '#512626',
                    color: '#FFDADA',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: deletingEdge ? 'wait' : 'pointer',
                    opacity: deletingEdge ? 0.6 : 1,
                  }}
                >
                  {deletingEdge ? 'Deleting...' : 'Delete relationship'}
                </button>
              </>
            ) : (
              <>
                <span className="status-badge entity-badge">ENTITY</span>
                <h4>{selected.label}</h4>
                <p className="detail-value">Graph entity</p>

                <p className="detail-label">CONNECTED MEMORIES</p>

                <div className="connected-memories">
                  {graphData?.edges
                    .filter(
                      (edge) =>
                        edge.data.source === selected.id ||
                        edge.data.target === selected.id,
                    )
                    .map(({ data: memory }) => (
                      <div
                        className="connected-memory"
                        key={memory.memory_id}
                      >
                        <div className="connected-memory-top">
                          <span>{memory.predicate}</span>
                          <span
                            className={`status-badge ${memory.status.toLowerCase()}`}
                          >
                            {memory.status}
                          </span>
                        </div>

                        <p className="connected-memory-value">
                          {memory.subject} → {memory.object_value}
                        </p>

                        {memory.context && (
                          <p className="connected-memory-context">
                            {memory.context}
                          </p>
                        )}
                      </div>
                    ))}
                </div>

                {deleteError && (
                  <p
                    className="detail-value"
                    style={{
                      color: '#FF8585',
                      marginTop: '14px',
                    }}
                  >
                    {deleteError}
                  </p>
                )}

                <button
                  type="button"
                  className="delete-node-button"
                  onClick={deleteSelectedNode}
                  disabled={deletingNode}
                  style={{
                    width: 'fit-content',
                    marginTop: '16px',
                    padding: '8px 12px',
                    border: '1px solid #A94747',
                    borderRadius: '6px',
                    background: '#512626',
                    color: '#FFDADA',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: deletingNode ? 'wait' : 'pointer',
                    opacity: deletingNode ? 0.6 : 1,
                  }}
                >
                  {deletingNode ? 'Deleting...' : 'Delete entity and memories'}
                </button>
              </>
            )}
          </div>
        ) : (
          <div className="empty-inspector">
            <div className="empty-icon">◇</div>
            <p>
              Select a node or memory edge in the graph to inspect its details.
            </p>
          </div>
        )}
      </aside>
    </main>
  )
}

export default App

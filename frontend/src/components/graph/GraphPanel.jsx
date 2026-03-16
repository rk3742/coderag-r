import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { api } from '../../utils/api'
import { useStore } from '../../store'
import { Loader2, X, ZoomIn, ZoomOut, RefreshCw } from 'lucide-react'

const TYPE_COLOR = {
  function: '#6366f1',
  method:   '#10b981',
  class:    '#f59e0b',
  module:   '#64748b',
}

export default function GraphPanel() {
  const svgRef = useRef()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [tooltip, setTooltip] = useState(null)
  const { activeRepo, toggleGraph } = useStore()
  const simRef = useRef()
  const zoomRef = useRef()

  useEffect(() => {
    if (!activeRepo?.id) return
    loadGraph()
  }, [activeRepo?.id])

  async function loadGraph() {
    setLoading(true)
    try {
      const d = await api.getGraph(activeRepo.id, 120)
      setData(d)
    } catch {}
    setLoading(false)
  }

  useEffect(() => {
    if (!data || !svgRef.current) return
    drawGraph(data)
  }, [data])

  function drawGraph({ nodes, edges }) {
    const el = svgRef.current
    d3.select(el).selectAll('*').remove()
    const W = el.clientWidth || 600
    const H = el.clientHeight || 500

    const svg = d3.select(el)
      .attr('width', W)
      .attr('height', H)

    const g = svg.append('g')

    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', e => g.attr('transform', e.transform))
    svg.call(zoom)
    zoomRef.current = zoom

    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id(d => d.id).distance(60).strength(0.5))
      .force('charge', d3.forceManyBody().strength(-120))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collision', d3.forceCollide(18))
    simRef.current = sim

    // Edges
    const link = g.append('g').selectAll('line')
      .data(edges).join('line')
      .attr('stroke', '#ffffff10')
      .attr('stroke-width', 1)

    // Arrow marker
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -4 8 8')
      .attr('refX', 18).attr('refY', 0)
      .attr('markerWidth', 5).attr('markerHeight', 5)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-4L8,0L0,4')
      .attr('fill', '#ffffff20')

    link.attr('marker-end', 'url(#arrowhead)')

    // Nodes
    const node = g.append('g').selectAll('g')
      .data(nodes).join('g')
      .attr('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
        .on('drag',  (e, d) => { d.fx = e.x; d.fy = e.y })
        .on('end',   (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null })
      )
      .on('mouseover', (e, d) => setTooltip({ x: e.offsetX, y: e.offsetY, node: d }))
      .on('mouseout', () => setTooltip(null))

    node.append('circle')
      .attr('r', d => d.type === 'class' ? 10 : 6)
      .attr('fill', d => TYPE_COLOR[d.type] || '#6366f1')
      .attr('fill-opacity', 0.85)
      .attr('stroke', d => TYPE_COLOR[d.type] || '#6366f1')
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.4)

    node.append('text')
      .text(d => d.label.length > 14 ? d.label.slice(0, 14) + '…' : d.label)
      .attr('x', 9).attr('y', 4)
      .attr('font-size', 10)
      .attr('fill', '#94a3b8')
      .attr('font-family', 'IBM Plex Mono, monospace')

    sim.on('tick', () => {
      link
        .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
      node.attr('transform', d => `translate(${d.x},${d.y})`)
    })
  }

  function zoomIn()  { d3.select(svgRef.current).transition().call(zoomRef.current.scaleBy, 1.4) }
  function zoomOut() { d3.select(svgRef.current).transition().call(zoomRef.current.scaleBy, 0.7) }

  return (
    <div className="h-full flex flex-col bg-surface-900 border-l border-white/5">
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-200">Dependency graph</p>
          {data && (
            <p className="text-xs text-slate-500">{data.total_nodes} nodes · {data.total_edges} edges</p>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button onClick={zoomIn}   className="btn-ghost p-1.5"><ZoomIn size={13} /></button>
          <button onClick={zoomOut}  className="btn-ghost p-1.5"><ZoomOut size={13} /></button>
          <button onClick={loadGraph} className="btn-ghost p-1.5"><RefreshCw size={13} /></button>
          <button onClick={toggleGraph} className="btn-ghost p-1.5"><X size={13} /></button>
        </div>
      </div>

      {/* Legend */}
      <div className="px-4 py-2 border-b border-white/5 flex gap-3">
        {Object.entries(TYPE_COLOR).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: color }} />
            <span className="text-xs text-slate-500">{type}</span>
          </div>
        ))}
      </div>

      {/* Graph canvas */}
      <div className="flex-1 relative overflow-hidden">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <Loader2 size={20} className="text-brand-400 animate-spin" />
          </div>
        )}
        <svg ref={svgRef} className="w-full h-full" />

        {/* Tooltip */}
        {tooltip && (
          <div
            className="absolute bg-surface-800 border border-white/10 rounded-lg px-3 py-2 pointer-events-none text-xs shadow-xl z-10"
            style={{ left: tooltip.x + 12, top: tooltip.y - 10 }}
          >
            <p className="font-mono text-slate-200">{tooltip.node.label}</p>
            <p className="text-slate-500">{tooltip.node.file}</p>
            <p className="text-slate-600">L{tooltip.node.line} · {tooltip.node.type}</p>
          </div>
        )}
      </div>
    </div>
  )
}

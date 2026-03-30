'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { useProjectStore } from '@/stores/projectStore';
import { useDisruptionStore } from '@/stores/disruptionStore';
import { GraphNode, GraphEdge } from '@/lib/types';
import { NODE_COLORS } from '@/lib/constants';
import NodeDetail from './NodeDetail';

const NODE_TYPE_FILTERS = ['project', 'equipment', 'supplier', 'route', 'zone'] as const;

export default function GraphViewer() {
  const svgRef = useRef<SVGSVGElement>(null);
  const { projects, equipment, suppliers, routes, zones } = useProjectStore();
  const { activeDisruptions } = useDisruptionStore();
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [filters, setFilters] = useState<Set<string>>(new Set(NODE_TYPE_FILTERS));

  const toggleFilter = (type: string) => {
    setFilters((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  const buildGraph = useCallback(() => {
    const nodes: GraphNode[] = [];
    const edges: GraphEdge[] = [];

    if (filters.has('project')) {
      projects.forEach((p) =>
        nodes.push({ id: p.id, label: p.name, type: 'project', data: p })
      );
    }
    if (filters.has('equipment')) {
      equipment.forEach((e) =>
        nodes.push({ id: e.id, label: e.name, type: 'equipment', data: e })
      );
    }
    if (filters.has('supplier')) {
      suppliers.forEach((s) =>
        nodes.push({ id: s.id, label: s.name, type: 'supplier', data: s })
      );
    }
    if (filters.has('route')) {
      routes.forEach((r) =>
        nodes.push({ id: r.id, label: r.name, type: 'route', data: r })
      );
    }
    if (filters.has('zone')) {
      zones.forEach((z) =>
        nodes.push({ id: z.id, label: z.name, type: 'zone', data: z })
      );
    }

    activeDisruptions.forEach((d) =>
      nodes.push({ id: d.id, label: d.name, type: 'disruption', data: d })
    );

    const nodeIds = new Set(nodes.map((n) => n.id));

    // Equipment -> Project edges
    equipment.forEach((e) => {
      if (nodeIds.has(e.id) && nodeIds.has(e.projectId))
        edges.push({ id: `${e.id}-${e.projectId}`, source: e.id, target: e.projectId, label: 'belongs_to', type: 'equipment-project' });
      if (nodeIds.has(e.id) && nodeIds.has(e.supplierId))
        edges.push({ id: `${e.id}-${e.supplierId}`, source: e.supplierId, target: e.id, label: 'supplies', type: 'supplier-equipment' });
      if (nodeIds.has(e.id) && nodeIds.has(e.routeId))
        edges.push({ id: `${e.id}-${e.routeId}`, source: e.id, target: e.routeId, label: 'shipped_via', type: 'equipment-route' });
    });

    // Disruption -> Zone/Route/Equipment edges
    activeDisruptions.forEach((d) => {
      d.affectedZoneIds.forEach((zid) => {
        if (nodeIds.has(zid))
          edges.push({ id: `${d.id}-${zid}`, source: d.id, target: zid, label: 'affects', type: 'disruption-zone' });
      });
      d.affectedRouteIds.forEach((rid) => {
        if (nodeIds.has(rid))
          edges.push({ id: `${d.id}-${rid}`, source: d.id, target: rid, label: 'disrupts', type: 'disruption-route' });
      });
    });

    return { nodes, edges };
  }, [projects, equipment, suppliers, routes, zones, activeDisruptions, filters]);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const container = svgRef.current.parentElement;
    if (!container) return;
    const width = container.clientWidth;
    const height = container.clientHeight;

    svg.attr('width', width).attr('height', height);

    const { nodes, edges } = buildGraph();
    if (nodes.length === 0) return;

    const g = svg.append('g');

    // Zoom
    const zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => g.attr('transform', event.transform));
    svg.call(zoomBehavior);

    // Simulation
    const simulation = d3.forceSimulation<GraphNode>(nodes)
      .force('link', d3.forceLink<GraphNode, GraphEdge>(edges).id((d) => d.id).distance(80).strength(0.3))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(30));

    // Edges
    const link = g.append('g')
      .selectAll('line')
      .data(edges)
      .enter()
      .append('line')
      .attr('stroke', '#1e3a5f')
      .attr('stroke-width', 1)
      .attr('stroke-opacity', 0.6);

    // Edge labels
    const linkLabel = g.append('g')
      .selectAll('text')
      .data(edges)
      .enter()
      .append('text')
      .text((d) => d.label)
      .attr('font-size', '7px')
      .attr('fill', '#4a5568')
      .attr('text-anchor', 'middle');

    // Nodes
    const node = g.append('g')
      .selectAll<SVGGElement, GraphNode>('g')
      .data(nodes)
      .enter()
      .append('g')
      .style('cursor', 'pointer')
      .call(
        d3.drag<SVGGElement, GraphNode>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    // Node circles
    node.append('circle')
      .attr('r', (d) => d.type === 'project' ? 14 : d.type === 'disruption' ? 12 : 10)
      .attr('fill', (d) => NODE_COLORS[d.type] || '#6b7280')
      .attr('stroke', '#0a0e1a')
      .attr('stroke-width', 2)
      .attr('opacity', 0.9);

    // Node labels
    node.append('text')
      .text((d) => d.label.length > 16 ? d.label.slice(0, 14) + '..' : d.label)
      .attr('font-size', '8px')
      .attr('fill', '#e2e8f0')
      .attr('text-anchor', 'middle')
      .attr('dy', 22);

    // Click handler
    node.on('click', (_event, d) => {
      setSelectedNode(d);
    });

    // Tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      linkLabel
        .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
        .attr('y', (d: any) => (d.source.y + d.target.y) / 2);

      node.attr('transform', (d) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [buildGraph]);

  return (
    <div className="flex flex-col h-full">
      {/* Filters */}
      <div className="flex flex-wrap gap-1.5 mb-2">
        {NODE_TYPE_FILTERS.map((type) => (
          <button
            key={type}
            onClick={() => toggleFilter(type)}
            className={`text-[9px] px-2 py-0.5 rounded-full border transition-colors ${
              filters.has(type)
                ? 'border-transparent text-white'
                : 'border-[#1e3a5f] text-slate-500 bg-transparent'
            }`}
            style={{
              background: filters.has(type) ? `${NODE_COLORS[type]}40` : undefined,
              borderColor: filters.has(type) ? `${NODE_COLORS[type]}60` : undefined,
            }}
          >
            {type}
          </button>
        ))}
      </div>

      {/* Graph */}
      <div className="flex-1 relative bg-[#080c16] rounded-md border border-[#1e3a5f]/30 overflow-hidden">
        <svg ref={svgRef} className="w-full h-full" />
        {selectedNode && (
          <div className="absolute top-0 right-0 w-48 h-full bg-[#0a0e1a]/95 border-l border-[#1e3a5f] overflow-y-auto">
            <NodeDetail node={selectedNode} onClose={() => setSelectedNode(null)} />
          </div>
        )}
      </div>
    </div>
  );
}

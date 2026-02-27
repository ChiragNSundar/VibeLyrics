import React, { useEffect, useState, useCallback, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { learningApi } from '../../services/api';
import './BrainMap.css';

interface GraphNode {
    id: string;
    val: number;
    category: string;
    frequency: number;
    x?: number;
    y?: number;
}

interface GraphLink {
    source: string;
    target: string;
    value: number;
}

interface GraphData {
    nodes: GraphNode[];
    links: GraphLink[];
}

const CATEGORY_COLORS: Record<string, string> = {
    signature: '#60a5fa',   // Blue
    slang: '#34d399',       // Emerald
    avoided: '#f87171',     // Red
    favorite: '#a78bfa',    // Purple
};

const BrainMap: React.FC = () => {
    const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
    const [loading, setLoading] = useState(true);
    const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [dimensions, setDimensions] = useState({ width: 600, height: 400 });

    useEffect(() => {
        const load = async () => {
            try {
                const res = await learningApi.getBrainMap();
                setGraphData({ nodes: res.nodes, links: res.links });
            } catch (err) {
                console.error('Failed to load brain map:', err);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    useEffect(() => {
        if (containerRef.current) {
            const rect = containerRef.current.getBoundingClientRect();
            setDimensions({ width: rect.width, height: 420 });
        }
    }, []);

    const nodeCanvasObject = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
        const label = node.id;
        const fontSize = Math.max(10, 12 / globalScale);
        const size = node.val || 4;
        const color = CATEGORY_COLORS[node.category] || '#60a5fa';

        // Glow effect
        ctx.shadowBlur = hoveredNode?.id === node.id ? 20 : 8;
        ctx.shadowColor = color;

        // Draw node circle
        ctx.beginPath();
        ctx.arc(node.x || 0, node.y || 0, size, 0, 2 * Math.PI);
        ctx.fillStyle = color;
        ctx.fill();

        // Reset shadow
        ctx.shadowBlur = 0;

        // Draw label
        ctx.font = `${fontSize}px 'Inter', sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
        ctx.fillText(label, node.x || 0, (node.y || 0) + size + fontSize);
    }, [hoveredNode]);

    if (loading) {
        return <div className="brain-map-loading">Mapping neural connections...</div>;
    }

    if (graphData.nodes.length === 0) {
        return <div className="brain-map-empty">No vocabulary data yet. Scrape an artist to build the brain map.</div>;
    }

    return (
        <div className="brain-map-container" ref={containerRef}>
            {hoveredNode && (
                <div className="brain-tooltip">
                    <strong>{hoveredNode.id}</strong>
                    <span>Frequency: {hoveredNode.frequency}</span>
                    <span className={`cat-badge ${hoveredNode.category}`}>{hoveredNode.category}</span>
                </div>
            )}
            <ForceGraph2D
                graphData={graphData as never}
                width={dimensions.width}
                height={dimensions.height}
                backgroundColor="rgba(0,0,0,0)"
                nodeCanvasObject={nodeCanvasObject as never}
                linkColor={() => 'rgba(148, 163, 184, 0.2)'}
                linkWidth={(link: GraphLink) => link.value || 1}
                onNodeHover={(node: GraphNode | null) => setHoveredNode(node || null)}
                cooldownTicks={100}
                d3AlphaDecay={0.02}
                d3VelocityDecay={0.3}
            />

            <div className="brain-legend">
                {Object.entries(CATEGORY_COLORS).map(([cat, color]) => (
                    <span key={cat} className="legend-item">
                        <span className="legend-dot" style={{ background: color }}></span>
                        {cat}
                    </span>
                ))}
            </div>
        </div>
    );
};

export default BrainMap;

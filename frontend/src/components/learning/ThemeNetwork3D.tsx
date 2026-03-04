import React, { useEffect, useRef, useState, useCallback } from 'react';
import { nlpApi } from '../../services/api';
import type { ThemeNode, ThemeLink } from '../../services/api';
import './ThemeNetwork3D.css';

interface ProjectedNode extends ThemeNode {
    sx: number;
    sy: number;
    scale: number;
}

const CLUSTER_COLORS = ['#60a5fa', '#34d399', '#f59e0b', '#f87171', '#a78bfa', '#ec4899'];

const ThemeNetwork3D: React.FC = () => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [nodes, setNodes] = useState<ThemeNode[]>([]);
    const [links, setLinks] = useState<ThemeLink[]>([]);
    const [loading, setLoading] = useState(true);
    const [hoveredNode, setHoveredNode] = useState<ThemeNode | null>(null);
    const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

    // Camera state
    const cameraRef = useRef({ rotX: 0.3, rotY: 0.5, zoom: 1.0 });
    const dragRef = useRef({ dragging: false, lastX: 0, lastY: 0 });
    const animRef = useRef<number>(0);

    useEffect(() => {
        const load = async () => {
            try {
                const res = await nlpApi.getThemeNetwork();
                setNodes(res.nodes || []);
                setLinks(res.links || []);
            } catch (err) {
                console.error('Failed to load theme network:', err);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    // 3D → 2D projection
    const project = useCallback((node: ThemeNode, width: number, height: number): ProjectedNode => {
        const { rotX, rotY, zoom } = cameraRef.current;
        let { x, y, z } = node;

        // Rotate Y
        const cosY = Math.cos(rotY);
        const sinY = Math.sin(rotY);
        const rx = x * cosY - z * sinY;
        const rz = x * sinY + z * cosY;

        // Rotate X
        const cosX = Math.cos(rotX);
        const sinX = Math.sin(rotX);
        const ry = y * cosX - rz * sinX;
        const rz2 = y * sinX + rz * cosX;

        // Perspective projection
        const d = 500;
        const perspective = d / (d + rz2 + 200);
        const sx = width / 2 + rx * perspective * zoom;
        const sy = height / 2 + ry * perspective * zoom;

        return { ...node, sx, sy, scale: perspective * zoom };
    }, []);

    // Render loop
    const render = useCallback(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const width = canvas.width;
        const height = canvas.height;

        ctx.clearRect(0, 0, width, height);

        // Project all nodes
        const projected = nodes.map(n => project(n, width, height));

        // Sort by depth (farthest first)
        projected.sort((a, b) => a.scale - b.scale);

        // Draw links
        ctx.globalAlpha = 0.3;
        for (const link of links) {
            const src = projected.find(n => n.id === link.source);
            const tgt = projected.find(n => n.id === link.target);
            if (!src || !tgt) continue;

            ctx.beginPath();
            ctx.moveTo(src.sx, src.sy);
            ctx.lineTo(tgt.sx, tgt.sy);
            ctx.strokeStyle = `rgba(148, 163, 184, ${0.1 + link.value * 0.15})`;
            ctx.lineWidth = Math.max(0.5, link.value * 0.5 * src.scale);
            ctx.stroke();
        }
        ctx.globalAlpha = 1;

        // Draw nodes
        for (const node of projected) {
            const r = Math.max(3, node.size * node.scale);
            const color = node.color || CLUSTER_COLORS[node.cluster % CLUSTER_COLORS.length];
            const isHovered = hoveredNode?.id === node.id;

            // Glow
            ctx.shadowBlur = isHovered ? 25 : 10;
            ctx.shadowColor = color;

            // Circle
            ctx.beginPath();
            ctx.arc(node.sx, node.sy, r, 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.globalAlpha = 0.4 + node.scale * 0.6;
            ctx.fill();

            // Inner bright core
            ctx.beginPath();
            ctx.arc(node.sx, node.sy, r * 0.5, 0, Math.PI * 2);
            ctx.fillStyle = '#fff';
            ctx.globalAlpha = 0.2 + node.scale * 0.3;
            ctx.fill();

            ctx.shadowBlur = 0;
            ctx.globalAlpha = 1;

            // Label
            if (node.scale > 0.5 || isHovered) {
                const fontSize = Math.max(9, 12 * node.scale);
                ctx.font = `${isHovered ? 'bold ' : ''}${fontSize}px 'Inter', sans-serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'top';
                ctx.fillStyle = `rgba(255, 255, 255, ${0.4 + node.scale * 0.5})`;
                ctx.fillText(node.label, node.sx, node.sy + r + 4);
            }
        }

        // Auto-rotate slowly
        cameraRef.current.rotY += 0.002;

        animRef.current = requestAnimationFrame(render);
    }, [nodes, links, hoveredNode, project]);

    // Start / stop animation
    useEffect(() => {
        if (nodes.length > 0) {
            animRef.current = requestAnimationFrame(render);
        }
        return () => {
            if (animRef.current) cancelAnimationFrame(animRef.current);
        };
    }, [nodes, links, render]);

    // Resize canvas
    useEffect(() => {
        const resize = () => {
            const canvas = canvasRef.current;
            const container = containerRef.current;
            if (!canvas || !container) return;
            const rect = container.getBoundingClientRect();
            canvas.width = rect.width;
            canvas.height = 420;
        };
        resize();
        window.addEventListener('resize', resize);
        return () => window.removeEventListener('resize', resize);
    }, []);

    // Mouse interactions
    const handleMouseDown = (e: React.MouseEvent) => {
        dragRef.current = { dragging: true, lastX: e.clientX, lastY: e.clientY };
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        if (dragRef.current.dragging) {
            const dx = e.clientX - dragRef.current.lastX;
            const dy = e.clientY - dragRef.current.lastY;
            cameraRef.current.rotY += dx * 0.005;
            cameraRef.current.rotX += dy * 0.005;
            dragRef.current.lastX = e.clientX;
            dragRef.current.lastY = e.clientY;
            return;
        }

        // Hover detection
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        let closest: ThemeNode | null = null;
        let closestDist = 30;

        for (const node of nodes) {
            const p = project(node, canvas.width, canvas.height);
            const dist = Math.sqrt((p.sx - mx) ** 2 + (p.sy - my) ** 2);
            if (dist < closestDist) {
                closestDist = dist;
                closest = node;
            }
        }

        setHoveredNode(closest);
        if (closest) {
            setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
        }
    };

    const handleMouseUp = () => {
        dragRef.current.dragging = false;
    };

    const handleWheel = (e: React.WheelEvent) => {
        e.preventDefault();
        cameraRef.current.zoom = Math.max(0.3, Math.min(3, cameraRef.current.zoom - e.deltaY * 0.001));
    };

    const resetCamera = () => {
        cameraRef.current = { rotX: 0.3, rotY: 0.5, zoom: 1.0 };
    };

    if (loading) {
        return <div className="theme-network-loading">Mapping theme connections...</div>;
    }

    if (nodes.length === 0) {
        return (
            <div className="theme-network-empty">
                No theme data yet. Write some lyrics across multiple sessions to see your recurring themes visualized here.
            </div>
        );
    }

    // Unique clusters
    const clusters = [...new Set(nodes.map(n => n.cluster))];

    return (
        <div className="theme-network-3d" ref={containerRef}>
            <div className="theme-network-controls">
                <button onClick={resetCamera} title="Reset view">⟳ Reset</button>
            </div>

            <canvas
                ref={canvasRef}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                onWheel={handleWheel}
            />

            {hoveredNode && (
                <div
                    className="theme-network-tooltip"
                    style={{ left: tooltipPos.x, top: tooltipPos.y }}
                >
                    <div className="tooltip-label" style={{ color: hoveredNode.color }}>
                        {hoveredNode.label}
                    </div>
                    <div className="tooltip-freq">Frequency: {hoveredNode.frequency}</div>
                    <div className="tooltip-sessions">
                        Across {hoveredNode.sessions_count} session{hoveredNode.sessions_count !== 1 ? 's' : ''}
                    </div>
                </div>
            )}

            <div className="theme-network-legend">
                {clusters.map(c => (
                    <span key={c} className="theme-legend-item">
                        <span
                            className="theme-legend-dot"
                            style={{ background: CLUSTER_COLORS[c % CLUSTER_COLORS.length] }}
                        />
                        Cluster {c + 1}
                    </span>
                ))}
            </div>
        </div>
    );
};

export default ThemeNetwork3D;

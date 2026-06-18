import React, { useRef, useEffect, useState } from 'react';
import './RhymeMap3D.css';

interface RhymeNode {
    text: string;
    x: number;
    y: number;
    z: number;
    baseSize: number;
    color: string;
    type: 'center' | 'perfect' | 'slant' | 'slang' | 'other';
    syllables: number;
    vowels: string;
}

interface RhymeMap3DProps {
    searchWord: string;
    results: Array<{
        word: string;
        syllable_count: number;
        vowel_sequence: string;
        is_slang?: boolean;
        upvotes: number;
    }>;
    onWordClick?: (word: string) => void;
}

export const RhymeMap3D: React.FC<RhymeMap3DProps> = ({
    searchWord,
    results,
    onWordClick,
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [hoveredNode, setHoveredNode] = useState<RhymeNode | null>(null);
    const [dimensions, setDimensions] = useState({ width: 300, height: 300 });

    // 3D parameters
    const rotationX = useRef(0.5);
    const rotationY = useRef(0.5);
    const zoom = useRef(1.0);
    const isDragging = useRef(false);
    const dragStart = useRef({ x: 0, y: 0 });
    const dragVelocity = useRef({ x: 0.005, y: 0.002 }); // Auto-rotation momentum

    // Re-generate nodes when results change
    const nodesRef = useRef<RhymeNode[]>([]);

    useEffect(() => {
        const nodes: RhymeNode[] = [];
        
        // 1. Center main search node
        nodes.push({
            text: searchWord || 'Word',
            x: 0,
            y: 0,
            z: 0,
            baseSize: 18,
            color: 'hsl(142, 85%, 55%)', // Bright green glow
            type: 'center',
            syllables: 0,
            vowels: '',
        });

        // 2. Child rhyming nodes clustered in 3D spheres
        results.forEach((item, index) => {
            // Distribute points on a sphere using Fibonacci lattice
            const phi = Math.acos(1 - 2 * (index + 0.5) / results.length);
            const theta = Math.PI * (1 + Math.sqrt(5)) * (index + 0.5);

            // Cluster radius depends on upvotes and type (closer for perfect, further for slant)
            const isSlang = !!item.is_slang;
            const isPerfect = item.upvotes > 2; // Let's guess perfect based on upvotes or slant mode
            
            let radius = 100 + Math.random() * 20;
            let type: 'perfect' | 'slant' | 'slang' | 'other' = 'other';
            let color = 'hsl(210, 80%, 55%)'; // Cyan/Blue fallback

            if (isSlang) {
                type = 'slang';
                color = 'hsl(40, 95%, 55%)'; // Gold/Yellow
                radius = 130 + Math.random() * 15;
            } else if (isPerfect) {
                type = 'perfect';
                color = 'hsl(190, 95%, 50%)'; // Electric Cyan
                radius = 75 + Math.random() * 15;
            } else {
                type = 'slant';
                color = 'hsl(275, 90%, 65%)'; // Vibrant Purple
                radius = 110 + Math.random() * 20;
            }

            nodes.push({
                text: item.word,
                x: radius * Math.sin(phi) * Math.cos(theta),
                y: radius * Math.sin(phi) * Math.sin(theta),
                z: radius * Math.cos(phi),
                baseSize: Math.max(8, 8 + Math.min(item.upvotes, 8)),
                color,
                type,
                syllables: item.syllable_count,
                vowels: item.vowel_sequence,
            });
        });

        nodesRef.current = nodes;
    }, [searchWord, results]);

    // Handle container resizing
    useEffect(() => {
        if (!containerRef.current) return;

        const updateDimensions = () => {
            if (containerRef.current) {
                setDimensions({
                    width: containerRef.current.clientWidth,
                    height: containerRef.current.clientHeight || 350,
                });
            }
        };

        const resizeObserver = new ResizeObserver(() => {
            updateDimensions();
        });

        resizeObserver.observe(containerRef.current);
        updateDimensions();

        return () => {
            resizeObserver.disconnect();
        };
    }, []);

    // Main animation loop
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let animationFrameId: number;

        const render = () => {
            ctx.clearRect(0, 0, dimensions.width, dimensions.height);

            const centerX = dimensions.width / 2;
            const centerY = dimensions.height / 2;
            const focalLength = 300 * zoom.current;

            // Slow idle rotation when not dragging
            if (!isDragging.current) {
                rotationY.current += dragVelocity.current.y;
                rotationX.current += dragVelocity.current.x;
                // Friction
                dragVelocity.current.x *= 0.98;
                dragVelocity.current.y *= 0.98;
                // Minimum idle velocity
                if (Math.abs(dragVelocity.current.x) < 0.002) dragVelocity.current.x = 0.002;
                if (Math.abs(dragVelocity.current.y) < 0.001) dragVelocity.current.y = 0.001;
            }

            const sinX = Math.sin(rotationX.current);
            const cosX = Math.cos(rotationX.current);
            const sinY = Math.sin(rotationY.current);
            const cosY = Math.cos(rotationY.current);

            // Project 3D coordinates
            const projected = nodesRef.current.map((node) => {
                // Rotate around Y axis
                let x1 = node.x * cosY - node.z * sinY;
                let z1 = node.x * sinY + node.z * cosY;

                // Rotate around X axis
                let y2 = node.y * cosX - z1 * sinX;
                let z2 = node.y * sinX + z1 * cosX;

                // Perspective projection scale
                const scale = focalLength / (focalLength + z2);
                const projX = centerX + x1 * scale;
                const projY = centerY + y2 * scale;
                const radius = Math.max(2, node.baseSize * scale);

                return {
                    node,
                    projX,
                    projY,
                    radius,
                    depth: z2,
                    scale,
                };
            });

            // Sort by depth (back to front) for painters algorithm
            projected.sort((a, b) => b.depth - a.depth);

            // Draw connection lines
            ctx.lineWidth = 0.8;
            projected.forEach((item) => {
                if (item.node.type === 'center') return;
                
                // Find projected center node
                const centerNode = projected.find((p) => p.node.type === 'center');
                if (centerNode) {
                    const alpha = Math.max(0.1, Math.min(0.4, item.scale));
                    ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
                    ctx.beginPath();
                    ctx.moveTo(centerNode.projX, centerNode.projY);
                    ctx.lineTo(item.projX, item.projY);
                    ctx.stroke();
                }
            });

            // Draw nodes and text
            projected.forEach((item) => {
                const { node, projX, projY, radius, scale } = item;
                const opacity = Math.max(0.2, Math.min(1.0, scale));

                // Glow radial gradient
                ctx.beginPath();
                const grad = ctx.createRadialGradient(projX, projY, 0, projX, projY, radius * 1.5);
                grad.addColorStop(0, node.color);
                grad.addColorStop(0.3, node.color.replace('55%', '50%').replace('50%', '45%'));
                grad.addColorStop(1, 'transparent');
                
                ctx.fillStyle = grad;
                ctx.arc(projX, projY, radius * 1.5, 0, Math.PI * 2);
                ctx.fill();

                // Draw central solid core
                ctx.beginPath();
                ctx.fillStyle = node.color;
                ctx.arc(projX, projY, radius * 0.5, 0, Math.PI * 2);
                ctx.fill();

                // Text labels (only if close enough or center node)
                const isHovered = hoveredNode && hoveredNode.text === node.text;
                if (scale > 0.65 || node.type === 'center' || isHovered) {
                    ctx.fillStyle = isHovered 
                        ? 'rgba(255, 255, 255, 0.95)' 
                        : `rgba(255, 255, 255, ${Math.min(0.85, opacity)})`;
                    
                    ctx.font = node.type === 'center'
                        ? 'bold 12px Outfit, Inter, sans-serif'
                        : isHovered
                        ? 'bold 11px Outfit, Inter, sans-serif'
                        : '10px Outfit, Inter, sans-serif';
                    
                    ctx.textAlign = 'center';
                    ctx.shadowColor = node.color;
                    ctx.shadowBlur = isHovered ? 8 : 2;
                    ctx.fillText(node.text, projX, projY + radius + 11);
                    ctx.shadowBlur = 0; // reset
                }
            });

            animationFrameId = requestAnimationFrame(render);
        };

        render();

        return () => {
            cancelAnimationFrame(animationFrameId);
        };
    }, [dimensions, hoveredNode]);

    // Handle mouse interactions
    const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
        isDragging.current = true;
        dragStart.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        if (isDragging.current) {
            const deltaX = e.clientX - dragStart.current.x;
            const deltaY = e.clientY - dragStart.current.y;
            
            // Adjust velocities
            dragVelocity.current.y = deltaX * 0.005;
            dragVelocity.current.x = deltaY * 0.005;

            rotationY.current += dragVelocity.current.y;
            rotationX.current += dragVelocity.current.x;

            dragStart.current = { x: e.clientX, y: e.clientY };
        } else {
            // Hover detection
            const centerX = dimensions.width / 2;
            const centerY = dimensions.height / 2;
            const focalLength = 300 * zoom.current;

            const sinX = Math.sin(rotationX.current);
            const cosX = Math.cos(rotationX.current);
            const sinY = Math.sin(rotationY.current);
            const cosY = Math.cos(rotationY.current);

            let foundNode: RhymeNode | null = null;
            let closestDistance = 15; // hover sensitivity

            nodesRef.current.forEach((node) => {
                // Project node
                let x1 = node.x * cosY - node.z * sinY;
                let z1 = node.x * sinY + node.z * cosY;
                let y2 = node.y * cosX - z1 * sinX;
                let z2 = node.y * sinX + z1 * cosX;

                const scale = focalLength / (focalLength + z2);
                const projX = centerX + x1 * scale;
                const projY = centerY + y2 * scale;

                const dist = Math.hypot(mouseX - projX, mouseY - projY);
                if (dist < closestDistance) {
                    closestDistance = dist;
                    foundNode = node;
                }
            });

            setHoveredNode(foundNode);
        }
    };

    const handleMouseUp = () => {
        isDragging.current = false;
    };

    const handleMouseWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
        e.preventDefault();
        zoom.current = Math.max(0.5, Math.min(2.5, zoom.current - e.deltaY * 0.001));
    };

    const handleCanvasClick = () => {
        if (hoveredNode && hoveredNode.type !== 'center' && onWordClick) {
            onWordClick(hoveredNode.text);
        }
    };

    return (
        <div ref={containerRef} className="rhyme-map-3d-wrapper">
            <canvas
                ref={canvasRef}
                width={dimensions.width}
                height={dimensions.height}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                onWheel={handleMouseWheel}
                onClick={handleCanvasClick}
                className="rhyme-map-canvas"
            />
            {hoveredNode && hoveredNode.type !== 'center' && (
                <div className="rhyme-map-tooltip glass-card border border-white/10">
                    <div className="tooltip-word">{hoveredNode.text}</div>
                    <div className="tooltip-details">
                        <span>{hoveredNode.syllables} Syl</span>
                        <span className="dot">•</span>
                        <span>Vowels: {hoveredNode.vowels}</span>
                        <span className="dot">•</span>
                        <span className="capitalize">{hoveredNode.type}</span>
                    </div>
                </div>
            )}
            <div className="rhyme-map-instructions">
                Drag to rotate • Scroll to zoom • Click a node to insert
            </div>
        </div>
    );
};

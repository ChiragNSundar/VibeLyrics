import React, { useRef, useEffect, useCallback } from 'react';
import './AudioVisualizer.css';

interface AudioVisualizerProps {
    audioContext: AudioContext | null;
    analyser: AnalyserNode | null;
    isPlaying: boolean;
    mode?: 'bars' | 'wave' | 'particles';
}

/**
 * Audio-reactive visualizer component
 * Displays frequency bars that react to the beat playback
 */
export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
    audioContext,
    analyser,
    isPlaying,
    mode = 'bars',
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<number | null>(null);
    const dataArrayRef = useRef<Uint8Array | null>(null);

    // Initialize data array when analyser is available
    useEffect(() => {
        if (analyser) {
            const bufferLength = analyser.frequencyBinCount;
            dataArrayRef.current = new Uint8Array(bufferLength);
        }
    }, [analyser]);

    // Draw visualization frame
    const draw = useCallback(() => {
        if (!canvasRef.current || !analyser || !dataArrayRef.current) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const width = canvas.width;
        const height = canvas.height;

        // Get frequency data
        analyser.getByteFrequencyData(dataArrayRef.current);
        const dataArray = dataArrayRef.current;

        // Clear canvas with fade effect for trail
        ctx.fillStyle = 'rgba(5, 5, 10, 0.3)';
        ctx.fillRect(0, 0, width, height);

        if (mode === 'bars') {
            drawBars(ctx, dataArray, width, height);
        } else if (mode === 'wave') {
            drawWave(ctx, dataArray, width, height);
        }

        animationRef.current = requestAnimationFrame(draw);
    }, [analyser, mode]);

    // Draw frequency bars
    const drawBars = (ctx: CanvasRenderingContext2D, dataArray: Uint8Array, width: number, height: number) => {
        const barCount = 64;
        const barWidth = width / barCount;
        const gap = 2;

        for (let i = 0; i < barCount; i++) {
            const dataIndex = Math.floor(i * dataArray.length / barCount);
            const value = dataArray[dataIndex];
            const percent = value / 255;
            const barHeight = percent * height * 0.8;

            // Gradient from purple to cyan (Dreamy colors)
            const hue = 260 + (i / barCount) * 60; // 260 (purple) to 320 (magenta)
            const saturation = 70 + percent * 30;
            const lightness = 40 + percent * 30;

            ctx.fillStyle = `hsl(${hue}, ${saturation}%, ${lightness}%)`;

            // Draw bar with rounded top
            const x = i * barWidth + gap / 2;
            const y = height - barHeight;
            ctx.beginPath();
            ctx.roundRect(x, y, barWidth - gap, barHeight, [4, 4, 0, 0]);
            ctx.fill();

            // Add glow effect for high values
            if (percent > 0.6) {
                ctx.shadowColor = `hsl(${hue}, 100%, 60%)`;
                ctx.shadowBlur = 10;
                ctx.fill();
                ctx.shadowBlur = 0;
            }
        }
    };

    // Draw waveform
    const drawWave = (ctx: CanvasRenderingContext2D, dataArray: Uint8Array, width: number, height: number) => {
        ctx.lineWidth = 2;
        ctx.strokeStyle = 'rgba(139, 92, 246, 0.8)';
        ctx.beginPath();

        const sliceWidth = width / dataArray.length;
        let x = 0;

        for (let i = 0; i < dataArray.length; i++) {
            const v = dataArray[i] / 255;
            const y = (v * height) / 2 + height / 4;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }

            x += sliceWidth;
        }

        ctx.lineTo(width, height / 2);
        ctx.stroke();

        // Add gradient fill below the wave
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, 'rgba(139, 92, 246, 0.3)');
        gradient.addColorStop(1, 'rgba(6, 182, 212, 0.1)');
        ctx.fillStyle = gradient;
        ctx.lineTo(width, height);
        ctx.lineTo(0, height);
        ctx.fill();
    };

    // Start/stop animation based on isPlaying
    useEffect(() => {
        if (isPlaying && audioContext && analyser) {
            draw();
        } else if (animationRef.current) {
            cancelAnimationFrame(animationRef.current);
        }

        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, [isPlaying, audioContext, analyser, draw]);

    // Handle resize
    useEffect(() => {
        const handleResize = () => {
            if (canvasRef.current) {
                canvasRef.current.width = canvasRef.current.offsetWidth;
                canvasRef.current.height = canvasRef.current.offsetHeight;
            }
        };

        handleResize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return (
        <div className="audio-visualizer">
            <canvas ref={canvasRef} className="visualizer-canvas" />
            {!isPlaying && (
                <div className="visualizer-placeholder">
                    <span className="visualizer-icon">🎵</span>
                    <span className="visualizer-text">Play a beat to see the visualizer</span>
                </div>
            )}
        </div>
    );
};

import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, Square, Metronome } from 'lucide-react';
import './BeatTimer.css';

interface BeatTimerProps {
    bpm: number;
}

export const BeatTimer: React.FC<BeatTimerProps> = ({ bpm }) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentBeat, setCurrentBeat] = useState(0); // 0 to 3 for 4/4 time
    const [currentBar, setCurrentBar] = useState(1);
    const [progress, setProgress] = useState(0); // 0 to 100

    const requestRef = useRef<number>();
    const startTimeRef = useRef<number>(0);
    const audioContextRef = useRef<AudioContext | null>(null);

    // Initialize Audio Context for click track
    useEffect(() => {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
        return () => {
            if (audioContextRef.current?.state !== 'closed') {
                audioContextRef.current?.close();
            }
        };
    }, []);

    const playClick = (isFirstBeat: boolean) => {
        if (!audioContextRef.current) return;

        // Resume context if suspended (browser auto-play policy)
        if (audioContextRef.current.state === 'suspended') {
            audioContextRef.current.resume();
        }

        const osc = audioContextRef.current.createOscillator();
        const gainNode = audioContextRef.current.createGain();

        osc.connect(gainNode);
        gainNode.connect(audioContextRef.current.destination);

        osc.type = 'sine';
        // Higher pitch for first beat of the bar
        osc.frequency.setValueAtTime(isFirstBeat ? 880 : 440, audioContextRef.current.currentTime);

        // Short, sharp decay
        gainNode.gain.setValueAtTime(1, audioContextRef.current.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioContextRef.current.currentTime + 0.1);

        osc.start(audioContextRef.current.currentTime);
        osc.stop(audioContextRef.current.currentTime + 0.1);
    };

    const animate = (time: number) => {
        if (!startTimeRef.current) startTimeRef.current = time;

        const msPerBeat = (60 / Math.max(bpm, 1)) * 1000;
        const msPerBar = msPerBeat * 4;

        const elapsedTime = time - startTimeRef.current;
        const totalBeatsElapsed = Math.floor(elapsedTime / msPerBeat);

        const beatInBar = totalBeatsElapsed % 4;
        const currentBarNum = Math.floor(totalBeatsElapsed / 4) + 1;

        // Calculate smooth progress through the current beat (0 to 100%)
        const timeInCurrentBeat = elapsedTime % msPerBeat;
        const beatProgress = (timeInCurrentBeat / msPerBeat) * 100;

        // Calculate smooth progress through the current bar (0 to 100%)
        const timeInCurrentBar = elapsedTime % msPerBar;
        const barProgress = (timeInCurrentBar / msPerBar) * 100;

        setCurrentBeat(oldBeat => {
            if (oldBeat !== beatInBar && isPlaying) {
                // We hit a new beat
                playClick(beatInBar === 0);
            }
            return beatInBar;
        });

        setCurrentBar(currentBarNum);
        setProgress(barProgress);

        requestRef.current = requestAnimationFrame(animate);
    };

    useEffect(() => {
        if (isPlaying) {
            startTimeRef.current = performance.now();
            requestRef.current = requestAnimationFrame(animate);
        } else {
            if (requestRef.current) {
                cancelAnimationFrame(requestRef.current);
            }
            // Reset visually when stopped
            setProgress(0);
            setCurrentBeat(0);
            setCurrentBar(1);
        }

        return () => {
            if (requestRef.current) {
                cancelAnimationFrame(requestRef.current);
            }
        };
    }, [isPlaying, bpm]);

    const togglePlay = () => {
        setIsPlaying(!isPlaying);
    };

    const stop = () => {
        setIsPlaying(false);
        setProgress(0);
        setCurrentBeat(0);
        setCurrentBar(1);
    };

    return (
        <div className="beat-timer-container">
            <div className="beat-controls">
                <button
                    className={`btn-icon ${isPlaying ? 'active' : ''}`}
                    onClick={togglePlay}
                    title={isPlaying ? "Pause" : "Play Metronome"}
                >
                    {isPlaying ? <Pause size={16} /> : <Play size={16} />}
                </button>
                <button
                    className="btn-icon"
                    onClick={stop}
                    title="Stop & Reset"
                    disabled={!isPlaying && currentBar === 1 && currentBeat === 0}
                >
                    <Square size={16} />
                </button>
                <div className="bpm-display">
                    <Metronome size={14} /> {bpm} BPM
                </div>
            </div>

            <div className="beat-visualizer">
                <div className="bar-info">
                    Bar <span className="highlight-text">{currentBar}</span>
                </div>

                <div className="track-container">
                    <div className="progress-bar" style={{ width: `${progress}%` }}></div>

                    {/* 4 Beat markers */}
                    <div className={`beat-marker ${currentBeat === 0 ? 'active first' : ''}`} style={{ left: '0%' }}></div>
                    <div className={`beat-marker ${currentBeat === 1 ? 'active' : ''}`} style={{ left: '25%' }}></div>
                    <div className={`beat-marker ${currentBeat === 2 ? 'active' : ''}`} style={{ left: '50%' }}></div>
                    <div className={`beat-marker ${currentBeat === 3 ? 'active' : ''}`} style={{ left: '75%' }}></div>
                </div>

                <div className="beat-info">
                    Beat <span className="highlight-text">{currentBeat + 1}</span> / 4
                </div>
            </div>
        </div>
    );
};

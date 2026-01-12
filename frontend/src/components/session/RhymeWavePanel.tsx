import React from 'react';
import { Button } from '../ui/Button';
import './RhymeWavePanel.css';

interface RhymeWavePanelProps {
    onClose: () => void;
}

export const RhymeWavePanel: React.FC<RhymeWavePanelProps> = ({ onClose }) => {
    return (
        <div className="rhymewave-panel">
            <div className="panel-header">
                <h3>🌊 RhymeWave</h3>
                <Button variant="icon" onClick={onClose}>
                    ✕
                </Button>
            </div>
            <div className="panel-content">
                <iframe
                    src="https://rhymewave.com"
                    title="RhymeWave"
                    className="rhymewave-iframe"
                />
            </div>
        </div>
    );
};

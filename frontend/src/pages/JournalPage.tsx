import React from 'react';
import { Card } from '../components/ui/Card';
import './JournalPage.css';

export const JournalPage: React.FC = () => {
    return (
        <div className="journal-page">
            <div className="page-header">
                <h1>📓 Journal</h1>
                <p className="subtitle">Write freely, capture ideas, process emotions</p>
            </div>

            <Card className="journal-card" glass>
                <textarea
                    className="journal-textarea"
                    placeholder="Start writing... This is your private space to brainstorm, vent, or draft ideas before turning them into lyrics."
                />
            </Card>

            <div className="journal-tips">
                <h3>💡 Journal Tips</h3>
                <ul>
                    <li>Free-write without judgment</li>
                    <li>Capture conversations and observations</li>
                    <li>Note rhyme schemes you want to try</li>
                    <li>Process emotions that might become songs</li>
                </ul>
            </div>
        </div>
    );
};

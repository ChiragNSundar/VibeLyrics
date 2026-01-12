import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navbar.css';

export const Navbar: React.FC = () => {
    const location = useLocation();

    const isActive = (path: string) => location.pathname === path;

    return (
        <nav className="navbar glass">
            <Link to="/" className="nav-brand">
                <span className="logo">🎤</span>
                <span className="brand-name gradient-text">VibeLyrics</span>
            </Link>

            <div className="nav-links">
                <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>
                    <span>📝</span>
                    <span>Workspace</span>
                </Link>
                <Link to="/learning" className={`nav-link ${isActive('/learning') ? 'active' : ''}`}>
                    <span>🧠</span>
                    <span>Learning</span>
                </Link>
                <Link to="/journal" className={`nav-link ${isActive('/journal') ? 'active' : ''}`}>
                    <span>📓</span>
                    <span>Journal</span>
                </Link>
                <Link to="/stats" className={`nav-link ${isActive('/stats') ? 'active' : ''}`}>
                    <span>📊</span>
                    <span>Stats</span>
                </Link>
                <Link to="/settings" className={`nav-link ${isActive('/settings') ? 'active' : ''}`}>
                    <span>⚙️</span>
                    <span>Settings</span>
                </Link>
            </div>
        </nav>
    );
};

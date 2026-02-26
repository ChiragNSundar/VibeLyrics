import React, { useRef, useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navbar.css';

const navLinks = [
    { to: '/', icon: '📝', label: 'Workspace' },
    { to: '/learning', icon: '🧠', label: 'Learning' },
    { to: '/ai-brain', icon: '🤖', label: 'AI Brain' },
    { to: '/journal', icon: '📓', label: 'Journal' },
    { to: '/stats', icon: '📊', label: 'Stats' },
    { to: '/settings', icon: '⚙️', label: 'Settings' },
];

export const Navbar: React.FC = () => {
    const location = useLocation();
    const navRef = useRef<HTMLDivElement>(null);
    const [sliderStyle, setSliderStyle] = useState({ left: 0, width: 0 });

    const activeIndex = navLinks.findIndex(link => link.to === location.pathname);

    useEffect(() => {
        if (navRef.current) {
            const links = navRef.current.querySelectorAll('.nav-link');
            if (links[activeIndex]) {
                const activeLink = links[activeIndex] as HTMLElement;
                setSliderStyle({
                    left: activeLink.offsetLeft,
                    width: activeLink.offsetWidth,
                });
            }
        }
    }, [activeIndex, location.pathname]);

    return (
        <nav className="navbar glass">
            <Link to="/" className="nav-brand">
                <span className="logo">🎤</span>
                <span className="brand-name gradient-text">VibeLyrics</span>
            </Link>

            <div className="nav-links" ref={navRef}>
                {/* Sliding indicator */}
                <div
                    className="nav-slider"
                    style={{
                        left: sliderStyle.left,
                        width: sliderStyle.width,
                    }}
                />

                {navLinks.map((link) => (
                    <Link
                        key={link.to}
                        to={link.to}
                        className={`nav-link ${location.pathname === link.to ? 'active' : ''}`}
                    >
                        <span>{link.icon}</span>
                        <span>{link.label}</span>
                    </Link>
                ))}
            </div>
        </nav>
    );
};

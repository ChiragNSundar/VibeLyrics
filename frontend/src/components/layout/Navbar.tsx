import React, { useRef, useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { toast } from 'react-hot-toast';
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

    // Connectivity state
    const [isOnline, setIsOnline] = useState(navigator.onLine);

    // PWA install states
    const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
    const [showInstallBtn, setShowInstallBtn] = useState(false);

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

    // Handle online/offline updates
    useEffect(() => {
        const handleOnline = () => {
            setIsOnline(true);
            toast.success("✅ Back online! Syncing updates...", {
                style: {
                    background: '#0d0d14',
                    color: '#f5f5f7',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                }
            });
        };

        const handleOffline = () => {
            setIsOnline(false);
            toast.error("⚠️ Connection lost. Running in offline mode.", {
                style: {
                    background: '#0d0d14',
                    color: '#f5f5f7',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                }
            });
        };

        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);

    // Handle PWA installation prompt detection
    useEffect(() => {
        const handleBeforeInstallPrompt = (e: Event) => {
            e.preventDefault();
            setDeferredPrompt(e);
            setShowInstallBtn(true);
        };

        window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt as any);

        // Hide install option if already running as installed app
        if (window.matchMedia('(display-mode: standalone)').matches) {
            setShowInstallBtn(false);
        }

        return () => {
            window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt as any);
        };
    }, []);

    const handleInstallClick = async () => {
        if (!deferredPrompt) return;
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        console.log(`PWA install outcome: ${outcome}`);
        setDeferredPrompt(null);
        setShowInstallBtn(false);
    };

    return (
        <nav className="navbar glass">
            <div className="nav-left">
                <Link to="/" className="nav-brand">
                    <span className="logo">🎤</span>
                    <span className="brand-name gradient-text">VibeLyrics</span>
                </Link>

                {/* Connectivity Badge */}
                <div className={`status-pill ${isOnline ? 'online' : 'offline'}`}>
                    <span className="pulse-dot"></span>
                    <span className="status-text">{isOnline ? 'Online' : 'Offline'}</span>
                </div>
            </div>

            <div className="nav-right">
                {/* PWA Install Action */}
                {showInstallBtn && (
                    <button onClick={handleInstallClick} className="btn-install glass-light glow">
                        <span className="install-icon">📥</span>
                        <span className="install-text">Install App</span>
                    </button>
                )}

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
            </div>
        </nav>
    );
};

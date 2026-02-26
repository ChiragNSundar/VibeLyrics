import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import './NotFoundPage.css';

export const NotFoundPage: React.FC = () => {
    return (
        <motion.div
            className="not-found-page"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
        >
            <div className="not-found-content">
                <span className="not-found-emoji">🎤</span>
                <h1 className="not-found-title">404</h1>
                <p className="not-found-subtitle">This verse doesn't exist yet</p>
                <p className="not-found-hint">The page you're looking for has gone off-beat.</p>
                <Link to="/" className="not-found-link">
                    Back to the Studio →
                </Link>
            </div>
        </motion.div>
    );
};

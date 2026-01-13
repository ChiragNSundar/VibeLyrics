import React from 'react';
import './Skeleton.css';

interface SkeletonProps {
    variant?: 'text' | 'card' | 'button' | 'avatar' | 'line';
    width?: string | number;
    height?: string | number;
    className?: string;
    count?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
    variant = 'text',
    width,
    height,
    className = '',
    count = 1,
}) => {
    const baseClass = `skeleton skeleton-${variant}`;

    const style: React.CSSProperties = {
        width: width,
        height: height,
    };

    if (count > 1) {
        return (
            <div className="skeleton-group">
                {Array.from({ length: count }).map((_, i) => (
                    <div key={i} className={`${baseClass} ${className}`} style={style} />
                ))}
            </div>
        );
    }

    return <div className={`${baseClass} ${className}`} style={style} />;
};

// Convenience components
export const SkeletonCard: React.FC<{ className?: string }> = ({ className }) => (
    <div className={`skeleton-card-wrapper ${className || ''}`}>
        <div className="skeleton-card-header">
            <Skeleton variant="text" width="60%" height="1.2rem" />
            <Skeleton variant="button" width="32px" height="32px" />
        </div>
        <div className="skeleton-card-meta">
            <Skeleton variant="button" width="60px" height="20px" />
            <Skeleton variant="button" width="80px" height="20px" />
        </div>
        <div className="skeleton-card-footer">
            <Skeleton variant="text" width="40%" height="0.8rem" />
            <Skeleton variant="text" width="30%" height="0.8rem" />
        </div>
    </div>
);

export const SkeletonLine: React.FC<{ lines?: number }> = ({ lines = 3 }) => (
    <div className="skeleton-lines">
        {Array.from({ length: lines }).map((_, i) => (
            <Skeleton
                key={i}
                variant="text"
                width={`${Math.random() * 30 + 60}%`}
                height="1rem"
            />
        ))}
    </div>
);

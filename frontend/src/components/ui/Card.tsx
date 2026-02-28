import React from 'react';
import './Card.css';

interface CardProps {
    children: React.ReactNode;
    className?: string;
    glass?: boolean;
    hover?: boolean;
    glow?: boolean;
    onClick?: () => void;
    style?: React.CSSProperties;
}

export const Card: React.FC<CardProps> = ({
    children,
    className = '',
    glass = false,
    hover = false,
    glow = false,
    onClick,
    style,
}) => {
    const classes = [
        'card',
        glass && 'card-glass',
        hover && 'card-hover',
        glow && 'card-glow',
        onClick && 'card-clickable',
        className,
    ]
        .filter(Boolean)
        .join(' ');

    return (
        <div className={classes} onClick={onClick} style={style}>
            {children}
        </div>
    );
};

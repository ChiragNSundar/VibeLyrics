import React, { useRef } from 'react';
import '../../styles/components/Button.css';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'icon';
    size?: 'sm' | 'md' | 'lg';
    isLoading?: boolean;
    children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
    variant = 'primary',
    size = 'md',
    isLoading = false,
    children,
    className = '',
    disabled,
    onClick,
    ...props
}) => {
    const buttonRef = useRef<HTMLButtonElement>(null);

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
        // Create ripple effect
        const button = buttonRef.current;
        if (button && variant !== 'icon') {
            const rect = button.getBoundingClientRect();
            const ripple = document.createElement('span');
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.className = 'btn-ripple';
            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;

            button.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        }

        // Call original onClick
        if (onClick) {
            onClick(e);
        }
    };

    const classes = [
        'btn',
        `btn-${variant}`,
        `btn-${size}`,
        className,
    ].filter(Boolean).join(' ');

    return (
        <button
            ref={buttonRef}
            className={classes}
            disabled={disabled || isLoading}
            onClick={handleClick}
            {...props}
        >
            {isLoading ? (
                <span className="btn-spinner" />
            ) : (
                children
            )}
        </button>
    );
};

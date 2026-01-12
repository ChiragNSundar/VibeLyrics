import React from 'react';
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
    ...props
}) => {
    const variantClass = variant === 'icon' ? 'btn-icon' : `btn-${variant}`;
    const sizeClass = size !== 'md' ? `btn-${size}` : '';

    return (
        <button
            className={`btn ${variantClass} ${sizeClass} ${className}`.trim()}
            disabled={disabled || isLoading}
            {...props}
        >
            {isLoading ? <span className="spinner" /> : children}
        </button>
    );
};

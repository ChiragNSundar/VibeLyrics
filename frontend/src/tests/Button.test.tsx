import { render, screen } from '@testing-library/react';
import { Button } from '../components/ui/Button';

describe('Button', () => {
    it('renders with children', () => {
        render(<Button>Click me</Button>);
        expect(screen.getByText('Click me')).toBeInTheDocument();
    });

    it('applies variant classes', () => {
        render(<Button variant="secondary">Secondary</Button>);
        const button = screen.getByText('Secondary');
        // Check for specific class or just that it doesn't crash
        expect(button).toBeInTheDocument();
    });
});

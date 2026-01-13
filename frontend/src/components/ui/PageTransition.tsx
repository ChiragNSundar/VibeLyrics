import type { ReactNode } from 'react';
import { motion, type Transition } from 'framer-motion';

interface PageTransitionProps {
    children: ReactNode;
}

const pageVariants = {
    initial: {
        opacity: 0,
        y: 20,
    },
    animate: {
        opacity: 1,
        y: 0,
    },
    exit: {
        opacity: 0,
        y: -20,
    },
};

const pageTransition: Transition = {
    type: 'tween',
    ease: [0.16, 1, 0.3, 1],
    duration: 0.4,
};

export const PageTransition = ({ children }: PageTransitionProps) => {
    return (
        <motion.div
            initial="initial"
            animate="animate"
            exit="exit"
            variants={pageVariants}
            transition={pageTransition}
        >
            {children}
        </motion.div>
    );
};

// Staggered children animation
export const staggerContainer = {
    initial: {},
    animate: {
        transition: {
            staggerChildren: 0.08,
            delayChildren: 0.1,
        },
    },
};

export const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 0.4,
            ease: [0.16, 1, 0.3, 1],
        },
    },
};

export const scaleIn = {
    initial: { opacity: 0, scale: 0.95 },
    animate: {
        opacity: 1,
        scale: 1,
        transition: {
            duration: 0.3,
            ease: [0.16, 1, 0.3, 1],
        },
    },
};

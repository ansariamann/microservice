import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface AnimatedButtonProps extends HTMLMotionProps<"button"> {
    variant?: 'primary' | 'secondary' | 'accent' | 'outline' | 'ghost';
    size?: 'sm' | 'md' | 'lg';
    isLoading?: boolean;
}

const AnimatedButton = React.forwardRef<HTMLButtonElement, AnimatedButtonProps>(
    ({ className, variant = 'primary', size = 'md', isLoading, children, ...props }, ref) => {

        const variants = {
            primary: "bg-primary text-white shadow-lg hover:shadow-primary/50",
            secondary: "bg-secondary text-white shadow-lg hover:shadow-secondary/50",
            accent: "bg-accent text-white shadow-lg hover:shadow-accent/50",
            outline: "bg-transparent border border-white/20 text-white hover:bg-white/10",
            ghost: "bg-transparent text-gray-300 hover:text-white hover:bg-white/5",
        };

        const sizes = {
            sm: "px-3 py-1.5 text-sm",
            md: "px-6 py-2.5 text-base",
            lg: "px-8 py-3.5 text-lg",
        };

        return (
            <motion.button
                ref={ref}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.95 }}
                className={cn(
                    "relative rounded-xl font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed",
                    variants[variant],
                    sizes[size],
                    className
                )}
                disabled={isLoading || props.disabled}
                {...props}
            >
                {isLoading ? (
                    <div className="flex items-center justify-center">
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                        <span>Loading...</span>
                    </div>
                ) : (
                    children
                )}
            </motion.button>
        );
    }
);

AnimatedButton.displayName = "AnimatedButton";

export default AnimatedButton;

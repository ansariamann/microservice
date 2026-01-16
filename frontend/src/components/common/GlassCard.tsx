import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface GlassCardProps extends HTMLMotionProps<"div"> {
    className?: string;
    children: React.ReactNode;
    hoverEffect?: boolean;
}

const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
    ({ className, children, hoverEffect = false, ...props }, ref) => {
        return (
            <motion.div
                ref={ref}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                whileHover={hoverEffect ? { y: -5, boxShadow: "0 20px 40px -10px rgba(0,0,0,0.3)" } : undefined}
                transition={{ duration: 0.4, ease: "easeOut" }}
                className={cn(
                    "bg-surface/30 backdrop-blur-md border border-white/10 rounded-2xl shadow-xl overflow-hidden",
                    hoverEffect && "hover:bg-surface/40 hover:border-white/20 transition-colors duration-300",
                    className
                )}
                {...props}
            >
                {children}
            </motion.div>
        );
    }
);

GlassCard.displayName = "GlassCard";

export default GlassCard;

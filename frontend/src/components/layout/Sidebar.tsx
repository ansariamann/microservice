import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    HomeIcon,
    ClipboardDocumentListIcon,
    UserCircleIcon,
    ArrowLeftOnRectangleIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import clsx from 'clsx';

const Sidebar: React.FC = () => {
    const { logout } = useAuth();
    const location = useLocation();

    const navItems = [
        { name: 'Dashboard', path: '/dashboard', icon: HomeIcon },
        { name: 'Tasks', path: '/tasks', icon: ClipboardDocumentListIcon },
        { name: 'Profile', path: '/profile', icon: UserCircleIcon },
    ];

    return (
        <motion.aside
            initial={{ x: -100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="hidden md:flex flex-col w-64 h-screen fixed left-0 top-0 glass border-r border-white/5 z-40"
        >
            <div className="p-8 flex items-center justify-center">
                <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary filter drop-shadow-lg">
                    TaskMaster
                </h1>
            </div>

            <nav className="flex-1 px-4 space-y-2 py-4">
                {navItems.map((item) => {
                    const isActive = location.pathname === item.path;
                    return (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            className={({ isActive }) => clsx(
                                "relative group flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-300",
                                isActive
                                    ? "text-white bg-primary/20 shadow-[0_0_20px_rgba(99,102,241,0.3)]"
                                    : "text-gray-400 hover:text-white hover:bg-white/5"
                            )}
                        >
                            <item.icon className={clsx("w-6 h-6 mr-3 transition-colors", isActive ? "text-primary" : "group-hover:text-white")} />
                            {item.name}

                            {isActive && (
                                <motion.div
                                    layoutId="sidebar-active"
                                    className="absolute inset-0 bg-primary/10 rounded-xl border border-primary/20 z-[-1]"
                                    initial={false}
                                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                />
                            )}
                        </NavLink>
                    );
                })}
            </nav>

            <div className="p-4 border-t border-white/10">
                <button
                    onClick={logout}
                    className="flex items-center w-full px-4 py-3 text-sm font-medium text-gray-400 rounded-xl hover:text-red-400 hover:bg-red-500/10 transition-all duration-300"
                >
                    <ArrowLeftOnRectangleIcon className="w-6 h-6 mr-3" />
                    Logout
                </button>
            </div>
        </motion.aside>
    );
};

export default Sidebar;

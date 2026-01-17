import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import NotificationPanel from "../notifications/NotificationPanel";
import { Bars3Icon, XMarkIcon } from "@heroicons/react/24/outline";
import { AnimatePresence, motion } from "framer-motion";
import clsx from "clsx";

const Navigation: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  const handleLogout = () => {
    logout();
    setIsMobileMenuOpen(false);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  const navLinkClasses = (path: string) =>
    clsx(
      "block px-3 py-2 rounded-md text-base font-medium transition-colors",
      isActive(path)
        ? "bg-primary/20 text-white shadow-[0_0_10px_rgba(99,102,241,0.3)]"
        : "text-gray-300 hover:text-white hover:bg-white/10"
    );

  return (
    <nav className="glass border-b border-white/10 fixed w-full top-0 z-50 md:hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link
              to="/dashboard"
              className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary"
            >
              TaskMaster
            </Link>
          </div>

          {/* Mobile menu button */}
          <div className="flex items-center space-x-4">
            <NotificationPanel />
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-300 hover:text-white hover:bg-white/10 focus:outline-none"
            >
              <span className="sr-only">Open main menu</span>
              {isMobileMenuOpen ? (
                <XMarkIcon className="block h-6 w-6" aria-hidden="true" />
              ) : (
                <Bars3Icon className="block h-6 w-6" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="md:hidden overflow-hidden glass border-b border-white/10"
          >
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
              <Link to="/dashboard" onClick={closeMobileMenu} className={navLinkClasses("/dashboard")}>
                Dashboard
              </Link>
              <Link to="/tasks" onClick={closeMobileMenu} className={navLinkClasses("/tasks")}>
                Tasks
              </Link>
              <Link to="/profile" onClick={closeMobileMenu} className={navLinkClasses("/profile")}>
                Profile
              </Link>
            </div>
            <div className="pt-4 pb-3 border-t border-white/10">
              <div className="flex items-center px-5">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-primary to-secondary flex items-center justify-center text-white font-bold">
                    {user?.name?.charAt(0) || 'U'}
                  </div>
                </div>
                <div className="ml-3">
                  <div className="text-base font-medium leading-none text-white">{user?.name}</div>
                  <div className="text-sm font-medium leading-none text-gray-400 mt-1">{user?.email}</div>
                </div>
              </div>
              <div className="mt-3 px-2 space-y-1">
                <button
                  onClick={handleLogout}
                  className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:text-white hover:bg-white/10"
                >
                  Logout
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

export default Navigation;

import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import NotificationPanel from "../notifications/NotificationPanel";
import { Bars3Icon, XMarkIcon } from "@heroicons/react/24/outline";

const Navigation: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const handleLogout = () => {
    logout();
    setIsMobileMenuOpen(false);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  const navLinkClasses = (path: string) =>
    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
      isActive(path)
        ? "bg-blue-100 text-blue-700"
        : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
    }`;

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200 fixed w-full top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link
              to="/dashboard"
              className="text-xl font-semibold text-gray-900 hover:text-blue-600 transition-colors"
            >
              Task Manager
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-4">
            <Link to="/dashboard" className={navLinkClasses("/dashboard")}>
              Dashboard
            </Link>

            <Link to="/tasks" className={navLinkClasses("/tasks")}>
              Tasks
            </Link>

            <Link to="/profile" className={navLinkClasses("/profile")}>
              Profile
            </Link>

            <div className="flex items-center space-x-3 ml-4 pl-4 border-l border-gray-200">
              {/* Notification Panel */}
              <NotificationPanel />

              <span className="text-sm text-gray-700 hidden lg:inline">
                Welcome, {user?.name}
              </span>
              <button
                onClick={handleLogout}
                className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Logout
              </button>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center space-x-2">
            <NotificationPanel />
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
              aria-expanded="false"
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
      {isMobileMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-white border-t border-gray-200">
            <Link
              to="/dashboard"
              onClick={closeMobileMenu}
              className={`block ${navLinkClasses("/dashboard")}`}
            >
              Dashboard
            </Link>

            <Link
              to="/tasks"
              onClick={closeMobileMenu}
              className={`block ${navLinkClasses("/tasks")}`}
            >
              Tasks
            </Link>

            <Link
              to="/profile"
              onClick={closeMobileMenu}
              className={`block ${navLinkClasses("/profile")}`}
            >
              Profile
            </Link>

            <div className="pt-4 pb-3 border-t border-gray-200">
              <div className="flex items-center px-3">
                <span className="text-sm text-gray-700">
                  Welcome, {user?.name}
                </span>
              </div>
              <div className="mt-3 px-3">
                <button
                  onClick={handleLogout}
                  className="w-full text-left bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navigation;

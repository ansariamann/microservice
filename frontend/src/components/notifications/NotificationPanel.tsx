import React, { useState, useRef, useEffect } from "react";
import { useNotifications } from "../../contexts/NotificationContext";
import NotificationItem from "./NotificationItem";
import ErrorMessage from "../common/ErrorMessage";
import LoadingSpinner from "../common/LoadingSpinner";
import { BellIcon } from "@heroicons/react/24/outline";
import { AnimatePresence, motion } from "framer-motion";
import GlassCard from "../common/GlassCard";

const NotificationPanel: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const {
    notifications,
    unreadCount,
    loading,
    error,
    markAsRead,
    markAllAsRead,
  } = useNotifications();

  // Close panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        panelRef.current &&
        !panelRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  // Close panel on escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      return () => document.removeEventListener("keydown", handleEscape);
    }
  }, [isOpen]);

  const handleMarkAsRead = async (notificationId: number) => {
    try {
      await markAsRead(notificationId);
    } catch (error) {
      console.error("Failed to mark notification as read:", error);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await markAllAsRead();
    } catch (error) {
      console.error("Failed to mark all notifications as read:", error);
    }
  };

  return (
    <div className="relative" ref={panelRef}>
      {/* Notification Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-400 hover:text-white transition-colors focus:outline-none rounded-xl hover:bg-white/10"
        title="Notifications"
      >
        <BellIcon className="h-6 w-6" />
        {unreadCount > 0 && (
          <span className="absolute top-1.5 right-1.5 inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold leading-none text-white transform translate-x-1/4 -translate-y-1/4 bg-red-500 rounded-full shadow-[0_0_10px_rgba(239,68,68,0.5)] animate-pulse-slow">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Notification Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute right-0 mt-2 w-80 sm:w-96 z-50 origin-top-right"
          >
            <GlassCard className="overflow-hidden" hoverEffect={false}>
              <div className="p-4 border-b border-white/10 flex items-center justify-between bg-black/20">
                <h3 className="font-semibold text-white">Notifications</h3>
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllAsRead}
                    className="text-xs text-primary hover:text-accent transition-colors"
                  >
                    Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-96 overflow-y-auto custom-scrollbar bg-black/10">
                {error && <div className="p-4"><ErrorMessage message={error} /></div>}

                {loading && notifications.length === 0 && (
                  <div className="flex justify-center py-8">
                    <LoadingSpinner size="md" text="Loading..." color="white" />
                  </div>
                )}

                {!loading && notifications.length === 0 && (
                  <div className="text-center py-12 px-4">
                    <BellIcon className="mx-auto h-12 w-12 text-gray-600 mb-3" />
                    <p className="text-gray-400 text-sm">No notifications yet</p>
                  </div>
                )}

                <div className="divide-y divide-white/5">
                  {notifications.map((notification) => (
                    <NotificationItem
                      key={notification.id}
                      notification={notification}
                      onMarkAsRead={handleMarkAsRead}
                    />
                  ))}
                </div>
              </div>

              <div className="p-2 bg-black/20 border-t border-white/10 text-center">
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-xs text-gray-400 hover:text-white transition-colors py-1 block w-full"
                >
                  Close
                </button>
              </div>
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NotificationPanel;

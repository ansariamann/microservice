import React, { ReactNode } from "react";
import { useAuth } from "../../contexts/AuthContext";
import Sidebar from "./Sidebar";
import Navigation from "./Navigation"; // Keep Navigation for mobile for now, or replace later
import { motion, AnimatePresence } from "framer-motion";

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-background text-white selection:bg-primary/30">
      {/* Background Ambient Glow */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 rounded-full blur-[120px] animate-pulse-slow" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-secondary/20 rounded-full blur-[120px] animate-pulse-slow delay-1000" />
      </div>

      <div className="relative z-10 flex h-screen overflow-hidden">
        {isAuthenticated && <Sidebar />}

        {/* Mobile Nav Fallback (Optional, can be hidden on desktop) */}
        <div className="md:hidden fixed top-0 w-full z-50">
          {isAuthenticated && <Navigation />}
        </div>

        <main className={`flex-1 overflow-y-auto overflow-x-hidden transition-all duration-300 ${isAuthenticated ? 'md:ml-64 pt-16 md:pt-0' : ''} p-4 md:p-8 custom-scrollbar`}>
          <AnimatePresence mode="wait">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};

export default Layout;

import React from "react";
import { useAuth } from "../contexts/AuthContext";
import GlassCard from "../components/common/GlassCard";
import { motion } from "framer-motion";
import {
  ClipboardDocumentCheckIcon,
  ClockIcon,
  ChartBarIcon,
  SparklesIcon
} from "@heroicons/react/24/outline";

const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  const containerAnimations = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemAnimations = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1
    }
  };

  const stats = [
    { name: 'Total Tasks', value: '12', icon: ClipboardDocumentCheckIcon, color: 'text-blue-400', bg: 'bg-blue-400/10' },
    { name: 'In Progress', value: '4', icon: ClockIcon, color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
    { name: 'Completed', value: '8', icon: SparklesIcon, color: 'text-green-400', bg: 'bg-green-400/10' },
    { name: 'Efficiency', value: '92%', icon: ChartBarIcon, color: 'text-purple-400', bg: 'bg-purple-400/10' },
  ];

  return (
    <motion.div
      variants={containerAnimations}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      <motion.div variants={itemAnimations}>
        <h1 className="text-4xl font-bold text-white mb-2">
          Dashboard
        </h1>
        <p className="text-gray-400">
          Welcome back, <span className="text-primary font-medium">{user?.name}</span>. Here's what's happening today.
        </p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <GlassCard key={stat.name} className="p-6 flex items-center space-x-4" hoverEffect>
            <div className={`p-3 rounded-xl ${stat.bg}`}>
              <stat.icon className={`w-6 h-6 ${stat.color}`} />
            </div>
            <div>
              <p className="text-sm text-gray-400">{stat.name}</p>
              <h3 className="text-2xl font-bold text-white">{stat.value}</h3>
            </div>
          </GlassCard>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <GlassCard className="lg:col-span-2 p-6 h-96" hoverEffect>
          <h2 className="text-xl font-bold text-white mb-4">Recent Activity</h2>
          <div className="flex items-center justify-center h-full text-gray-500">
            Chart Placeholder
          </div>
        </GlassCard>

        {/* Quick Actions / Notifications */}
        <GlassCard className="p-6 h-96" hoverEffect>
          <h2 className="text-xl font-bold text-white mb-4">Notifications</h2>
          <div className="space-y-4">
            {/* Mock Notifications */}
            {[1, 2, 3].map((_, i) => (
              <div key={i} className="flex items-start space-x-3 p-3 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">
                <div className="w-2 h-2 mt-2 rounded-full bg-accent" />
                <div>
                  <p className="text-sm text-gray-200">New comment on "Design Update"</p>
                  <p className="text-xs text-gray-500">2 hours ago</p>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </motion.div>
  );
};

export default DashboardPage;

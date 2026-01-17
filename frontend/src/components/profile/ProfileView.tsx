import React from "react";
import { User } from "../../types/auth";
import GlassCard from "../common/GlassCard";
import AnimatedButton from "../common/AnimatedButton";
import { UserCircleIcon, EnvelopeIcon, CalendarIcon, ClockIcon } from "@heroicons/react/24/outline";

interface ProfileViewProps {
  user: User;
  onEdit: () => void;
}

const ProfileView: React.FC<ProfileViewProps> = ({ user, onEdit }) => {
  return (
    <GlassCard className="max-w-4xl mx-auto p-8 relative overflow-hidden" hoverEffect={false}>
      {/* Decorative Background */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-64 h-64 bg-secondary/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2 pointer-events-none" />

      <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between mb-8 gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-primary to-secondary flex items-center justify-center text-3xl font-bold text-white shadow-lg">
            {user.name.charAt(0)}
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white mb-1">{user.name}</h1>
            <p className="text-gray-400 flex items-center">
              <span className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse" />
              Active Member
            </p>
          </div>
        </div>
        <AnimatedButton onClick={onEdit} variant="primary">
          Edit Profile
        </AnimatedButton>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative z-10">
        <div className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-primary/50 transition-colors duration-300">
          <div className="flex items-center text-gray-400 mb-2">
            <UserCircleIcon className="w-5 h-5 mr-2" />
            <span className="text-sm font-medium">Full Name</span>
          </div>
          <p className="text-lg text-white font-medium pl-7">{user.name}</p>
        </div>

        <div className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-primary/50 transition-colors duration-300">
          <div className="flex items-center text-gray-400 mb-2">
            <EnvelopeIcon className="w-5 h-5 mr-2" />
            <span className="text-sm font-medium">Email Address</span>
          </div>
          <p className="text-lg text-white font-medium pl-7">{user.email}</p>
        </div>

        <div className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-primary/50 transition-colors duration-300">
          <div className="flex items-center text-gray-400 mb-2">
            <CalendarIcon className="w-5 h-5 mr-2" />
            <span className="text-sm font-medium">Member Since</span>
          </div>
          <p className="text-lg text-white font-medium pl-7">
            {new Date(user.created_at).toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </p>
        </div>

        <div className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-primary/50 transition-colors duration-300">
          <div className="flex items-center text-gray-400 mb-2">
            <ClockIcon className="w-5 h-5 mr-2" />
            <span className="text-sm font-medium">Last Updated</span>
          </div>
          <p className="text-lg text-white font-medium pl-7">
            {new Date(user.updated_at).toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </p>
        </div>
      </div>

      <div className="mt-8 pt-6 border-t border-white/10 text-center md:text-left">
        <p className="text-sm text-gray-500">
          Your profile information is visible to other team members and is used for task assignments.
        </p>
      </div>
    </GlassCard>
  );
};

export default ProfileView;

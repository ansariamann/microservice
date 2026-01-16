import React from "react";
import { useAuth } from "../contexts/AuthContext";

const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="px-4 py-6 sm:px-0">
        <div className="border-4 border-dashed border-gray-200 rounded-lg p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Welcome to your Dashboard, {user?.name}!
          </h1>
          <p className="text-gray-600">
            Dashboard content will be implemented in future tasks. This
            includes:
          </p>
          <ul className="mt-4 list-disc list-inside text-gray-600 space-y-2">
            <li>Task overview and statistics</li>
            <li>Recent notifications</li>
            <li>Quick actions</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;

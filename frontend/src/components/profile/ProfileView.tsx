import React from "react";
import { User } from "../../types/auth";

interface ProfileViewProps {
  user: User;
  onEdit: () => void;
}

const ProfileView: React.FC<ProfileViewProps> = ({ user, onEdit }) => {
  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">User Profile</h1>
          <button
            onClick={onEdit}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
          >
            Edit Profile
          </button>
        </div>

        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Full Name
              </label>
              <div className="mt-1 text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                {user.name}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Email Address
              </label>
              <div className="mt-1 text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                {user.email}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Member Since
              </label>
              <div className="mt-1 text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                {new Date(user.created_at).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Last Updated
              </label>
              <div className="mt-1 text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                {new Date(user.updated_at).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </div>
            </div>
          </div>

          <div className="border-t border-gray-200 pt-6">
            <div className="text-sm text-gray-500">
              <p>
                Your profile information is used to personalize your experience
                and help other team members identify you when working on shared
                tasks.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileView;

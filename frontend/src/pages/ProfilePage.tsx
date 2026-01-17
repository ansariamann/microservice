import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import ProfileView from "../components/profile/ProfileView";
import ProfileEditForm from "../components/profile/ProfileEditForm";
import AuthService from "../services/authService";
import { getErrorMessage } from "../utils/errorHandler";
import LoadingSpinner from "../components/common/LoadingSpinner";

const ProfilePage: React.FC = () => {
  const { user, login } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");

  if (!user) {
    return (
      <div className="flex justify-center items-center py-20">
        <LoadingSpinner text="Loading profile..." />
      </div>
    );
  }

  const handleEdit = () => {
    setIsEditing(true);
    setError("");
  };

  const handleCancel = () => {
    setIsEditing(false);
    setError("");
  };

  const handleProfileUpdate = async (data: { name: string; email: string }) => {
    setIsLoading(true);
    setError("");

    try {
      // Use AuthService for actual API call
      const updatedUser = await AuthService.updateProfile(data);

      // Update the auth context with the new user data
      login({
        access_token: localStorage.getItem("token") || "mock-jwt-token",
        token_type: "bearer",
        user: updatedUser,
      });

      setIsEditing(false);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="py-6">
      {isEditing ? (
        <ProfileEditForm
          user={user}
          onSubmit={handleProfileUpdate}
          onCancel={handleCancel}
          isLoading={isLoading}
          error={error}
        />
      ) : (
        <ProfileView user={user} onEdit={handleEdit} />
      )}
    </div>
  );
};

export default ProfilePage;

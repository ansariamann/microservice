import React, { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import RegisterForm from "../components/auth/RegisterForm";
import { UserRegistration } from "../types/auth";
import AuthService from "../services/authService";
import { getErrorMessage } from "../utils/errorHandler";

const RegisterPage: React.FC = () => {
  const { isAuthenticated, login } = useAuth();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");

  // Redirect to dashboard if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleRegister = async (data: UserRegistration) => {
    setIsLoading(true);
    setError("");

    try {
      // Use AuthService for actual API call
      const authResponse = await AuthService.register(data);
      login(authResponse);
      navigate("/dashboard");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <RegisterForm
      onSubmit={handleRegister}
      isLoading={isLoading}
      error={error}
    />
  );
};

export default RegisterPage;

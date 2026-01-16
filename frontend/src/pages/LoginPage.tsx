import React, { useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import LoginForm from "../components/auth/LoginForm";
import { UserLogin } from "../types/auth";
import AuthService from "../services/authService";
import { getErrorMessage } from "../utils/errorHandler";

const LoginPage: React.FC = () => {
  const { isAuthenticated, login } = useAuth();
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");

  // Redirect to dashboard if already authenticated
  if (isAuthenticated) {
    const from = location.state?.from?.pathname || "/dashboard";
    return <Navigate to={from} replace />;
  }

  const handleLogin = async (data: UserLogin) => {
    setIsLoading(true);
    setError("");

    try {
      // Use AuthService for actual API call
      const authResponse = await AuthService.login(data);
      login(authResponse);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <LoginForm onSubmit={handleLogin} isLoading={isLoading} error={error} />
  );
};

export default LoginPage;

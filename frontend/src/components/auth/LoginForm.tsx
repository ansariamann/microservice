import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";
import { Link } from "react-router-dom";
import { UserLogin } from "../../types/auth";
import ErrorMessage from "../common/ErrorMessage";
import GlassCard from "../common/GlassCard";
import AnimatedButton from "../common/AnimatedButton";
import { motion } from "framer-motion";

const schema = yup.object({
  email: yup
    .string()
    .required("Email is required")
    .email("Please enter a valid email address"),
  password: yup
    .string()
    .required("Password is required")
    .min(6, "Password must be at least 6 characters"),
});

interface LoginFormProps {
  onSubmit: (data: UserLogin) => Promise<void>;
  isLoading?: boolean;
  error?: string;
}

const LoginForm: React.FC<LoginFormProps> = ({
  onSubmit,
  isLoading,
  error,
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<UserLogin>({
    resolver: yupResolver(schema),
    mode: "onChange",
  });

  const getInputClasses = (fieldName: keyof UserLogin) => {
    const hasError = errors[fieldName];
    return `mt-1 block w-full px-4 py-3 bg-surface/50 border ${hasError ? "border-red-500/50 focus:ring-red-500" : "border-white/10 focus:ring-primary"
      } rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent transition-all duration-300 backdrop-blur-sm`;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background Blobs */}
      <div className="absolute top-[-20%] left-[-20%] w-[50%] h-[50%] bg-primary/20 rounded-full blur-[100px] animate-pulse-slow" />
      <div className="absolute bottom-[-20%] right-[-20%] w-[50%] h-[50%] bg-secondary/20 rounded-full blur-[100px] animate-pulse-slow delay-1000" />

      <GlassCard className="w-full max-w-md p-8 relative z-10" hoverEffect={false}>
        <div className="text-center mb-8">
          <motion.h2
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary"
          >
            Welcome Back
          </motion.h2>
          <p className="mt-2 text-sm text-gray-400">
            Sign in to manage your tasks effectively
          </p>
        </div>

        <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
          {error && <ErrorMessage message={error} className="mb-4" />}

          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 ml-1">
                Email Address
              </label>
              <input
                {...register("email")}
                id="email"
                type="email"
                autoComplete="email"
                className={getInputClasses("email")}
                placeholder="Enter your email"
              />
              {errors.email && (
                <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-1 text-sm text-red-400 ml-1">
                  {errors.email.message}
                </motion.p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 ml-1">
                Password
              </label>
              <div className="relative">
                <input
                  {...register("password")}
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  className={getInputClasses("password")}
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-white transition-colors"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  <span className="text-xs uppercase font-medium tracking-wider">
                    {showPassword ? "Hide" : "Show"}
                  </span>
                </button>
              </div>
              {errors.password && (
                <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-1 text-sm text-red-400 ml-1">
                  {errors.password.message}
                </motion.p>
              )}
            </div>
          </div>

          <div className="pt-2">
            <AnimatedButton
              type="submit"
              variant="primary"
              size="lg"
              className="w-full"
              isLoading={isLoading || isSubmitting}
            >
              Sign In
            </AnimatedButton>
          </div>

          <div className="text-center mt-4">
            <p className="text-sm text-gray-400">
              Don't have an account?{" "}
              <Link to="/register" className="font-medium text-primary hover:text-accent transition-colors">
                Sign up now
              </Link>
            </p>
          </div>
        </form>
      </GlassCard>
    </div>
  );
};

export default LoginForm;

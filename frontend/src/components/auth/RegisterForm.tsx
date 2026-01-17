import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";
import { Link, useNavigate } from "react-router-dom";
import { UserRegistration } from "../../types/auth";
import ErrorMessage from "../common/ErrorMessage";
import GlassCard from "../common/GlassCard";
import AnimatedButton from "../common/AnimatedButton";
import { motion } from "framer-motion";

const schema = yup.object({
  name: yup
    .string()
    .required("Name is required")
    .min(2, "Name must be at least 2 characters")
    .max(50, "Name must be less than 50 characters"),
  email: yup
    .string()
    .required("Email is required")
    .email("Please enter a valid email address")
    .max(100, "Email must be less than 100 characters"),
  password: yup
    .string()
    .required("Password is required")
    .min(6, "Password must be at least 6 characters")
    .max(100, "Password must be less than 100 characters")
    .matches(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      "Password must contain at least one uppercase letter, one lowercase letter, and one number"
    ),
  confirmPassword: yup
    .string()
    .required("Please confirm your password")
    .oneOf([yup.ref("password")], "Passwords must match"),
});

type FormData = UserRegistration & {
  confirmPassword: string;
};

interface RegisterFormProps {
  onSubmit: (data: UserRegistration) => Promise<void>;
  isLoading?: boolean;
  error?: string;
}

const RegisterForm: React.FC<RegisterFormProps> = ({
  onSubmit,
  isLoading,
  error,
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
  } = useForm<FormData>({
    resolver: yupResolver(schema),
    mode: "onChange",
  });

  const handleFormSubmit = async (data: FormData) => {
    const { confirmPassword, ...registrationData } = data;
    await onSubmit(registrationData);
  };

  const getInputClasses = (fieldName: keyof FormData) => {
    const hasError = errors[fieldName];
    return `mt-1 block w-full px-4 py-3 bg-surface/50 border ${hasError ? "border-red-500/50 focus:ring-red-500" : "border-white/10 focus:ring-primary"
      } rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:border-transparent transition-all duration-300 backdrop-blur-sm`;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background Blobs */}
      <div className="absolute top-[10%] right-[10%] w-[40%] h-[40%] bg-accent/20 rounded-full blur-[100px] animate-pulse-slow" />
      <div className="absolute bottom-[10%] left-[10%] w-[40%] h-[40%] bg-primary/20 rounded-full blur-[100px] animate-pulse-slow delay-1000" />

      <GlassCard className="w-full max-w-md p-8 relative z-10" hoverEffect={false}>
        <div className="text-center mb-8">
          <motion.h2
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-secondary to-accent"
          >
            Create Account
          </motion.h2>
          <p className="mt-2 text-sm text-gray-400">
            Join us and start organizing your life
          </p>
        </div>

        <form className="space-y-5" onSubmit={handleSubmit(handleFormSubmit)}>
          {error && <ErrorMessage message={error} className="mb-4" />}

          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-300 ml-1">Full Name</label>
            <input
              {...register("name")}
              id="name"
              className={getInputClasses("name")}
              placeholder="John Doe"
            />
            {errors.name && <p className="mt-1 text-sm text-red-400 ml-1">{errors.name.message}</p>}
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-300 ml-1">Email Address</label>
            <input
              {...register("email")}
              id="email"
              type="email"
              className={getInputClasses("email")}
              placeholder="john@example.com"
            />
            {errors.email && <p className="mt-1 text-sm text-red-400 ml-1">{errors.email.message}</p>}
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-300 ml-1">Password</label>
            <div className="relative">
              <input
                {...register("password")}
                id="password"
                type={showPassword ? "text" : "password"}
                className={getInputClasses("password")}
                placeholder="••••••••"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-white"
                onClick={() => setShowPassword(!showPassword)}
              >
                <span className="text-xs uppercase">{showPassword ? "Hide" : "Show"}</span>
              </button>
            </div>
            {errors.password && <p className="mt-1 text-sm text-red-400 ml-1">{errors.password.message}</p>}
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-300 ml-1">Confirm Password</label>
            <div className="relative">
              <input
                {...register("confirmPassword")}
                id="confirmPassword"
                type={showConfirmPassword ? "text" : "password"}
                className={getInputClasses("confirmPassword")}
                placeholder="••••••••"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-white"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              >
                <span className="text-xs uppercase">{showConfirmPassword ? "Hide" : "Show"}</span>
              </button>
            </div>
            {errors.confirmPassword && <p className="mt-1 text-sm text-red-400 ml-1">{errors.confirmPassword.message}</p>}
          </div>

          <div className="pt-4">
            <AnimatedButton
              type="submit"
              variant="secondary"
              size="lg"
              className="w-full"
              isLoading={isLoading || isSubmitting}
            >
              Sign Up
            </AnimatedButton>
          </div>

          <div className="text-center mt-4">
            <p className="text-sm text-gray-400">
              Already have an account?{" "}
              <Link to="/login" className="font-medium text-secondary hover:text-pink-400 transition-colors">
                Sign in
              </Link>
            </p>
          </div>
        </form>
      </GlassCard>
    </div>
  );
};

export default RegisterForm;

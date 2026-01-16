import React from "react";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  color?: "blue" | "white" | "gray";
  className?: string;
  text?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = "md",
  color = "blue",
  className = "",
  text,
}) => {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-8 w-8",
  };

  const colorClasses = {
    blue: "border-blue-600",
    white: "border-white",
    gray: "border-gray-600",
  };

  const spinnerClasses = `animate-spin rounded-full border-2 border-t-transparent ${sizeClasses[size]} ${colorClasses[color]}`;

  if (text) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className={spinnerClasses} role="status" aria-hidden="true"></div>
        <span className="text-sm text-gray-600">{text}</span>
      </div>
    );
  }

  return (
    <div
      className={`${spinnerClasses} ${className}`}
      role="status"
      aria-hidden="true"
    ></div>
  );
};

export default LoadingSpinner;

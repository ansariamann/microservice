import React from "react";
import { ExclamationCircleIcon, XMarkIcon } from "@heroicons/react/24/outline";

interface ErrorMessageProps {
  message: string;
  onDismiss?: () => void;
  variant?: "error" | "warning" | "info";
  className?: string;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({
  message,
  onDismiss,
  variant = "error",
  className = "",
}) => {
  const baseClasses = "rounded-md p-4 flex items-start space-x-3";
  const variantClasses = {
    error: "bg-red-50 border border-red-200",
    warning: "bg-yellow-50 border border-yellow-200",
    info: "bg-blue-50 border border-blue-200",
  };

  const iconClasses = {
    error: "text-red-400",
    warning: "text-yellow-400",
    info: "text-blue-400",
  };

  const textClasses = {
    error: "text-red-800",
    warning: "text-yellow-800",
    info: "text-blue-800",
  };

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      role="alert"
    >
      <div className="flex-shrink-0">
        <ExclamationCircleIcon
          className={`h-5 w-5 ${iconClasses[variant]}`}
          aria-hidden="true"
        />
      </div>
      <div className="flex-1">
        <p className={`text-sm font-medium ${textClasses[variant]}`}>
          {message}
        </p>
      </div>
      {onDismiss && (
        <div className="flex-shrink-0">
          <button
            type="button"
            onClick={onDismiss}
            className={`inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
              variant === "error"
                ? "text-red-500 hover:bg-red-100 focus:ring-red-500"
                : variant === "warning"
                ? "text-yellow-500 hover:bg-yellow-100 focus:ring-yellow-500"
                : "text-blue-500 hover:bg-blue-100 focus:ring-blue-500"
            }`}
          >
            <span className="sr-only">Dismiss</span>
            <XMarkIcon className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      )}
    </div>
  );
};

export default ErrorMessage;

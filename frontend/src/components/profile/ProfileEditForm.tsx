import React from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";
import { User } from "../../types/auth";
import ErrorMessage from "../common/ErrorMessage";
import LoadingSpinner from "../common/LoadingSpinner";

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
});

type ProfileUpdateData = {
  name: string;
  email: string;
};

interface ProfileEditFormProps {
  user: User;
  onSubmit: (data: ProfileUpdateData) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  error?: string;
}

const ProfileEditForm: React.FC<ProfileEditFormProps> = ({
  user,
  onSubmit,
  onCancel,
  isLoading,
  error,
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<ProfileUpdateData>({
    resolver: yupResolver(schema),
    defaultValues: {
      name: user.name,
      email: user.email,
    },
    mode: "onChange",
  });

  const getInputClasses = (fieldName: keyof ProfileUpdateData) => {
    const hasError = errors[fieldName];
    return `mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none sm:text-sm transition-colors ${
      hasError
        ? "border-red-300 focus:ring-red-500 focus:border-red-500"
        : "border-gray-300 focus:ring-blue-500 focus:border-blue-500"
    }`;
  };

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="mb-6">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
            Edit Profile
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            Update your profile information below.
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {error && <ErrorMessage message={error} />}

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label
                htmlFor="name"
                className="block text-sm font-medium text-gray-700"
              >
                Full Name
              </label>
              <input
                {...register("name")}
                id="name"
                type="text"
                autoComplete="name"
                className={getInputClasses("name")}
                placeholder="Enter your full name"
                aria-invalid={errors.name ? "true" : "false"}
                aria-describedby={errors.name ? "name-error" : undefined}
              />
              {errors.name && (
                <p id="name-error" className="mt-1 text-sm text-red-600">
                  {errors.name.message}
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700"
              >
                Email Address
              </label>
              <input
                {...register("email")}
                id="email"
                type="email"
                autoComplete="email"
                className={getInputClasses("email")}
                placeholder="Enter your email address"
                aria-invalid={errors.email ? "true" : "false"}
                aria-describedby={errors.email ? "email-error" : undefined}
              />
              {errors.email && (
                <p id="email-error" className="mt-1 text-sm text-red-600">
                  {errors.email.message}
                </p>
              )}
            </div>
          </div>

          <div className="border-t border-gray-200 pt-6">
            <div className="flex flex-col sm:flex-row justify-end space-y-2 sm:space-y-0 sm:space-x-3">
              <button
                type="button"
                onClick={onCancel}
                className="w-full sm:w-auto bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading || isSubmitting || !isDirty}
                className="w-full sm:w-auto bg-blue-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading || isSubmitting ? (
                  <LoadingSpinner size="sm" color="white" text="Saving..." />
                ) : (
                  "Save Changes"
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfileEditForm;

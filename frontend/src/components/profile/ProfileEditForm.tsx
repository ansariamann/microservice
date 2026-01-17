import React from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";
import { User } from "../../types/auth";
import ErrorMessage from "../common/ErrorMessage";
import GlassCard from "../common/GlassCard";
import AnimatedButton from "../common/AnimatedButton";
import { UserCircleIcon, EnvelopeIcon } from "@heroicons/react/24/outline";

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
    return `mt-1 block w-full bg-surface/50 border ${hasError ? "border-red-500/50 focus:ring-red-500" : "border-white/10 focus:ring-primary"
      } rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 transition-all duration-300 backdrop-blur-sm`;
  };

  return (
    <GlassCard className="max-w-2xl mx-auto p-8" hoverEffect={false}>
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary mb-2">
          Edit Profile
        </h1>
        <p className="text-gray-400">
          Update your personal information
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {error && <ErrorMessage message={error} />}

        <div className="space-y-6">
          <div>
            <label htmlFor="name" className="flex items-center text-sm font-medium text-gray-300 mb-1 ml-1">
              <UserCircleIcon className="w-4 h-4 mr-2" />
              Full Name
            </label>
            <input
              {...register("name")}
              id="name"
              type="text"
              autoComplete="name"
              className={getInputClasses("name")}
              placeholder="Enter your full name"
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-400 ml-1">
                {errors.name.message}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="email" className="flex items-center text-sm font-medium text-gray-300 mb-1 ml-1">
              <EnvelopeIcon className="w-4 h-4 mr-2" />
              Email Address
            </label>
            <input
              {...register("email")}
              id="email"
              type="email"
              autoComplete="email"
              className={getInputClasses("email")}
              placeholder="Enter your email address"
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-400 ml-1">
                {errors.email.message}
              </p>
            )}
          </div>
        </div>

        <div className="pt-6 border-t border-white/10 flex flex-col sm:flex-row justify-end gap-3">
          <AnimatedButton
            type="button"
            variant="ghost"
            onClick={onCancel}
            className="w-full sm:w-auto"
          >
            Cancel
          </AnimatedButton>
          <AnimatedButton
            type="submit"
            variant="primary"
            className="w-full sm:w-auto"
            disabled={!isDirty}
            isLoading={isLoading || isSubmitting}
          >
            Save Changes
          </AnimatedButton>
        </div>
      </form>
    </GlassCard>
  );
};

export default ProfileEditForm;

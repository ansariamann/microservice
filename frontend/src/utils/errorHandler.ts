import { AxiosError } from "axios";

export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}

/**
 * Extract error message from various error types
 */
export const getErrorMessage = (error: unknown): string => {
  if (typeof error === "string") {
    return error;
  }

  if (error instanceof Error) {
    return error.message;
  }

  if (isAxiosError(error)) {
    return extractAxiosErrorMessage(error);
  }

  return "An unexpected error occurred";
};

/**
 * Check if error is an Axios error
 */
export const isAxiosError = (error: any): error is AxiosError => {
  return error?.isAxiosError === true;
};

/**
 * Extract error message from Axios error
 */
export const extractAxiosErrorMessage = (error: AxiosError): string => {
  // Check for structured API error response
  if (error.response?.data) {
    const data = error.response.data as any;

    // Check for standard error format
    if (data.error?.message) {
      return data.error.message;
    }

    // Check for simple message format
    if (data.message) {
      return data.message;
    }

    // Check for validation errors
    if (data.errors && Array.isArray(data.errors)) {
      return data.errors.map((err: any) => err.message || err).join(", ");
    }
  }

  // Handle HTTP status codes
  if (error.response?.status) {
    switch (error.response.status) {
      case 400:
        return "Invalid request. Please check your input.";
      case 401:
        return "Authentication required. Please log in.";
      case 403:
        return "You do not have permission to perform this action.";
      case 404:
        return "The requested resource was not found.";
      case 409:
        return "A conflict occurred. The resource may already exist.";
      case 422:
        return "Validation failed. Please check your input.";
      case 429:
        return "Too many requests. Please try again later.";
      case 500:
        return "Internal server error. Please try again later.";
      case 502:
        return "Service temporarily unavailable. Please try again later.";
      case 503:
        return "Service unavailable. Please try again later.";
      default:
        return `Request failed with status ${error.response.status}`;
    }
  }

  // Handle network errors
  if (
    error.code === "NETWORK_ERROR" ||
    error.message?.includes("Network Error")
  ) {
    return "Network error. Please check your internet connection.";
  }

  // Handle timeout errors
  if (error.code === "ECONNABORTED" || error.message?.includes("timeout")) {
    return "Request timed out. Please try again.";
  }

  return error.message || "An unexpected error occurred";
};

/**
 * Create a standardized API error object
 */
export const createApiError = (error: unknown): ApiError => {
  const message = getErrorMessage(error);

  if (isAxiosError(error)) {
    return {
      message,
      code: error.code,
      details: error.response?.data,
    };
  }

  return { message };
};

/**
 * Log error for debugging purposes
 */
export const logError = (error: unknown, context?: string): void => {
  const errorInfo = createApiError(error);

  console.error("API Error:", {
    context,
    message: errorInfo.message,
    code: errorInfo.code,
    details: errorInfo.details,
    timestamp: new Date().toISOString(),
  });
};

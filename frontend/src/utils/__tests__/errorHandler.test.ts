import { describe, it, expect } from "vitest";
import { AxiosError } from "axios";
import {
  getErrorMessage,
  isAxiosError,
  extractAxiosErrorMessage,
  createApiError,
} from "../errorHandler";

describe("errorHandler", () => {
  describe("getErrorMessage", () => {
    it("should return string error as is", () => {
      const error = "Simple error message";
      expect(getErrorMessage(error)).toBe(error);
    });

    it("should return Error message", () => {
      const error = new Error("Error object message");
      expect(getErrorMessage(error)).toBe("Error object message");
    });

    it("should handle unknown error types", () => {
      const error = { someProperty: "value" };
      expect(getErrorMessage(error)).toBe("An unexpected error occurred");
    });
  });

  describe("isAxiosError", () => {
    it("should identify Axios errors", () => {
      const axiosError = { isAxiosError: true };
      expect(isAxiosError(axiosError)).toBe(true);
    });

    it("should reject non-Axios errors", () => {
      const regularError = new Error("Regular error");
      expect(isAxiosError(regularError)).toBe(false);
    });
  });

  describe("extractAxiosErrorMessage", () => {
    it("should extract structured API error message", () => {
      const axiosError = {
        response: {
          data: {
            error: {
              message: "Structured error message",
            },
          },
        },
      } as AxiosError;

      expect(extractAxiosErrorMessage(axiosError)).toBe(
        "Structured error message"
      );
    });

    it("should extract simple message format", () => {
      const axiosError = {
        response: {
          data: {
            message: "Simple message",
          },
        },
      } as AxiosError;

      expect(extractAxiosErrorMessage(axiosError)).toBe("Simple message");
    });

    it("should handle validation errors array", () => {
      const axiosError = {
        response: {
          data: {
            errors: [
              { message: "Field 1 error" },
              { message: "Field 2 error" },
            ],
          },
        },
      } as AxiosError;

      expect(extractAxiosErrorMessage(axiosError)).toBe(
        "Field 1 error, Field 2 error"
      );
    });

    it("should handle HTTP status codes", () => {
      const axiosError = {
        response: {
          status: 404,
        },
      } as AxiosError;

      expect(extractAxiosErrorMessage(axiosError)).toBe(
        "The requested resource was not found."
      );
    });

    it("should handle network errors", () => {
      const axiosError = {
        code: "NETWORK_ERROR",
        message: "Network Error",
      } as AxiosError;

      expect(extractAxiosErrorMessage(axiosError)).toBe(
        "Network error. Please check your internet connection."
      );
    });

    it("should handle timeout errors", () => {
      const axiosError = {
        code: "ECONNABORTED",
        message: "timeout of 5000ms exceeded",
      } as AxiosError;

      expect(extractAxiosErrorMessage(axiosError)).toBe(
        "Request timed out. Please try again."
      );
    });

    it("should return generic message for unknown errors", () => {
      const axiosError = {
        message: "Unknown error",
      } as AxiosError;

      expect(extractAxiosErrorMessage(axiosError)).toBe("Unknown error");
    });
  });

  describe("createApiError", () => {
    it("should create API error from Axios error", () => {
      const axiosError = {
        isAxiosError: true,
        code: "NETWORK_ERROR",
        message: "Network Error",
        response: {
          data: { details: "Additional info" },
        },
      } as AxiosError;

      const result = createApiError(axiosError);

      expect(result).toEqual({
        message: "Network error. Please check your internet connection.",
        code: "NETWORK_ERROR",
        details: { details: "Additional info" },
      });
    });

    it("should create API error from regular error", () => {
      const error = new Error("Regular error");
      const result = createApiError(error);

      expect(result).toEqual({
        message: "Regular error",
      });
    });

    it("should create API error from string", () => {
      const error = "String error";
      const result = createApiError(error);

      expect(result).toEqual({
        message: "String error",
      });
    });
  });
});

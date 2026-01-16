import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { useAsync } from "../useAsync";

describe("useAsync", () => {
  it("should initialize with correct default state", () => {
    const mockAsyncFunction = vi.fn();
    const { result } = renderHook(() => useAsync(mockAsyncFunction));

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("should initialize with loading true when immediate is true", () => {
    const mockAsyncFunction = vi.fn();
    const { result } = renderHook(() => useAsync(mockAsyncFunction, true));

    expect(result.current.loading).toBe(true);
  });

  it("should handle successful async operation", async () => {
    const mockData = { id: 1, name: "Test" };
    const mockAsyncFunction = vi.fn().mockResolvedValue(mockData);
    const { result } = renderHook(() => useAsync(mockAsyncFunction));

    await act(async () => {
      const returnedData = await result.current.execute();
      expect(returnedData).toEqual(mockData);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(mockAsyncFunction).toHaveBeenCalledTimes(1);
  });

  it("should handle async operation with arguments", async () => {
    const mockData = { id: 1, name: "Test" };
    const mockAsyncFunction = vi.fn().mockResolvedValue(mockData);
    const { result } = renderHook(() => useAsync(mockAsyncFunction));

    await act(async () => {
      await result.current.execute("arg1", "arg2");
    });

    expect(mockAsyncFunction).toHaveBeenCalledWith("arg1", "arg2");
  });

  it("should handle async operation failure", async () => {
    const mockError = new Error("Test error");
    const mockAsyncFunction = vi.fn().mockRejectedValue(mockError);
    const { result } = renderHook(() => useAsync(mockAsyncFunction));

    await act(async () => {
      try {
        await result.current.execute();
      } catch (error) {
        // Expected to throw
      }
    });

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe("Test error");
  });

  it("should set loading state during execution", async () => {
    let resolvePromise: (value: any) => void;
    const mockAsyncFunction = vi.fn().mockImplementation(() => {
      return new Promise((resolve) => {
        resolvePromise = resolve;
      });
    });

    const { result } = renderHook(() => useAsync(mockAsyncFunction));

    act(() => {
      result.current.execute();
    });

    // Should be loading
    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBeNull();

    await act(async () => {
      resolvePromise({ data: "test" });
    });

    // Should no longer be loading
    expect(result.current.loading).toBe(false);
  });

  it("should reset state correctly", () => {
    const mockAsyncFunction = vi.fn();
    const { result } = renderHook(() => useAsync(mockAsyncFunction));

    // Set some state
    act(() => {
      result.current.reset();
    });

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("should clear error on new execution", async () => {
    const mockAsyncFunction = vi
      .fn()
      .mockRejectedValueOnce(new Error("First error"))
      .mockResolvedValueOnce({ data: "success" });

    const { result } = renderHook(() => useAsync(mockAsyncFunction));

    // First execution fails
    await act(async () => {
      try {
        await result.current.execute();
      } catch (error) {
        // Expected to throw
      }
    });

    expect(result.current.error).toBe("First error");

    // Second execution succeeds
    await act(async () => {
      await result.current.execute();
    });

    expect(result.current.error).toBeNull();
    expect(result.current.data).toEqual({ data: "success" });
  });
});

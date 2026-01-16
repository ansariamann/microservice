import { useState, useCallback } from "react";
import { getErrorMessage } from "../utils/errorHandler";

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export interface UseAsyncReturn<T> extends AsyncState<T> {
  execute: (...args: any[]) => Promise<T | undefined>;
  reset: () => void;
}

/**
 * Custom hook for managing async operations with loading and error states
 */
export const useAsync = <T = any>(
  asyncFunction: (...args: any[]) => Promise<T>,
  immediate = false
): UseAsyncReturn<T> => {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: immediate,
    error: null,
  });

  const execute = useCallback(
    async (...args: any[]): Promise<T | undefined> => {
      setState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const result = await asyncFunction(...args);
        setState({ data: result, loading: false, error: null });
        return result;
      } catch (error) {
        const errorMessage = getErrorMessage(error);
        setState({ data: null, loading: false, error: errorMessage });
        throw error;
      }
    },
    [asyncFunction]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
};

export default useAsync;

import { useState, useEffect, useCallback } from "react";

export interface GpuStatus {
  gpu_available: boolean;
  vram_used_mb: number | null;
  vram_total_mb: number | null;
  percent_used: number | null;
  models_loaded: string[];
}

const GPU_ENDPOINT = "/api/health/gpu";
const POLL_INTERVAL_MS = 30_000; // 30 seconds

async function fetchGpuStatus(): Promise<GpuStatus> {
  const res = await fetch(GPU_ENDPOINT);
  if (!res.ok) {
    return {
      gpu_available: false,
      vram_used_mb: null,
      vram_total_mb: null,
      percent_used: null,
      models_loaded: [],
    };
  }
  return res.json() as Promise<GpuStatus>;
}

export function useGpuStatus() {
  const [status, setStatus] = useState<GpuStatus>({
    gpu_available: false,
    vram_used_mb: null,
    vram_total_mb: null,
    percent_used: null,
    models_loaded: [],
  });

  const refresh = useCallback(async () => {
    try {
      const data = await fetchGpuStatus();
      setStatus(data);
    } catch (err) {
      // Non-blocking — keep existing state on network errors
      console.warn("[useGpuStatus] Failed to fetch GPU status:", err);
    }
  }, []);

  useEffect(() => {
    // Initial fetch
    void refresh();

    const interval = setInterval(() => {
      void refresh();
    }, POLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [refresh]);

  return status;
}

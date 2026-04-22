import { useState, useEffect } from "react";

interface PatchStatusData {
  current: string | null;
  latest_available: string | null;
  is_stale: boolean;
  ingest_status: string;
  last_ingested: string | null;
  patch_notes_url: string | null;
}

export function PatchStatus() {
  const [status, setStatus] = useState<PatchStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);

  const fetchStatus = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/patch/status");
      if (res.ok) {
        setStatus(await res.json());
      }
    } catch {
      // silently ignore — patch status is non-critical
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Refresh every 30 minutes
    const interval = setInterval(fetchStatus, 30 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const handleCheck = async () => {
    setChecking(true);
    await fetchStatus();
    setChecking(false);
  };

  if (loading && !status) {
    return (
      <span
        style={{
          fontSize: "0.7rem",
          color: "var(--muted-foreground, #6b7280)",
          display: "inline-flex",
          alignItems: "center",
          gap: "4px",
        }}
      >
        checking...
      </span>
    );
  }

  if (!status?.current) {
    return null;
  }

  const isStale = status.is_stale;

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        flexShrink: 0,
      }}
    >
      <span
        style={{
          fontSize: "0.7rem",
          fontFamily: "monospace",
          padding: "1px 6px",
          borderRadius: "4px",
          border: `1px solid ${isStale ? "#a16207" : "#15803d"}`,
          color: isStale ? "#fbbf24" : "#4ade80",
          backgroundColor: isStale ? "rgba(161,98,7,0.15)" : "rgba(21,128,61,0.15)",
          lineHeight: "1.4",
        }}
      >
        Patch {status.current}
      </span>
      {isStale && (
        <span
          style={{
            fontSize: "0.65rem",
            color: "#fbbf24",
          }}
        >
          {status.latest_available} available
        </span>
      )}
      {!isStale && (
        <span
          style={{
            fontSize: "0.65rem",
            color: "#4ade80",
          }}
        >
          up to date
        </span>
      )}
      <button
        onClick={handleCheck}
        disabled={checking}
        title="Check for updates"
        style={{
          fontSize: "0.7rem",
          color: "var(--muted-foreground, #6b7280)",
          background: "none",
          border: "none",
          cursor: checking ? "wait" : "pointer",
          padding: "2px 4px",
          borderRadius: "3px",
          opacity: checking ? 0.5 : 1,
          transition: "color 0.15s, opacity 0.15s",
          lineHeight: 1,
        }}
      >
        {checking ? "..." : "\u21bb"}
      </button>
    </span>
  );
}

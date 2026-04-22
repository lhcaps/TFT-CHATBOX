import { useGpuStatus, type GpuStatus } from "../hooks/useGpuStatus";

interface GpuBadgeProps {
  status: GpuStatus;
}

export function GpuBadge({ status }: GpuBadgeProps) {
  if (!status.gpu_available) {
    return (
      <span
        title="GPU status unavailable"
        style={{
          fontSize: "0.7rem",
          color: "var(--muted-foreground, #6b7280)",
          display: "inline-flex",
          alignItems: "center",
          gap: "4px",
        }}
      >
        <span
          style={{
            display: "inline-block",
            width: 6,
            height: 6,
            borderRadius: "50%",
            backgroundColor: "#6b7280",
          }}
        />
        GPU N/A
      </span>
    );
  }

  const used = status.vram_used_mb ?? 0;
  const total = status.vram_total_mb ?? 1;
  const pct = status.percent_used ?? 0;

  const color =
    pct > 80 ? "#ef4444" : pct > 60 ? "#eab308" : "#22c55e";

  return (
    <span
      title={`${used} / ${total} MB VRAM · ${status.models_loaded.join(", ") || "no models loaded"}`}
      style={{
        fontSize: "0.7rem",
        color: "var(--muted-foreground, #6b7280)",
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        cursor: "default",
      }}
    >
      <span
        style={{
          display: "inline-block",
          width: 6,
          height: 6,
          borderRadius: "50%",
          backgroundColor: color,
          flexShrink: 0,
        }}
      />
      {used} / {total} MB
    </span>
  );
}

export function GpuStatusBadge() {
  const status = useGpuStatus();
  return <GpuBadge status={status} />;
}

"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif",
          background: "linear-gradient(180deg, #f8fafc 0%, #f0fdfa 55%, #ecfeff 100%)",
          color: "#0f172a",
        }}
      >
        <div
          style={{
            maxWidth: 420,
            padding: 32,
            borderRadius: 12,
            border: "1px solid #99f6e4",
            background: "#ffffff",
            textAlign: "center",
            boxShadow: "0 10px 30px rgba(15, 118, 110, 0.08)",
          }}
        >
          <p
            style={{
              margin: 0,
              color: "#0d9488",
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: "0.18em",
              textTransform: "uppercase",
            }}
          >
            Critical error
          </p>
          <h1 style={{ margin: "12px 0 8px", fontSize: 24 }}>Application failed to render</h1>
          <p style={{ margin: 0, color: "#64748b", fontSize: 14 }}>
            A root-level failure occurred. Retrying usually recovers the session.
          </p>
          {error.digest ? (
            <p
              style={{
                marginTop: 12,
                color: "#94a3b8",
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
                fontSize: 12,
              }}
            >
              Ref: {error.digest}
            </p>
          ) : null}
          <button
            type="button"
            onClick={reset}
            style={{
              marginTop: 24,
              border: 0,
              borderRadius: 8,
              background: "#0d9488",
              color: "#ffffff",
              padding: "10px 18px",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}

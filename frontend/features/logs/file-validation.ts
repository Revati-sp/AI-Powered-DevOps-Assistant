import { MAX_UPLOAD_MB } from "@/lib/constants/app";

export const ALLOWED_LOG_EXTENSIONS = [".log", ".txt"] as const;

export type LogFileValidationError = {
  code: "empty" | "extension" | "size" | "binary" | "encoding";
  message: string;
};

export type LogFileValidationResult =
  { ok: true; file: File } | { ok: false; error: LogFileValidationError };

const MAX_BYTES = MAX_UPLOAD_MB * 1024 * 1024;

function hasAllowedExtension(name: string): boolean {
  const lower = name.toLowerCase();
  return ALLOWED_LOG_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

/**
 * Client-side preflight for log uploads (.log/.txt, size, non-empty).
 * Backend validation remains authoritative.
 */
export function validateLogFile(file: File | null | undefined): LogFileValidationResult {
  if (!file || file.size === 0) {
    return {
      ok: false,
      error: {
        code: "empty",
        message: "Select a non-empty .log or .txt file.",
      },
    };
  }

  if (!hasAllowedExtension(file.name)) {
    return {
      ok: false,
      error: {
        code: "extension",
        message: "Unsupported file type. Only .log and .txt files are allowed.",
      },
    };
  }

  if (file.size > MAX_BYTES) {
    return {
      ok: false,
      error: {
        code: "size",
        message: `File exceeds maximum size of ${MAX_UPLOAD_MB} MB.`,
      },
    };
  }

  return { ok: true, file };
}

/**
 * Optional deeper check after reading bytes (null bytes / binary-ish).
 */
export function looksLikeBinaryText(sample: string): boolean {
  if (!sample) return false;
  if (sample.includes("\0")) return true;
  const slice = sample.slice(0, 8192);
  let disallowed = 0;
  for (let i = 0; i < slice.length; i += 1) {
    const code = slice.charCodeAt(i);
    const allowed = code === 9 || code === 10 || code === 13 || (code >= 0x20 && code < 0x7f);
    if (!allowed) disallowed += 1;
  }
  return disallowed / slice.length > 0.3;
}

export const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "AI-Powered DevOps Assistant";

export const LLM_PROVIDERS = ["gemini", "llama", "mistral"] as const;
export type LlmProvider = (typeof LLM_PROVIDERS)[number];

export const CHAT_MESSAGE_MAX = 8000;
export const MAX_UPLOAD_MB = 5;
export const PASSWORD_MIN = 12;
export const PASSWORD_MAX = 128;

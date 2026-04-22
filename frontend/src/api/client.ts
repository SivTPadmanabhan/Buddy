const BASE_URL = "http://localhost:8000";

export interface Source {
  source_file: string | null;
  chunk_index: number | null;
  score: number | null;
}

export interface ChatResponse {
  response: string;
  sources: Source[];
}

export interface LimitError {
  error: string;
  limit_reached: true;
}

export interface SyncResponse {
  files_processed: number;
  chunks_upserted: number;
  files_skipped: number;
  limit_reached: boolean;
  errors: string[];
}

export interface SyncStatus {
  last_sync: string | null;
  files_synced: number;
  vector_usage: {
    used: number;
    limit: number;
    percent: number;
  };
}

export interface UsageEntry {
  used: number;
  limit: number;
  percent: number;
}

export interface UsageStatus {
  gemini_requests: UsageEntry;
  gemini_tokens: UsageEntry;
  pinecone_vectors: UsageEntry;
}

export interface HealthResponse {
  status: string;
  usage: UsageStatus;
  services: Record<string, unknown>;
}

export class BuddyApiError extends Error {
  status: number;
  limitReached: boolean;

  constructor(message: string, status: number, limitReached: boolean = false) {
    super(message);
    this.status = status;
    this.limitReached = limitReached;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const body = await res.json();

  if (!res.ok) {
    const isLimit = body?.limit_reached === true;
    throw new BuddyApiError(
      body?.error || body?.detail || `Request failed (${res.status})`,
      res.status,
      isLimit,
    );
  }

  return body as T;
}

export const api = {
  chat(message: string): Promise<ChatResponse> {
    return request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
  },

  triggerSync(): Promise<SyncResponse> {
    return request<SyncResponse>("/sync", { method: "POST" });
  },

  getSyncStatus(): Promise<SyncStatus> {
    return request<SyncStatus>("/sync/status");
  },

  getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>("/health");
  },

  getUsage(): Promise<UsageStatus> {
    return request<UsageStatus>("/usage");
  },
};

import {
  AuditProgress,
  DisputeEvaluationResponse,
  DisputeScenario,
  FlaggedLeaseRisk,
  LeaseAuditResponse,
} from "./types";

/** Backend base URL. Set NEXT_PUBLIC_API_URL in production; falls back to the local FastAPI dev server. */
export const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

const CONNECT_TIMEOUT_MS = 20_000; // time allowed for the server to start responding (cold starts on free tiers)
const STREAM_IDLE_TIMEOUT_MS = 45_000; // max silence between SSE chunks

/** Error shown in the retry banner. `retryable` is true for network / timeout / 5xx failures. */
export class ApiError extends Error {
  retryable: boolean;
  constructor(message: string, retryable = true) {
    super(message);
    this.name = "ApiError";
    this.retryable = retryable;
  }
}

function describeNetworkFailure(err: unknown): ApiError {
  if (err instanceof ApiError) return err;
  if (err instanceof DOMException && err.name === "AbortError") {
    return new ApiError("The LeaseGuard API took too long to respond. It may be waking up from sleep.", true);
  }
  return new ApiError(`Could not reach the LeaseGuard API at ${API_BASE}. Check your connection or try again.`, true);
}

async function request(path: string, init: RequestInit = {}, timeoutMs = CONNECT_TIMEOUT_MS): Promise<Response> {
  const controller = new AbortController();
  const outer = init.signal;
  if (outer) outer.addEventListener("abort", () => controller.abort(), { once: true });
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, { ...init, signal: controller.signal });
    if (!res.ok) {
      let detail = `${res.status} ${res.statusText}`;
      try {
        const body = await res.json();
        if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      } catch {
        /* non-JSON error body */
      }
      throw new ApiError(detail, res.status >= 500 || res.status === 429);
    }
    return res;
  } catch (err) {
    if (outer?.aborted) throw err; // caller cancelled: not an error to display
    throw describeNetworkFailure(err);
  } finally {
    clearTimeout(timer);
  }
}

export interface AuditHandlers {
  onProgress: (p: AuditProgress) => void;
  onClause: (risk: FlaggedLeaseRisk) => void;
}

/**
 * Streams a lease audit over Server-Sent Events. POST (not EventSource) so a PDF can be uploaded.
 * Resolves with the final LeaseAuditResponse delivered by the `complete` event.
 */
export async function streamLeaseAudit(
  handlers: AuditHandlers,
  file?: File,
  signal?: AbortSignal
): Promise<LeaseAuditResponse> {
  const form = new FormData();
  if (file) form.append("file", file);
  const res = await request("/api/v1/leases/analyze-stream", { method: "POST", body: form, signal });
  if (!res.body) throw new ApiError("Streaming is not supported by this browser.", false);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: LeaseAuditResponse | null = null;

  const dispatch = (raw: string) => {
    let event = "message";
    const dataLines: string[] = [];
    for (const line of raw.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart());
    }
    if (!dataLines.length) return;
    const data = JSON.parse(dataLines.join("\n"));
    if (event === "progress") handlers.onProgress(data as AuditProgress);
    else if (event === "clause_analyzed") handlers.onClause(data as FlaggedLeaseRisk);
    else if (event === "complete") result = data as LeaseAuditResponse;
    else if (event === "error") throw new ApiError(data.detail || "Audit failed", false);
  };

  for (;;) {
    let idle: ReturnType<typeof setTimeout> | undefined;
    const chunk = await Promise.race([
      reader.read(),
      new Promise<never>((_, reject) => {
        idle = setTimeout(
          () => reject(new ApiError("The audit stream stalled. Please retry.", true)),
          STREAM_IDLE_TIMEOUT_MS
        );
      }),
    ]).catch((err) => {
      reader.cancel().catch(() => undefined);
      throw err instanceof ApiError ? err : describeNetworkFailure(err);
    });
    clearTimeout(idle);
    if (chunk.done) break;
    buffer += decoder.decode(chunk.value, { stream: true }).replace(/\r\n/g, "\n");
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      dispatch(buffer.slice(0, sep));
      buffer = buffer.slice(sep + 2);
    }
  }
  if (!result) throw new ApiError("The audit stream ended before completing. Please retry.", true);
  return result;
}

export async function fetchSampleScenario(signal?: AbortSignal): Promise<DisputeScenario> {
  const res = await request("/api/v1/disputes/sample-scenario", { signal });
  return (await res.json()) as DisputeScenario;
}

export async function evaluateDispute(
  scenario: DisputeScenario,
  signal?: AbortSignal
): Promise<DisputeEvaluationResponse> {
  const res = await request("/api/v1/disputes/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(scenario),
    signal,
  });
  return (await res.json()) as DisputeEvaluationResponse;
}

export async function downloadDemandLetterPdf(scenario: DisputeScenario): Promise<Blob> {
  const res = await request("/api/v1/disputes/demand-letter", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ evaluation: scenario }),
  });
  const blob = await res.blob();
  if (blob.type !== "application/pdf") throw new ApiError("The server did not return a PDF.", true);
  return blob;
}

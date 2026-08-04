import {
  getSessionGeneration,
  invalidateSession,
  setAccessTokenIfCurrent,
} from "@/lib/auth/token-storage";

const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

function normalizeApiBaseUrl(baseUrl: string) {
  try {
    return new URL(baseUrl).toString().replace(/\/+$/, "");
  } catch {
    return DEFAULT_API_BASE_URL;
  }
}

export const API_BASE_URL = normalizeApiBaseUrl(
  process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL,
);

export type ApiMethod = "GET" | "POST" | "PATCH" | "DELETE";

export type ApiRequestOptions = {
  method?: ApiMethod;
  token?: string;
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined | null>;
  headers?: HeadersInit;
  cache?: RequestCache;
  credentials?: RequestCredentials;
  csrf?: boolean;
  retryAuth?: boolean;
};

export class APIError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data: unknown = null) {
    super(message);
    this.name = "APIError";
    this.status = status;
    this.data = data;
  }
}

function buildUrl(path: string, params?: ApiRequestOptions["params"]) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(`${API_BASE_URL}${normalizedPath}`);

  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });

  return url.toString();
}

async function parseResponse(response: Response) {
  const contentType = response.headers.get("content-type");

  if (response.status === 204) {
    return null;
  }

  if (contentType?.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

let csrfToken: string | null = null;
let csrfPromise: Promise<string> | null = null;

async function ensureCsrfToken() {
  if (csrfToken) {
    return csrfToken;
  }
  if (!csrfPromise) {
    csrfPromise = fetch(buildUrl("/accounts/csrf/"), {
      method: "GET",
      credentials: "include",
      cache: "no-store",
      headers: { Accept: "application/json" },
    })
      .then(async (response) => {
        const data = (await parseResponse(response)) as {
          csrf_token?: string;
        };
        if (!response.ok || !data.csrf_token) {
          throw new APIError("CSRF bootstrap failed.", response.status, data);
        }
        csrfToken = data.csrf_token;
        return csrfToken;
      })
      .finally(() => {
        csrfPromise = null;
      });
  }
  return csrfPromise;
}

let refreshPromise: Promise<string> | null = null;

export async function refreshSession() {
  if (!refreshPromise) {
    const generation = getSessionGeneration();
    refreshPromise = (async () => {
      try {
        const token = await ensureCsrfToken();
        const response = await fetch(buildUrl("/auth/token/refresh/"), {
          method: "POST",
          credentials: "include",
          cache: "no-store",
          headers: {
            Accept: "application/json",
            "X-CSRFToken": token,
          },
        });
        const data = (await parseResponse(response)) as { access?: string };
        if (!response.ok || !data.access) {
          throw new APIError(
            "Authentication session is unavailable.",
            response.status,
            data,
          );
        }
        if (!setAccessTokenIfCurrent(data.access, generation)) {
          throw new APIError("Stale authentication response ignored.", 401);
        }
        return data.access;
      } catch (error) {
        if (generation === getSessionGeneration()) {
          invalidateSession();
        }
        throw error;
      }
    })().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

export async function apiFetch<T>(
  path: string,
  {
    method = "GET",
    token,
    body,
    params,
    headers,
    cache = "no-store",
    credentials = "omit",
    csrf = false,
    retryAuth = true,
  }: ApiRequestOptions = {},
): Promise<T> {
  const url = buildUrl(path, params);
  const hasBody = body !== undefined && body !== null;

  async function perform(activeToken?: string) {
    const requestHeaders = new Headers(headers);
    requestHeaders.set("Accept", "application/json");
    if (hasBody) {
      requestHeaders.set("Content-Type", "application/json");
    }
    if (activeToken) {
      requestHeaders.set("Authorization", `Bearer ${activeToken}`);
    }
    if (csrf) {
      requestHeaders.set("X-CSRFToken", await ensureCsrfToken());
    }
    return fetch(url, {
      method,
      headers: requestHeaders,
      body: hasBody ? JSON.stringify(body) : undefined,
      cache,
      credentials,
    });
  }

  let response = await perform(token);
  if (response.status === 401 && token && retryAuth) {
    const refreshedAccess = await refreshSession();
    response = await perform(refreshedAccess);
  }

  const data = await parseResponse(response);
  if (!response.ok) {
    const message =
      typeof data === "object" && data && "detail" in data
        ? String(data.detail)
        : `درخواست با خطا مواجه شد. کد خطا: ${response.status}`;
    throw new APIError(message, response.status, data);
  }
  return data as T;
}

export const apiClient = {
  get: <T>(path: string, options?: Omit<ApiRequestOptions, "method" | "body">) =>
    apiFetch<T>(path, { ...options, method: "GET" }),
  post: <T>(
    path: string,
    body?: unknown,
    options?: Omit<ApiRequestOptions, "method" | "body">,
  ) => apiFetch<T>(path, { ...options, method: "POST", body }),
  patch: <T>(
    path: string,
    body?: unknown,
    options?: Omit<ApiRequestOptions, "method" | "body">,
  ) => apiFetch<T>(path, { ...options, method: "PATCH", body }),
  delete: <T>(
    path: string,
    options?: Omit<ApiRequestOptions, "method" | "body">,
  ) => apiFetch<T>(path, { ...options, method: "DELETE" }),
};

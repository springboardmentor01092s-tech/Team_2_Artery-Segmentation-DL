export function apiUrl(path: string): string {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://") || path.startsWith("blob:") || path.startsWith("data:")) {
    return path;
  }
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  if (typeof window !== "undefined") {
    const port = window.location.port;
    if (port && port !== "8000") {
      return `${window.location.protocol}//${window.location.hostname}:8000${cleanPath}`;
    }
  }
  return cleanPath;
}

export async function request<T>(
  path: string, token?: string, body?: unknown, method = "GET",
): Promise<T> {
  const url = apiUrl(path);
  const response = await fetch(url, {
    method,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const detail = error.detail;
    const message = Array.isArray(detail)
      ? detail.map((item: { loc?: (string | number)[]; msg?: string }) => `${item.loc?.filter(part => part !== "body").join(" · ") || "Input"}: ${item.msg || "Invalid value"}`).join("; ")
      : typeof detail === "string" ? detail : `Request failed (${response.status})`;
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}


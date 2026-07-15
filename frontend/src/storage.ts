export function readLocal<T>(key: string, fallback: T): T {
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) as T : fallback;
  } catch {
    return fallback;
  }
}

export function writeLocal(key: string, value: unknown) {
  localStorage.setItem(key, JSON.stringify(value));
}

export function resetAizenStorage() {
  Object.keys(localStorage).filter((key) => key.startsWith("aizen-")).forEach((key) => localStorage.removeItem(key));
}

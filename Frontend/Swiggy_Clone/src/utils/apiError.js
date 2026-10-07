// FastAPI's error body is {"detail": "a string"} for a raised HTTPException
// (every intentional error in Backend/main.py), but {"detail": [{"msg": "...",
// ...}, ...]} for its own request-validation failures (422) -- using that
// array directly as an Error message renders as "[object Object]" instead
// of anything readable.
export function extractErrorMessage(data, fallback) {
  const detail = data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
  }
  return fallback;
}

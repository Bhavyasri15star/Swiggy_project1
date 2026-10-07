// Backend base URL. Override per-environment via REACT_APP_API_URL
// (e.g. in a .env / .env.local file, or as a shell env var before `npm start`).
// Falls back to localhost for normal single-machine development.
export const API_BASE_URL =
  process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

// AuthService (Express + Prisma) base URL. Same override convention as above.
export const AUTH_BASE_URL =
  process.env.REACT_APP_AUTH_URL || "http://127.0.0.1:4000";

// Mapbox token for the address-picker map iframe (Address.jsx). No safe
// fallback value exists -- get your own free token at mapbox.com and set
// REACT_APP_MAPBOX_TOKEN. Without it the map iframe just shows an error
// tile; it's decorative only, not required for placing an order.
export const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN || "";

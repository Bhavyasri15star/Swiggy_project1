require("dotenv").config();

const express = require("express");
const cors = require("cors");
const { Prisma } = require("@prisma/client");
const authRoutes = require("./routes/auth");

const app = express();
const PORT = process.env.PORT || 4000;

const allowedOrigins = (process.env.CORS_ORIGINS || "")
  .split(",")
  .map((o) => o.trim())
  .filter(Boolean);

app.use(
  cors({
    origin: allowedOrigins.length ? allowedOrigins : true,
  })
);
app.use(express.json());

app.get("/", (req, res) => {
  res.json({ message: "Auth service is running" });
});

app.use("/auth", authRoutes);

// Last-resort error handler — every route in auth.js is wrapped in
// asyncHandler (see src/middleware/asyncHandler.js), which forwards a
// rejected promise here via next(err) instead of hanging the request
// forever. Classify what we can so a DB outage doesn't look identical to
// a genuine bug: connection failures get 503 (transient, safe to retry),
// unique-constraint conflicts get 409, everything else falls back to a
// generic 500 — never leaking internal error details to the client.
app.use((err, req, res, next) => {
  console.error(err);

  // P1xxx = Prisma can't reach/initialize against the database at all.
  const isConnectionFailure =
    err instanceof Prisma.PrismaClientInitializationError ||
    (err instanceof Prisma.PrismaClientKnownRequestError && err.code?.startsWith("P1"));
  if (isConnectionFailure) {
    return res.status(503).json({ error: "Service temporarily unavailable — please try again shortly" });
  }

  // P2002 = unique constraint violation (e.g. duplicate email slipping
  // past the app-level check via a race condition).
  if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === "P2002") {
    return res.status(409).json({ error: "That value is already in use" });
  }

  res.status(500).json({ error: "Internal server error" });
});

// Defense in depth: asyncHandler covers every route, but this catches
// anything that somehow still slips through (e.g. a future route added
// without it) so it's at least logged instead of silently crashing.
process.on("unhandledRejection", (err) => {
  console.error("Unhandled rejection (a route is likely missing asyncHandler):", err);
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`Auth service listening on http://0.0.0.0:${PORT}`);
});

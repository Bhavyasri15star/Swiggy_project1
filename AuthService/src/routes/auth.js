const express = require("express");
const crypto = require("crypto");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const prisma = require("../lib/prisma");
const { requireAuth } = require("../middleware/auth");
const { sendOtpEmail } = require("../lib/email");
const { asyncHandler } = require("../middleware/asyncHandler");

const router = express.Router();

const JWT_SECRET = process.env.JWT_SECRET;
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || "1h";
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const OTP_TTL_MS = 10 * 60 * 1000;

function signToken(user) {
  return jwt.sign(
    { sub: user.id, email: user.email, name: user.name },
    JWT_SECRET,
    { expiresIn: JWT_EXPIRES_IN }
  );
}

function publicUser(user) {
  return { id: user.id, email: user.email, name: user.name, createdAt: user.createdAt };
}

router.post("/signup", asyncHandler(async (req, res) => {
  const { email, password, name } = req.body || {};

  if (typeof email !== "string" || !EMAIL_RE.test(email)) {
    return res.status(400).json({ error: "A valid email is required" });
  }
  if (typeof password !== "string" || password.length < 8) {
    return res.status(400).json({ error: "Password must be at least 8 characters" });
  }

  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) {
    return res.status(409).json({ error: "An account with this email already exists" });
  }

  const passwordHash = await bcrypt.hash(password, 10);
  const user = await prisma.user.create({
    data: { email, passwordHash, name: typeof name === "string" ? name : null },
  });

  const token = signToken(user);
  return res.status(201).json({ token, user: publicUser(user) });
}));

router.post("/login", asyncHandler(async (req, res) => {
  const { email, password } = req.body || {};

  if (typeof email !== "string" || typeof password !== "string") {
    return res.status(400).json({ error: "Email and password are required" });
  }

  const user = await prisma.user.findUnique({ where: { email } });
  // Same error for "no such user" and "wrong password" — don't leak which one.
  const valid = user ? await bcrypt.compare(password, user.passwordHash) : false;
  if (!valid) {
    return res.status(401).json({ error: "Invalid email or password" });
  }

  const token = signToken(user);
  return res.json({ token, user: publicUser(user) });
}));

router.post("/otp/request", asyncHandler(async (req, res) => {
  const { email } = req.body || {};
  if (typeof email !== "string" || !EMAIL_RE.test(email)) {
    return res.status(400).json({ error: "A valid email is required" });
  }

  // Invalidate any earlier unused code for this email before issuing a new
  // one, so only the most recently sent code ever works.
  await prisma.emailOtp.deleteMany({ where: { email } });

  const code = crypto.randomInt(100000, 1000000).toString(); // 6 digits, zero-padding not needed at this range
  await prisma.emailOtp.create({
    data: { email, code, expiresAt: new Date(Date.now() + OTP_TTL_MS) },
  });

  const result = await sendOtpEmail(email, code);
  return res.json({
    message: "OTP sent",
    // Only present when Brevo isn't configured — lets you test the flow
    // without needing a real inbox. A configured deployment never includes this.
    ...(result.devFallback ? { devCode: code } : {}),
  });
}));

router.post("/otp/verify", asyncHandler(async (req, res) => {
  const { email, code } = req.body || {};
  if (typeof email !== "string" || typeof code !== "string") {
    return res.status(400).json({ error: "Email and code are required" });
  }

  const otp = await prisma.emailOtp.findFirst({ where: { email, code } });
  if (!otp || otp.expiresAt < new Date()) {
    return res.status(401).json({ error: "Invalid or expired code" });
  }

  // Single-use: consume it immediately so it can't be replayed.
  await prisma.emailOtp.delete({ where: { id: otp.id } });

  let user = await prisma.user.findUnique({ where: { email } });
  if (!user) {
    // First successful verify for this email creates the account — same
    // passwordless-signup pattern phone-OTP apps use. No usable password;
    // this user can only sign in via OTP unless they set one later.
    const passwordHash = await bcrypt.hash(crypto.randomUUID(), 10);
    user = await prisma.user.create({ data: { email, passwordHash } });
  }

  const token = signToken(user);
  return res.json({ token, user: publicUser(user) });
}));

router.get("/me", requireAuth, asyncHandler(async (req, res) => {
  const user = await prisma.user.findUnique({ where: { id: req.user.sub } });
  if (!user) {
    return res.status(404).json({ error: "User not found" });
  }
  return res.json({ user: publicUser(user) });
}));

module.exports = router;

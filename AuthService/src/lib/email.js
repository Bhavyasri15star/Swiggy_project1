// Sends the OTP email via Mailjet's transactional email API (free tier, no
// card required — https://app.mailjet.com, Account Settings > API Key
// Management). Mailjet uses a public/private key pair as HTTP Basic Auth,
// unlike single-key providers.
// If MAILJET_API_KEY / MAILJET_API_SECRET aren't set, falls back to logging
// the code to this process's console instead of failing — lets the whole
// OTP flow be developed and tested before Mailjet is actually configured.

const MAILJET_API_KEY = process.env.MAILJET_API_KEY;
const MAILJET_API_SECRET = process.env.MAILJET_API_SECRET;
const MAILJET_SENDER_EMAIL = process.env.MAILJET_SENDER_EMAIL;
const MAILJET_SENDER_NAME = process.env.MAILJET_SENDER_NAME || "Swiggy Clone";

async function sendOtpEmail(toEmail, code) {
  if (!MAILJET_API_KEY || !MAILJET_API_SECRET) {
    console.log(`[DEV] No MAILJET_API_KEY/MAILJET_API_SECRET set — OTP for ${toEmail}: ${code}`);
    return { delivered: false, devFallback: true };
  }

  const basicAuth = Buffer.from(`${MAILJET_API_KEY}:${MAILJET_API_SECRET}`).toString("base64");

  const res = await fetch("https://api.mailjet.com/v3.1/send", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Basic ${basicAuth}`,
    },
    body: JSON.stringify({
      Messages: [
        {
          From: { Email: MAILJET_SENDER_EMAIL, Name: MAILJET_SENDER_NAME },
          To: [{ Email: toEmail }],
          Subject: "Your sign-in code",
          HTMLPart: `<p>Your verification code is <strong>${code}</strong>. It expires in 10 minutes.</p>`,
        },
      ],
    }),
  });

  const body = await res.json().catch(() => ({}));
  const status = body?.Messages?.[0]?.Status;
  if (!res.ok || status !== "success") {
    throw new Error(`Mailjet API error (${res.status}): ${JSON.stringify(body)}`);
  }

  return { delivered: true, devFallback: false };
}

module.exports = { sendOtpEmail };

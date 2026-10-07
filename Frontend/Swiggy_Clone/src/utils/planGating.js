import { getStoredAuth } from "./authApi";

const TRIAL_DURATION_DAYS = 14;

// Scoped to whoever is currently logged in, same reasoning and pattern as
// cartKey.js's getCartKey() -- otherwise two accounts on the same browser
// would share one trial/plan status.
function planKey() {
  const auth = getStoredAuth();
  return auth ? `Plan_${auth.user.id}` : "Plan_guest";
}

function trialUsedKey() {
  const auth = getStoredAuth();
  return auth ? `trial_used_${auth.user.id}` : "trial_used_guest";
}

export function hasUsedTrial() {
  const value = localStorage.getItem(trialUsedKey());
  return value === "true";
}

export function startFreeTrial() {
  if (hasUsedTrial()) {
    return { success: false, reason: "already_used" };
  }

  const trialStart = Date.now();
  const trialEnd = trialStart + TRIAL_DURATION_DAYS * 24 * 60 * 60 * 1000;
  const plan = { type: "free_trial", trialStart, trialEnd };
  localStorage.setItem(planKey(), JSON.stringify(plan));
  localStorage.setItem(trialUsedKey(), "true");
  return { success: true, plan };
}

export function activateBasicPlan() {
  const plan = { type: "basic" };
  localStorage.setItem(planKey(), JSON.stringify(plan));
  return plan;
}

export function cancelPlan() {
  localStorage.removeItem(planKey());
}

export function getPlanStatus() {
  const plan = JSON.parse(localStorage.getItem(planKey())) || null;

  if (!plan) {
    return { type: "none", isTrialActive: false, isPaidActive: false, daysLeft: 0, trialUsed: hasUsedTrial() };
  }

  if (plan.type === "basic") {
    return { type: "basic", isTrialActive: false, isPaidActive: true, daysLeft: 0, trialUsed: hasUsedTrial() };
  }

  if (plan.type === "free_trial") {
    const isTrialActive = Date.now() < plan.trialEnd;
    const daysLeft = isTrialActive
      ? Math.ceil((plan.trialEnd - Date.now()) / (24 * 60 * 60 * 1000))
      : 0;
    return { type: "free_trial", isTrialActive, isPaidActive: false, daysLeft, trialUsed: hasUsedTrial() };
  }

  return { type: "none", isTrialActive: false, isPaidActive: false, daysLeft: 0, trialUsed: hasUsedTrial() };
}
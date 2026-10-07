import { getPlanStatus, startFreeTrial, activateBasicPlan, cancelPlan } from "../utils/planGating";
import { getStoredAuth } from "../utils/authApi";
import "./CheckoutPage/PaymentDetails.css";

export function PlanButtons() {
  // Plan/trial state lives in localStorage with no tie to the signed-in
  // user at all -- without this check, a signed-out visitor could see and
  // click "Start Free Trial" on checkout.
  const auth = getStoredAuth();
  const { type, isTrialActive, isPaidActive, daysLeft, trialUsed } = getPlanStatus();

  if (!auth) {
    return null;
  }

  const handleStartTrial = () => {
    const result = startFreeTrial();
    if (!result.success) {
      alert("You've already used your free trial. Please subscribe to Basic to continue.");
      return;
    }
    window.location.reload();
  };

  const handleSubscribeBasic = () => {
    if (isTrialActive) {
      alert(`You still have ${daysLeft} day(s) left on your free trial. You can subscribe once it ends.`);
      return;
    }
    // Razorpay checkout would normally go here before calling activateBasicPlan()
    activateBasicPlan();
    window.location.reload();
  };

  const handleCancel = () => {
    cancelPlan();
    window.location.reload();
  };

  return (
    <div className="plan_buttons">
      {isTrialActive && (
        <span className="plan_status">Free trial — {daysLeft} day(s) left</span>
      )}
      {isPaidActive && (
        <span className="plan_status">Basic plan active 🎉</span>
      )}
      {type === "none" && trialUsed && (
        <span className="plan_status">Free trial already used</span>
      )}

      {type === "none" && !trialUsed && (
        <button className="trial_btn" onClick={handleStartTrial}>
          Start Free Trial
        </button>
      )}

      {!isTrialActive && (
        <button className="basic_btn" onClick={handleSubscribeBasic}>
          Subscribe to Basic
        </button>
      )}

      {isPaidActive && (
        <button className="cancel_btn" onClick={handleCancel}>
          Cancel Plan
        </button>
      )}
    </div>
  );
}
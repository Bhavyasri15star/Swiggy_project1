// A coupon applied in PaymentDetails.jsx needs to reach Address.jsx's actual
// "place the order" call (handleClick) -- the two are sibling components
// with no shared props, so (matching this app's existing pattern for
// cross-component state, e.g. getCartKey/foodId/Address) it's passed via
// localStorage instead.
const KEY = "appliedCoupon";

export function getAppliedCoupon() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || null;
  } catch {
    return null;
  }
}

export function setAppliedCoupon({ code, discount_amount }) {
  localStorage.setItem(KEY, JSON.stringify({ code, discount_amount }));
}

export function clearAppliedCoupon() {
  localStorage.removeItem(KEY);
}


const DAY_GATED_CATEGORIES = { "WEDNESDAY EXCLUSIVES": "Wednesday" };

export function isAvailableToday(item) {
  const requiredDay = DAY_GATED_CATEGORIES[item.category];
  if (!requiredDay) return true;
  const today = new Date().toLocaleDateString("en-US", { weekday: "long" });
  return today === requiredDay;
}

export function filterAvailableCartItems(cart) {
  if(!Array.isArray(cart)) return [];
  return cart.filter(isAvailableToday);
}

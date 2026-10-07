import { getStoredAuth } from "./authApi";

// The cart's localStorage key is scoped to whoever is currently logged in
// (via AuthService), so different accounts on the same browser don't share
// a cart. Anonymous browsing still works, under a shared guest key.
export function getCartKey() {
  const auth = getStoredAuth();
  return auth ? `Cart_${auth.user.id}` : "Cart_guest";
}

// Called right after a successful login/signup: carries over whatever was
// in the guest cart so items added before logging in aren't lost, but only
// if this user doesn't already have their own saved cart.
export function migrateGuestCartToUser(userId) {
  const userKey = `Cart_${userId}`;
  if (localStorage.getItem(userKey)) return; // user already has a cart, don't overwrite it

  const guestCart = localStorage.getItem("Cart_guest");
  if (guestCart) {
    localStorage.setItem(userKey, guestCart);
  }
}

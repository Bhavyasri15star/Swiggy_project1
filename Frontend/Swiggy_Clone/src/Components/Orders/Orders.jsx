import React, { useEffect, useState } from "react";
import { Navbar } from "../RestaurantPage/Navbar";
import { API_BASE_URL } from "../../config";
import { getStoredAuth, authFetch } from "../../utils/authApi";
import { extractErrorMessage } from "../../utils/apiError";
import "./Orders.css";

const CANCELLATION_WINDOW_MS = 10 * 60 * 1000;

function canCancel(order) {
  if (order.status !== "placed") return false;
  return Date.now() - new Date(order.created_at).getTime() <= CANCELLATION_WINDOW_MS;
}

export function Orders() {
  const auth = getStoredAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [cancellingId, setCancellingId] = useState(null);

  const fetchOrders = (from, to) => {
    setLoading(true);
    setError("");
    const params = new URLSearchParams();
    if (from) params.set("from_date", from);
    if (to) params.set("to_date", to);
    const qs = params.toString();

    authFetch(`${API_BASE_URL}/orders${qs ? `?${qs}` : ""}`)
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(extractErrorMessage(data, "Failed to load orders"));
        return data;
      })
      .then((data) => setOrders(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (auth) fetchOrders();
    else setLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (fromDate && toDate && fromDate > toDate) {
      alert("From date must not be after to date");
      return;
    }
    fetchOrders(fromDate, toDate);
  };

  const handleCancel = (orderId) => {
    setCancellingId(orderId);
    authFetch(`${API_BASE_URL}/orders/${orderId}/cancel`, { method: "POST" })
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(extractErrorMessage(data, "Failed to cancel order"));
        setOrders((prev) => prev.map((o) => (o.id === orderId ? data : o)));
      })
      .catch((err) => alert(err.message))
      .finally(() => setCancellingId(null));
  };

  if (!auth) {
    return (
      <>
        <Navbar />
        <div className="orders_page">
          <h2>My Orders</h2>
          <p>Please sign in from the nav bar above to see your order history.</p>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="orders_page">
        <h2>My Orders</h2>

        <form className="orders_filter" onSubmit={handleSearch}>
          <label>
            From
            <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
          </label>
          <label>
            To
            <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
          </label>
          <button type="submit">Search</button>
        </form>

        {loading ? (
          <p>Loading...</p>
        ) : error ? (
          <p className="orders_error">{error}</p>
        ) : orders.length === 0 ? (
          <p>No orders found{fromDate || toDate ? " for this date range" : ""}.</p>
        ) : (
          <div className="orders_list">
            {orders.map((order) => (
              <div className="order_card" key={order.id}>
                <div className="order_card_header">
                  <span>{new Date(order.created_at).toLocaleString()}</span>
                  <span className="order_total">&#8377;{order.total_amount.toFixed(2)}</span>
                </div>
                {order.items.map((item, idx) => (
                  <div className="order_item_line" key={idx}>
                    <span>
                      {item.item_name} &times; {item.quantity}
                      {item.restaurant_name && (
                        <span style={{ display: "block", fontSize: "12px", color: "gray" }}>
                          from {item.restaurant_name}
                        </span>
                      )}
                    </span>
                    <span>&#8377;{(item.price * item.quantity).toFixed(2)}</span>
                  </div>
                ))}
                {order.applied_coupon_code && (
                  <div className="order_item_line">
                    <span>Coupon ({order.applied_coupon_code})</span>
                    <span>&#8211; &#8377;{order.discount_amount.toFixed(2)}</span>
                  </div>
                )}
                {order.status !== "placed" && (
                  <p className={`order_status order_status_${order.status}`}>
                    {order.status === "cancelled" ? "Cancelled" : "Delivered"}
                  </p>
                )}
                {canCancel(order) && (
                  <button
                    className="cancel_order_btn"
                    disabled={cancellingId === order.id}
                    onClick={() => handleCancel(order.id)}
                  >
                    {cancellingId === order.id ? "Cancelling..." : "Cancel Order"}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

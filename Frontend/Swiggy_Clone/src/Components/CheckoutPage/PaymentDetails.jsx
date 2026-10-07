import React, { useState, useEffect } from "react";
import CloseIcon from "@mui/icons-material/Close";
import { Drawer, Box } from "@mui/material";
import Button from "@mui/material/Button";
import "./PaymentDetails.css";
import Veg from "../Assets/veg.jpg";
import NonVegan from "../Assets/NonVeg.jpg";
import { Navbar } from "../RestaurantPage/Navbar";
import { Address } from "./Address";
import { filterAvailableCartItems } from "../../utils/dayGating";
import { getPlanStatus } from "../../utils/planGating";
import { PlanButtons } from "../PlanButtons";
import { getCartKey } from "../../utils/cartKey";
import { authFetch } from "../../utils/authApi";
import { API_BASE_URL } from "../../config";
import { getAppliedCoupon, setAppliedCoupon, clearAppliedCoupon } from "../../utils/couponKey";
import { extractErrorMessage } from "../../utils/apiError";

export const PaymentDetails = () => {
  const [isDraweropen, setisDraweropen] = useState(false);
  const [couponCode, setCouponCode] = useState("");
  const [appliedCoupon, setAppliedCouponState] = useState(getAppliedCoupon());
  const [couponError, setCouponError] = useState("");
  const [applyingCoupon, setApplyingCoupon] = useState(false);
  const [state, setState] = useState([]);

  const { isTrialActive, isPaidActive } = getPlanStatus();
  const DELIVERY_FEE = 39;
  const deliveryFee = isTrialActive || isPaidActive ? 0 : DELIVERY_FEE;

  useEffect(() => {
    let cart = JSON.parse(localStorage.getItem(getCartKey())) || [];
    let available_cart = filterAvailableCartItems(cart);
    if (available_cart.length !== cart.length) {
      localStorage.setItem(getCartKey(), JSON.stringify(available_cart));
    }
    setState(available_cart);
  }, []);

  const cartTotal = state.reduce((sum, e) => sum + e.price * e.q, 0);

  // A rejection ("minimum order value", "only applies to: X") is only true
  // for the cart as it was at the moment of that Apply click -- clear it
  // whenever the cart itself changes (item added/removed, quantity changed)
  // so it doesn't linger and look like it still applies to the new total.
  useEffect(() => {
    setCouponError("");
  }, [state]);

  // Real backend check (min order value, for now) -- not the old client-only
  // "apply a hardcoded % off" buttons. See core/schemas.py's
  // CouponValidateRequest / main.validate_coupon_endpoint.
  const handleApplyCoupon = async () => {
    setCouponError("");
    setApplyingCoupon(true);
    try {
      const res = await authFetch(`${API_BASE_URL}/coupons/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: couponCode.trim(),
          cart_items: state.map((e) => ({ name: e.name, price: e.price, quantity: e.q })),
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(extractErrorMessage(data, "Coupon not valid"));
      const applied = { code: data.code, discount_amount: data.discount_amount };
      setAppliedCouponState(applied);
      setAppliedCoupon(applied);
      setisDraweropen(false);
    } catch (err) {
      setCouponError(err.message);
    } finally {
      setApplyingCoupon(false);
    }
  };

  const handleRemoveCoupon = () => {
    setAppliedCouponState(null);
    clearAppliedCoupon();
    setCouponCode("");
    setCouponError("");
  };

  const qHandler = (e) => {
    let id=(e.target.parentElement.id)
      let index=-1
      for (let i = 0; i < state.length; i++) {
        if (state[i].id == id) {
          index=i
        }
      }
    let temp = [...state]
      if (e.target.innerHTML === "+") temp[index].q++
      else if (temp[index].q !== 1) temp[index].q--
      else temp.splice(index,1)
      setState(temp)
      localStorage.setItem(getCartKey(), JSON.stringify(temp));
  }
  

  return (
    <>
      <Navbar />
      <Address />
      <Drawer
        anchor="right"
        open={isDraweropen}
        onclose={() => {
          setisDraweropen(false);
        }}
      >
        <Box role="presentation" p={4} width="400px">
          <CloseIcon
            onClick={() => {
              setisDraweropen(false);
            }}
            style={{ cursor: "pointer", position: "absolute", left: "30px" }}
            className="close_address"
          />
          <h2 style={{ marginBottom: "20px" }}>Apply Coupon</h2>
          <input
            type="text"
            placeholder="Enter coupon code"
            value={couponCode}
            onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
            style={{ width: "100%", padding: "10px", marginBottom: "12px", textTransform: "uppercase" }}
          />
          {couponError && (
            <p style={{ color: "crimson", fontSize: "13px", marginBottom: "12px" }}>{couponError}</p>
          )}
          <div className="button_save">
            <Button
              className="btn_address"
              variant="contained"
              disabled={!couponCode.trim() || applyingCoupon}
              onClick={handleApplyCoupon}
            >
              {applyingCoupon ? "CHECKING..." : "APPLY"}
            </Button>
          </div>
        </Box>
      </Drawer>
      <div>
        <div className="cart_body">
          {state.length === 0 ? (
            <div className="payment_cart_empty">
              <h2 className="payment_empty_cart_title">Cart Empty</h2>
              <img
                src="https://res.cloudinary.com/swiggy/image/upload/fl_lossy,f_auto,q_auto,w_480/Cart_empty_-_menu_2x_ejjkf2"
                alt=""
                className="payment_empty_cart_img"
              />
              <p className="payment_empty_cart_para">
                Good food is always cooking! <br /> Go ahead, order some
                yummy items from the menu.
              </p>
            </div>
          ) : (
            <>
          <div className="items_div_parent">
            {state
              ? state.map((e) => (
                  <div className="items_div" key={e.id} id={e.id}>
                    {e.veg ? (
                      <img src={Veg} alt="" className="logo_veg_nonVeg" />
                    ) : (
                      <img src={NonVegan} alt="" className="logo_veg_nonVeg" />
                    )}
                    <p className="product">
                      {e.name}
                      {e.restaurant_name && (
                        <span style={{ display: "block", fontSize: "12px", color: "gray" }}>
                          from {e.restaurant_name}
                        </span>
                      )}
                    </p>
                    <button className="decrease" onClick={qHandler}>
                      -
                    </button>
                    <p className="value">{e.q}</p>
                    <button className="increase" onClick={qHandler}>
                      +
                    </button>
                    <p className="price">&#8377;{e.price}</p>
                  </div>
                ))
              : ""}
          </div>
          {appliedCoupon ? (
            <div className="applynow" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span>Coupon "{appliedCoupon.code}" applied &#8211; &#8377;{appliedCoupon.discount_amount} off</span>
              <Button size="small" onClick={handleRemoveCoupon}>Remove</Button>
            </div>
          ) : (
            <button
              className="applynow"
              onClick={() => {
                setisDraweropen(true);
              }}
            >
              &nbsp;&nbsp; &nbsp;&nbsp;Apply Coupon&nbsp;&nbsp;&nbsp;&nbsp;
            </button>
          )}
          <PlanButtons />
          <hr style={{ margin: "20px 0", border: "1px solid #eee" }} />
          <p className="billdetails">Bill Details</p>
          <div className="itemdetails">
            <p className="bill_details_user">Item Total</p>
            <p className="amount"> &#8377;{cartTotal.toFixed(2)}</p>
          </div>
          {appliedCoupon && (
            <div className="itemdetails">
              <p className="bill_details_user">Coupon discount ({appliedCoupon.code})</p>
              <p className="amount">&#8211; &#8377;{appliedCoupon.discount_amount.toFixed(2)}</p>
            </div>
          )}
          <div className="itemdetails">
            <p className="bill_details_user">Delivery Fee | 4.6kms</p>
            <p className="amount">
              {deliveryFee === 0 ? (
               <><strike>&#8377;{DELIVERY_FEE}.00</strike>&nbsp;&nbsp;FREE</>
               ) : (
             <>&#8377;{deliveryFee}.00</>
          )}
            </p>
          </div>

          <div className="bordertotal"></div>
          <div className="itemdetails">
            <p className="bill_details_user">Taxes and Charges</p>
            <p className="amount">FREE</p>
          </div>
          <div className="total_pay_for_user">
            <p className="amount_tag">TO PAY</p>
            <span className="amount_to_paid">
              {" "}
              &#8377;{" "}
              {(cartTotal - (appliedCoupon?.discount_amount || 0) + deliveryFee).toFixed(2)}
            </span>
          </div>
            </>
          )}
        </div>
      </div>
    </>
  );
};

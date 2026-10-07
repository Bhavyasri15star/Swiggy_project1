import React, { useState, useEffect } from "react";
import Logo from "../Assets/swiggy.svg";
import Arrow from "../Assets/arrow.svg";
import Cart from "../Assets/cart.png";
import Search from "../Assets/search.svg";
import Discount from "../Assets/discount.svg";
import Help from "../Assets/help.svg";
import User from "../Assets/user.png";
import CloseIcon from "@mui/icons-material/Close";
import { Drawer, Box } from "@mui/material";
import { Link, useNavigate } from "react-router-dom";
import "./Navbar.css";
import { PlanButtons } from "../PlanButtons";
import {
  login as authLogin,
  signup as authSignup,
  requestOtp,
  verifyOtp,
  storeAuth,
  getStoredAuth,
  clearAuth,
} from "../../utils/authApi";
import { getCartKey, migrateGuestCartToUser } from "../../utils/cartKey";
export function Navbar() {
  const [isDraweropen, setisDraweropen] = useState(false);
  const [user_signin, setUser_signin] = useState(false);
  const [user_details, setUser_details] = useState(null);
  const [login, setLogin] = useState(true);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [len, setLen] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [authMode, setAuthMode] = useState("password"); // "password" | "otp"
  const [otpSent, setOtpSent] = useState(false);
  const [otpCode, setOtpCode] = useState("");

  const location = JSON.parse(localStorage.getItem("Location"));
  let cart = JSON.parse(localStorage.getItem(getCartKey())) || [];
  const navigate = useNavigate();
  useEffect(() => {
    const stored = getStoredAuth();
    if (stored) {
      setUser_details(stored.user);
      setUser_signin(true);
    }
  }, []);

  useEffect(() => {
    setLen(cart.length);
  }, [cart]);

  // Shared by every successful auth path (password login, signup, OTP verify).
  const completeSignIn = ({ token, user }) => {
    storeAuth({ token, user });
    migrateGuestCartToUser(user.id);
    setUser_details(user);
    setUser_signin(true);
    setisDraweropen(false);
    setAuthMode("password");
    setOtpSent(false);
    setOtpCode("");
  };

  const handleSignOut = () => {
    clearAuth();
    setUser_details(null);
    setUser_signin(false);
    setisDraweropen(false);
  };

  // AuthService (Express + Prisma) login/signup
  const onLogInSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      completeSignIn(await authLogin({ email, password }));
    } catch (err) {
      alert(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const onSigninSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      completeSignIn(await authSignup({ email, password, name }));
    } catch (err) {
      alert(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Passwordless: request a code, then verify it.
  const handleRequestOtp = async (e) => {
    e.preventDefault();
    if (!email) {
      alert("Enter your email first.");
      return;
    }
    setSubmitting(true);
    try {
      await requestOtp({ email });
      setOtpSent(true);
    } catch (err) {
      alert(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      completeSignIn(await verifyOtp({ email, code: otpCode }));
    } catch (err) {
      alert(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Drawer
        anchor="right"
        open={isDraweropen}
        onClose={() => {
          setisDraweropen(false);
        }}
      >
        <Box role="presentation" p={4} width="500px">
          <CloseIcon
            className="close_icon"
            onClick={() => {
              setisDraweropen(false);
            }}
            style={{ cursor: "pointer" }}
          />
          {user_signin ? (
            <div className="login_form">
              <div className="left_div">
                <h2>My Account</h2>
              </div>
              <hr className="hr_line_drawer" />
              <p style={{ margin: "30px 0", fontSize: "16px" }}>
                Signed in as <strong>{user_details?.email}</strong>
              </p>
              <input
                type="button"
                value="SIGN OUT"
                className="login_btn"
                onClick={handleSignOut}
              />
            </div>
          ) : authMode === "otp" ? (
            <div className="login_form">
              <div className="left_div">
                <h2>Sign in with a code</h2>
                <p className="link_register">
                  or{" "}
                  <a
                    onClick={() => {
                      setAuthMode("password");
                      setOtpSent(false);
                      setOtpCode("");
                    }}
                    style={{ cursor: "pointer" }}
                  >
                    use a password instead
                  </a>
                </p>
              </div>
              <hr className="hr_line_drawer" />
              <div className="right_div">
                <img
                  src="https://res.cloudinary.com/swiggy/image/upload/fl_lossy,f_auto,q_auto/Image-login_btpq7r"
                  alt=""
                  className="food_wrap"
                />
              </div>
              <form>
                <input
                  type="email"
                  name="email"
                  placeholder="Email"
                  className="Number_input"
                  autoFocus={true}
                  spellCheck="false"
                  value={email}
                  disabled={otpSent}
                  onChange={(e) => {
                    setEmail(e.target.value);
                  }}
                />
                <br />
                {otpSent && (
                  <>
                    <input
                      type="text"
                      name="otp_code"
                      placeholder="6-digit code"
                      className="Number_input"
                      autoFocus={true}
                      value={otpCode}
                      onChange={(e) => {
                        setOtpCode(e.target.value);
                      }}
                    />
                    <br />
                  </>
                )}
                <input
                  type="submit"
                  value={
                    submitting ? "PLEASE WAIT..." : otpSent ? "VERIFY CODE" : "SEND CODE"
                  }
                  className="login_btn"
                  disabled={submitting}
                  onClick={otpSent ? handleVerifyOtp : handleRequestOtp}
                />
              </form>
              {otpSent && (
                <p className="link_register">
                  <a onClick={handleRequestOtp} style={{ cursor: "pointer" }}>
                    Resend code
                  </a>
                </p>
              )}
              <div className="foot_text">
                <p>
                  By continuing, I accept the terms & Conditions & Privacy
                  Policy
                </p>
              </div>
            </div>
          ) : login ? (
            <div className="login_form">
              <div className="left_div">
                <h2>Login</h2>
                <p className="link_register">
                  or{" "}
                  <a
                    onClick={() => setLogin(false)}
                    style={{ cursor: "pointer" }}
                  >
                    create an account
                  </a>
                  {" · "}
                  <a
                    onClick={() => setAuthMode("otp")}
                    style={{ cursor: "pointer" }}
                  >
                    sign in with a code
                  </a>
                </p>
              </div>
              <hr className="hr_line_drawer" />
              <div className="right_div">
                <img
                  src="https://res.cloudinary.com/swiggy/image/upload/fl_lossy,f_auto,q_auto/Image-login_btpq7r"
                  alt=""
                  className="food_wrap"
                />
              </div>
              <form>
                <input
                  type="email"
                  name="email"
                  placeholder="Email"
                  className="Number_input"
                  autoFocus={true}
                  spellCheck="false"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                  }}
                />
                <br />
                <input
                  type="password"
                  name="password"
                  placeholder="Password"
                  className="Number_input"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                  }}
                />
                <br />
                <input
                  type="submit"
                  value={submitting ? "PLEASE WAIT..." : "CONTINUE"}
                  className="login_btn"
                  disabled={submitting}
                  onClick={onLogInSubmit}
                />
              </form>
              <div className="foot_text">
                <p>
                  By clicking on Login, I accept the terms & Conditions &
                  Privacy Policy
                </p>
              </div>
            </div>
          ) : (
            <div className="login_form">
              <div className="left_div">
                <h2>Sign up</h2>
                <p className="link_register">
                  or{" "}
                  <a
                    style={{ cursor: "pointer" }}
                    onClick={() => setLogin(true)}
                  >
                    login to your account
                  </a>
                  {" · "}
                  <a
                    onClick={() => setAuthMode("otp")}
                    style={{ cursor: "pointer" }}
                  >
                    sign in with a code
                  </a>
                </p>
              </div>
              <hr className="hr_line_drawer" />
              <div className="right_div">
                <img
                  src="https://res.cloudinary.com/swiggy/image/upload/fl_lossy,f_auto,q_auto/Image-login_btpq7r"
                  alt=""
                  className="food_wrap"
                />
              </div>
              <form>
                <input
                  type="text"
                  name="user_name"
                  placeholder="Name"
                  className="Number_input_1"
                  autoFocus={true}
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                  }}
                />
                <br />
                <input
                  type="email"
                  name="email"
                  placeholder="Email"
                  className="Number_input_1"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                  }}
                />
                <br />
                <input
                  type="password"
                  name="password"
                  placeholder="Password"
                  className="Number_input"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                  }}
                />
                <br />

                <input
                  type="submit"
                  value={submitting ? "PLEASE WAIT..." : "CONTINUE"}
                  className="login_btn"
                  disabled={submitting}
                  onClick={onSigninSubmit}
                />
              </form>

              <div className="foot_text">
                <p>
                  By clicking on Login, I accept the terms & Conditions &
                  Privacy Policy
                </p>
              </div>
            </div>
          )}
        </Box>
      </Drawer>

      <nav className="navbar">
        <img src={Logo} alt="" className="logo" />
        <div className="div1_nav">
          <p className="other">Other</p>
          <div className="location">
            {location} &nbsp;
            <img src={Arrow} alt="" className="arrow" />
          </div>
        </div>
        <div className="div2_nav">
          <p className="search" onClick={() => navigate("/restaurants")} style={{ cursor: "pointer" }}>
            <img src={Search} alt="" className="search_icon" />
            Search{" "}
          </p>
        </div>
        <div className="div3_nav">
          <p className="offers" onClick={() => navigate("/offers")} style={{ cursor: "pointer" }}>
            <img src={Discount} alt="" className="discount_icon" />
            Offers <span className="new">NEW</span>{" "}
          </p>
        </div>
        <div className="div4_nav">
          <p className="help">
            <img src={Help} alt="" className="help_icon" />
            Help
          </p>
        </div>
        {user_signin ? (
          <div className="div_orders_nav">
            <p className="orders_link" onClick={() => navigate("/orders")}>
              Orders
            </p>
          </div>
        ) : (
          ""
        )}
        <div className="div5_nav">
          <p
            className="sign_in"
            onClick={() => {
              if (!user_signin) {
                setLogin(true);
                setAuthMode("password");
              }
              setisDraweropen(true);
            }}
          >
            <img src={User} alt="" className="user_icon" />
            {user_signin ? user_details.name : "Sign In"}
          </p>
        </div>
        <div className="div6_nav">
          <Link to="/payment" style={{ textDecoration: "none" }}>
            <p className="cart">
              <img src={Cart} alt="" className="cart_icon" />
              Cart
            </p>
          </Link>
          <span className="cart_num">{len}</span>
        </div>
      </nav>
    </>
  );
}

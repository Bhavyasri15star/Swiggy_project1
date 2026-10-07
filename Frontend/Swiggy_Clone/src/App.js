import React from "react";
import { Routes, Route } from "react-router-dom";
import { LandingPage } from "./Components/LandingPage/LandingPage";
import "./App.css";
import { Food_Main } from "./Components/RestaurantPage/Food_Main";
import { Food_Detail } from "./Components/RestaurantPage/Food_Detail";
import { PaymentDetails } from "./Components/CheckoutPage/PaymentDetails";
import {ThankYou} from "./Components/Thankyou/Thankyou";
import { Orders } from "./Components/Orders/Orders";
import { Offers } from "./Components/Offers/Offers";
import { getCartKey } from "./utils/cartKey";
function App() {
  if (!localStorage.getItem(getCartKey())) {
    localStorage.setItem(getCartKey(), JSON.stringify([]))
  }
  if (!localStorage.getItem("user_details")) {
    localStorage.setItem("user_details", JSON.stringify({"name": "", "email": "", "number": ""}))
  }
  if (!localStorage.getItem("verificationId")) {
    localStorage.setItem("verificationId", JSON.stringify({"verificationId":""}))
  }
  return (
    <>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/restaurants" element={<Food_Main />} />
        <Route path="/:food/:id" element={<Food_Detail />} />
        <Route path="/payment" element={<PaymentDetails />} />
        <Route path="/orders" element={<Orders />} />
        <Route path="/offers" element={<Offers />} />
        <Route path="/thankyou" element={<ThankYou />} />
      </Routes>
    </>
  );
}

export default App;

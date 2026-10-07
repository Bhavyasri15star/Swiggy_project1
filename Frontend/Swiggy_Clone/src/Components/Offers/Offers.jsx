import React from "react";
import { Navbar } from "../RestaurantPage/Navbar";
import Discount from "../Assets/discount.svg";
import "./Offers.css";

const DUMMY_OFFERS = [
  { code: "TRYNEW", title: "50% OFF", subtitle: "Up to ₹100 on your first order", color: "#fc8019" },
  { code: "FLAT50", title: "FLAT ₹50 OFF", subtitle: "On orders above ₹199", color: "#48c479" },
  { code: "FREEDEL", title: "FREE DELIVERY", subtitle: "No minimum order value", color: "#db7c38" },
  { code: "WEEKEND20", title: "20% OFF", subtitle: "Weekend special, up to ₹150", color: "#5d5fef" },
  { code: "BIGSAVER", title: "FLAT ₹125 OFF", subtitle: "On orders above ₹349", color: "#e64a19" },
  { code: "SWEETTOOTH", title: "30% OFF", subtitle: "On desserts, up to ₹60", color: "#c2185b" },
];

export function Offers() {
  return (
    <>
      <Navbar />
      <div className="offers_page">
        <h2 className="offers_heading">Offers for you</h2>
        <p className="offers_note">
          Demo data — these codes aren't wired up to checkout yet.
        </p>
        <div className="offers_grid">
          {DUMMY_OFFERS.map((offer) => (
            <div className="offer_card" key={offer.code}>
              <div className="offer_card_top" style={{ backgroundColor: offer.color }}>
                <img src={Discount} alt="" className="offer_icon" />
                <div>
                  <h3>{offer.title}</h3>
                  <p>{offer.subtitle}</p>
                </div>
              </div>
              <div className="offer_card_bottom">
                <span className="offer_code">CODE: {offer.code}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

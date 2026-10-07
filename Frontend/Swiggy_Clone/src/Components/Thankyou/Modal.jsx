import * as React from "react";
import Logo from "../Assets/swiggy.svg";
import { useNavigate } from "react-router-dom";
import "./Modal.css";
import { getCartKey } from '../../utils/cartKey';

export function BasicModal() {
  // Set by Address.jsx right after a real order is created via POST /orders —
  // this used to be a client-generated random id with no connection to any
  // actual order (and, since its inputs were all hardcoded constants, was
  // really the same "random" id every single time).
  const id = localStorage.getItem("lastOrderId") || "N/A";
  const navigate = useNavigate();

  const handleClose = () => {
    window.scrollTo(0, 0);
    localStorage.setItem(getCartKey(), JSON.stringify([]));
    navigate("/restaurants");
  };
  window.scrollTo(0, 0);
  return (
    <div className="content">
      <div className="wrapper-1">
        <div className="wrapper-2">
          <img src={Logo} alt="" className="modal_image" />
          <h1 className="modal_h1">Thankyou</h1>
          <p>
            Order Id
          </p>
          <p>
          {id}
          </p>
          <button className="go-home" onClick={handleClose}>
            <a>go home</a>
          </button>
          
        </div>
      </div>
      <div className="pyro">
          <div className="before"></div>
          <div className="after"></div>
        </div>
      </div>
  );
}

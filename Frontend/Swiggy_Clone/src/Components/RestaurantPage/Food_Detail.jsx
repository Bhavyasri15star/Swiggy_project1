import React, { useState, useEffect } from "react";
import OfferImg from "../Assets/offerImg.jpg";
import Veg from "../Assets/veg.jpg";
import NonVegan from "../Assets/NonVeg.jpg";
import "./Food_Detail.css";
import { Navbar } from "./Navbar";
import Backdrop from "@mui/material/Backdrop";
import Box from "@mui/material/Box";
import Modal from "@mui/material/Modal";
import Fade from "@mui/material/Fade";
import ScrollToTop from "react-scroll-to-top";
import { useWindowScroll } from "react-use";
import Typography from "@mui/material/Typography";
import { useParams, Link } from "react-router-dom";
import { PreLoader } from "../PreLoader";
import { filterAvailableCartItems } from "../../utils/dayGating";
import { API_BASE_URL } from "../../config";
import {isAvailableToday} from "../../utils/dayGating";
import { getCartKey } from "../../utils/cartKey";
const style = {
  position: "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  width: "fit-content",
  border: "1px solid lightgray",
  borderRadius: "7px",
  boxShadow: 24,
  p: 2,
};
export const Food_Detail = () => {
  const {id}=useParams();
  const [open, setOpen] = useState(false);
  const [data, setData] = useState(null);
  const [showData, setShowData] = useState([]);
  const [mdata, setMdata] = useState([]);
  const [isClick, setisClick] = useState(false);
  const [query, setQuery] = useState("");
  const [cart, setCart] = useState([]);
  const [Value, isValue] = useState("");
  const [scrolled, setScrolled] = useState(0);
  const [loading, isLoading] = useState(false);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    isLoading(true);
    fakePromise(3000).then(() => isLoading(false));
  }, []);

  function fakePromise(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  const handlechange = (e) => {
    setQuery(e.target.value);
    let temp = [];
    data.items.forEach((o) => {
      if (o.name.toLowerCase().includes(query.toLowerCase())) {
        temp.push(o);
      }
    });
    setShowData(temp);
    if (showData.length === 0) {
      setShowData(temp);
    }
  };

  const { x, y } = useWindowScroll();
  useEffect(() => {
    const height =
      document.documentElement.scrollHeight -
      document.documentElement.clientHeight;
    setScrolled((y / height) * 100);
  }, [y]);

  useEffect(() => {
    setNotFound(false);
    setData(null);

    fetch(`${API_BASE_URL}/restaurants/${id}`)
      .then((res) => {
        if (res.status === 404) {
          setNotFound(true);
          return null;
        }
        if (!res.ok) throw new Error("Failed to fetch restaurant");
        return res.json();
      })
      .then((selectedFood) => {
        if (!selectedFood) return; // 404 already handled above
        setData(selectedFood);
        setShowData(selectedFood.items); // backend already filters via _is_available_today
        localStorage.setItem("foodId", JSON.stringify(selectedFood));
      })
      .catch(() => {
        // Network/server failure (not a 404) — fall back to the cached
        // restaurant only if it's actually the one this URL asked for.
        let selectedFood = JSON.parse(localStorage.getItem("foodId") || "null");
        if (selectedFood && String(selectedFood.id) === String(id)) {
          setData(selectedFood);
          setShowData(selectedFood.items.filter(isAvailableToday));
        } else {
          setNotFound(true);
        }
      });

    let cart_value = JSON.parse(localStorage.getItem(getCartKey())) || [];
    let available_cart = filterAvailableCartItems(cart_value);
    if (available_cart.length !== cart_value.length) {
      localStorage.setItem(getCartKey(), JSON.stringify(available_cart));
    }
    setCart(available_cart);
  }, [id]);

  // Renamed from the shadowing `data` used before -- this needs the
  // restaurant-level `data` state (name/id) still in scope to snapshot onto
  // the cart line, which a same-named param would have hidden.
  const handleOpen = (clickedItem) => {
    setMdata(clickedItem);
    setOpen(true);
    let array = cart.map((item)=>({...item}));
    const existingIndex= array.findIndex((item)=>item.id===clickedItem.id);
    if(existingIndex!==-1){
      array[existingIndex].q+=1;
    }
    else{
      array.push({...clickedItem, restaurant_id: data.id, restaurant_name: data.name, q:1});
    }
    setCart(array);
    localStorage.setItem(getCartKey(), JSON.stringify(array));
  };

  const veg = () => {
    let veg_only = [];
    showData.forEach((e) => {
      if (e.veg) {
        veg_only.push(e);
      }
    });
    setShowData(veg_only);
  };
  const handleClose = () => setOpen(false);

  const filterData = (e) => {
    let paras = document.querySelectorAll(".side_section p");
    paras.forEach((p) => p.classList.remove("active_filter"));

    e.target.classList.add("active_filter");
    let fil = e.target.innerText.toLowerCase();
    let newarr = data.items
    .filter((item) => item.category.toLowerCase() === fil)
    .filter(isAvailableToday); // <-- add this
    setShowData([...newarr]);
    isValue(e.target.innerText);
    setisClick(true);

    
  };

  const qHandler = (e) => {
    let id = e.target.parentElement.id;
    let index = -1;
    for (let i = 0; i < cart.length; i++) {
      if (String(cart[i].id) === String(id)) {
        index = i;
      }
    }
    let temp = [...cart];
    if (e.target.innerHTML === "+") temp[index].q++;
    else if (temp[index].q !== 1) temp[index].q--;
    else temp.splice(index, 1);
    setCart(temp);
    localStorage.setItem(getCartKey(), JSON.stringify(temp));
  };

  if (loading || (!data && !notFound)) {
    return <PreLoader />;
  }

  if (notFound) {
    return (
      <>
        <Navbar />
        <div className="restaurant_not_found" style={{ padding: "120px 24px", textAlign: "center" }}>
          <h2>Restaurant not found</h2>
          <p>We couldn't find a restaurant for this link. It may have been removed.</p>
          <Link className="link" to="/restaurants">
            <button className="checkout">Back to restaurants</button>
          </Link>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="scroll-container">
        <div className="indicator" style={{ width: `${scrolled}%` }}></div>
      </div>{" "}
      <ScrollToTop smooth color="#fc8019" />
      <Modal
        aria-labelledby="transition-modal-title"
        aria-describedby="transition-modal-description"
        open={open}
        onClose={handleClose}
        closeAfterTransition
        BackdropComponent={Backdrop}
        BackdropProps={{
          timeout: 500,
        }}
      >
        <Fade in={open}>
          <Box sx={style} className="modal_window">
            <Typography id="transition-modal-title" variant="h6" component="h2">
              {mdata ? mdata.name : ""}
              <p className="modal_description">
                <i className="fa fa-check" aria-hidden="true"></i>&nbsp;Added to
                your cart
              </p>
            </Typography>
            <Typography id="transition-modal-description" sx={{ mt: 2 }}>
              <div className="food_img_modal">
                <img src={mdata ? mdata.img_url : ""} alt="" />
              </div>
            </Typography>
          </Box>
        </Fade>
      </Modal>
      <Navbar />
      <div className="topbar">
        <div className="topbar_content">
          <div className="food_img_topbar">
            <img src={data ? data.img_url : ""} alt="" />
          </div>
          <div className="food_details_section">
            <h2 className="heading">{data ? data.name : ""} </h2>

            <p className="cuisines">{data ? data.cuisines.join(", ") : ""}</p>

            <p className="hotel_location">
              Delta Square, Baramunda, Delta Square
            </p>
            <div className="food_overview">
              <p className="food_rating">
                <i className="fas fa-star "></i>
                <b>&nbsp;{data ? data.rating : ""}</b> <br />
                500+ Ratings
              </p>
              <p className="food_timing">
                <b>{data ? data.average_time : ""} MINS</b>
                <br />
                Delivery Time
              </p>
              <p className="food_pricing">
                {" "}
                <b>&#8377;{data ? data.average_cost : ""}</b> <br />
                Cost for two
              </p>
            </div>
            <div className="querySearch_user">
              <div className="input_div">
                <input
                  type="text"
                  className="search_query"
                  placeholder="Search for dishes..."
                  autoFocus={true}
                  spellCheck="false"
                  value={query}
                  onChange={(e) => handlechange(e)}
                />
              </div>
              <div className="veg_only">
                <button onClick={veg}>Veg Only</button>
              </div>
            </div>
          </div>
          <div className="offer-section">
            <img src={OfferImg} alt="" className="offer_img" />
          </div>
        </div>
      </div>
      <div className="food_products">
        <h4 className="title">{isClick ? Value : "All Food Items"}</h4>
        <p className="itemCount">
          {showData.length}
          &nbsp;ITEMS
        </p>

        {showData
          ? showData.map((ele, index) => (
              <div className="food_products_card" key={index}>
                <div className="card_left_div">
                  <div className="veg_logo">
                    {ele.veg ? (
                      <img src={Veg} alt="" />
                    ) : (
                      <img src={NonVegan} alt="" />
                    )}
                    {ele.best_seller ? (
                      <p className="best_seller">
                        <i className="fas fa-star"></i>&nbsp;BEST SELLER
                      </p>
                    ) : (
                      ""
                    )}
                  </div>
                  <h4 className="product_title">{ele.name}</h4>
                  <p className="product_price">&#8377;{ele.price}</p>
                  <p className="product_descrip">{ele.description}</p>
                </div>
                <div className="card_right_div">
                  <div className="food_img">
                    <img src={ele.img_url} alt="" />
                  </div>
                  <button className="add_cart" onClick={() => handleOpen(ele)}>
                    ADD
                  </button>
                </div>
              </div>
            ))
          : ""}

        {cart.length ? (
          <div className="item_added">
            <h2 className="header">Cart</h2>
            <p className="no_items">{cart.length}&nbsp;Items</p>
            <div className="items_div_parent">
              {cart
                ? cart.map((e) => (
                    <div className="items_div" key={e.id} id={e.id}>
                      {e.veg ? (
                        <img src={Veg} alt="" className="logo_veg_nonVeg" />
                      ) : (
                        <img
                          src={NonVegan}
                          alt=""
                          className="logo_veg_nonVeg"
                        />
                      )}
                      <p className="product">{e.name}</p>
                      <button className="decrease" onClick={qHandler}>
                        -
                      </button>
                      <p className="value">{e.q}</p>
                      <button className="increase" onClick={qHandler}>
                        +
                      </button>
                      <p className="price">
                        &#8377;{(e.price * e.q).toFixed(2)}
                      </p>
                    </div>
                  ))
                : ""}
            </div>
            <div className="sub_total">
              <div className="header_1">
                <h2>
                  Subtotal <br />
                  <p>Extra charges may apply</p>
                </h2>
              </div>
              <div className="total_price_1">
                &#8377;
                {cart
                  .map((e) => (e = e.price * e.q))
                  .reduce((a, b) => a + b, 0)
                  .toFixed(2)}
              </div>
            </div>
            <Link className="link" to="/payment">
              <button className="checkout">
                CHECKOUT&nbsp;&nbsp;&nbsp;<i className="fas fa-arrow-right"></i>
              </button>
            </Link>
          </div>
        ) : (
          <div className="cart_empty">
            <h2 className="empty_cart">Cart Empty</h2>
            <img
              src="https://res.cloudinary.com/swiggy/image/upload/fl_lossy,f_auto,q_auto,w_480/Cart_empty_-_menu_2x_ejjkf2"
              alt=""
              className="empty_cart_img"
            />
            <p className="empty_cart_para">
              Good food is always cooking! <br /> Go ahead, order some yummy
              items from the menu.
            </p>
          </div>
        )}
      </div>
      <div className="side_section">
        <p className="side_section_filters_recommend" onClick={filterData}>
          Recommended
        </p>
        <p className="side_section_filters" onClick={filterData}>
          WEDNESDAY EXCLUSIVES
        </p>
        <p className="side_section_filters" onClick={filterData}>
          MATCH DAY SPECIALS (SAVE UPTO 32%)
        </p>
        <p className="side_section_filters" onClick={filterData}>
          STAY HOME SPECIALS
        </p>
        <p className="side_section_filters" onClick={filterData}>
          BIG SAVE COMBOS
        </p>
        <p className="side_section_filters" onClick={filterData}>
          BIRYANI BUCKETS (NEW)
        </p>
        <p className="side_section_filters" onClick={filterData}>
          BURGERS
        </p>
        <p className="side_section_filters" onClick={filterData}>
          SNACKS
        </p>
        <p className="side_section_filters" onClick={filterData}>
          SIDES & BEVERAGES
        </p>
      </div>
    </>
  );
};

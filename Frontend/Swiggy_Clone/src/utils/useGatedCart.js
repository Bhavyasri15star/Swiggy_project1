import {useState, useEffect} from 'react';
import {filterAvailableCartItems} from "./dayGating";
import {getCartKey} from "./cartKey";
export function useGatedCart(){
    const[cart,setCart]=useState([]);
    useEffect(()=>{
        const stored=JSON.parse(localStorage.getItem(getCartKey()))|| [];
        const available= filterAvailableCartItems(stored);
        if(available.length!==stored.length){
            localStorage.setItem(getCartKey(),JSON.stringify(available));

        }
        setCart(available);
    },[]);
    return [cart,setCart];
}

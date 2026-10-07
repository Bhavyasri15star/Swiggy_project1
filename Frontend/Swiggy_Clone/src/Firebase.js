import firebase from 'firebase/compat/app'
import 'firebase/compat/auth'
import 'firebase/compat/firestore';


const firebaseConfig = {
  apiKey: "AIzaSyDw9tpAbPeIY4qjONHQFKie_Muqo1nnQyc",
  authDomain: "my-swiggy-clone-30491.firebaseapp.com",
  projectId: "my-swiggy-clone-30491",
  storageBucket: "my-swiggy-clone-30491.firebasestorage.app",
  messagingSenderId: "581686084113",
  appId: "1:581686084113:web:93005339558008b90a67b0",
  measurementId: "G-JM611DFV5Q"
}

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
export default firebase
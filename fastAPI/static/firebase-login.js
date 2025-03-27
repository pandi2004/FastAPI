// Import Firebase SDK modules (Use latest stable version: 10.7.1)
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import {
  getFirestore,
  doc,
  getDoc,
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

// Your Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyASL8YOQOAPKZqgFP9J4o4vvmJoGCkzHzE",
  authDomain: "fastapiproject-19c47.firebaseapp.com",
  projectId: "fastapiproject-19c47",
  storageBucket: "fastapiproject-19c47.firebasestorage.app",
  messagingSenderId: "770273801116",
  appId: "1:770273801116:web:afa4ebd5b6b232a0d14e59"
};


// Initialize Firebase
let app, auth, db;

try {
  app = initializeApp(firebaseConfig);
  auth = getAuth(app);
  db = getFirestore(app);
  console.log("Firebase Connected Successfully!");
} catch (error) {
  console.error("Firebase Connection Failed:", error);
}

//Check Firebase Auth State
onAuthStateChanged(auth, (user) => {
  if (user) {
    console.log("User Logged In - ID:", user.uid);
  } else {
    console.log("No User Logged In.");
  }
});

// Check Firestore Connection
async function checkFirestoreConnection() {
  try {
    const testDocRef = doc(db, "testCollection", "testDocument");
    const docSnap = await getDoc(testDocRef);

    if (docSnap.exists()) {
      console.log("Firestore Connected - Test Document Found:", docSnap.data());
    } else {
      console.log("Firestore Connected - No Test Document Found.");
    }
  } catch (error) {
    console.error("Firestore Connection Failed:", error);
  }
}
checkFirestoreConnection();

// Handle User Sign Up
document.getElementById("sign-up").addEventListener("click", () => {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  console.log(email, password);

  const API_KEY = "AIzaSyAKKq2CMmRLA44v-YmCedQxYViSXr80rDI"; // Update this
  fetch(
    `https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=${API_KEY}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: email,
        password: password,
        returnSecureToken: true,
      }),
    }
  )
    .then((response) => response.json())
    .then((data) => {
      document.cookie = `token=${data.token};path=/;SameSite=Strict`;
      alert("You have Successfully Signed Up");
      window.location.href = "/";
      
    })
    .catch((error) => console.error(" Sign Up Failed:", error));
});

// Handle User Login
document.getElementById("login").addEventListener("click", () => {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  signInWithEmailAndPassword(auth, email, password)
    .then((userCredential) => {
      const user = userCredential.user;
      return user.getIdToken();
    })
    .then((token) => {
      document.cookie = `token=${token};path=/;SameSite=Strict`;
      alert("Loged In Successfully")
      window.location.href = "/";
    })
    .catch((error) => console.log(" Login Failed:", error.code, error.message));
});


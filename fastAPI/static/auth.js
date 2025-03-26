
/// Function to Get Token from Cookies
function getCookie(name) {
    let cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        let [key, value] = cookie.trim().split('=');
        if (key === name) return value;
    }
    return "";
}

// Function to Check Authentication Status
function checkAuthStatus() {
    let token = getCookie("token"); // Get token from cookies
    let authButton = document.getElementById("auth-button");

    if (authButton) {
        if (token) {
            console.log("User is logged in:", token);
            authButton.innerText = "Logout"; // Change text to "Logout"
            authButton.href = "#"; // Prevent navigation
            authButton.addEventListener("click", logoutUser);
        } else {
            console.log("User is NOT logged in.");
            authButton.innerText = "Login"; // Change text to "Login"
            authButton.href = "/login"; // Redirect to login page
        }
    }
}

// Function to Logout User (Remove Token)
function logoutUser() {
    document.cookie = "token=;path=/;expires=Thu, 01 Jan 1970 00:00:00 UTC;SameSite=Strict";
    alert("You have Logged Out")
    window.location.href = "/"; // Redirect to login page
}

// Run on Page Load
window.addEventListener("load", checkAuthStatus);
// firebase-login.js
// Initialize Firebase (replace with your actual configuration)

  firebase.initializeApp(firebaseConfig);
  
  window.addEventListener('load', () => {
    updateUI(document.cookie);
  });
  
  function updateUI(cookie) {
    const token = parseCookieToken(cookie);
    if (token) {
      document.getElementById('login-box').style.display = 'none';
    } else {
      document.getElementById('login-box').style.display = 'block';
    }
  }
  
  function parseCookieToken(cookie) {
    let token = '';
    const pairs = cookie.split(';');
    for (let pair of pairs) {
      let [key, value] = pair.trim().split('=');
      if (key === 'token') {
        token = value;
        break;
      }
    }
    return token;
  }
  
  function signOut() {
    firebase.auth().signOut().then(() => {
      // Clear token cookie and reload page
      document.cookie = "token=; path=/; SameSite=Strict;";
      window.location.href = "/";
    }).catch((error) => {
      console.error("Sign out error:", error);
    });
  }
  
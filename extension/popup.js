const loggedOut = document.getElementById("loggedOut");
const loggedIn = document.getElementById("loggedIn");
const status = document.getElementById("status");
const error = document.getElementById("error");

async function render() {
  const session = await chrome.runtime.sendMessage({ type: "GET_SESSION" });
  error.textContent = "";
  if (session?.accessToken) {
    status.textContent = `Logged in as ${session.email}`;
    loggedOut.style.display = "none";
    loggedIn.style.display = "block";
  } else {
    loggedOut.style.display = "block";
    loggedIn.style.display = "none";
  }
}

document.getElementById("loginBtn").addEventListener("click", async () => {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  error.textContent = "";
  const result = await chrome.runtime.sendMessage({ type: "LOGIN", email, password });
  if (!result?.ok) {
    error.textContent = result?.message ?? "Could not log in.";
    return;
  }
  await render();
});

document.getElementById("logoutBtn").addEventListener("click", async () => {
  await chrome.runtime.sendMessage({ type: "LOGOUT" });
  await render();
});

render();

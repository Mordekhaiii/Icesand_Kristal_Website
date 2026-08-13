document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    const welcomeMessage = document.getElementById("welcomeMessage");
    const logoutButton = document.getElementById("logoutButton");
    const userSpan = document.getElementById("user");

    // Handle login
    loginForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const username = document.getElementById("username").value;
        if (username) {
            loginForm.classList.add("hidden");
            userSpan.textContent = username;
            welcomeMessage.classList.remove("hidden");
        }
    });

    // Handle logout
    logoutButton.addEventListener("click", () => {
        welcomeMessage.classList.add("hidden");
        loginForm.classList.remove("hidden");
        loginForm.reset();
    });
});

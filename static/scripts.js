
function toggleDarkMode() {
    var body = document.body;
    body.classList.toggle("dark-mode");
    var isDarkMode = body.classList.contains("dark-mode");
    localStorage.setItem("darkModeEnabled", isDarkMode);
}

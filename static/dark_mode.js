function handleDarkMode() {
    var body = document.body;
    var mode_switch = document.getElementById('dark-mode-switch')
    if (mode_switch.checked)
         body.classList.add("dark-mode");
    else
         body.classList.remove("dark-mode");
    localStorage.setItem("darkModeEnabled", mode_switch.checked);
}
document.getElementById('dark-mode-switch').addEventListener('change', handleDarkMode);

// Check if dark mode was previously enabled
var darkModeEnabled = localStorage.getItem("darkModeEnabled");
if (darkModeEnabled === "true") {
    var body = document.body;
    body.classList.add("dark-mode");
    document.getElementById('dark-mode-switch').checked = true;
}
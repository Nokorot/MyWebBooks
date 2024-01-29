function toggleDarkMode() {
    var body = document.body;
    body.classList.toggle("dark-mode");
    var isDarkMode = body.classList.contains("dark-mode");
    localStorage.setItem("darkModeEnabled", isDarkMode);
}

document.addEventListener("DOMContentLoaded", function () {
    const dropbtns = document.querySelectorAll(".dropbtn");
    dropbtns.forEach(function (element) {
        element.addEventListener("click", function () {
            element.closest('.dropdown').classList.toggle("hidden");
        });
    });

    const collapsbtns = document.querySelectorAll(".collapsbtn");
    collapsbtns.forEach(function (element) {
        element.addEventListener("click", function () {
            var collapsible = element.closest('.collapsible')
            collapsible.classList.toggle("hidden");

            var isHidden = collapsible.classList.contains("hidden");
            localStorage.setItem(collapsible.id + "-state", isHidden);
            console.log("SET", collapsible.id + "-state", isHidden);
        });
    });
});

// Close the dropdown menu if the user clicks outside of it
window.onclick = function(event) {
  if (!event.target.matches('.dropbtn')) {
    var dropdowns = document.getElementsByClassName("dropdown");
    for (let element of dropdowns) {
        element.classList.add('hidden');
    }
  }
}

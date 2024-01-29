const collapsbtns = document.querySelectorAll(".collapsible");
collapsbtns.forEach(function (collapsible) {
    var isHidden = localStorage.getItem(collapsible.id + "-state");
    isHidden = JSON.parse(isHidden);
    collapsible.classList.toggle("hidden", isHidden);
});

const filterbar = document.getElementById("problem-filter");
const toggle = document.getElementById("filter-toggle");
filterbar.addEventListener("click", () => {
	filterbar.classList.toggle("hide");
	toggle.textContent = filterbar.classList.contains("hide") ? "+" : "-";
});

document.querySelectorAll(".language-menu").forEach((menu) => {
  const button = menu.querySelector("button");
  button.addEventListener("click", () => {
    const open = menu.classList.toggle("open");
    button.setAttribute("aria-expanded", String(open));
  });
});

document.addEventListener("click", (event) => {
  document.querySelectorAll(".language-menu.open").forEach((menu) => {
    if (!menu.contains(event.target)) {
      menu.classList.remove("open");
      menu.querySelector("button").setAttribute("aria-expanded", "false");
    }
  });
});

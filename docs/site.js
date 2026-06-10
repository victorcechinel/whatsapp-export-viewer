document.querySelectorAll(".language-menu").forEach((menu) => {
  const button = menu.querySelector("button");
  button.addEventListener("click", () => {
    const open = menu.classList.toggle("open");
    button.setAttribute("aria-expanded", String(open));
  });

  menu.querySelectorAll("[data-lang]").forEach((link) => {
    link.addEventListener("click", (event) => {
      const lang = link.getAttribute("data-lang");
      if (!lang || window.location.protocol === "file:") {
        return;
      }

      const basePath = menu.getAttribute("data-site-base") || "/";
      const isProjectPage = window.location.pathname.startsWith(basePath);
      if (!isProjectPage) {
        return;
      }

      event.preventDefault();
      window.location.assign(`${basePath}${lang}/`);
    });
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

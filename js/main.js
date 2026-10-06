/**
 * Main application logic for La Première Brique.
 * Handles scroll effects, mobile hamburger menus, interactive sliders,
 * number formatting, and translations.
 */

document.addEventListener("DOMContentLoaded", () => {
  // --- 0. Remove Store Badges & Social Links ---
  document.querySelectorAll(".hero_main_btns, .footer_head_stores, .footer_head_socials").forEach((block) => {
    block.remove();
  });

  const navbarEl = document.getElementById("navbar");

  document.querySelectorAll('a[href*="lapremierebrique.fr"]').forEach((link) => {
    const href = link.getAttribute("href") || "";
    if (href.includes("users/sign_in")) link.setAttribute("href", "/login.html");
    else if (href.includes("users/sign_up")) link.setAttribute("href", "/signup.html");
    else if (href.includes("projects") || href.includes("investir")) link.setAttribute("href", "/projects.html");
    else if (href.includes("se-financer")) link.setAttribute("href", "/se-financer.html");
    else if (href.includes("blog")) link.setAttribute("href", "/blog.html");
    else if (href.includes("a-propos")) link.setAttribute("href", "/a-propos.html");
    else link.setAttribute("href", "/");
    link.removeAttribute("target");
  });

  // --- 1. Navbar Scroll Transition ---
  const logoIcon = document.querySelector(".navbar_home_logo.logo");
  const hamburgerIcon = document.querySelector(".navbar_mobile_hamburger");
  const cta1 = navbarEl ? navbarEl.querySelector(".navbar_cta_1") : null;
  const cta2 = navbarEl ? navbarEl.querySelector(".navbar_cta_2") : null;
  const variation = navbarEl ? navbarEl.getAttribute("data-wf--component-navbar-main--variant") : "transparent";

  function handleScroll() {
    if (!navbarEl) return;
    if (window.scrollY === 0) {
      navbarEl.classList.remove("is-scrolled");
      navbarEl.style.backgroundColor = "transparent";

      if (variation === "transparent") {
        if (logoIcon) logoIcon.style.color = "#A42515";
        navbarEl.style.color = "#101010";
        if (hamburgerIcon) hamburgerIcon.style.color = "#101010";
      }
      if (variation === "white") {
        if (logoIcon) logoIcon.style.color = "white";
        navbarEl.style.color = "white";
        if (cta1) cta1.classList.remove("is-scrolled");
        if (cta2) cta2.classList.remove("is-scrolled");
        if (hamburgerIcon) hamburgerIcon.style.color = "white";
      }
    } else {
      navbarEl.classList.add("is-scrolled");
      if (logoIcon) logoIcon.style.color = "#A42515";
      navbarEl.style.backgroundColor = "white";
      navbarEl.style.color = "#101010";
      if (hamburgerIcon) hamburgerIcon.style.color = "#101010";

      if (variation === "white") {
        if (cta1) cta1.classList.add("is-scrolled");
        if (cta2) cta2.classList.add("is-scrolled");
      }
    }
  }

  window.addEventListener("scroll", handleScroll, { passive: true });
  handleScroll();

  // --- 2. Mobile Hamburger Toggle ---
  const navbarWrapperContent = document.querySelector(".navbar_wrapper_content");

  if (hamburgerIcon && navbarWrapperContent) {
    hamburgerIcon.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const isOpen = hamburgerIcon.classList.toggle("w--open");
      navbarWrapperContent.classList.toggle("w--open", isOpen);
      document.body.style.overflow = isOpen ? "hidden" : "";
    });
  }

  // --- 3. Desktop Dropdown Menus (hover to open) ---
  if (window.innerWidth >= 992) {
    const dropdownWrappers = document.querySelectorAll(".navbar_menu_dropdown.link, .w-dropdown");
    dropdownWrappers.forEach((wrapper) => {
      const toggle = wrapper.querySelector(".navbar_menu_dropdown-toggle, .w-dropdown-toggle");
      const menu = wrapper.querySelector(".w-dropdown-list, .navbar_menu_dropdown.lightbox");

      if (!toggle || !menu) return;

      wrapper.addEventListener("mouseenter", () => {
        toggle.classList.add("w--open");
        menu.classList.add("w--open");
        menu.style.display = "flex";
        menu.style.opacity = "1";
        menu.style.visibility = "visible";
      });

      wrapper.addEventListener("mouseleave", () => {
        toggle.classList.remove("w--open");
        menu.classList.remove("w--open");
        menu.style.display = "";
        menu.style.opacity = "";
        menu.style.visibility = "";
      });
    });
  }

  // --- 3b. Mobile Dropdown Toggle (click) ---
  const dropdownToggles = document.querySelectorAll(".navbar_menu_dropdown-toggle");
  dropdownToggles.forEach((toggle) => {
    toggle.addEventListener("click", (e) => {
      if (window.innerWidth < 992) {
        e.preventDefault();
        e.stopPropagation();

        const parent = toggle.parentElement;
        const menu = parent.querySelector(".w-dropdown-list, .navbar_menu_dropdown.lightbox");

        toggle.classList.toggle("w--open");
        if (menu) {
          const isMenuOpen = menu.style.display === "flex" || menu.style.display === "block";
          menu.style.display = isMenuOpen ? "none" : "flex";
          menu.style.flexDirection = "column";
        }
      }
    });
  });

  // --- 4. Number Formatting (1075000 -> 1 075 000) ---
  function formatNumbers() {
    const elements = document.querySelectorAll("[data-format-number]");
    elements.forEach((el) => {
      const rawText = el.innerText.trim();
      const number = parseFloat(rawText);
      if (!isNaN(number)) {
        el.innerText = number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
      }
    });
  }
  formatNumbers();

  // --- 5. Date Translations for Blog Articles ---
  const monthMap = {
    January: "Janvier",
    February: "Février",
    March: "Mars",
    April: "Avril",
    May: "Mai",
    June: "Juin",
    July: "Juillet",
    August: "Août",
    September: "Septembre",
    October: "Octobre",
    November: "Novembre",
    December: "Décembre",
  };

  function translateDates() {
    const dateElements = document.querySelectorAll("[data-article-date]");
    dateElements.forEach((el) => {
      const text = el.innerText.trim();
      const parts = text.split(" ");
      if (parts.length === 2) {
        const [monthEn, year] = parts;
        const monthFr = monthMap[monthEn];
        if (monthFr) {
          el.innerText = `${monthFr} ${year}`;
        }
      }
    });
  }
  translateDates();

  // --- 6. Custom Project Scroll Slider Logic (Autoplay + pagination) ---
  const projectSliders = document.querySelectorAll(".section_slider_main");
  projectSliders.forEach((section) => {
    const cards = Array.from(section.querySelectorAll(".slider_main_card"));
    const counterContainer = section.querySelector(".slider_main_counter");
    if (!cards.length || !counterContainer) return;

    let activeIndex = 0;
    const bulletContainer = document.createElement("div");
    bulletContainer.className = "slider_bullets";

    // Create bullets
    cards.forEach((card, idx) => {
      const bullet = document.createElement("button");
      bullet.className = `slider_bullet ${idx === 0 ? "is-active" : ""}`;
      bullet.addEventListener("click", () => {
        setActiveSlide(idx);
      });
      bulletContainer.appendChild(bullet);
    });

    counterContainer.appendChild(bulletContainer);

    // Style elements
    const style = document.createElement("style");
    style.innerHTML = `
      .slider_bullets {
        display: flex;
        gap: 8px;
        margin-top: 15px;
        justify-content: center;
      }
      .slider_bullet {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: rgba(16, 16, 16, 0.3);
        border: none;
        padding: 0;
        cursor: pointer;
        transition: background-color 0.3s, transform 0.3s;
      }
      .slider_bullet.is-active {
        background-color: var(--color-primary);
        transform: scale(1.2);
      }
      .slider_main_card {
        display: none;
        opacity: 0;
        transition: opacity 0.5s ease;
      }
      .slider_main_card.is-active {
        display: flex !important;
        opacity: 1;
      }
      .slider_main_progress_bar_fill {
        height: 100%;
        background-color: var(--color-primary);
        border-radius: 4px;
      }
    `;
    document.head.appendChild(style);

    function setActiveSlide(idx) {
      cards[activeIndex].classList.remove("is-active");
      bulletContainer.children[activeIndex].classList.remove("is-active");

      activeIndex = idx;

      cards[activeIndex].classList.add("is-active");
      bulletContainer.children[activeIndex].classList.add("is-active");

      // Update count text
      const countText = counterContainer.querySelector(".slider_main_count_text");
      if (countText) {
        countText.innerText = (activeIndex + 1).toString();
      }

      // Animate progress bar fill inside active slide
      const fillBar = cards[activeIndex].querySelector(".slider_main_progress_bar_fill");
      const pctText = cards[activeIndex].querySelector(".slider_main_progress_percentage.percentage-number");
      if (fillBar && pctText) {
        const percentage = parseFloat(pctText.innerText) || 0;
        fillBar.style.width = "0%";
        setTimeout(() => {
          fillBar.style.width = `${Math.min(percentage, 100)}%`;
        }, 50);
      }
    }

    // Initialize first slide progress
    setActiveSlide(0);

    // Autoplay
    let interval = setInterval(() => {
      let nextIdx = (activeIndex + 1) % cards.length;
      setActiveSlide(nextIdx);
    }, 8000);

    section.addEventListener("mouseenter", () => clearInterval(interval));
    section.addEventListener("mouseleave", () => {
      interval = setInterval(() => {
        let nextIdx = (activeIndex + 1) % cards.length;
        setActiveSlide(nextIdx);
      }, 8000);
    });
  });
});

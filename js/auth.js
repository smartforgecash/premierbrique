/**
 * Django-backed authentication UI.
 * Keeps the exported frontend intact while reflecting server session state.
 */

const Auth = {
  init() {
    this.loadSession();
    this.setupSignupEmailForm();
    this.setupOauthPlaceholders();
  },

  getCookie(name) {
    const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
    return match ? decodeURIComponent(match[1]) : "";
  },

  logout() {
    const csrfToken = this.getCookie("csrftoken");
    fetch("/logout/", {
      method: "POST",
      credentials: "same-origin",
      headers: csrfToken ? { "X-CSRFToken": csrfToken } : {},
    }).finally(() => {
      window.location.href = "/";
    });
  },

  async loadSession() {
    try {
      const response = await fetch("/auth/session.json", {
        credentials: "same-origin",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) return;

      const session = await response.json();
      this.updateNavbar(session);
      this.showServerMessages(session.messages || []);
    } catch (error) {
      // Keep the static export usable even if the backend endpoint is unavailable.
    }
  },

  updateNavbar(session) {
    const navbarEl = document.getElementById("navbar");
    if (!navbarEl || !session.authenticated) return;

    const cta1 = navbarEl.querySelector(".navbar_cta_1");
    const cta2 = navbarEl.querySelector(".navbar_cta_2");

    if (cta1) {
      cta1.style.display = "none";
    }

    if (!cta2) return;

    const cta2Text = cta2.querySelector(".button_text");
    if (cta2Text) {
      cta2Text.innerText = "Compte";
    }

    cta2.setAttribute("href", "/account/");
    cta2.classList.add("navbar_account_btn");

    let accountDropdown = navbarEl.querySelector(".navbar_account_dropdown");
    if (!accountDropdown) {
      accountDropdown = document.createElement("div");
      accountDropdown.className = "navbar_account_dropdown";
      accountDropdown.innerHTML = `
        <div class="navbar_account_dropdown_header">
          <span class="user_email_display">${session.email || "briqueur@email.com"}</span>
        </div>
        <div class="navbar_account_dropdown_body">
          <a href="/account/" class="navbar_account_item"><i class="ph ph-user"></i> Mon compte</a>
          <a href="/wallet/" class="navbar_account_item"><i class="ph ph-wallet"></i> Porte-monnaie</a>
          <a href="/investments/" class="navbar_account_item"><i class="ph ph-chart-line-up"></i> Mes investissements</a>
          <a href="/projects.html" class="navbar_account_item"><i class="ph ph-buildings"></i> Projets</a>
          <hr class="dropdown-divider">
          <button type="button" class="navbar_account_item text-danger navbar_logout_btn"><i class="ph ph-sign-out"></i> Déconnexion</button>
        </div>
      `;
      cta2.parentElement.appendChild(accountDropdown);
      this.injectAccountStyles();

      accountDropdown.querySelector(".navbar_logout_btn")?.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        this.logout();
      });

      cta2.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        accountDropdown.classList.toggle("is-active");
      });

      document.addEventListener("click", () => {
        accountDropdown.classList.remove("is-active");
      });
    }
  },

  injectAccountStyles() {
    if (document.getElementById("django-auth-styles")) return;

    const style = document.createElement("style");
    style.id = "django-auth-styles";
    style.innerHTML = `
      .navbar_btns_wrapper { position: relative; }
      .navbar_account_dropdown {
        display: none;
        position: absolute;
        top: calc(100% + 10px);
        right: 0;
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        width: 220px;
        z-index: 1010;
        overflow: hidden;
        font-family: "Manrope", sans-serif;
      }
      .navbar_account_dropdown.is-active {
        display: block;
        animation: dropdownFade 0.2s ease forwards;
      }
      @keyframes dropdownFade {
        from { opacity: 0; transform: translateY(5px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .navbar_account_dropdown_header {
        padding: 12px 16px;
        background-color: #fbf5ee;
        border-bottom: 1px solid #e0e0e0;
        font-size: 0.8rem;
        color: #101010;
        font-weight: 600;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .navbar_account_item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 16px;
        color: #101010;
        text-decoration: none;
        font-size: 0.9rem;
        transition: background-color 0.2s;
        width: 100%;
        border: 0;
        background: transparent;
        text-align: left;
        cursor: pointer;
        font-family: inherit;
      }
      .navbar_account_item:hover {
        background-color: #f5f5f5;
        color: #A42515;
        text-decoration: none;
      }
      .navbar_account_item.text-danger:hover {
        color: #dc3545;
        background-color: #ffeef0;
      }
      .dropdown-divider {
        margin: 4px 0;
        border-top: 1px solid #e0e0e0;
      }
    `;
    document.head.appendChild(style);
  },

  showServerMessages(messages) {
    messages.forEach((message) => {
      this.showAlert(message.text, message.level || "info");
    });
  },

  setupOauthPlaceholders() {
    const oauthButtons = document.querySelectorAll(
      '.btn-outline-dark[rel="nofollow"], button[onclick*="Median.socialLogin"]'
    );
    oauthButtons.forEach((button) => {
      button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        const text = button.textContent.toLowerCase();
        const inlineAction = button.getAttribute("onclick") || "";
        if (text.includes("google") || inlineAction.includes("google")) {
          window.location.href = "/login/google/";
        } else {
          this.showAlert("Connexion externe indisponible.", "info");
        }
      });
    });
  },

  setupSignupEmailForm() {
    const form = document.getElementById("signup-email-form");
    if (!form) return;

    const emailInput = document.getElementById("user_registration_email");
    const passwordInput = document.getElementById("user_registration_password");
    const passwordConfirmationInput = document.getElementById("user_registration_password_confirmation");
    const termsCheckbox = document.getElementById("user_registration_terms_accepted");
    const submitButton =
      form.querySelector('[data-user-registration-target="submitButton"]') ||
      form.querySelector('button[type="submit"]');

    const urlParams = new URLSearchParams(window.location.search);
    const emailParam = urlParams.get("email");
    if (emailParam && emailInput) {
      emailInput.value = emailParam;
    }

    const validate = () => {
      if (!emailInput || !termsCheckbox || !submitButton) return;

      const email = emailInput.value.trim();
      const emailLooksValid = email.includes("@") && email.includes(".");
      const passwordLooksValid = !passwordInput || passwordInput.value.length >= 8;
      const passwordsMatch = !passwordConfirmationInput || passwordInput.value === passwordConfirmationInput.value;
      if (emailLooksValid && passwordLooksValid && passwordsMatch && termsCheckbox.checked) {
        submitButton.removeAttribute("disabled");
      } else {
        submitButton.setAttribute("disabled", "disabled");
      }
    };

    emailInput?.addEventListener("input", validate);
    passwordInput?.addEventListener("input", validate);
    passwordConfirmationInput?.addEventListener("input", validate);
    termsCheckbox?.addEventListener("change", validate);
    validate();
  },

  showAlert(message, type = "info") {
    const existing = document.querySelector(".auth-alert");
    if (existing) existing.remove();

    const alertDiv = document.createElement("div");
    const normalizedType = type.includes("error") ? "danger" : type.includes("success") ? "success" : "info";
    alertDiv.className = `auth-alert alert alert-${normalizedType} py-3 px-4`;
    alertDiv.setAttribute("role", "alert");
    alertDiv.style.position = "fixed";
    alertDiv.style.top = "20px";
    alertDiv.style.left = "50%";
    alertDiv.style.transform = "translateX(-50%)";
    alertDiv.style.zIndex = "2000";
    alertDiv.style.boxShadow = "0 10px 25px rgba(0,0,0,0.1)";
    alertDiv.style.border = "none";
    alertDiv.style.borderRadius = "8px";

    if (normalizedType === "success") {
      alertDiv.style.backgroundColor = "#d4edda";
      alertDiv.style.color = "#155724";
    } else if (normalizedType === "danger") {
      alertDiv.style.backgroundColor = "#f8d7da";
      alertDiv.style.color = "#721c24";
    } else {
      alertDiv.style.backgroundColor = "#e2e3e5";
      alertDiv.style.color = "#383d41";
    }

    alertDiv.innerText = message;
    document.body.appendChild(alertDiv);

    setTimeout(() => {
      alertDiv.style.opacity = "0";
      alertDiv.style.transition = "opacity 0.5s ease";
      setTimeout(() => alertDiv.remove(), 500);
    }, 3000);
  },
};

document.addEventListener("DOMContentLoaded", () => {
  Auth.init();
});

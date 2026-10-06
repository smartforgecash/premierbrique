from pathlib import Path

workspace = Path(__file__).resolve().parent.parent
main_js_path = workspace / "js" / "main.js"

if main_js_path.exists():
    content = main_js_path.read_text(encoding="utf-8")
    
    # 1. Replace the rewrite block
    rewrite_target = """  // --- 0b. Standalone navbar: same public structure, local app routes only. ---
  const navbarEl = document.getElementById("navbar");
  if (navbarEl) {
    const originalBrand = navbarEl.querySelector(".navbar_home_link")?.innerHTML || `
      <span class="pb-brand-symbol" aria-hidden="true"></span>
      <span class="pb-brand-text">la première brique</span>
    `;
    navbarEl.innerHTML = `
      <div class="pb-navbar-inner">
        <a class="pb-brand" href="/" aria-label="Accueil Premier Brique">
          ${originalBrand}
        </a>
        <button class="pb-menu-toggle" type="button" aria-label="Menu">
          <span></span><span></span><span></span>
        </button>
        <nav class="pb-nav-links" aria-label="Navigation principale">
          <a href="/projects.html">Projets</a>
          <div class="pb-nav-item">
            <button type="button" aria-expanded="false">Nos solutions</button>
            <div class="pb-dropdown">
              <a href="/investir.html">Immobilier locatif nouvelle génération</a>
              <a href="/se-financer.html">Financement d'opérations immobilières</a>
            </div>
          </div>
          <div class="pb-nav-item">
            <button type="button" aria-expanded="false">Comment ça marche ?</button>
            <div class="pb-dropdown">
              <a href="/investir.html">Investir</a>
              <a href="/se-financer.html">Se financer</a>
            </div>
          </div>
          <div class="pb-nav-item">
            <button type="button" aria-expanded="false">Ressources</button>
            <div class="pb-dropdown">
              <a href="/blog.html">Blog & Actualités</a>
              <a href="/performances.html">Performances</a>
              <a href="/risques.html">Risques</a>
            </div>
          </div>
          <a href="/a-propos.html">À propos</a>
        </nav>
        <div class="pb-nav-actions">
          <a class="pb-btn pb-btn-outline navbar_cta_1" href="/login.html">Connexion</a>
          <a class="pb-btn pb-btn-primary navbar_cta_2" href="/signup.html">Rejoindre les briqueurs</a>
        </div>
      </div>
    `;

    navbarEl.querySelectorAll(".pb-nav-item > button").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.preventDefault();
        const item = button.closest(".pb-nav-item");
        const isOpen = item.classList.toggle("is-open");
        button.setAttribute("aria-expanded", isOpen ? "true" : "false");
        navbarEl.querySelectorAll(".pb-nav-item").forEach((other) => {
          if (other !== item) {
            other.classList.remove("is-open");
            other.querySelector("button")?.setAttribute("aria-expanded", "false");
          }
        });
      });
    });

    document.addEventListener("click", (event) => {
      if (!navbarEl.contains(event.target)) {
        navbarEl.querySelectorAll(".pb-nav-item").forEach((item) => {
          item.classList.remove("is-open");
          item.querySelector("button")?.setAttribute("aria-expanded", "false");
        });
      }
    });
  }"""
    
    rewrite_replacement = """  const navbarEl = document.getElementById("navbar");"""
    
    if rewrite_target in content:
        content = content.replace(rewrite_target, rewrite_replacement)
        print("Replaced rewrite block in main.js")
    else:
        # Normalize newlines and try replacing
        content_norm = content.replace("\r\n", "\n")
        rewrite_target_norm = rewrite_target.replace("\r\n", "\n")
        if rewrite_target_norm in content_norm:
            content = content_norm.replace(rewrite_target_norm, rewrite_replacement)
            print("Replaced rewrite block in main.js (normalized newlines)")
        else:
            print("Warning: Could not find exact rewrite block in main.js")
            
    # 2. Replace pb-menu-toggle selector
    hamburger_target = 'const hamburgerIcon = document.querySelector(".pb-menu-toggle");'
    hamburger_replacement = 'const hamburgerIcon = document.querySelector(".navbar_mobile_hamburger");'
    if hamburger_target in content:
        content = content.replace(hamburger_target, hamburger_replacement)
        print("Updated hamburger selector in main.js")
    
    # 3. Replace mobile toggle event handler
    toggle_target = """  // --- 2. Mobile Hamburger Toggle ---
  const navbarWrapperContent = document.querySelector(".pb-nav-links");

  if (hamburgerIcon && navbarWrapperContent) {
    hamburgerIcon.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const isOpen = hamburgerIcon.classList.toggle("w--open");
      navbarWrapperContent.classList.toggle("is-open", isOpen);
      document.body.style.overflow = isOpen ? "hidden" : "";
    });
  }"""
    
    toggle_replacement = """  // --- 2. Mobile Hamburger Toggle ---
  const navbarWrapperContent = document.querySelector(".navbar_wrapper_content");

  if (hamburgerIcon && navbarWrapperContent) {
    hamburgerIcon.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const isOpen = hamburgerIcon.classList.toggle("w--open");
      navbarWrapperContent.classList.toggle("w--open", isOpen);
      document.body.style.overflow = isOpen ? "hidden" : "";
    });
  }"""
    
    if toggle_target in content:
        content = content.replace(toggle_target, toggle_replacement)
        print("Updated mobile toggle block in main.js")
    else:
        content_norm = content.replace("\r\n", "\n")
        toggle_target_norm = toggle_target.replace("\r\n", "\n")
        if toggle_target_norm in content_norm:
            content = content_norm.replace(toggle_target_norm, toggle_replacement)
            print("Updated mobile toggle block in main.js (normalized newlines)")
        else:
            print("Warning: Could not find exact toggle block in main.js")
            
    main_js_path.write_text(content, encoding="utf-8")
    print("main.js modification completed")

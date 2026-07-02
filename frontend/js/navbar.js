function renderNavbar(active) {
  const links = [
    { href: "dashboard.html", label: "Dashboard" },
    { href: "expenses.html", label: "Expenses" },
    { href: "bins.html", label: "Bin Schedule" },
  ];

  const linkHtml = links.map(l =>
    `<li class="nav-item"><a class="nav-link ${active === l.href ? "active fw-bold" : ""}" href="${l.href}">${l.label}</a></li>`
  ).join("");

  document.getElementById("navbar").innerHTML = `
    <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm mb-4">
      <div class="container">
        <a class="navbar-brand" href="dashboard.html">🇮🇪 Student Hub</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navContent">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navContent">
          <ul class="navbar-nav me-auto">${linkHtml}</ul>
          <button class="btn btn-outline-secondary btn-sm" onclick="logout()">Log Out</button>
        </div>
      </div>
    </nav>`;
}

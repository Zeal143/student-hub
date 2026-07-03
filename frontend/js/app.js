const Hub = {
  API_BASE: "http://localhost:5000/api",

  KEYS: {
    token: "hub_token",
    user: "hub_user_cache"
  },

  /* ---------------- low-level fetch helper ---------------- */
  async apiFetch(path, options = {}) {
    const headers = options.headers || {};
    headers["Content-Type"] = "application/json";
    const token = localStorage.getItem(this.KEYS.token);
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${this.API_BASE}${path}`, { ...options, headers });

    if (res.status === 401) {
      localStorage.removeItem(this.KEYS.token);
      localStorage.removeItem(this.KEYS.user);
      window.location.href = "index.html";
      return null;
    }

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.error || "Something went wrong. Please try again.");
    }
    return data;
  },

  /* ---------------- auth ---------------- */
  async register(name, email, password) {
    return this.apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password })
    });
  },

  async login(email, password) {
    const data = await this.apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
    localStorage.setItem(this.KEYS.token, data.access_token);
    localStorage.setItem(this.KEYS.user, JSON.stringify(data.user));
    return data.user;
  },

  currentUser() {
    const raw = localStorage.getItem(this.KEYS.user);
    return raw ? JSON.parse(raw) : null;
  },

  async refreshUser() {
    const user = await this.apiFetch("/auth/me");
    if (user) localStorage.setItem(this.KEYS.user, JSON.stringify(user));
    return user;
  },

  logout() {
    localStorage.removeItem(this.KEYS.token);
    localStorage.removeItem(this.KEYS.user);
    window.location.href = "index.html";
  },

  requireAuth() {
    if (!localStorage.getItem(this.KEYS.token)) {
      window.location.href = "index.html";
    }
  },

  /* ---------------- categories ---------------- */
  async getCategories() {
    return this.apiFetch("/categories");
  },

  /* ---------------- expenses ---------------- */
  async getExpenses() {
    return this.apiFetch("/expenses");
  },

  async addExpense({ amount, category_id, date, description }) {
    return this.apiFetch("/expenses", {
      method: "POST",
      body: JSON.stringify({ amount, category_id, date, description })
    });
  },

  async deleteExpense(id) {
    return this.apiFetch(`/expenses/${id}`, { method: "DELETE" });
  },

  async spendingByCategory() {
    return this.apiFetch("/expenses/summary");
  },

  spendingByWeekFrom(expenses, weeks = 4) {
    // Computed client-side from an already-fetched expenses list.
    const labels = [];
    const totals = [];
    const now = new Date();
    for (let i = weeks - 1; i >= 0; i--) {
      const end = new Date(now);
      end.setDate(end.getDate() - i * 7);
      const start = new Date(end);
      start.setDate(start.getDate() - 6);
      const sum = expenses
        .filter(e => {
          const d = new Date(e.date);
          return d >= start && d <= end;
        })
        .reduce((s, e) => s + Number(e.amount), 0);
      labels.push(`${start.getDate()}/${start.getMonth() + 1}`);
      totals.push(Math.round(sum * 100) / 100);
    }
    return { labels, totals };
  },

  /* ---------------- budgets ---------------- */
  async getBudgets() {
    // Backend already computes spent/remaining/over_budget per category.
    return this.apiFetch("/budgets");
  },

  async setBudget(category_id, monthly_limit) {
    return this.apiFetch("/budgets", {
      method: "POST",
      body: JSON.stringify({ category_id, monthly_limit })
    });
  },

  budgetStatus(pct) {
    if (pct >= 100) return "progress-over";
    if (pct >= 80) return "progress-warn";
    return "progress-ok";
  },

  /* ---------------- savings goals ---------------- */
  async getGoals() {
    return this.apiFetch("/savings");
  },

  async addGoal({ name, target_amount, target_date }) {
    return this.apiFetch("/savings", {
      method: "POST",
      body: JSON.stringify({ name, target_amount, target_date })
    });
  },

  async updateGoal(id, { current_amount, target_amount }) {
    const body = {};
    if (current_amount !== undefined) body.current_amount = current_amount;
    if (target_amount !== undefined) body.target_amount = target_amount;
    return this.apiFetch(`/savings/${id}`, {
      method: "PUT",
      body: JSON.stringify(body)
    });
  },

  async deleteGoal(id) {
    return this.apiFetch(`/savings/${id}`, { method: "DELETE" });
  },

  /* ---------------- bin schedule ---------------- */
  async getProviders() {
    return this.apiFetch("/bins/providers");
  },

  async setBinInfo(eircode, provider_id) {
    return this.apiFetch("/bins/settings", {
      method: "POST",
      body: JSON.stringify({ eircode, provider_id })
    });
  },

  async getSchedule() {
    // Returns [{bin_type, colour, collection_date, provider_name, ...}, ...]
    return this.apiFetch("/bins/schedule");
  },

  BIN_LABELS: {
    general: { label: "General waste", icon: "ti-trash", cls: "general" },
    recycling: { label: "Recycling", icon: "ti-recycle", cls: "recycling" },
    organic: { label: "Organic / food", icon: "ti-leaf", cls: "organic" }
  },

  formatDate(isoDateString) {
    const date = new Date(isoDateString + "T00:00:00");
    return date.toLocaleDateString("en-IE", { weekday: "short", day: "numeric", month: "short" });
  },

  /* ---------------- dashboard (combined) ---------------- */
  async getDashboard() {
    return this.apiFetch("/dashboard");
  },

  /* ---------------- navbar ---------------- */
  renderNavbar(active) {
    const user = this.currentUser();
    const initials = user ? user.name.split(" ").map(p => p[0]).slice(0, 2).join("").toUpperCase() : "?";
    const links = [
      { href: "dashboard.html", label: "Dashboard", key: "dashboard" },
      { href: "expenses.html", label: "Expenses", key: "expenses" },
      { href: "bins.html", label: "Bins", key: "bins" },
      { href: "account.html", label: "Account", key: "account" }
    ];
    const linkHtml = links.map(l =>
      `<a class="nav-link ${l.key === active ? "active" : ""}" href="${l.href}">${l.label}</a>`
    ).join("");

    const el = document.getElementById("navbar");
    if (!el) return;
    el.innerHTML = `
      <nav class="hub-navbar navbar navbar-expand-md py-2">
        <div class="container-fluid px-3 px-md-4">
          <a class="brand" href="dashboard.html">
            <span class="brand-mark">SH</span>
            Student hub
          </a>
          <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#hubNav">
            <span class="navbar-toggler-icon"></span>
          </button>
          <div class="collapse navbar-collapse" id="hubNav">
            <div class="navbar-nav ms-md-auto d-flex flex-md-row gap-1 mt-2 mt-md-0 align-items-md-center">
              ${linkHtml}
              <div class="d-flex align-items-center gap-2 ms-md-3 mt-2 mt-md-0">
                <span class="hub-user-pill">${initials}</span>
                <button class="btn btn-sm btn-hub-outline" onclick="Hub.logout()">
                  <i class="ti ti-logout-2" style="font-size:14px; vertical-align:-2px;"></i> Log out
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>`;
  }
};

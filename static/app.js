const app = document.querySelector("#app");
let state = { user: null, view: "dashboard", data: {}, query: "" };

const money = value => new Intl.NumberFormat("en-IN", {
  style: "currency", currency: "INR", maximumFractionDigits: 0
}).format(value || 0);

const api = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  if (response.status === 204) return null;
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Request failed");
  return payload;
};

const toast = message => {
  const node = document.createElement("div");
  node.className = "toast";
  node.textContent = message;
  document.body.appendChild(node);
  setTimeout(() => node.remove(), 2600);
};

const titleCase = text => String(text || "").replaceAll("_", " ");

async function boot() {
  const { user } = await api("/api/me");
  state.user = user;
  if (!user) return renderLogin();
  await loadData();
  renderShell();
}

function renderLogin() {
  app.innerHTML = document.querySelector("#login-template").innerHTML;
  const form = document.querySelector("#login-form");
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const body = Object.fromEntries(new FormData(form).entries());
    try {
      const { user } = await api("/api/login", { method: "POST", body: JSON.stringify(body) });
      state.user = user;
      await loadData();
      renderShell();
    } catch (error) {
      document.querySelector("#login-error").textContent = error.message;
    }
  });
  document.querySelectorAll("[data-login]").forEach(button => {
    button.addEventListener("click", () => {
      const [email, password] = button.dataset.login.split("|");
      form.email.value = email;
      form.password.value = password;
    });
  });
}

async function loadData() {
  const common = [
    api("/api/dashboard"),
    api("/api/scholarships"),
    api("/api/applications"),
    api("/api/notifications")
  ];
  if (state.user.role !== "student") common.push(api("/api/students"));
  if (state.user.role === "admin") common.push(api("/api/audit-logs"));
  const [dashboard, scholarships, applications, notifications, students, audit] = await Promise.all(common);
  state.data = {
    dashboard,
    scholarships: scholarships.scholarships,
    applications: applications.applications,
    notifications: notifications.notifications,
    students: students?.students || [],
    audit: audit?.logs || []
  };
}

function renderShell() {
  const navItems = [
    ["dashboard", "Dashboard"],
    ["scholarships", "Scholarships"],
    ["applications", "Applications"],
    ...(state.user.role !== "student" ? [["students", "Students"]] : []),
    ...(state.user.role === "admin" ? [["admin", "Administration"]] : [])
  ];
  app.innerHTML = `
    <section class="shell">
      <aside class="sidebar">
        <div class="brand"><span>SMS</span><div><h2>Scholarship Cell</h2><p>DBMS Portal</p></div></div>
        <nav class="nav">
          ${navItems.map(([id, label]) => `<button class="${state.view === id ? "active" : ""}" data-view="${id}">${label}</button>`).join("")}
        </nav>
        <button class="logout" id="logout">Sign out</button>
      </aside>
      <section class="content">
        <header class="topbar">
          <div><h1>${navItems.find(([id]) => id === state.view)?.[1] || "Dashboard"}</h1><p>${subtitle()}</p></div>
          <div class="profile-pill"><div class="avatar">${state.user.name.split(" ").map(x => x[0]).slice(0,2).join("")}</div><div><strong>${state.user.name}</strong><p>${state.user.role} - ${state.user.department || "Institution"}</p></div></div>
        </header>
        <div id="view"></div>
      </section>
    </section>
  `;
  document.querySelectorAll("[data-view]").forEach(button => {
    button.addEventListener("click", () => {
      state.view = button.dataset.view;
      renderShell();
    });
  });
  document.querySelector("#logout").addEventListener("click", async () => {
    await api("/api/logout", { method: "POST" });
    state = { user: null, view: "dashboard", data: {}, query: "" };
    renderLogin();
  });
  renderView();
}

function subtitle() {
  const map = {
    dashboard: "Live institutional performance across awards, applications, reviews, and disbursements.",
    scholarships: "Create, publish, monitor, and apply for scholarship schemes.",
    applications: "Track applicant profiles, documents, scores, review decisions, and payment status.",
    students: "Verified student registry with academic and financial profile data.",
    admin: "Administrative controls, new scheme setup, and audit trail."
  };
  return map[state.view];
}

function renderView() {
  const container = document.querySelector("#view");
  const views = {
    dashboard: renderDashboard,
    scholarships: renderScholarships,
    applications: renderApplications,
    students: renderStudents,
    admin: renderAdmin
  };
  container.innerHTML = views[state.view]();
  bindView();
}

function renderDashboard() {
  const { stats, pipeline, upcoming } = state.data.dashboard;
  return `
    <div class="grid stats">
      ${stat("Open Scholarships", stats.open_scholarships)}
      ${stat("Applications", stats.total_applications)}
      ${stat("Approved Awards", stats.approved)}
      ${stat("Funds Disbursed", money(stats.disbursed))}
    </div>
    <div class="grid two-col" style="margin-top:18px">
      <section class="card">
        <h2 class="section-title">Application Pipeline</h2>
        ${pipeline.map(row => `<div class="pipeline-row"><strong>${titleCase(row.status)}</strong><span class="badge ${row.status}">${row.total}</span></div>`).join("") || empty("No application data yet")}
      </section>
      <section class="card">
        <h2 class="section-title">Upcoming Deadlines</h2>
        ${upcoming.map(item => `<div class="list-row"><div><strong>${item.title}</strong><div class="meta">${item.provider} - ${money(item.amount)}</div></div><span>${item.deadline}</span></div>`).join("")}
      </section>
    </div>
  `;
}

function stat(label, value) {
  return `<section class="card stat"><div class="label">${label}</div><div class="value">${value}</div></section>`;
}

function renderScholarships() {
  const filtered = state.data.scholarships.filter(s =>
    `${s.title} ${s.provider} ${s.eligibility}`.toLowerCase().includes(state.query.toLowerCase())
  );
  return `
    <div class="toolbar">
      <input class="search" id="search" placeholder="Search scholarships..." value="${state.query}">
      ${state.user.role === "admin" ? `<button class="primary" style="width:auto;margin:0" data-view="admin">Create Scholarship</button>` : ""}
    </div>
    <div class="grid scholarship-grid">
      ${filtered.map(s => `
        <article class="card scholarship-card">
          <div><h3>${s.title}</h3><div class="meta">${s.provider} - Deadline ${s.deadline}</div></div>
          <div class="amount">${money(s.amount)}</div>
          <p>${s.eligibility}</p>
          <div class="facts">
            <div class="fact">Minimum CGPA<strong>${s.min_cgpa}</strong></div>
            <div class="fact">Income Limit<strong>${money(s.max_income)}</strong></div>
            <div class="fact">Seats<strong>${s.awarded}/${s.seats} awarded</strong></div>
            <div class="fact">Applications<strong>${s.applications}</strong></div>
          </div>
          <div class="inline-actions">
            <span class="badge ${s.status}">${s.status}</span>
            ${state.user.role === "student" && s.eligible ? `<button data-apply="${s.id}">Apply</button>` : ""}
            ${state.user.role === "student" && !s.eligible ? `<span class="badge rejected">Not eligible</span>` : ""}
          </div>
        </article>
      `).join("") || empty("No scholarships found")}
    </div>
  `;
}

function renderApplications() {
  return `
    <table>
      <thead><tr><th>Applicant</th><th>Scholarship</th><th>Profile</th><th>Documents</th><th>Status</th><th>Actions</th></tr></thead>
      <tbody>
        ${state.data.applications.map(a => `
          <tr>
            <td><strong>${a.student_name}</strong><div class="meta">${a.roll_number || ""}</div></td>
            <td><strong>${a.scholarship}</strong><div class="meta">${a.provider} - ${money(a.amount)}</div></td>
            <td>CGPA ${a.cgpa || "-"}<div class="meta">Income ${money(a.annual_income)}</div></td>
            <td><div class="documents">${a.documents.map(d => `<span>${d.document_type}: <span class="badge ${d.verification_status}">${d.verification_status}</span></span>`).join("")}</div></td>
            <td><span class="badge ${a.status}">${titleCase(a.status)}</span><div class="meta">Score ${a.score}/100 - Payment ${titleCase(a.payment_status)}</div></td>
            <td>${applicationActions(a)}</td>
          </tr>
        `).join("") || `<tr><td colspan="6">${empty("No applications yet")}</td></tr>`}
      </tbody>
    </table>
  `;
}

function applicationActions(a) {
  if (state.user.role === "student") return `<span class="meta">Submitted ${a.submitted_at}</span>`;
  const review = `
    <div class="inline-actions">
      <button class="neutral" data-review="${a.id}|under_review|75">Review</button>
      <button data-review="${a.id}|approved|90">Approve</button>
      <button class="danger" data-review="${a.id}|rejected|35">Reject</button>
    </div>
  `;
  const pay = state.user.role === "admin" && a.status === "approved"
    ? `<div class="inline-actions" style="margin-top:8px"><button data-disburse="${a.id}">Disburse</button></div>`
    : "";
  return review + pay;
}

function renderStudents() {
  return `
    <table>
      <thead><tr><th>Name</th><th>Course</th><th>Academics</th><th>Financial Profile</th><th>Applications</th></tr></thead>
      <tbody>${state.data.students.map(s => `
        <tr>
          <td><strong>${s.name}</strong><div class="meta">${s.email} - ${s.roll_number}</div></td>
          <td>${s.course}<div class="meta">Year ${s.year} - ${s.department}</div></td>
          <td><strong>${s.cgpa}</strong> CGPA</td>
          <td>${money(s.annual_income)}<div class="meta">${s.category}</div></td>
          <td><span class="badge">${s.applications}</span></td>
        </tr>`).join("")}</tbody>
    </table>
  `;
}

function renderAdmin() {
  return `
    <div class="grid two-col">
      <section class="card">
        <h2 class="section-title">Create Scholarship Scheme</h2>
        <form id="scholarship-form" class="form-grid">
          <label>Title<input name="title" required placeholder="Prime Merit Scholarship"></label>
          <label>Provider<input name="provider" required placeholder="University Trust"></label>
          <label>Amount<input name="amount" type="number" required value="85000"></label>
          <label>Seats<input name="seats" type="number" required value="25"></label>
          <label>Minimum CGPA<input name="min_cgpa" type="number" step="0.1" required value="8.0"></label>
          <label>Maximum Income<input name="max_income" type="number" required value="350000"></label>
          <label>Deadline<input name="deadline" type="date" required value="2026-08-30"></label>
          <label class="full">Eligibility<textarea name="eligibility" required>Academic merit, verified income certificate, and active enrollment required.</textarea></label>
          <button class="primary full" type="submit">Publish Scholarship</button>
        </form>
      </section>
      <section class="card">
        <h2 class="section-title">Audit Trail</h2>
        ${state.data.audit.map(log => `<div class="list-row"><div><strong>${log.action}</strong><div class="meta">${log.actor} - ${log.entity} #${log.entity_id || "-"}</div></div><span>${log.created_at}</span></div>`).join("") || empty("No audit activity yet")}
      </section>
    </div>
  `;
}

function empty(message) {
  return `<div class="meta">${message}</div>`;
}

function bindView() {
  document.querySelector("#search")?.addEventListener("input", event => {
    state.query = event.target.value;
    renderView();
  });
  document.querySelectorAll("[data-view]").forEach(button => {
    button.addEventListener("click", () => {
      state.view = button.dataset.view;
      renderShell();
    });
  });
  document.querySelectorAll("[data-apply]").forEach(button => {
    button.addEventListener("click", async () => {
      const purpose = prompt("Purpose of scholarship application", "I need this scholarship to support tuition fees, academic materials, project work, and professional certification expenses.");
      if (!purpose) return;
      await mutate("/api/applications", { scholarship_id: Number(button.dataset.apply), purpose }, "Application submitted");
    });
  });
  document.querySelectorAll("[data-review]").forEach(button => {
    button.addEventListener("click", async () => {
      const [application_id, decision, score] = button.dataset.review.split("|");
      await mutate("/api/review", {
        application_id: Number(application_id),
        decision,
        score: Number(score),
        remarks: `${titleCase(decision)} by scholarship committee.`
      }, `Application ${titleCase(decision)}`);
    });
  });
  document.querySelectorAll("[data-disburse]").forEach(button => {
    button.addEventListener("click", async () => {
      await mutate("/api/disburse", { application_id: Number(button.dataset.disburse) }, "Disbursement processed");
    });
  });
  document.querySelector("#scholarship-form")?.addEventListener("submit", async event => {
    event.preventDefault();
    const body = Object.fromEntries(new FormData(event.target).entries());
    await mutate("/api/scholarships", body, "Scholarship published");
    event.target.reset();
  });
}

async function mutate(url, body, message) {
  try {
    await api(url, { method: "POST", body: JSON.stringify(body) });
    await loadData();
    renderShell();
    toast(message);
  } catch (error) {
    toast(error.message);
  }
}

boot().catch(error => {
  app.innerHTML = `<section class="login-card" style="margin:40px auto"><h2>Startup error</h2><p class="error">${error.message}</p></section>`;
});

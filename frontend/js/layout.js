/* Auth guard + shared sidebar rendering. */

function requireAuth() {
  if (!auth.token()) {
    window.location.href = "login.html";
    return false;
  }
  return true;
}

function renderSidebar(activePage) {
  const doctor = auth.doctor() || { name: "Doctor", specialty: "" };
  const links = [
    { href: "dashboard.html", label: "Dashboard", key: "dashboard" },
    { href: "patients.html", label: "Patients", key: "patients" },
    { href: "history.html", label: "History", key: "history" },
  ];

  return `
    <aside class="sidebar">
      <div class="logo">Seizure<span>Shield</span></div>
      <nav class="nav">
        ${links.map(l =>
    `<a href="${l.href}" class="${l.key === activePage ? "active" : ""}">${l.label}</a>`
  ).join("")}
      </nav>
      <div class="sidebar-footer">
        <div class="name">${doctor.name}</div>
        <div class="role">${doctor.specialty || ""}</div>
        <button onclick="signOut()">Sign out</button>
      </div>
    </aside>
  `;
}

function signOut() {
  auth.clear();
  window.location.href = "login.html";
}

function initLayout(activePage) {
  if (!requireAuth()) return false;
  document.getElementById("sidebar-slot").outerHTML = renderSidebar(activePage);
  return true;
}

/* Small shared helpers */
function statusBadge(status) {
  if (!status || status === "No analysis yet") return `<span class="badge none">No analysis yet</span>`;
  const cls = status === "Normal" ? "normal" : "warning";
  return `<span class="badge ${cls}">${status}</span>`;
}

function formatDate(iso) {
  return new Date(iso).toLocaleString(undefined, {
    year: "numeric", month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}
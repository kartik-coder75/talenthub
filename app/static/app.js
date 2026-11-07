"use strict";

/* ====================== helpers ====================== */
const $ = (sel, el = document) => el.querySelector(sel);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g,
  (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtDate = (d) => {
  if (!d) return "—";
  const iso = /(Z|[+-]\d\d:\d\d)$/.test(d) ? d : d + "Z"; // server sends naive UTC
  return new Date(iso).toLocaleString();
};
const label = (s) => String(s).replace(/_/g, " ");
const empty = (msg) => `<div class="card empty">${esc(msg)}</div>`;

const BADGE = {
  APPLIED: "", SHORTLISTED: "progress", INTERVIEW_SCHEDULED: "progress", SELECTED: "good", OFFERED: "warn",
  OFFER_ACCEPTED: "good", REJECTED: "bad", NOT_SELECTED: "bad", OFFER_DECLINED: "bad", OFFER_WITHDRAWN: "bad",
  ISSUED: "warn", ACCEPTED: "good", DECLINED: "bad", WITHDRAWN: "bad", PENDING: "", PASSED: "good", FAILED: "bad",
};
const badge = (s) => `<span class="badge ${BADGE[s] ?? ""}">${esc(label(s))}</span>`;

const state = {
  token: sessionStorage.getItem("th_token"),
  user: null, profile: null, tab: null,
  onlyEligible: false, expanded: new Set(), studentFilter: { branch: "", placed: "" },
};

function toast(msg, isError = false) {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "toast" + (isError ? " error" : "");
  t.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (t.hidden = true), isError ? 6000 : 3000);
}

function formatError(data, status) {
  if (data && typeof data.detail === "string") return data.detail;
  if (data && Array.isArray(data.detail)) {
    return data.detail.map((e) => `${(e.loc || []).slice(1).join(".")}: ${e.msg}`).join("; ");
  }
  return `Request failed (${status})`;
}

async function api(path, { method = "GET", body, form = false } = {}) {
  const headers = {};
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  let payload;
  if (body !== undefined) {
    if (form) {
      payload = new URLSearchParams(body);
      headers["Content-Type"] = "application/x-www-form-urlencoded";
    } else {
      payload = JSON.stringify(body);
      headers["Content-Type"] = "application/json";
    }
  }
  const res = await fetch(path, { method, headers, body: payload });
  const data = await res.json().catch(() => null);
  if (res.status === 401 && state.token) {
    logout();
    throw new Error("Your session has expired. Please log in again.");
  }
  if (!res.ok) throw new Error(formatError(data, res.status));
  return data;
}

/* ====================== modal ====================== */
function closeModal() { const m = $("#modal"); m.hidden = true; m.innerHTML = ""; }

function openModal({ title, fields, submit = "Save", onSubmit }) {
  const m = $("#modal");
  m.innerHTML = `<form class="modal-box"><h3>${esc(title)}</h3>${fields}
    <p class="form-error" hidden></p>
    <div class="actions"><button type="button" class="ghost" data-close>Cancel</button>
    <button type="submit" class="primary">${esc(submit)}</button></div></form>`;
  m.hidden = false;
  const form = $("form", m), err = $(".form-error", m);
  m.onclick = (e) => { if (e.target === m || e.target.hasAttribute("data-close")) closeModal(); };
  form.onsubmit = async (e) => {
    e.preventDefault();
    err.hidden = true;
    const btn = $("button[type=submit]", form);
    btn.disabled = true;
    try { await onSubmit(new FormData(form)); closeModal(); }
    catch (ex) { err.textContent = ex.message; err.hidden = false; btn.disabled = false; }
  };
  const first = $("input, select, textarea", form);
  if (first) first.focus();
}

/* ====================== auth screen ====================== */
function logout() {
  sessionStorage.removeItem("th_token");
  Object.assign(state, { token: null, user: null, profile: null, tab: null });
  state.expanded.clear();
  renderAuth();
}

function renderAuth(mode = "login") {
  const forms = {
    login: `
      <label>Username</label><input name="username" required autocomplete="username">
      <label>Password</label><input name="password" type="password" required autocomplete="current-password">
      <div class="actions"><button class="primary" type="submit">Log in</button></div>
      <div class="hint">Placement coordinator demo account: <b>coordinator</b> / <b>Coordinator@123</b></div>`,
    student: `
      <div class="row"><div><label>Username</label><input name="username" required minlength="3" maxlength="50" pattern="[A-Za-z0-9_.\\-]+" title="Letters, digits, . _ - only"></div>
      <div><label>Password (min 8)</label><input name="password" type="password" required minlength="8"></div></div>
      <label>Full name</label><input name="name" required maxlength="100">
      <div class="row"><div><label>Branch</label><input name="branch" required minlength="2" placeholder="CSE"></div>
      <div><label>CGPA (0-10)</label><input name="cgpa" type="number" step="0.01" min="0" max="10" required></div>
      <div><label>Active backlogs</label><input name="active_backlogs" type="number" min="0" value="0" required></div></div>
      <div class="actions"><button class="primary" type="submit">Create student account</button></div>`,
    company: `
      <div class="row"><div><label>Username</label><input name="username" required minlength="3" maxlength="50" pattern="[A-Za-z0-9_.\\-]+" title="Letters, digits, . _ - only"></div>
      <div><label>Password (min 8)</label><input name="password" type="password" required minlength="8"></div></div>
      <label>Company name</label><input name="name" required maxlength="150">
      <label>Industry</label><input name="industry" maxlength="100">
      <div class="actions"><button class="primary" type="submit">Create company account</button></div>`,
  };
  $("#app").innerHTML = `<div class="auth"><h1 style="text-align:center;color:var(--primary)">TalentHub</h1>
    <p class="muted" style="text-align:center">Campus placement management</p>
    <div class="tabs">${[["login", "Log in"], ["student", "Student sign-up"], ["company", "Company sign-up"]]
      .map(([k, t]) => `<button data-mode="${k}" class="${k === mode ? "active" : ""}">${t}</button>`).join("")}</div>
    <form class="card" id="authForm">${forms[mode]}<p class="form-error" hidden></p></form></div>`;

  document.querySelectorAll(".auth .tabs button").forEach((b) => (b.onclick = () => renderAuth(b.dataset.mode)));
  const form = $("#authForm"), err = $(".form-error", form);
  form.onsubmit = async (e) => {
    e.preventDefault();
    err.hidden = true;
    const f = Object.fromEntries(new FormData(form));
    const btn = $("button[type=submit]", form);
    btn.disabled = true;
    try {
      if (mode === "student") {
        await api("/auth/register/student", { method: "POST", body: {
          username: f.username, password: f.password, name: f.name, branch: f.branch,
          cgpa: Number(f.cgpa), active_backlogs: Number(f.active_backlogs) } });
      } else if (mode === "company") {
        await api("/auth/register/company", { method: "POST", body: {
          username: f.username, password: f.password, name: f.name, industry: f.industry || "" } });
      }
      const tok = await api("/auth/login", { method: "POST", form: true, body: { username: f.username, password: f.password } });
      state.token = tok.access_token;
      sessionStorage.setItem("th_token", state.token);
      await boot();
    } catch (ex) { err.textContent = ex.message; err.hidden = false; btn.disabled = false; }
  };
}

/* ====================== shell ====================== */
const TABS = {
  STUDENT: [["jobs", "Browse jobs", tabJobs], ["applications", "My applications", tabApplications], ["profile", "Profile", tabProfile]],
  COMPANY: [["myjobs", "My jobs", tabMyJobs], ["post", "Post a job", tabPostJob]],
  COORDINATOR: [["dashboard", "Dashboard", tabDashboard], ["students", "Students", tabStudents]],
};

async function boot() {
  if (!state.token) return renderAuth();
  try {
    state.user = await api("/auth/me");
    await loadProfile();
  } catch (e) { return logout(); }
  renderShell();
}

async function loadProfile() {
  if (state.user.role === "STUDENT") state.profile = await api("/students/me");
  else if (state.user.role === "COMPANY") state.profile = await api("/companies/me");
  else state.profile = null;
}

function renderShell() {
  const tabs = TABS[state.user.role];
  const name = state.profile?.name ?? state.user.username;
  $("#app").innerHTML = `
    <header class="topbar"><span class="brand">TalentHub</span><span class="spacer"></span>
      <span class="who">${state.profile ? `${esc(name)} · ${esc(state.user.role.toLowerCase())}` : "Placement coordinator"}</span>
      <button class="ghost" id="logoutBtn">Log out</button></header>
    <nav class="nav">${tabs.map(([k, t]) => `<button data-tab="${k}">${t}</button>`).join("")}</nav>
    <main id="content"></main>`;
  $("#logoutBtn").onclick = logout;
  document.querySelectorAll(".nav button").forEach((b) => (b.onclick = () => showTab(b.dataset.tab)));
  $("#content").onclick = onAction;
  showTab(tabs[0][0]);
}

async function showTab(name) {
  state.tab = name;
  document.querySelectorAll(".nav button").forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
  const el = $("#content");
  el.innerHTML = `<p class="muted">Loading…</p>`;
  const fn = TABS[state.user.role].find((t) => t[0] === name)[2];
  try { await fn(el); }
  catch (ex) { el.innerHTML = `<div class="card form-error">${esc(ex.message)}</div>`; }
}
const refresh = () => showTab(state.tab);

/* ====================== student tabs ====================== */
async function tabJobs(el) {
  const [jobs, apps] = await Promise.all([
    api(`/jobs?eligible_only=${state.onlyEligible}`), api("/applications/me")]);
  const applied = new Map(apps.map((a) => [a.job_id, a]));
  el.innerHTML = `${state.profile.is_placed ? `<div class="banner">You have accepted an offer, so new applications are disabled.</div>` : ""}
    <div class="toolbar"><h2 style="margin:0">Open jobs</h2><span class="spacer"></span>
      <label class="check"><input type="checkbox" id="onlyElig" ${state.onlyEligible ? "checked" : ""}> Only jobs I'm eligible for</label></div>
    ${jobs.length ? `<div class="grid">${jobs.map((j) => jobCard(j, applied.get(j.id))).join("")}</div>` : empty("No open jobs to show.")}`;
  $("#onlyElig").onchange = (e) => { state.onlyEligible = e.target.checked; refresh(); };
}

function jobCard(j, application) {
  return `<article class="card"><h3>${esc(j.title)}</h3>
    <div class="muted small">${esc(j.company_name)}${j.location ? " · " + esc(j.location) : ""}</div>
    <div class="pkg">₹ ${esc(j.package_lpa)} LPA</div>
    <ul class="criteria"><li>Minimum CGPA: ${esc(j.min_cgpa)}</li><li>Max active backlogs: ${esc(j.max_active_backlogs)}</li>
      <li>Branches: ${j.allowed_branches.length ? esc(j.allowed_branches.join(", ")) : "All"}</li></ul>
    ${j.description ? `<p class="small">${esc(j.description)}</p>` : ""}
    <div class="elig" id="elig-${j.id}"></div>
    <div class="actions"><button class="ghost" data-action="check-elig" data-id="${j.id}">Check eligibility</button>
      ${application ? badge(application.status)
        : `<button class="primary" data-action="apply" data-id="${j.id}" ${state.profile.is_placed ? "disabled" : ""}>Apply</button>`}
    </div></article>`;
}

async function tabApplications(el) {
  const apps = await api("/applications/me");
  if (!apps.length) { el.innerHTML = empty("You haven't applied to any jobs yet."); return; }
  el.innerHTML = `<h2>My applications</h2><div class="grid">${apps.slice().reverse().map((a) => {
    const iv = a.interview, of = a.offer;
    return `<article class="card"><h3>${esc(a.job.title)}</h3>
      <div class="muted small">${esc(a.job.company_name)} · applied ${fmtDate(a.applied_at)}</div>
      <p>${badge(a.status)}</p>
      ${iv ? `<p class="small"><b>Interview:</b> ${fmtDate(iv.scheduled_at)} (${esc(iv.mode.toLowerCase())}${iv.location ? ", " + esc(iv.location) : ""})
        ${iv.result !== "PENDING" ? badge(iv.result) : ""}${iv.remarks ? `<br><span class="muted">${esc(iv.remarks)}</span>` : ""}</p>` : ""}
      ${of ? `<p class="small"><b>Offer:</b> ₹ ${esc(of.package_lpa)} LPA ${badge(of.status)}</p>` : ""}
      ${of && of.status === "ISSUED" ? `<div class="actions">
        <button class="primary" data-action="accept-offer" data-id="${of.id}">Accept offer</button>
        <button class="danger" data-action="decline-offer" data-id="${of.id}">Decline</button></div>` : ""}
    </article>`;
  }).join("")}</div>`;
}

async function tabProfile(el) {
  await loadProfile();
  const p = state.profile;
  el.innerHTML = `<h2>My profile</h2><div class="card stack" style="max-width:460px">
    <div><span class="muted small">Name</span><div>${esc(p.name)}</div></div>
    <div><span class="muted small">Branch</span><div>${esc(p.branch)}</div></div>
    <div><span class="muted small">CGPA</span><div>${esc(p.cgpa)}</div></div>
    <div><span class="muted small">Active backlogs</span><div>${esc(p.active_backlogs)}</div></div>
    <div><span class="muted small">Placement status</span><div>${p.is_placed ? badge("ACCEPTED").replace("ACCEPTED", "PLACED") : badge("PENDING").replace("PENDING", "NOT YET PLACED")}</div></div>
    <p class="muted small">Academic details are verified by the placement coordinator. Contact them if something is wrong.</p>
    <button class="ghost" data-action="edit-name">Change my name</button></div>`;
}

/* ====================== company tabs ====================== */
async function tabPostJob(el) {
  el.innerHTML = `<h2>Post a job</h2><form class="card" id="jobForm" style="max-width:640px">
    <label>Job title</label><input name="title" required maxlength="150">
    <label>Description</label><textarea name="description" rows="3" maxlength="5000"></textarea>
    <div class="row"><div><label>Location</label><input name="location" maxlength="100"></div>
      <div><label>Package (LPA)</label><input name="package_lpa" type="number" step="0.1" min="0.1" required></div></div>
    <div class="row"><div><label>Minimum CGPA</label><input name="min_cgpa" type="number" step="0.01" min="0" max="10" value="0" required></div>
      <div><label>Max active backlogs</label><input name="max_active_backlogs" type="number" min="0" value="0" required></div></div>
    <label>Allowed branches <span class="muted">(comma-separated, leave empty for all)</span></label>
    <input name="allowed_branches" placeholder="CSE, IT, ECE">
    <p class="form-error" hidden></p>
    <div class="actions"><button class="primary" type="submit">Publish job</button></div></form>`;
  const form = $("#jobForm"), err = $(".form-error", form);
  form.onsubmit = async (e) => {
    e.preventDefault();
    err.hidden = true;
    const f = Object.fromEntries(new FormData(form));
    try {
      await api("/jobs", { method: "POST", body: {
        title: f.title, description: f.description, location: f.location,
        package_lpa: Number(f.package_lpa), min_cgpa: Number(f.min_cgpa),
        max_active_backlogs: Number(f.max_active_backlogs),
        allowed_branches: f.allowed_branches.split(",").map((s) => s.trim()).filter(Boolean) } });
      toast("Job published");
      showTab("myjobs");
    } catch (ex) { err.textContent = ex.message; err.hidden = false; }
  };
}

async function tabMyJobs(el) {
  const jobs = (await api("/jobs")).filter((j) => j.company_id === state.profile.id);
  if (!jobs.length) { el.innerHTML = empty("You have no open jobs. Use “Post a job” to create one."); return; }
  const applicants = {};
  await Promise.all(jobs.filter((j) => state.expanded.has(j.id)).map(async (j) => {
    applicants[j.id] = await api(`/jobs/${j.id}/applications`);
  }));
  el.innerHTML = `<h2>My open jobs</h2><div class="stack">${jobs.map((j) => {
    const open = state.expanded.has(j.id);
    return `<article class="card"><div class="toolbar" style="margin:0">
      <div style="flex:1"><h3>${esc(j.title)}</h3>
        <div class="muted small">₹ ${esc(j.package_lpa)} LPA · min CGPA ${esc(j.min_cgpa)} · max backlogs ${esc(j.max_active_backlogs)} ·
        branches: ${j.allowed_branches.length ? esc(j.allowed_branches.join(", ")) : "all"}</div></div>
      <div class="actions" style="margin:0"><button class="ghost" data-action="toggle-applicants" data-id="${j.id}">${open ? "Hide" : "View"} applicants</button>
        <button class="danger" data-action="close-job" data-id="${j.id}">Close job</button></div></div>
      ${open ? applicantsTable(applicants[j.id]) : ""}</article>`;
  }).join("")}</div>`;
}

function applicantsTable(list) {
  if (!list.length) return `<p class="muted" style="margin-top:.75rem">No applications yet.</p>`;
  return `<div class="table-wrap" style="margin-top:.75rem"><table><thead><tr>
    <th>Student</th><th>CGPA</th><th>Backlogs</th><th>Status</th><th>Interview / offer</th><th>Actions</th></tr></thead><tbody>
    ${list.map((a) => {
      const iv = a.interview, of = a.offer;
      return `<tr><td><b>${esc(a.student.name)}</b><div class="muted small">${esc(a.student.branch)}</div></td>
        <td>${esc(a.student.cgpa)}</td><td>${esc(a.student.active_backlogs)}</td><td>${badge(a.status)}</td>
        <td class="small">${iv ? `${fmtDate(iv.scheduled_at)} (${esc(iv.mode.toLowerCase())}) ${iv.result !== "PENDING" ? badge(iv.result) : ""}` : ""}
          ${of ? `<div>Offer ₹ ${esc(of.package_lpa)} LPA ${badge(of.status)}</div>` : ""}</td>
        <td><div class="actions">${applicantActions(a)}</div></td></tr>`;
    }).join("")}</tbody></table></div>`;
}

function applicantActions(a) {
  const b = (action, text, cls = "ghost") => `<button class="${cls}" data-action="${action}" data-id="${a.id}">${text}</button>`;
  switch (a.status) {
    case "APPLIED": return b("shortlist", "Shortlist", "primary") + b("reject", "Reject", "danger");
    case "SHORTLISTED": return b("schedule", "Schedule interview", "primary") + b("reject", "Reject", "danger");
    case "INTERVIEW_SCHEDULED": return b("result", "Record result", "primary");
    case "SELECTED": return b("issue-offer", "Issue offer", "primary");
    default: return "";
  }
}

/* ====================== coordinator tabs ====================== */
async function tabDashboard(el) {
  const [s, placed] = await Promise.all([api("/reports/placement-statistics"), api("/reports/placed-students")]);
  const stat = (n, t) => `<div class="stat"><div class="n">${esc(n)}</div><div class="muted small">${t}</div></div>`;
  el.innerHTML = `<h2>Placement statistics</h2><div class="stats">
    ${stat(s.total_students, "Students")}${stat(s.placed_students, "Placed")}${stat(s.placement_percentage + "%", "Placement rate")}
    ${stat(s.total_companies, "Companies")}${stat(s.open_jobs + " / " + s.total_jobs, "Open / total jobs")}${stat(s.total_applications, "Applications")}
    ${stat(s.offers_issued, "Offers issued")}${stat(s.offers_accepted, "Offers accepted")}${stat(s.offers_pending, "Offers pending")}
    ${stat(s.average_package_lpa, "Avg package (LPA)")}${stat(s.highest_package_lpa, "Highest (LPA)")}</div>
    <div class="grid" style="margin-top:1.25rem">
      <div class="card"><h3>Branch-wise</h3>${s.branch_wise.length ? `<div class="table-wrap"><table><thead><tr><th>Branch</th><th>Placed / total</th><th>%</th></tr></thead><tbody>
        ${s.branch_wise.map((b) => `<tr><td>${esc(b.branch)}</td><td>${b.placed_students} / ${b.total_students}</td>
          <td><div class="bar"><span style="width:${b.placement_percentage}%"></span></div>${b.placement_percentage}%</td></tr>`).join("")}</tbody></table></div>` : `<p class="muted">No students yet.</p>`}</div>
      <div class="card"><h3>Company-wise offers</h3>${s.company_wise.length ? `<div class="table-wrap"><table><thead><tr><th>Company</th><th>Issued</th><th>Accepted</th></tr></thead><tbody>
        ${s.company_wise.map((c) => `<tr><td>${esc(c.company)}</td><td>${c.offers_issued}</td><td>${c.offers_accepted}</td></tr>`).join("")}</tbody></table></div>` : `<p class="muted">No companies yet.</p>`}</div></div>
    <div class="card" style="margin-top:1rem"><h3>Placed students</h3>${placed.length ? `<div class="table-wrap"><table><thead><tr><th>Student</th><th>Branch</th><th>Company</th><th>Role</th><th>Package (LPA)</th></tr></thead><tbody>
      ${placed.map((p) => `<tr><td>${esc(p.student_name)}</td><td>${esc(p.branch)}</td><td>${esc(p.company)}</td><td>${esc(p.job_title)}</td><td>${esc(p.package_lpa)}</td></tr>`).join("")}</tbody></table></div>` : `<p class="muted">No placements recorded yet.</p>`}</div>`;
}

async function tabStudents(el) {
  const f = state.studentFilter;
  const qs = new URLSearchParams();
  if (f.branch.trim()) qs.set("branch", f.branch.trim());
  if (f.placed !== "") qs.set("placed", f.placed);
  const students = await api("/students" + (qs.toString() ? "?" + qs : ""));
  el.innerHTML = `<h2>Students</h2><form class="toolbar" id="filterForm">
    <div><label>Branch</label><input name="branch" value="${esc(f.branch)}" placeholder="e.g. CSE"></div>
    <div><label>Placement</label><select name="placed"><option value="">All</option>
      <option value="true" ${f.placed === "true" ? "selected" : ""}>Placed</option>
      <option value="false" ${f.placed === "false" ? "selected" : ""}>Not placed</option></select></div>
    <button class="primary" type="submit">Filter</button></form>
    ${students.length ? `<div class="card table-wrap"><table><thead><tr><th>ID</th><th>Name</th><th>Branch</th><th>CGPA</th><th>Backlogs</th><th>Status</th><th></th></tr></thead><tbody>
      ${students.map((s) => `<tr><td>${s.id}</td><td>${esc(s.name)}</td><td>${esc(s.branch)}</td><td>${esc(s.cgpa)}</td><td>${esc(s.active_backlogs)}</td>
        <td>${s.is_placed ? badge("ACCEPTED").replace("ACCEPTED", "PLACED") : badge("PENDING").replace("PENDING", "NOT PLACED")}</td>
        <td><button class="ghost" data-action="edit-student" data-id="${s.id}"
          data-branch="${esc(s.branch)}" data-cgpa="${esc(s.cgpa)}" data-backlogs="${esc(s.active_backlogs)}">Edit record</button></td></tr>`).join("")}
      </tbody></table></div>` : empty("No students match these filters.")}`;
  $("#filterForm").onsubmit = (e) => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    state.studentFilter = { branch: d.branch, placed: d.placed };
    refresh();
  };
}

/* ====================== click actions ====================== */
async function onAction(e) {
  const btn = e.target.closest("[data-action]");
  if (!btn) return;
  const { action, id } = btn.dataset;
  const post = (path, body) => api(path, { method: "POST", body });
  try {
    switch (action) {
      case "check-elig": {
        const r = await api(`/jobs/${id}/eligibility`);
        const box = $(`#elig-${id}`);
        box.className = "elig " + (r.eligible ? "yes" : "no");
        box.textContent = r.eligible ? "You are eligible for this job." : "Not eligible: " + r.reasons.join("; ");
        return;
      }
      case "apply": await post("/applications", { job_id: Number(id) }); toast("Application submitted"); return refresh();
      case "accept-offer":
        if (!confirm("Accept this offer? Your other open offers will be withdrawn and you can't apply to more jobs.")) return;
        await post(`/offers/${id}/accept`); await loadProfile(); toast("Offer accepted. Congratulations!"); return refresh();
      case "decline-offer":
        if (!confirm("Decline this offer?")) return;
        await post(`/offers/${id}/decline`); toast("Offer declined"); return refresh();
      case "edit-name":
        return openModal({ title: "Change name", fields: `<label>Full name</label><input name="name" required maxlength="100" value="${esc(state.profile.name)}">`,
          onSubmit: async (fd) => { state.profile = await api("/students/me", { method: "PATCH", body: { name: fd.get("name") } });
            $(".who").textContent = `${state.profile.name} · student`; refresh(); } });

      case "toggle-applicants": state.expanded.has(Number(id)) ? state.expanded.delete(Number(id)) : state.expanded.add(Number(id)); return refresh();
      case "close-job":
        if (!confirm("Close this job? Students will no longer be able to apply.")) return;
        await post(`/jobs/${id}/close`); toast("Job closed"); return refresh();
      case "shortlist": await post(`/applications/${id}/shortlist`); toast("Student shortlisted"); return refresh();
      case "reject":
        if (!confirm("Reject this application?")) return;
        await post(`/applications/${id}/reject`); toast("Application rejected"); return refresh();
      case "schedule":
        return openModal({ title: "Schedule interview", submit: "Schedule", fields: `
          <label>Date and time</label><input name="when" type="datetime-local" required>
          <label>Mode</label><select name="mode"><option>ONLINE</option><option>ONSITE</option></select>
          <label>Location / meeting link</label><input name="location" maxlength="200">`,
          onSubmit: async (fd) => { await post(`/applications/${id}/interview`, {
            scheduled_at: new Date(fd.get("when")).toISOString(), mode: fd.get("mode"), location: fd.get("location") });
            toast("Interview scheduled"); refresh(); } });
      case "result":
        return openModal({ title: "Record interview result", fields: `
          <label>Result</label><select name="result"><option value="PASSED">Passed</option><option value="FAILED">Failed</option></select>
          <label>Remarks</label><textarea name="remarks" rows="3" maxlength="2000"></textarea>`,
          onSubmit: async (fd) => { await api(`/applications/${id}/interview/result`, { method: "PUT",
            body: { result: fd.get("result"), remarks: fd.get("remarks") } }); toast("Result recorded"); refresh(); } });
      case "issue-offer":
        return openModal({ title: "Issue offer", submit: "Issue offer", fields: `
          <label>Package in LPA <span class="muted">(leave empty to use the job's package)</span></label>
          <input name="package_lpa" type="number" step="0.1" min="0.1">`,
          onSubmit: async (fd) => { const v = fd.get("package_lpa");
            await post(`/applications/${id}/offer`, v ? { package_lpa: Number(v) } : {}); toast("Offer issued"); refresh(); } });

      case "edit-student":
        return openModal({ title: "Edit academic record", fields: `
          <label>Branch</label><input name="branch" required minlength="2" value="${esc(btn.dataset.branch)}">
          <div class="row"><div><label>CGPA</label><input name="cgpa" type="number" step="0.01" min="0" max="10" required value="${esc(btn.dataset.cgpa)}"></div>
          <div><label>Active backlogs</label><input name="backlogs" type="number" min="0" required value="${esc(btn.dataset.backlogs)}"></div></div>`,
          onSubmit: async (fd) => { await api(`/students/${id}/academic-record`, { method: "PATCH", body: {
            branch: fd.get("branch"), cgpa: Number(fd.get("cgpa")), active_backlogs: Number(fd.get("backlogs")) } });
            toast("Record updated"); refresh(); } });
    }
  } catch (ex) { toast(ex.message, true); }
}

boot();

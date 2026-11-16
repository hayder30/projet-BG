/* Brazilian Glow – stock management (plain JavaScript, no build step) */
const API = (window.API_URL || "http://localhost:8000/api").replace(/\/$/, "");

const state = {
  token: localStorage.getItem("bg_token"),
  user: JSON.parse(localStorage.getItem("bg_user") || "null"),
  view: "dashboard",
  categories: [],
  suppliers: [],
  products: [],
  filters: { q: "", category_id: "", low_stock: false },
};

const $ = (sel, el = document) => el.querySelector(sel);
const isAdmin = () => state.user && state.user.role === "admin";

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const money = (n) => Number(n || 0).toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " TND";
const fmtDate = (iso) => new Date(iso).toLocaleString("en-GB", { dateStyle: "short", timeStyle: "short" });

function toast(msg, isError = false) {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "show" + (isError ? " err" : "");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (t.className = ""), 2800);
}

/* ---------- API ---------- */
function errorText(data) {
  if (!data || !data.detail) return "Something went wrong";
  if (typeof data.detail === "string") return data.detail;
  return data.detail.map((d) => `${(d.loc || []).slice(1).join(".")}: ${d.msg}`).join(", ");
}

async function api(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  let res;
  try {
    res = await fetch(API + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  } catch {
    throw new Error("Cannot reach the server. Check that the API is running.");
  }
  if (res.status === 401 && path !== "/auth/login") {
    logout();
    throw new Error("Your session expired. Sign in again.");
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(errorText(data));
  return data;
}

/* ---------- auth ---------- */
function showLogin() {
  $("#app").hidden = true;
  $("#login-screen").hidden = false;
}

function logout() {
  state.token = null;
  state.user = null;
  localStorage.removeItem("bg_token");
  localStorage.removeItem("bg_user");
  showLogin();
}

$("#login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("#login-error").textContent = "";
  const f = new FormData(e.target);
  try {
    const data = await api("/auth/login", { method: "POST", body: { username: f.get("username"), password: f.get("password") } });
    state.token = data.access_token;
    state.user = data.user;
    localStorage.setItem("bg_token", state.token);
    localStorage.setItem("bg_user", JSON.stringify(state.user));
    e.target.reset();
    startApp();
  } catch (err) {
    $("#login-error").textContent = err.message;
  }
});

$("#logout").addEventListener("click", logout);

/* ---------- dialog helper ---------- */
const dlg = $("#dlg");
let dlgSubmit = null;

function openDialog(title, bodyHtml, okLabel, onSubmit) {
  $("#dlg-title").textContent = title;
  $("#dlg-body").innerHTML = bodyHtml;
  $("#dlg-ok").textContent = okLabel;
  $("#dlg-error").textContent = "";
  dlgSubmit = onSubmit;
  dlg.showModal();
}

$("#dlg-cancel").addEventListener("click", () => dlg.close());
$("#dlg-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!dlgSubmit) return;
  try {
    await dlgSubmit(new FormData(e.target));
    dlg.close();
  } catch (err) {
    $("#dlg-error").textContent = err.message;
  }
});

/* ---------- navigation ---------- */
function setView(view) {
  state.view = view;
  document.querySelectorAll("#nav button").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
  render();
}

$("#nav").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-view]");
  if (btn) setView(btn.dataset.view);
});

async function loadLookups() {
  [state.categories, state.suppliers] = await Promise.all([api("/categories"), api("/suppliers")]);
}

async function startApp() {
  $("#login-screen").hidden = true;
  $("#app").hidden = false;
  $("#whoami").textContent = `${state.user.username} (${state.user.role})`;
  document.querySelectorAll("[data-admin]").forEach((el) => (el.hidden = !isAdmin()));
  try {
    await loadLookups();
  } catch (err) {
    return toast(err.message, true);
  }
  setView("dashboard");
}

async function render() {
  const view = $("#view");
  view.innerHTML = '<p class="muted">Loading…</p>';
  try {
    if (state.view === "dashboard") await renderDashboard(view);
    else if (state.view === "products") await renderProducts(view);
    else if (state.view === "movements") await renderMovements(view);
    else if (state.view === "settings") await renderSettings(view);
  } catch (err) {
    view.innerHTML = `<p class="error">${esc(err.message)}</p>`;
  }
}

/* ---------- shared bits ---------- */
function stockBadge(p) {
  if (p.quantity === 0) return '<span class="badge out">Out of stock</span>';
  if (p.is_low_stock) return `<span class="badge low">Low · ${p.quantity}</span>`;
  return `<span class="badge ok">${p.quantity}</span>`;
}

const typeLabel = { in: "Stock in", out: "Stock out", adjust: "Adjustment" };

function options(items, selected, blank) {
  const first = blank ? `<option value="">${esc(blank)}</option>` : "";
  return first + items.map((i) => `<option value="${i.id}" ${i.id === selected ? "selected" : ""}>${esc(i.name)}</option>`).join("");
}

function movementsTable(rows) {
  if (!rows.length) return '<p class="empty">No stock movements yet.</p>';
  return `<div class="table-wrap"><table>
    <thead><tr><th>Date</th><th>Product</th><th>Type</th><th class="num">Qty</th><th class="num">Stock after</th><th>Reason</th><th>By</th></tr></thead>
    <tbody>${rows
      .map(
        (m) => `<tr>
        <td>${fmtDate(m.created_at)}</td><td>${esc(m.product_name)}</td><td>${typeLabel[m.type]}</td>
        <td class="num">${m.quantity}</td><td class="num">${m.quantity_after}</td>
        <td>${esc(m.reason)}</td><td>${esc(m.username || "")}</td></tr>`
      )
      .join("")}</tbody></table></div>`;
}

/* ---------- dashboard ---------- */
async function renderDashboard(view) {
  const d = await api("/dashboard");
  const maxUnits = Math.max(1, ...Object.values(d.units_by_category));
  view.innerHTML = `
    <div class="page-head"><h2>Dashboard</h2></div>
    <div class="tiles">
      <div class="tile"><div class="num">${d.total_products}</div><div class="lbl">Products</div></div>
      <div class="tile"><div class="num">${d.total_units}</div><div class="lbl">Units in stock</div></div>
      <div class="tile"><div class="num">${money(d.stock_value_retail)}</div><div class="lbl">Stock value (retail)</div></div>
      <div class="tile ${d.low_stock_count ? "alert" : ""}"><div class="num">${d.low_stock_count}</div>
        <div class="lbl">Low or out of stock (${d.out_of_stock_count} out)</div></div>
    </div>
    <div class="grid-2">
      <section class="panel"><h3>Needs restocking</h3>
        ${
          d.low_stock_products.length
            ? `<div class="table-wrap"><table><thead><tr><th>Product</th><th class="num">Stock</th><th class="num">Alert at</th></tr></thead><tbody>
              ${d.low_stock_products.map((p) => `<tr><td>${esc(p.name)}</td><td class="num">${stockBadge(p)}</td><td class="num">${p.low_stock_threshold}</td></tr>`).join("")}
              </tbody></table></div>`
            : '<p class="empty">Everything is well stocked.</p>'
        }
      </section>
      <section class="panel"><h3>Units by category</h3>
        <div class="bars">${
          Object.entries(d.units_by_category)
            .map(([name, n]) => `<div class="bar-row"><span>${esc(name)}</span><div class="bar"><span style="width:${(n / maxUnits) * 100}%"></span></div><b>${n}</b></div>`)
            .join("") || '<p class="empty">No products yet.</p>'
        }</div>
      </section>
    </div>
    <section class="panel"><h3>Recent movements</h3>${movementsTable(d.recent_movements)}</section>`;
}

/* ---------- products ---------- */
async function renderProducts(view) {
  view.innerHTML = `
    <div class="page-head"><h2>Products</h2>
      ${isAdmin() ? '<button class="btn primary" id="add-product">Add product</button>' : ""}
    </div>
    <div class="toolbar">
      <input type="search" id="f-q" placeholder="Search name or SKU" value="${esc(state.filters.q)}">
      <select id="f-cat">${options(state.categories, Number(state.filters.category_id), "All categories")}</select>
      <label class="inline"><input type="checkbox" id="f-low" ${state.filters.low_stock ? "checked" : ""}> Low stock only</label>
    </div>
    <div id="product-list"></div>`;

  $("#f-q").addEventListener("input", debounce((e) => { state.filters.q = e.target.value; loadProducts(); }, 250));
  $("#f-cat").addEventListener("change", (e) => { state.filters.category_id = e.target.value; loadProducts(); });
  $("#f-low").addEventListener("change", (e) => { state.filters.low_stock = e.target.checked; loadProducts(); });
  const add = $("#add-product");
  if (add) add.addEventListener("click", () => productDialog());
  await loadProducts();
}

async function loadProducts() {
  const f = state.filters;
  const qs = new URLSearchParams();
  if (f.q) qs.set("q", f.q);
  if (f.category_id) qs.set("category_id", f.category_id);
  if (f.low_stock) qs.set("low_stock", "true");
  state.products = await api("/products?" + qs);
  const box = $("#product-list");
  if (!box) return;
  if (!state.products.length) {
    box.innerHTML = '<p class="empty">No products match. Change the filters or add a product.</p>';
    return;
  }
  box.innerHTML = `<div class="table-wrap"><table>
    <thead><tr><th>SKU</th><th>Product</th><th>Category</th><th class="num">Price</th><th class="num">Stock</th><th></th></tr></thead>
    <tbody>${state.products
      .map(
        (p) => `<tr>
        <td>${esc(p.sku)}</td><td>${esc(p.name)}</td><td>${esc(p.category_name || "–")}</td>
        <td class="num">${money(p.price)}</td><td class="num">${stockBadge(p)}</td>
        <td><div class="row-actions">
          <button class="btn small" data-act="move" data-id="${p.id}">Move stock</button>
          ${isAdmin() ? `<button class="btn small" data-act="edit" data-id="${p.id}">Edit</button>
          <button class="btn small danger" data-act="delete" data-id="${p.id}">Delete</button>` : ""}
        </div></td></tr>`
      )
      .join("")}</tbody></table></div>`;
}

$("#view").addEventListener("click", async (e) => {
  const btn = e.target.closest("button[data-act]");
  if (!btn) return;
  const id = Number(btn.dataset.id);
  const act = btn.dataset.act;
  if (act === "move") movementDialog(id);
  else if (act === "edit") productDialog(state.products.find((p) => p.id === id));
  else if (act === "delete") {
    const p = state.products.find((x) => x.id === id);
    if (!confirm(`Delete "${p.name}" and its stock history? This cannot be undone.`)) return;
    try { await api(`/products/${id}`, { method: "DELETE" }); toast("Product deleted"); loadProducts(); }
    catch (err) { toast(err.message, true); }
  } else if (act === "del-cat" || act === "del-sup") {
    try {
      await api(`/${act === "del-cat" ? "categories" : "suppliers"}/${id}`, { method: "DELETE" });
      await loadLookups(); toast("Deleted"); render();
    } catch (err) { toast(err.message, true); }
  }
});

function productDialog(p) {
  const editing = !!p;
  const body = `<div class="form-grid">
    <label>SKU <input name="sku" required value="${esc(p?.sku)}"></label>
    <label>Name <input name="name" required value="${esc(p?.name)}"></label>
    <label>Category <select name="category_id">${options(state.categories, p?.category_id, "None")}</select></label>
    <label>Supplier <select name="supplier_id">${options(state.suppliers, p?.supplier_id, "None")}</select></label>
    <label>Selling price (TND) <input name="price" type="number" min="0" step="0.01" required value="${p?.price ?? ""}"></label>
    <label>Purchase cost (TND) <input name="cost" type="number" min="0" step="0.01" value="${p?.cost ?? 0}"></label>
    ${editing ? "" : '<label>Starting stock <input name="quantity" type="number" min="0" step="1" value="0"></label>'}
    <label>Alert when stock is at or below <input name="low_stock_threshold" type="number" min="0" step="1" value="${p?.low_stock_threshold ?? 5}"></label>
    <label class="full">Description <textarea name="description" rows="2">${esc(p?.description)}</textarea></label>
  </div>`;
  openDialog(editing ? "Edit product" : "Add product", body, editing ? "Save changes" : "Add product", async (f) => {
    const data = {
      sku: f.get("sku").trim(),
      name: f.get("name").trim(),
      description: f.get("description"),
      price: Number(f.get("price")),
      cost: Number(f.get("cost") || 0),
      low_stock_threshold: Number(f.get("low_stock_threshold")),
      category_id: f.get("category_id") ? Number(f.get("category_id")) : null,
      supplier_id: f.get("supplier_id") ? Number(f.get("supplier_id")) : null,
    };
    if (editing) await api(`/products/${p.id}`, { method: "PUT", body: data });
    else await api("/products", { method: "POST", body: { ...data, quantity: Number(f.get("quantity") || 0) } });
    toast(editing ? "Product updated" : "Product added");
    render();
  });
}

/* ---------- stock movements ---------- */
async function movementDialog(productId) {
  const all = await api("/products");
  const product = all.find((x) => x.id === productId);
  const body = `<div class="form-grid">
    <label class="full">Product <select name="product_id">${options(all, productId)}</select></label>
    <label>Action <select name="type">
      <option value="in">Add stock (delivery, return)</option>
      <option value="out">Remove stock (sale, damage)</option>
      <option value="adjust">Set exact count (inventory)</option>
    </select></label>
    <label>Quantity <input name="quantity" type="number" min="0" step="1" required></label>
    <label class="full">Reason <input name="reason" maxlength="200" placeholder="e.g. Supplier delivery, Online order #123"></label>
  </div>`;
  openDialog(product ? `Move stock: ${product.name}` : "New stock movement", body, "Save movement", async (f) => {
    await api("/stock/movements", {
      method: "POST",
      body: { product_id: Number(f.get("product_id")), type: f.get("type"), quantity: Number(f.get("quantity")), reason: f.get("reason") },
    });
    toast("Stock updated");
    render();
  });
}

async function renderMovements(view) {
  const rows = await api("/stock/movements?limit=200");
  view.innerHTML = `<div class="page-head"><h2>Stock movements</h2>
    <button class="btn primary" id="new-move">New movement</button></div>${movementsTable(rows)}`;
  $("#new-move").addEventListener("click", () => movementDialog());
}

/* ---------- settings (admin) ---------- */
async function renderSettings(view) {
  const users = await api("/auth/users");
  view.innerHTML = `
    <div class="page-head"><h2>Settings</h2></div>
    <div class="grid-2">
      <section class="panel"><h3>Categories</h3>
        <form id="cat-form" class="toolbar"><input name="name" placeholder="New category" required><button class="btn primary">Add</button></form>
        ${state.categories.map((c) => `<div class="toolbar">${esc(c.name)} <button class="btn small danger" data-act="del-cat" data-id="${c.id}">Delete</button></div>`).join("") || '<p class="empty">No categories.</p>'}
      </section>
      <section class="panel"><h3>Suppliers</h3>
        <form id="sup-form" class="toolbar"><input name="name" placeholder="New supplier" required><input name="phone" placeholder="Phone"><button class="btn primary">Add</button></form>
        ${state.suppliers.map((s) => `<div class="toolbar">${esc(s.name)} <span class="muted">${esc(s.phone)}</span> <button class="btn small danger" data-act="del-sup" data-id="${s.id}">Delete</button></div>`).join("") || '<p class="empty">No suppliers.</p>'}
      </section>
    </div>
    <section class="panel"><h3>Users</h3>
      <form id="user-form" class="toolbar">
        <input name="username" placeholder="Username" minlength="3" required>
        <input name="password" type="password" placeholder="Password (6+ characters)" minlength="6" required>
        <select name="role"><option value="staff">Staff</option><option value="admin">Admin</option></select>
        <button class="btn primary">Add user</button>
      </form>
      <div class="table-wrap"><table><thead><tr><th>Username</th><th>Role</th></tr></thead>
      <tbody>${users.map((u) => `<tr><td>${esc(u.username)}</td><td>${esc(u.role)}</td></tr>`).join("")}</tbody></table></div>
    </section>`;

  const submit = (id, path, build, msg) =>
    $(id).addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        await api(path, { method: "POST", body: build(new FormData(e.target)) });
        await loadLookups();
        toast(msg);
        render();
      } catch (err) { toast(err.message, true); }
    });
  submit("#cat-form", "/categories", (f) => ({ name: f.get("name").trim() }), "Category added");
  submit("#sup-form", "/suppliers", (f) => ({ name: f.get("name").trim(), phone: f.get("phone") }), "Supplier added");
  submit("#user-form", "/auth/users", (f) => ({ username: f.get("username").trim(), password: f.get("password"), role: f.get("role") }), "User added");
}

function debounce(fn, ms) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

/* ---------- boot ---------- */
if (state.token && state.user) startApp();
else showLogin();

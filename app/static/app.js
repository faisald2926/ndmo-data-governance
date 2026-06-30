"use strict";

/* ---------------- i18n ---------------- */
const T = {
  ar: {
    appTitle:"حوكمة البيانات", loginSubtitle:"سجّل الدخول للمتابعة",
    username:"اسم المستخدم", password:"كلمة المرور", login:"دخول", logout:"خروج",
    demoHint:"تجريبي: admin / admin123 — أو viewer / viewer123",
    overview:"نظرة عامة", records:"السجلات", quality:"الجودة", evaluation:"التقييم",
    lineage:"تتبّع الأثر", classify:"تصنيف مباشر", users:"المستخدمون",
    m_total:"إجمالي السجلات", m_classified:"المُصنّفة", m_review:"تحتاج مراجعة", m_quality:"مشاكل الجودة",
    levelDist:"توزيع مستويات التصنيف", qualityByDim:"مشاكل الجودة حسب البُعد",
    runPipeline:"تشغيل المعالجة", seedData:"تحميل البيانات", running:"جارٍ التنفيذ…", noData:"لا توجد بيانات بعد — شغّل المعالجة.",
    filterLevel:"المستوى", filterReview:"المراجعة", all:"الكل", onlyReview:"تحتاج مراجعة فقط",
    colId:"#", colSource:"المصدر", colLevel:"المستوى", colImpact:"فئة الأثر", colConf:"الثقة",
    colDecided:"حُدّد بواسطة", colRationale:"التبرير", colReview:"مراجعة", colActions:"إجراءات",
    save:"حفظ", yes:"نعم", no:"لا", refresh:"تحديث",
    filterDim:"البُعد", colRowId:"معرّف الصف", colColumn:"العمود", colDim:"البُعد", colDefect:"النوع", colDesc:"الوصف",
    runEval:"تشغيل التقييم", accuracy:"دقة التصنيف", evaluated:"عدد السجلات المُقيّمة",
    confusion:"مصفوفة الالتباس (الصحيح ↓ / المتوقع →)", qualityPR:"الجودة: الدقة والاسترجاع",
    dimension:"البُعد", precision:"الدقة", recall:"الاسترجاع",
    noLineage:"لا يوجد أثر — شغّل المعالجة.",
    classifyPrompt:"أدخل نصًا عربيًا لتصنيفه:", classifyBtn:"صنّف",
    level:"المستوى", confidence:"الثقة", reviewNeeded:"تحتاج مراجعة", evidence:"الدليل", rationale:"التبرير",
    createUser:"إضافة مستخدم", uName:"اسم المستخدم", uPass:"كلمة المرور", uRole:"الدور",
    roleAdmin:"مدير", roleViewer:"مشاهد", create:"إنشاء", colUser:"المستخدم", colRole:"الدور",
    colCreated:"تاريخ الإنشاء", del:"حذف", confirmDel:"حذف هذا المستخدم؟",
    loading:"جارٍ التحميل…", adminOnly:"للمدير فقط",
  },
  en: {
    appTitle:"Data Governance", loginSubtitle:"Sign in to continue",
    username:"Username", password:"Password", login:"Sign in", logout:"Sign out",
    demoHint:"Demo: admin / admin123 — or viewer / viewer123",
    overview:"Overview", records:"Records", quality:"Quality", evaluation:"Evaluation",
    lineage:"Lineage", classify:"Live classify", users:"Users",
    m_total:"Total records", m_classified:"Classified", m_review:"Needs review", m_quality:"Quality findings",
    levelDist:"Classification level distribution", qualityByDim:"Quality findings by dimension",
    runPipeline:"Run pipeline", seedData:"Seed data", running:"Running…", noData:"No data yet — run the pipeline.",
    filterLevel:"Level", filterReview:"Review", all:"All", onlyReview:"Needs review only",
    colId:"#", colSource:"Source", colLevel:"Level", colImpact:"Impact", colConf:"Conf.",
    colDecided:"Decided by", colRationale:"Rationale", colReview:"Review", colActions:"Actions",
    save:"Save", yes:"Yes", no:"No", refresh:"Refresh",
    filterDim:"Dimension", colRowId:"Row id", colColumn:"Column", colDim:"Dimension", colDefect:"Type", colDesc:"Description",
    runEval:"Run evaluation", accuracy:"Classification accuracy", evaluated:"Records evaluated",
    confusion:"Confusion matrix (true ↓ / predicted →)", qualityPR:"Quality: precision & recall",
    dimension:"Dimension", precision:"Precision", recall:"Recall",
    noLineage:"No lineage yet — run the pipeline.",
    classifyPrompt:"Enter Arabic text to classify:", classifyBtn:"Classify",
    level:"Level", confidence:"Confidence", reviewNeeded:"Needs review", evidence:"Evidence", rationale:"Rationale",
    createUser:"Add user", uName:"Username", uPass:"Password", uRole:"Role",
    roleAdmin:"Admin", roleViewer:"Viewer", create:"Create", colUser:"User", colRole:"Role",
    colCreated:"Created", del:"Delete", confirmDel:"Delete this user?",
    loading:"Loading…", adminOnly:"Admin only",
  }
};
const LVL_EN = {"عام":"Public","مقيّد":"Restricted","سري":"Secret","سري للغاية":"Top secret"};
const LVL_CLASS = {"عام":"public","مقيّد":"restricted","سري":"secret","سري للغاية":"topsecret"};
const LEVELS = ["عام","مقيّد","سري","سري للغاية"];
const LVL_FILL = {"عام":"#1d9e75","مقيّد":"#ba7517","سري":"#d85a30","سري للغاية":"#c0392b"};

const state = { token:null, role:null, username:null, lang:"ar", section:"overview" };

const t = k => (T[state.lang][k] ?? k);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const lvlLabel = l => state.lang === "ar" ? l : (LVL_EN[l] || l);
const lvlBadge = l => `<span class="lvl ${LVL_CLASS[l]||""}">${esc(lvlLabel(l))}</span>`;
const $ = s => document.querySelector(s);

/* ---------------- API ---------------- */
async function api(path, opts={}){
  opts.headers = Object.assign({"Content-Type":"application/json"}, opts.headers||{});
  if (state.token) opts.headers["Authorization"] = "Bearer " + state.token;
  const r = await fetch(path, opts);
  if (r.status === 401){ doLogout(); throw new Error("unauthorized"); }
  if (!r.ok){ let d; try{ d=(await r.json()).detail; }catch{ d=r.statusText; } throw new Error(d || ("HTTP "+r.status)); }
  return r.status === 204 ? null : r.json();
}

/* ---------------- language ---------------- */
function applyLang(){
  document.documentElement.lang = state.lang;
  document.documentElement.dir = state.lang === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach(el => el.textContent = t(el.dataset.i18n));
  const swap = state.lang === "ar" ? "English" : "العربية";
  const lt = $("#lang-toggle"); if (lt) lt.textContent = swap;
  const ll = $("#login-lang"); if (ll) ll.textContent = swap;
}
function setLang(l){ state.lang = l; localStorage.setItem("ndmo_lang", l); applyLang();
  if (!$("#app").hidden){ buildNav(); route(state.section); } }

/* ---------------- auth ---------------- */
async function doLogin(username, password){
  const r = await fetch("/auth/login", {method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({username, password})});
  if (!r.ok) throw new Error("bad");
  const d = await r.json();
  state.token=d.access_token; state.role=d.role; state.username=d.username;
  localStorage.setItem("ndmo_token",d.access_token);
  localStorage.setItem("ndmo_role",d.role); localStorage.setItem("ndmo_user",d.username);
  showApp();
}
function doLogout(){
  state.token=state.role=state.username=null;
  ["ndmo_token","ndmo_role","ndmo_user"].forEach(k=>localStorage.removeItem(k));
  $("#app").hidden = true; $("#login").hidden = false;
}
const isAdmin = () => state.role === "admin";

/* ---------------- shell ---------------- */
const SECTIONS = [
  ["overview", renderOverview], ["records", renderRecords], ["quality", renderQuality],
  ["evaluation", renderEvaluation], ["lineage", renderLineage], ["classify", renderClassify],
  ["users", renderUsers, true],
];
function buildNav(){
  const nav = $("#sidenav"); nav.innerHTML = "";
  SECTIONS.forEach(([key,, adminOnly]) => {
    if (adminOnly && !isAdmin()) return;
    const b = document.createElement("button");
    b.className = "nav-item" + (key===state.section ? " active" : "");
    b.innerHTML = `<span class="t">${esc(t(key))}</span>`;
    b.onclick = () => { state.section = key; buildNav(); route(key); };
    nav.appendChild(b);
  });
}
function route(key){
  const fn = (SECTIONS.find(s => s[0]===key) || SECTIONS[0])[1];
  $("#content").innerHTML = `<p class="spinner">${esc(t("loading"))}</p>`;
  fn().catch(e => { $("#content").innerHTML = `<p class="error">${esc(e.message)}</p>`; });
}
function showApp(){
  $("#login").hidden = true; $("#app").hidden = false;
  $("#user-name").textContent = state.username;
  $("#user-role").textContent = isAdmin() ? t("roleAdmin") : t("roleViewer");
  applyLang(); buildNav(); route(state.section);
}

/* ---------------- views ---------------- */
async function renderOverview(){
  const s = await api("/stats");
  const adminBtns = isAdmin()
    ? `<div class="controls"><button class="primary" id="run-pipe">${esc(t("runPipeline"))}</button>
       <button class="ghost" id="seed">${esc(t("seedData"))}</button>
       <span id="pipe-status" class="spinner"></span></div>` : "";
  const lvl = s.classification_by_level || {};
  const maxL = Math.max(1, ...LEVELS.map(l => lvl[l]||0));
  const bars = LEVELS.map(l => `<div class="barrow"><span class="name">${esc(lvlLabel(l))}</span>
    <div class="track"><div class="fill" style="width:${Math.max(2,Math.round((lvl[l]||0)/maxL*100))}%;background:${LVL_FILL[l]}"></div></div>
    <span class="cnt">${(lvl[l]||0).toLocaleString()}</span></div>`).join("");
  const dim = s.quality_findings_by_dimension || {};
  const maxD = Math.max(1, ...Object.values(dim));
  const dimBars = Object.keys(dim).length ? Object.entries(dim).map(([d,c]) =>
    `<div class="barrow"><span class="name">${esc(d)}</span>
     <div class="track"><div class="fill" style="width:${Math.max(2,Math.round(c/maxD*100))}%;background:#185fa5"></div></div>
     <span class="cnt">${c.toLocaleString()}</span></div>`).join("") : `<p class="muted">—</p>`;
  $("#content").innerHTML = `
    <h2 class="section-title">${esc(t("overview"))}</h2>
    <p class="section-sub">NDMO</p>
    ${adminBtns}
    <div class="metrics">
      <div class="metric"><div class="label">${esc(t("m_total"))}</div><div class="value">${(s.total_records||0).toLocaleString()}</div></div>
      <div class="metric"><div class="label">${esc(t("m_classified"))}</div><div class="value">${(s.classified||0).toLocaleString()}</div></div>
      <div class="metric"><div class="label">${esc(t("m_review"))}</div><div class="value">${(s.needs_review||0).toLocaleString()}</div></div>
      <div class="metric"><div class="label">${esc(t("m_quality"))}</div><div class="value">${Object.values(dim).reduce((a,b)=>a+b,0).toLocaleString()}</div></div>
    </div>
    <div class="card"><h3>${esc(t("levelDist"))}</h3><div style="margin-top:12px">${bars}</div></div>
    <div class="card"><h3>${esc(t("qualityByDim"))}</h3><div style="margin-top:12px">${dimBars}</div></div>`;
  if (isAdmin()){
    $("#run-pipe").onclick = async () => {
      $("#pipe-status").textContent = t("running");
      try{ await api("/pipeline/run",{method:"POST",body:JSON.stringify({max_per_file:300})}); route("overview"); }
      catch(e){ $("#pipe-status").textContent = e.message; }
    };
    $("#seed").onclick = async () => {
      $("#pipe-status").textContent = t("running");
      try{ await api("/data/seed",{method:"POST"}); $("#pipe-status").textContent="✓"; }
      catch(e){ $("#pipe-status").textContent = e.message; }
    };
  }
}

async function renderRecords(){
  const lvlOpts = `<option value="">${esc(t("all"))}</option>` + LEVELS.map(l=>`<option value="${l}">${esc(lvlLabel(l))}</option>`).join("");
  $("#content").innerHTML = `
    <h2 class="section-title">${esc(t("records"))}</h2>
    <div class="controls">
      <label>${esc(t("filterLevel"))}</label><select id="f-level">${lvlOpts}</select>
      <label>${esc(t("filterReview"))}</label><select id="f-review"><option value="">${esc(t("all"))}</option><option value="true">${esc(t("onlyReview"))}</option></select>
      <button class="btn-sm" id="f-go">${esc(t("refresh"))}</button>
    </div>
    <div class="table-wrap"><table id="rec-tbl"></table></div>`;
  const load = async () => {
    const lv=$("#f-level").value, rv=$("#f-review").value;
    let q="/records?limit=200"; if(lv) q+="&level="+encodeURIComponent(lv); if(rv) q+="&needs_review=true";
    const rows = await api(q);
    const adminCol = isAdmin() ? `<th>${esc(t("colActions"))}</th>` : "";
    let html = `<thead><tr><th>${esc(t("colId"))}</th><th>${esc(t("colSource"))}</th><th>${esc(t("colLevel"))}</th>
      <th>${esc(t("colConf"))}</th><th>${esc(t("colDecided"))}</th><th>${esc(t("colRationale"))}</th><th>${esc(t("colReview"))}</th>${adminCol}</tr></thead><tbody>`;
    html += rows.map(r => {
      const act = isAdmin() ? `<td><div class="row-edit">
        <select data-id="${r.id}" class="lvl-sel">${LEVELS.map(l=>`<option value="${l}" ${l===r.ndmo_level?"selected":""}>${esc(lvlLabel(l))}</option>`).join("")}</select>
        <button class="btn-sm save-lvl" data-id="${r.id}">${esc(t("save"))}</button></div></td>` : "";
      return `<tr><td>${r.id}</td><td>${esc(r.source_file)}<br><span class="muted">${esc(r.record_id)}</span></td>
        <td>${lvlBadge(r.ndmo_level)}</td><td>${r.confidence ?? ""}</td><td><span class="pill">${esc(r.decided_by||"")}</span></td>
        <td>${esc(r.rationale||"")}</td><td>${r.needs_review?`<span class="flag">●</span>`:""}</td>${act}</tr>`;
    }).join("") || `<tr><td colspan="8" class="muted">${esc(t("noData"))}</td></tr>`;
    html += "</tbody>";
    $("#rec-tbl").innerHTML = html;
    if (isAdmin()) document.querySelectorAll(".save-lvl").forEach(b => b.onclick = async () => {
      const id=b.dataset.id, val=document.querySelector(`.lvl-sel[data-id="${id}"]`).value;
      b.textContent="…"; try{ await api(`/records/${id}`,{method:"PATCH",body:JSON.stringify({ndmo_level:val})}); b.textContent="✓"; }
      catch(e){ b.textContent=e.message; }
    });
  };
  $("#f-go").onclick = load; await load();
}

async function renderQuality(){
  const dims=["Completeness","Uniqueness","Timeliness","Validity","Accuracy","Consistency"];
  $("#content").innerHTML = `
    <h2 class="section-title">${esc(t("quality"))}</h2>
    <div class="controls"><label>${esc(t("filterDim"))}</label>
      <select id="q-dim"><option value="">${esc(t("all"))}</option>${dims.map(d=>`<option>${d}</option>`).join("")}</select>
      <button class="btn-sm" id="q-go">${esc(t("refresh"))}</button></div>
    <div class="table-wrap"><table id="q-tbl"></table></div>`;
  const load = async () => {
    const d=$("#q-dim").value; let q="/quality/findings?limit=400"; if(d) q+="&dimension="+d;
    const rows = await api(q);
    let html=`<thead><tr><th>${esc(t("colSource"))}</th><th>${esc(t("colRowId"))}</th><th>${esc(t("colColumn"))}</th>
      <th>${esc(t("colDim"))}</th><th>${esc(t("colDefect"))}</th><th>${esc(t("colDesc"))}</th></tr></thead><tbody>`;
    html += rows.map(r=>`<tr><td>${esc(r.file)}</td><td>${esc(r.row_id)}</td><td>${esc(r.column)}</td>
      <td><span class="pill">${esc(r.dq_dimension)}</span></td><td>${esc(r.defect_type)}</td><td>${esc(r.description)}</td></tr>`).join("")
      || `<tr><td colspan="6" class="muted">${esc(t("noData"))}</td></tr>`;
    $("#q-tbl").innerHTML = html+"</tbody>";
  };
  $("#q-go").onclick = load; await load();
}

async function renderEvaluation(){
  $("#content").innerHTML = `<h2 class="section-title">${esc(t("evaluation"))}</h2>
    <div class="controls"><button class="primary" id="ev-go">${esc(t("runEval"))}</button><span id="ev-status" class="spinner"></span></div>
    <div id="ev-out"></div>`;
  $("#ev-go").onclick = async () => {
    $("#ev-status").textContent = t("loading");
    try{
      const ev = await api("/evaluate"); $("#ev-status").textContent="";
      const c = ev.classification, lv = c.levels;
      const acc = c.accuracy==null ? "—" : (c.accuracy*100).toFixed(1)+"%";
      let cm = `<div class="table-wrap"><table class="confusion"><thead><tr><th></th>${lv.map(p=>`<th>${esc(lvlLabel(p))}</th>`).join("")}</tr></thead><tbody>`;
      cm += lv.map(tr=>`<tr><th>${esc(lvlLabel(tr))}</th>${lv.map(p=>`<td class="${tr===p?"diag":""}">${(c.confusion_matrix[tr]?.[p]??0)}</td>`).join("")}</tr>`).join("");
      cm += "</tbody></table></div>";
      const q = ev.quality.by_dimension;
      let qt = `<div class="table-wrap"><table><thead><tr><th>${esc(t("dimension"))}</th><th>${esc(t("precision"))}</th><th>${esc(t("recall"))}</th></tr></thead><tbody>`;
      qt += Object.entries(q).map(([d,m])=>`<tr><td>${esc(d)}</td><td>${m.precision??"—"}</td><td>${m.recall??"—"}</td></tr>`).join("")+"</tbody></table></div>";
      $("#ev-out").innerHTML = `<div class="metrics">
        <div class="metric"><div class="label">${esc(t("accuracy"))}</div><div class="value">${acc}</div></div>
        <div class="metric"><div class="label">${esc(t("evaluated"))}</div><div class="value">${(c.evaluated||0).toLocaleString()}</div></div></div>
        <div class="card"><h3>${esc(t("confusion"))}</h3>${cm}</div>
        <div class="card"><h3>${esc(t("qualityPR"))}</h3>${qt}</div>`;
    }catch(e){ $("#ev-status").textContent = e.message; }
  };
}

async function renderLineage(){
  const lin = await api("/lineage");
  if (!lin.events || !lin.events.length){ $("#content").innerHTML = `<h2 class="section-title">${esc(t("lineage"))}</h2><p class="muted">${esc(t("noLineage"))}</p>`; return; }
  const steps = lin.events.map((e,i)=>`<div class="card" style="margin-bottom:10px">
    <b>${esc(e.job)}</b> ${e.derived_level?lvlBadge(e.derived_level):""}
    ${e.note?`<div class="muted" style="margin-top:6px">${esc(e.note)}</div>`:""}</div>
    ${i<lin.events.length-1?`<div style="text-align:center;color:#999">↓</div>`:""}`).join("");
  $("#content").innerHTML = `<h2 class="section-title">${esc(t("lineage"))}</h2>${steps}`;
}

async function renderClassify(){
  $("#content").innerHTML = `<h2 class="section-title">${esc(t("classify"))}</h2>
    <div class="card"><p>${esc(t("classifyPrompt"))}</p>
    <textarea id="cl-text">أعاني من حالة صحية وأطلب إعفاءً، هويتي 1043215789</textarea>
    <div class="controls" style="margin-top:10px"><button class="primary" id="cl-go">${esc(t("classifyBtn"))}</button></div>
    <div id="cl-out"></div></div>`;
  $("#cl-go").onclick = async () => {
    const txt = $("#cl-text").value;
    $("#cl-out").innerHTML = `<p class="spinner">${esc(t("loading"))}</p>`;
    try{
      const r = await api("/classify",{method:"POST",body:JSON.stringify({text:txt})});
      $("#cl-out").innerHTML = `<div class="metrics" style="margin-top:14px">
        <div class="metric"><div class="label">${esc(t("level"))}</div><div class="value" style="font-size:18px">${lvlBadge(r.ndmo_level)}</div></div>
        <div class="metric"><div class="label">${esc(t("confidence"))}</div><div class="value">${r.confidence}</div></div>
        <div class="metric"><div class="label">${esc(t("reviewNeeded"))}</div><div class="value" style="font-size:18px">${r.needs_review?t("yes"):t("no")}</div></div>
        </div>
        <p><b>${esc(t("evidence"))}:</b> ${esc(r.evidence||"—")}</p>
        <p><b>${esc(t("rationale"))}:</b> ${esc(r.rationale||"—")}</p>
        <p class="muted">${esc(r.decided_by||"")}</p>`;
    }catch(e){ $("#cl-out").innerHTML = `<p class="error">${esc(e.message)}</p>`; }
  };
}

async function renderUsers(){
  if (!isAdmin()){ $("#content").innerHTML = `<p class="error">${esc(t("adminOnly"))}</p>`; return; }
  const load = async () => {
    const users = await api("/users");
    let html = `<thead><tr><th>${esc(t("colId"))}</th><th>${esc(t("colUser"))}</th><th>${esc(t("colRole"))}</th><th>${esc(t("colCreated"))}</th><th></th></tr></thead><tbody>`;
    html += users.map(u=>`<tr><td>${u.id}</td><td>${esc(u.username)}</td>
      <td><span class="pill">${u.role==="admin"?t("roleAdmin"):t("roleViewer")}</span></td>
      <td class="muted">${esc((u.created_at||"").slice(0,10))}</td>
      <td>${u.username!==state.username?`<button class="btn-sm del-u" data-id="${u.id}">${esc(t("del"))}</button>`:""}</td></tr>`).join("");
    $("#u-tbl").innerHTML = html+"</tbody>";
    document.querySelectorAll(".del-u").forEach(b=>b.onclick=async()=>{
      if(!confirm(t("confirmDel")))return;
      try{ await api(`/users/${b.dataset.id}`,{method:"DELETE"}); load(); }catch(e){ alert(e.message); }
    });
  };
  $("#content").innerHTML = `<h2 class="section-title">${esc(t("users"))}</h2>
    <div class="card"><h3>${esc(t("createUser"))}</h3>
      <div class="controls" style="margin-top:10px">
        <input id="nu-name" placeholder="${esc(t("uName"))}" />
        <input id="nu-pass" type="password" placeholder="${esc(t("uPass"))}" />
        <select id="nu-role"><option value="viewer">${esc(t("roleViewer"))}</option><option value="admin">${esc(t("roleAdmin"))}</option></select>
        <button class="primary" id="nu-go">${esc(t("create"))}</button><span id="nu-status" class="spinner"></span>
      </div></div>
    <div class="table-wrap"><table id="u-tbl"></table></div>`;
  $("#nu-go").onclick = async () => {
    const username=$("#nu-name").value.trim(), password=$("#nu-pass").value, role=$("#nu-role").value;
    if(!username||!password){ $("#nu-status").textContent="!"; return; }
    $("#nu-status").textContent="…";
    try{ await api("/users",{method:"POST",body:JSON.stringify({username,password,role})});
      $("#nu-name").value=$("#nu-pass").value=""; $("#nu-status").textContent="✓"; load(); }
    catch(e){ $("#nu-status").textContent=e.message; }
  };
  await load();
}

/* ---------------- boot ---------------- */
function boot(){
  state.lang = localStorage.getItem("ndmo_lang") || "ar";
  $("#login-form").onsubmit = async e => {
    e.preventDefault(); $("#login-error").hidden = true;
    try{ await doLogin($("#username").value.trim(), $("#password").value); }
    catch{ $("#login-error").textContent = state.lang==="ar"?"بيانات الدخول غير صحيحة":"Invalid credentials"; $("#login-error").hidden=false; }
  };
  $("#login-lang").onclick = () => setLang(state.lang==="ar"?"en":"ar");
  $("#lang-toggle").onclick = () => setLang(state.lang==="ar"?"en":"ar");
  $("#logout").onclick = doLogout;
  applyLang();
  const tok = localStorage.getItem("ndmo_token");
  if (tok){
    state.token=tok; state.role=localStorage.getItem("ndmo_role"); state.username=localStorage.getItem("ndmo_user");
    api("/auth/me").then(showApp).catch(doLogout);
  }
}
boot();

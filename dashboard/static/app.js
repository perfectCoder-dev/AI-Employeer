/* ── JS for AI Employee Dashboard ──────────────────────────────────── */
// Use same-origin API so the dashboard works on any PORT/HOST.
const API = `${window.location.origin}/api`;
const TOKEN_STORAGE_KEY = 'aiEmployeeApprovalToken';

// ── State ─────────────────────────────────────────────────────────────
let currentView = 'dashboard';
let statsCache  = null;

function getApprovalToken() {
  return sessionStorage.getItem(TOKEN_STORAGE_KEY) || '';
}

function setApprovalToken(token) {
  if (token) sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
  else sessionStorage.removeItem(TOKEN_STORAGE_KEY);
}

async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getApprovalToken();
  if (token) headers.set('X-Approval-Token', token);

  let response = await fetch(url, { ...options, headers });
  if (response.status !== 403) return response;

  const entered = window.prompt('Enter dashboard approval token');
  if (!entered) return response;
  setApprovalToken(entered.trim());
  headers.set('X-Approval-Token', entered.trim());
  response = await fetch(url, { ...options, headers });
  if (response.status === 403) setApprovalToken('');
  return response;
}

// ── Navigation ────────────────────────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(el => {
  el.addEventListener('click', e => {
    e.preventDefault();
    switchView(el.dataset.view);
  });
});

function switchView(view) {
  currentView = view;
  document.querySelectorAll('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.view === view));
  document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.id === `view-${view}`));
  const titles = {
    dashboard:   ['Dashboard', 'Real-time agent overview'],
    pending:     ['Pending Approval', 'Items awaiting your decision'],
    needs_action:['Needs Action',     'Items queued for processing'],
    done:        ['Done',             'Successfully completed items'],
    plans:       ['Plans',            'AI-generated action plans'],
    activity:    ['Activity Log',     'Full audit trail of agent actions'],
    failed:      ['Failed',           'Items that encountered errors'],
  };
  const [title, sub] = titles[view] || [view, ''];
  document.getElementById('view-title').textContent    = title;
  document.getElementById('view-subtitle').textContent = sub;
  loadView(view);
}

// ── Data loaders ──────────────────────────────────────────────────────
async function fetchJSON(url) {
  const r = await apiFetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

async function loadStats() {
  try {
    const s = await fetchJSON(`${API}/stats`);
    statsCache = s;
    // KPI values
    setKPI('pending', s.pending_approval);
    setKPI('action',  s.needs_action);
    setKPI('done',    s.done);
    setKPI('failed',  s.failed);
    setKPI('plans',   s.plans);
    setKPI('total',   s.total_actions);

    // Badges
    setEl('badge-pending', s.pending_approval);
    setEl('badge-action',  s.needs_action);

    // Bars (max = done + failed for context)
    const max = Math.max(s.done + s.failed + s.pending_approval, 1);
    setBar('bar-pending', s.pending_approval, max);
    setBar('bar-action',  s.needs_action,     max);
    setBar('bar-done',    s.done,             max);
    setBar('bar-failed',  s.failed,           max);
    setBar('bar-plans',   s.plans,            Math.max(s.plans, 1));
    setBar('bar-total',   s.total_actions,    Math.max(s.total_actions, 1));

    // Recent activity
    renderActivityList(s.recent_activity || []);

    // Breakdown
    renderBreakdown(s.action_breakdown || {});

    document.getElementById('last-updated').textContent = 'Updated ' + new Date().toLocaleTimeString();
    document.getElementById('agent-status-text').textContent = 'Agents active';
  } catch(err) {
    document.getElementById('agent-status-text').textContent = 'Server offline';
    document.getElementById('agent-dot').style.background = 'var(--red)';
    document.getElementById('agent-dot').style.boxShadow = '0 0 8px var(--red)';
    console.error('Stats load failed:', err);
  }
}

function setKPI(id, val) {
  const el = document.getElementById(`kpi-${id}`);
  if (el) el.textContent = val ?? '—';
}
function setEl(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val ?? 0;
}
function setBar(id, val, max) {
  const el = document.getElementById(id);
  if (el) el.style.width = `${Math.min(100, (val / max) * 100)}%`;
}

// ── Render helpers ────────────────────────────────────────────────────
function actionColor(action) {
  if (!action) return '#6b7280';
  if (action.includes('success') || action.includes('done')) return 'var(--green)';
  if (action.includes('fail'))   return 'var(--red)';
  if (action.includes('linkedin')) return 'var(--accent)';
  if (action.includes('approval') || action.includes('pending')) return 'var(--amber)';
  if (action.includes('plan'))   return 'var(--purple)';
  return 'var(--blue)';
}

function renderActivityList(items) {
  const el = document.getElementById('recent-activity');
  if (!items.length) { el.innerHTML = emptyState('No recent activity'); return; }
  el.innerHTML = items.map(item => `
    <div class="activity-item">
      <div class="activity-dot" style="background:${actionColor(item.action)}"></div>
      <div class="activity-content">
        <div class="activity-action">${humanAction(item.action)}</div>
        <div class="activity-file">${item.filename || ''}</div>
      </div>
      <div class="activity-time">${fmtTime(item.timestamp)}</div>
    </div>
  `).join('');
}

function renderBreakdown(breakdown) {
  const el = document.getElementById('action-breakdown');
  const entries = Object.entries(breakdown).sort((a,b) => b[1]-a[1]);
  const maxVal  = entries[0]?.[1] || 1;
  if (!entries.length) { el.innerHTML = emptyState('No data'); return; }
  el.innerHTML = entries.map(([action, count]) => `
    <div class="breakdown-row">
      <div class="breakdown-label">${humanAction(action)}</div>
      <div class="breakdown-bar-wrap">
        <div class="breakdown-bar-fill" style="width:${(count/maxVal)*100}%"></div>
      </div>
      <div class="breakdown-count">${count}</div>
    </div>
  `).join('');
}

// ── Folder views ──────────────────────────────────────────────────────
async function loadFolderView(folderKey, listId, countId, showApprove = false) {
  const listEl  = document.getElementById(listId);
  const countEl = document.getElementById(countId);
  listEl.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';
  try {
    const items = await fetchJSON(`${API}/folder/${folderKey}`);
    if (countEl) countEl.textContent = `${items.length} item${items.length !== 1 ? 's' : ''}`;
    if (!items.length) { listEl.innerHTML = emptyState('Nothing here yet'); return; }
    listEl.innerHTML = items.map(item => renderItemRow(item, folderKey, showApprove)).join('');
    // Attach listeners
    listEl.querySelectorAll('.item-row').forEach(row => {
      row.addEventListener('click', e => {
        if (e.target.closest('.item-actions button')) return;
        openModal(row.dataset.folder, row.dataset.id);
      });
    });
    if (showApprove) {
      listEl.querySelectorAll('.btn-approve').forEach(btn => {
        btn.addEventListener('click', async e => {
          e.stopPropagation();
          await approveItem(btn.dataset.id, listId, countId);
        });
      });
      listEl.querySelectorAll('.btn-reject').forEach(btn => {
        btn.addEventListener('click', async e => {
          e.stopPropagation();
          await rejectItem(btn.dataset.id, listId, countId);
        });
      });
    }
  } catch(err) {
    listEl.innerHTML = `<div class="empty-state">Error loading data</div>`;
    console.error(err);
  }
}

function renderItemRow(item, folder, showApprove) {
  const typeIcon = typeToIcon(item.type);
  const iconClass = item.type === 'linkedin_post' ? 'icon-linkedin'
                  : item.type === 'plan'          ? 'icon-plan'
                  : item.type === 'email'          ? 'icon-email'
                  : 'icon-default';
  const prio = item.priority || 'medium';
  const from  = item.from_ ? `<span>From: ${escHtml(item.from_)}</span> · ` : '';
  return `
    <div class="item-row" data-id="${item.id}" data-folder="${folder}">
      <div class="item-type-icon ${iconClass}">${typeIcon}</div>
      <div class="item-body">
        <div class="item-subject">${escHtml(item.subject || item.name)}</div>
        <div class="item-meta">${from}<span>${fmtDate(item.created)}</span></div>
      </div>
      <div class="item-actions">
        <span class="priority-pill prio-${prio}">${prio}</span>
        ${showApprove ? `
          <button class="btn-approve" data-id="${item.id}">✓ Approve</button>
          <button class="btn-reject"  data-id="${item.id}">✗ Reject</button>
        ` : ''}
      </div>
    </div>
  `;
}

function typeToIcon(type) {
  if (type === 'linkedin_post') return `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6zM2 9h4v12H2z"/><circle cx="4" cy="4" r="2"/></svg>`;
  if (type === 'plan')          return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`;
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>`;
}

// ── Approve / Reject ─────────────────────────────────────────────────
async function approveItem(filename, listId, countId) {
  try {
    const r = await apiFetch(`${API}/approve/${encodeURIComponent(filename)}`, { method: 'POST' });
    const data = await r.json();
    if (data.success) {
      toast(`✓ Approved: ${filename}`, 'success');
      loadFolderView('pending_approval', listId, countId, true);
      loadStats();
    } else toast(data.error || 'Approve failed', 'error');
  } catch(err) { toast('Network error', 'error'); }
}

async function rejectItem(filename, listId, countId) {
  try {
    const r = await apiFetch(`${API}/reject/${encodeURIComponent(filename)}`, { method: 'POST' });
    const data = await r.json();
    if (data.success) {
      toast(`✗ Rejected: ${filename}`, 'error');
      loadFolderView('pending_approval', listId, countId, true);
      loadStats();
    } else toast(data.error || 'Reject failed', 'error');
  } catch(err) { toast('Network error', 'error'); }
}

// ── Activity log view ─────────────────────────────────────────────────
async function loadActivityLog() {
  const el = document.getElementById('log-timeline');
  el.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';
  try {
    const logs = await fetchJSON(`${API}/logs`);
    if (!logs.length) { el.innerHTML = emptyState('No log entries yet'); return; }
    el.innerHTML = logs.map((entry, i) => `
      <div class="log-entry">
        <div class="log-timeline-line">
          <div class="log-dot" style="background:${actionColor(entry.action)}"></div>
          ${i < logs.length - 1 ? '<div class="log-line"></div>' : ''}
        </div>
        <div class="log-content">
          <div class="log-action">${humanAction(entry.action)}</div>
          <div class="log-file">${entry.filename || ''} ${entry.details?.destination ? '→ ' + shortPath(entry.details.destination) : ''}</div>
          <div class="log-time">${fmtDate(entry.timestamp)} · ${fmtTime(entry.timestamp)}</div>
        </div>
      </div>
    `).join('');
  } catch(err) {
    el.innerHTML = emptyState('Could not load logs');
    console.error(err);
  }
}

// ── Modal ─────────────────────────────────────────────────────────────
async function openModal(folder, filename) {
  try {
    const item = await fetchJSON(`${API}/file/${folder}/${encodeURIComponent(filename)}`);
    document.getElementById('modal-title').textContent    = item.subject || item.name;
    document.getElementById('modal-from').textContent     = item.from_ ? `From: ${item.from_}` : '';
    document.getElementById('modal-type-badge').textContent = item.type || 'email';
    document.getElementById('modal-priority-badge').textContent = item.priority || 'medium';
    document.getElementById('modal-body').textContent     = item.body || '(no content)';

    const actionsEl = document.getElementById('modal-actions');
    actionsEl.innerHTML = '';
    if (folder === 'pending_approval') {
      const appBtn = document.createElement('button');
      appBtn.className = 'btn-approve'; appBtn.textContent = '✓ Approve';
      appBtn.onclick = async () => {
        await approveItem(filename, 'pending-list', 'pending-count');
        closeModal();
        if (currentView === 'dashboard') loadStats();
      };
      const rejBtn = document.createElement('button');
      rejBtn.className = 'btn-reject'; rejBtn.textContent = '✗ Reject';
      rejBtn.onclick = async () => {
        await rejectItem(filename, 'pending-list', 'pending-count');
        closeModal();
        if (currentView === 'dashboard') loadStats();
      };
      actionsEl.append(appBtn, rejBtn);
    }

    document.getElementById('modal-overlay').style.display = 'flex';
  } catch(err) {
    toast('Could not load file details', 'error');
    console.error(err);
  }
}

function closeModal() {
  document.getElementById('modal-overlay').style.display = 'none';
}
document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('modal-overlay').addEventListener('click', e => {
  if (e.target === document.getElementById('modal-overlay')) closeModal();
});

// ── View router ───────────────────────────────────────────────────────
function loadView(view) {
  switch(view) {
    case 'dashboard':    loadStats(); break;
    case 'pending':      loadFolderView('pending_approval', 'pending-list', 'pending-count', true); break;
    case 'needs_action': loadFolderView('needs_action',     'needs-list',   'needs-count',   false); break;
    case 'done':         loadFolderView('done',             'done-list',    'done-count',    false); break;
    case 'plans':        loadFolderView('plans',            'plans-list',   'plans-count',   false); break;
    case 'activity':     loadActivityLog(); break;
    case 'failed':       loadFolderView('failed',           'failed-list',  'failed-count',  false); break;
  }
}

// ── Refresh button ────────────────────────────────────────────────────
document.getElementById('btn-refresh').addEventListener('click', () => {
  const btn = document.getElementById('btn-refresh');
  btn.style.animation = 'spin 0.5s linear';
  setTimeout(() => btn.style.animation = '', 600);
  loadView(currentView);
});

// ── Toast ─────────────────────────────────────────────────────────────
function toast(msg, type = 'success') {
  const c  = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ── Utils ─────────────────────────────────────────────────────────────
function fmtDate(iso) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }); }
  catch { return iso; }
}
function fmtTime(iso) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }); }
  catch { return ''; }
}
function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function emptyState(msg) {
  return `<div class="empty-state">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 13h6m-3-3v6m-9 1V7a2 2 0 0 1 2-2h6l2 2h6a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2z"/></svg>
    ${msg}
  </div>`;
}
function humanAction(a) {
  if (!a) return 'Unknown';
  return a.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
function shortPath(p) {
  if (!p) return '';
  const parts = p.split(/[/\\]/);
  return parts.slice(-2).join('/');
}

// ── Auto-refresh every 30 s ───────────────────────────────────────────
setInterval(() => loadView(currentView), 30000);

// ── Init ──────────────────────────────────────────────────────────────
loadView('dashboard');

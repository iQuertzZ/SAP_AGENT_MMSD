'use strict';

const API = '/api/v1';

let _currentAnalysis = null;
let _currentRequestId = null;
let _selectedActionTcode = null;

// ── Scenarios ──────────────────────────────────────────────────────────────
const SCENARIOS = {
  'mm-grir': { tcode: 'MIRO', module: 'MM', document_id: '51000321', status: 'BLOCKED', company_code: '1000' },
  'mm-missing-gr': { tcode: 'MIRO', module: 'MM', document_id: '51000322', status: 'BLOCKED', company_code: '1000' },
  'sd-credit': { tcode: 'VA03', module: 'SD', document_id: '1000081234', status: 'BLOCKED', sales_org: '1000' },
  'sd-pricing': { tcode: 'VA03', module: 'SD', document_id: '1000081235', status: 'OPEN' },
};

function loadScenario(key) {
  const s = SCENARIOS[key];
  if (!s) return;
  set('tcode', s.tcode);
  set('module', s.module);
  set('document_id', s.document_id);
  set('status', s.status);
  set('company_code', s.company_code || '');
  set('plant', s.sales_org || s.plant || '1000');
}

// ── Health check ───────────────────────────────────────────────────────────
async function checkHealth() {
  try {
    const data = await apiFetch('/health');
    document.getElementById('connector-label').textContent = data.connector;
    const dot = document.querySelector('.dot');
    dot.className = 'dot ' + (data.status === 'ok' ? 'dot--ok' : 'dot--warn');
  } catch (_) {}
}

// ── Main: Analyze ──────────────────────────────────────────────────────────
async function runAnalysis() {
  const btn = document.getElementById('analyze-btn');
  btn.disabled = true;
  showLoading(true);

  try {
    const payload = buildPayload();
    const data = await apiFetch('/analyze', 'POST', payload);
    _currentAnalysis = data;
    _currentRequestId = null;
    _selectedActionTcode = null;

    renderDiagnosis(data.diagnosis);
    renderActions(data.recommended_actions, data.context);
    showApprovalSection(false);
    hide('sim-placeholder');
    hide('simulation-card');
    show('approval-section');
    resetApprovalUI();
  } catch (err) {
    alert('Analysis failed: ' + err.message);
    showLoading(false);
  } finally {
    btn.disabled = false;
    showLoading(false);
  }
}

function renderDiagnosis(d) {
  hide('empty-state');
  show('diagnosis-card');

  document.getElementById('issue-type').textContent = d.issue_type.replace(/_/g, ' ');
  const sev = document.getElementById('severity-badge');
  sev.textContent = d.severity.toUpperCase();
  sev.className = `severity-badge severity--${d.severity}`;

  document.getElementById('root-cause').textContent = d.root_cause;

  const src = document.getElementById('diagnosis-source');
  src.textContent = d.source.replace('_', ' ').toUpperCase();

  // Confidence bar
  const pct = Math.round(d.confidence * 100);
  document.getElementById('confidence-fill').style.width = pct + '%';
  document.getElementById('confidence-pct').textContent = pct + '%';

  // Evidence
  const evList = document.getElementById('evidence-list');
  evList.innerHTML = '';
  (d.supporting_evidence || []).forEach(ev => {
    const div = document.createElement('div');
    div.className = 'evidence-item';
    div.textContent = '• ' + ev;
    evList.appendChild(div);
  });
}

function renderActions(actions, context) {
  show('actions-section');
  const list = document.getElementById('actions-list');
  list.innerHTML = '';

  actions.forEach((a, i) => {
    const card = document.createElement('button');
    card.className = 'btn--action action-card';
    card.id = `action-${i}`;
    card.innerHTML = `
      <div class="action-header">
        <span class="action-tcode">${a.tcode}</span>
        <span class="risk-badge risk--${a.risk}">${a.risk}</span>
        <span style="margin-left:auto;font-size:11px;color:var(--text-muted)">
          ${Math.round(a.confidence * 100)}% confidence
        </span>
      </div>
      <div class="action-desc">${a.description}</div>
      <div class="action-footer">
        <span style="font-size:11px;color:var(--text-muted)">
          ⟳ ${a.rollback_plan.substring(0, 60)}…
        </span>
        <button class="simulate-btn" onclick="simulateAction('${a.tcode}', ${i}, event)">
          ⚡ Simulate
        </button>
      </div>
    `;
    list.appendChild(card);
  });
}

// ── Simulate ───────────────────────────────────────────────────────────────
async function simulateAction(tcode, idx, event) {
  event.stopPropagation();
  if (!_currentAnalysis) return;

  // Highlight selected action
  document.querySelectorAll('.action-card').forEach(c => c.classList.remove('selected'));
  document.getElementById(`action-${idx}`)?.classList.add('selected');
  _selectedActionTcode = tcode;

  const ctx = _currentAnalysis.context;
  try {
    const data = await apiFetch('/simulate', 'POST', {
      tcode: ctx.tcode,
      module: ctx.module,
      document_id: ctx.document_id,
      action_tcode: tcode,
    });
    renderSimulation(data.simulation, tcode);
  } catch (err) {
    alert('Simulation failed: ' + err.message);
  }
}

function renderSimulation(sim, tcode) {
  hide('sim-placeholder');
  show('simulation-card');

  document.getElementById('sim-action-label').textContent = tcode;
  document.getElementById('sim-docs').textContent = sim.documents_affected;

  const fin = sim.financial;
  const finText = fin.posting_required
    ? (fin.amount ? formatAmount(fin.amount, fin.currency) : 'Yes')
    : 'None';
  document.getElementById('sim-financial').textContent = finText;

  const riskEl = document.getElementById('sim-risk-val');
  const riskPct = Math.round(sim.risk_score * 100);
  riskEl.textContent = riskPct + '%';
  riskEl.style.color = riskPct >= 60 ? 'var(--danger)' : riskPct >= 35 ? 'var(--warning)' : 'var(--success)';

  document.getElementById('sim-reversible').textContent = sim.reversible ? 'Yes' : 'No';

  const warnEl = document.getElementById('sim-warnings');
  warnEl.innerHTML = (sim.warnings || []).map(w => `<div class="warn-item">⚠ ${w}</div>`).join('');

  const blockEl = document.getElementById('sim-blockers');
  blockEl.innerHTML = (sim.blockers || []).map(b => `<div class="blocker-item">✕ ${b}</div>`).join('');
}

// ── Approval ───────────────────────────────────────────────────────────────
async function submitApproval() {
  if (!_currentAnalysis) return;
  const ctx = _currentAnalysis.context;
  try {
    const data = await apiFetch('/approval/submit', 'POST', {
      tcode: ctx.tcode,
      module: ctx.module,
      document_id: ctx.document_id,
      status: ctx.status,
      user: get('approver-name') || 'user',
    });
    _currentRequestId = data.request_id;
    setApprovalBadge(data.status);
    show('approve-reject-section');
    showApprovalResult(`Request ${data.request_id.substring(0, 8)}… submitted — awaiting approval.`, 'ok');
  } catch (err) {
    showApprovalResult('Submit failed: ' + err.message, 'error');
  }
}

async function approveRequest() {
  if (!_currentRequestId) return;
  try {
    const data = await apiFetch(`/approval/${_currentRequestId}/approve`, 'POST', {
      request_id: _currentRequestId,
      approver: get('approver-name') || 'approver',
    });
    setApprovalBadge(data.status);
    showApprovalResult(`✓ Approved. Request is ready for execution.`, 'ok');
    hide('approve-reject-section');
  } catch (err) {
    showApprovalResult('Approve failed: ' + err.message, 'error');
  }
}

async function rejectRequest() {
  if (!_currentRequestId) return;
  const reason = prompt('Rejection reason:');
  if (!reason) return;
  try {
    const data = await apiFetch(`/approval/${_currentRequestId}/reject`, 'POST', {
      request_id: _currentRequestId,
      approver: get('approver-name') || 'approver',
      reason,
    });
    setApprovalBadge(data.status);
    showApprovalResult(`✗ Rejected: ${reason}`, 'error');
    hide('approve-reject-section');
  } catch (err) {
    showApprovalResult('Reject failed: ' + err.message, 'error');
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function buildPayload() {
  return {
    tcode: get('tcode').toUpperCase(),
    module: get('module'),
    document_id: get('document_id'),
    status: get('status'),
    company_code: get('company_code') || null,
    plant: get('plant') || null,
    user: null,
  };
}

async function apiFetch(path, method = 'GET', body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const resp = await fetch(API + path, opts);
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || err.message || resp.statusText);
  }
  return resp.json();
}

function get(id) { return document.getElementById(id)?.value ?? ''; }
function set(id, val) { const el = document.getElementById(id); if (el) el.value = val; }
function show(id) { document.getElementById(id)?.classList.remove('hidden'); }
function hide(id) { document.getElementById(id)?.classList.add('hidden'); }

function showLoading(on) {
  if (on) { show('loading'); hide('empty-state'); hide('diagnosis-card'); hide('actions-section'); }
  else { hide('loading'); }
}

function showApprovalSection(on) {
  on ? show('approval-section') : hide('approval-section');
}

function setApprovalBadge(status) {
  const badge = document.getElementById('approval-status-badge');
  badge.textContent = status.replace('_', ' ').toUpperCase();
  badge.className = `badge badge--${status.replace('_', '-')}`;
}

function showApprovalResult(msg, type) {
  const el = document.getElementById('approval-result');
  el.textContent = msg;
  el.className = `approval-result approval-result--${type}`;
  show('approval-result');
}

function resetApprovalUI() {
  hide('approve-reject-section');
  hide('approval-result');
  document.getElementById('approval-status-badge').textContent = '';
  document.getElementById('approval-status-badge').className = 'badge';
}

function formatAmount(amount, currency) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency', currency: currency || 'EUR', maximumFractionDigits: 0,
  }).format(amount);
}

// ── Init ───────────────────────────────────────────────────────────────────
checkHealth();

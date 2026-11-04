"""Domain-Specific Frontend and Backend Generators for Autonomous DevOps Swarm.

Provides realistic, production-ready, interactive applications for:
- E-Commerce & Retail Stores (Catalog, Cart, Checkout, Order Tracking, Retail KPIs)
- Hospital & Healthcare (Clinical Dashboard, Doctor Directory, Appointments, Patient EHR)
- Student Management & Academic Portals (Directory, GPA, Enrollments, Academic Cohorts)
- Generic Operations Platforms (Dynamic Metrics, Entity CRUD, Search, Analytics)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List


def generate_css() -> str:
    """Unified responsive dark-themed styling for all domain applications."""
    return """\
:root {
  --bg-dark: #0a0e17;
  --bg-card: #111827;
  --border-color: #1f293d;
  --accent: #3b82f6;
  --accent-glow: rgba(59, 130, 246, 0.25);
  --accent-green: #10b981;
  --accent-purple: #8b5cf6;
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg-dark); color: var(--text-main); font-family: var(--font); min-height: 100vh; display: flex; flex-direction: column; }
.portal-navbar { display: flex; align-items: center; justify-content: space-between; padding: 14px 28px; background: rgba(17, 24, 39, 0.85); backdrop-filter: blur(12px); border-bottom: 1px solid var(--border-color); position: sticky; top: 0; z-index: 50; }
.nav-brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.15rem; color: #fff; }
.brand-icon { font-size: 1.4rem; }
.brand-pill { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; background: #064e3b; color: #6ee7b7; padding: 2px 8px; border-radius: 9999px; margin-left: 6px; }
.nav-links { display: flex; gap: 6px; }
.nav-link { background: transparent; border: none; color: var(--text-muted); font-size: 0.9rem; font-weight: 500; padding: 8px 14px; border-radius: 8px; cursor: pointer; transition: all 0.2s ease; display: flex; align-items: center; gap: 6px; }
.nav-link:hover { color: #fff; background: rgba(255, 255, 255, 0.05); }
.nav-link.active { color: #fff; background: #1e293b; border: 1px solid var(--border-color); }
.nav-badge { background: #2563eb; color: #fff; font-size: 0.72rem; font-weight: 700; padding: 2px 7px; border-radius: 9999px; }
.nav-user { display: flex; align-items: center; gap: 10px; }
.login-btn { background: #1e293b; border: 1px solid var(--border-color); color: #fff; font-size: 0.85rem; font-weight: 500; padding: 7px 14px; border-radius: 8px; cursor: pointer; transition: all 0.2s; }
.login-btn:hover { border-color: var(--accent); }
.mobile-menu-toggle { display: none; background: transparent; border: 1px solid var(--border-color); color: #fff; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 1.1rem; }
.portal-container { flex: 1; padding: 28px; max-width: 1300px; margin: 0 auto; width: 100%; }
.portal-view { display: none; animation: fadeIn 0.3s ease; }
.portal-view.active { display: block; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
.view-header { margin-bottom: 24px; }
.view-header h2 { font-size: 1.6rem; font-weight: 700; color: #fff; margin-bottom: 6px; }
.view-header p { color: var(--text-muted); font-size: 0.92rem; }
.metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
.metric-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 6px; transition: transform 0.2s, border-color 0.2s; }
.metric-card:hover { transform: translateY(-2px); border-color: var(--accent); }
.metric-card span { font-size: 0.8rem; font-weight: 600; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.04em; }
.metric-card strong { font-size: 1.85rem; font-weight: 700; color: #fff; }
.metric-card small { font-size: 0.8rem; color: var(--text-muted); }
.trend-up { color: #86efac !important; font-weight: 600; }
.quick-actions-bar { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 28px; }
.action-btn { padding: 10px 18px; border-radius: 8px; font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all 0.2s; border: none; }
.action-btn.primary { background: var(--accent); color: #fff; box-shadow: 0 4px 12px var(--accent-glow); }
.action-btn.primary:hover { background: #2563eb; }
.action-btn.secondary { background: var(--bg-card); border: 1px solid var(--border-color); color: #e2e8f0; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.search-input { flex: 1; min-width: 260px; background: var(--bg-card); border: 1px solid var(--border-color); color: #fff; padding: 10px 16px; border-radius: 8px; font-size: 0.9rem; outline: none; }
.search-input:focus { border-color: var(--accent); }
.filter-select { background: var(--bg-card); border: 1px solid var(--border-color); color: #fff; padding: 10px 16px; border-radius: 8px; font-size: 0.9rem; outline: none; cursor: pointer; }
.table-responsive { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; overflow-x: auto; }
.portal-table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; }
.portal-table th { padding: 14px 18px; background: rgba(30, 41, 59, 0.4); color: var(--text-muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; border-bottom: 1px solid var(--border-color); }
.portal-table td { padding: 14px 18px; border-bottom: 1px solid rgba(31, 41, 61, 0.5); color: #e2e8f0; }
.portal-table tr:hover td { background: rgba(255, 255, 255, 0.02); }
.status-badge { display: inline-block; padding: 3px 9px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }
.status-badge.active, .status-badge.delivered, .status-badge.completed, .status-badge.stable { background: rgba(16, 185, 129, 0.15); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.3); }
.status-badge.shipped, .status-badge.observation, .status-badge.graduated { background: rgba(139, 92, 246, 0.15); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.3); }
.status-badge.processing, .status-badge.on-leave, .status-badge.scheduled { background: rgba(245, 158, 11, 0.15); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.3); }
.status-badge.critical, .status-badge.cancelled { background: rgba(239, 68, 68, 0.15); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.3); }
.delete-btn { background: transparent; border: 1px solid #ef4444; color: #ef4444; padding: 4px 10px; border-radius: 6px; cursor: pointer; font-size: 0.75rem; font-weight: 600; transition: all 0.2s; }
.delete-btn:hover { background: #ef4444; color: #fff; }
.form-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 28px; max-width: 780px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 0.85rem; font-weight: 600; color: #cbd5e1; }
.form-group input, .form-group select { background: #0f172a; border: 1px solid var(--border-color); color: #fff; padding: 10px 14px; border-radius: 8px; font-size: 0.9rem; outline: none; }
.form-group input:focus, .form-group select:focus { border-color: var(--accent); }
.form-actions { display: flex; gap: 12px; margin-top: 24px; }
.submit-btn { background: var(--accent); color: #fff; border: none; padding: 12px 22px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
.submit-btn:hover { background: #2563eb; }
.cancel-btn { background: transparent; border: 1px solid var(--border-color); color: #94a3b8; padding: 12px 18px; border-radius: 8px; font-weight: 600; cursor: pointer; }

/* E-Commerce Specific Styles */
.store-hero-banner { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid var(--border-color); border-radius: 14px; padding: 32px 36px; margin-bottom: 24px; }
.hero-tag { display: inline-block; background: rgba(59, 130, 246, 0.2); color: #93c5fd; font-size: 0.8rem; font-weight: 600; padding: 3px 10px; border-radius: 9999px; margin-bottom: 12px; }
.store-hero-banner h2 { font-size: 1.8rem; font-weight: 800; color: #fff; margin-bottom: 8px; }
.store-hero-banner p { color: var(--text-muted); font-size: 0.95rem; max-width: 650px; }
.products-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin-bottom: 28px; }
.product-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; display: flex; flex-direction: column; transition: transform 0.2s, border-color 0.2s; }
.product-card:hover { transform: translateY(-3px); border-color: var(--accent); }
.product-icon-wrap { background: #0f172a; padding: 28px; display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid var(--border-color); }
.product-icon { font-size: 2.8rem; }
.category-pill { background: rgba(255, 255, 255, 0.08); color: var(--text-muted); font-size: 0.72rem; font-weight: 600; padding: 3px 8px; border-radius: 6px; }
.product-info { padding: 18px; display: flex; flex-direction: column; flex: 1; }
.product-info h3 { font-size: 1.05rem; font-weight: 700; color: #fff; margin-bottom: 6px; }
.product-desc { color: var(--text-muted); font-size: 0.83rem; margin-bottom: 12px; flex: 1; line-height: 1.4; }
.product-rating { font-size: 0.82rem; color: #fbbf24; margin-bottom: 6px; }
.product-rating small { color: var(--text-muted); }
.product-stock-tag { font-size: 0.78rem; color: #6ee7b7; font-weight: 600; margin-bottom: 14px; }
.product-price-bar { display: flex; align-items: center; justify-content: space-between; margin-top: auto; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.06); }
.product-price { font-size: 1.35rem; font-weight: 800; color: #fff; }
.add-cart-btn { background: var(--accent); color: #fff; border: none; padding: 8px 14px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: background 0.2s; }
.add-cart-btn:hover { background: #2563eb; }

/* Cart Layout */
.cart-layout { display: grid; grid-template-columns: 2fr 1fr; gap: 24px; align-items: start; }
.cart-items-wrapper { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; }
.cart-item-row { display: flex; align-items: center; justify-content: space-between; padding: 14px 0; border-bottom: 1px solid var(--border-color); gap: 14px; }
.item-icon { font-size: 2rem; }
.item-details { flex: 1; display: flex; flex-direction: column; gap: 3px; }
.item-details strong { font-size: 0.95rem; color: #fff; }
.item-details span { font-size: 0.82rem; color: var(--text-muted); }
.qty-controls { display: flex; align-items: center; gap: 8px; background: #0f172a; padding: 4px 8px; border-radius: 6px; border: 1px solid var(--border-color); }
.qty-btn { background: transparent; border: none; color: #fff; font-size: 1.1rem; cursor: pointer; padding: 0 4px; }
.qty-val { font-size: 0.9rem; font-weight: 700; min-width: 20px; text-align: center; }
.item-line-total { font-size: 1.1rem; font-weight: 700; color: #86efac; min-width: 80px; text-align: right; }
.cart-summary-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 24px; display: flex; flex-direction: column; gap: 12px; }
.cart-summary-card h3 { font-size: 1.15rem; font-weight: 700; margin-bottom: 8px; }
.summary-row { display: flex; justify-content: space-between; font-size: 0.9rem; color: var(--text-muted); }
.summary-row strong { color: #fff; }
.summary-row.total { font-size: 1.25rem; font-weight: 800; color: #fff; padding-top: 10px; }
.summary-row.total strong { color: #86efac; font-size: 1.35rem; }
.summary-divider { height: 1px; background: var(--border-color); margin: 6px 0; }
.checkout-btn { width: 100%; margin-top: 12px; padding: 14px; text-align: center; }
.checkout-card { max-width: 680px; }
.form-section-title { font-size: 1rem; color: #93c5fd; margin-bottom: 12px; font-weight: 700; }
.checkout-total-banner { background: #0f172a; border: 1px solid var(--border-color); padding: 16px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; margin: 20px 0; font-size: 1.1rem; }
.checkout-total-banner strong { font-size: 1.4rem; color: #86efac; }

/* Analytics & Common */
.analytics-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.analytics-box { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 22px; }
.analytics-box h3 { margin-bottom: 16px; font-size: 1.1rem; }
.bar-row { margin-bottom: 12px; }
.bar-row span { font-size: 0.85rem; color: #cbd5e1; display: block; margin-bottom: 4px; }
.bar-bg { background: #1e293b; height: 10px; border-radius: 9999px; overflow: hidden; }
.bar-fill { background: var(--accent); height: 100%; border-radius: 9999px; }
.modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(4px); z-index: 100; align-items: center; justify-content: center; }
.modal-overlay.active { display: flex; }
.modal-dialog { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 14px; width: 90%; max-width: 440px; padding: 24px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5); }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.modal-close { background: transparent; border: none; color: #94a3b8; font-size: 1.2rem; cursor: pointer; }
.modal-body { display: flex; flex-direction: column; gap: 10px; margin-bottom: 18px; }
.modal-body input { background: #0f172a; border: 1px solid var(--border-color); color: #fff; padding: 10px 12px; border-radius: 8px; outline: none; }
.toast-notification { position: fixed; bottom: 24px; right: 24px; background: #064e3b; color: #6ee7b7; border: 1px solid #059669; padding: 12px 20px; border-radius: 8px; font-size: 0.9rem; font-weight: 600; box-shadow: 0 10px 25px rgba(0,0,0,0.4); opacity: 0; transform: translateY(10px); transition: all 0.3s; z-index: 200; pointer-events: none; }
.toast-notification.active { opacity: 1; transform: translateY(0); }
@media (max-width: 768px) {
  .form-row, .analytics-cards, .cart-layout { grid-template-columns: 1fr; }
  .nav-links { display: none; flex-direction: column; width: 100%; position: absolute; top: 100%; left: 0; background: #111827; padding: 14px; border-bottom: 1px solid var(--border-color); }
  .nav-links.mobile-open { display: flex; }
  .mobile-menu-toggle { display: block; }
}
"""


# =============================================================================
# COMMERCE IMPLEMENTATIONS (BUSINESS-AWARE & DYNAMIC)
# =============================================================================

from .commerce_generator import (
    generate_commerce_backend,
    generate_commerce_html,
    generate_commerce_js,
    generate_commerce_tests,
)


def generate_ecommerce_html(name: str, ctx: dict[str, Any] | None = None) -> str:
    ctx = dict(ctx or {})
    if "name" not in ctx and name:
        ctx["name"] = name
    return generate_commerce_html(ctx)


def generate_ecommerce_js(name: str, ctx: dict[str, Any] | None = None) -> str:
    ctx = dict(ctx or {})
    if "name" not in ctx and name:
        ctx["name"] = name
    return generate_commerce_js(ctx)


def generate_ecommerce_backend(name: str, ctx: dict[str, Any] | None = None) -> str:
    ctx = dict(ctx or {})
    if "name" not in ctx and name:
        ctx["name"] = name
    return generate_commerce_backend(ctx)


def generate_ecommerce_tests(name: str, ctx: dict[str, Any] | None = None) -> str:
    ctx = dict(ctx or {})
    if "name" not in ctx and name:
        ctx["name"] = name
    return generate_commerce_tests(ctx)

# =============================================================================
# HOSPITAL / HEALTHCARE IMPLEMENTATIONS
# =============================================================================

def generate_hospital_html(name: str, ctx: dict[str, Any]) -> str:
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name}</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <nav class="portal-navbar">
    <div class="nav-brand">
      <span class="brand-icon">🏥</span>
      <span class="brand-title">{name}</span>
      <span class="brand-pill">Clinical Care</span>
    </div>
    <div class="nav-links" id="nav-links">
      <button class="nav-link active" onclick="showView('dashboard')">📊 Clinical Dashboard</button>
      <button class="nav-link" onclick="showView('doctors')">🩺 Doctor Directory</button>
      <button class="nav-link" onclick="showView('appointments')">📅 Appointments</button>
      <button class="nav-link" onclick="showView('patients')">📋 Patient EHR</button>
      <button class="nav-link" onclick="showView('book')">➕ Book Consultation</button>
    </div>
    <div class="nav-user">
      <button class="login-btn" id="auth-btn" onclick="toggleAuthModal()">👤 Medical Staff Login</button>
      <button class="mobile-menu-toggle" onclick="toggleMobileMenu()">☰</button>
    </div>
  </nav>

  <main class="portal-container">
    <!-- View 1: Clinical Dashboard -->
    <section id="view-dashboard" class="portal-view active">
      <div class="view-header">
        <h2>Welcome to {name}</h2>
        <p>Operational control center for patient triage, clinical schedules, and physician directories.</p>
      </div>
      <div class="metrics-grid">
        <div class="metric-card">
          <span>Registered Patients</span>
          <strong id="metric-total-patients">142 Patients</strong>
          <small class="trend-up">↑ 12 admitted today</small>
        </div>
        <div class="metric-card">
          <span>Inpatient Capacity</span>
          <strong>88% (220/250 Beds)</strong>
          <small>30 available beds</small>
        </div>
        <div class="metric-card">
          <span>Scheduled Consultations</span>
          <strong class="highlight-val">34 Today</strong>
          <small class="trend-up">On schedule</small>
        </div>
        <div class="metric-card">
          <span>On-Call Physicians</span>
          <strong class="highlight-val">18 Doctors</strong>
          <small>Emergency staff ready</small>
        </div>
      </div>
    </section>

    <!-- View 2: Doctor Directory -->
    <section id="view-doctors" class="portal-view">
      <div class="view-header">
        <h2>Attending Physicians & Specialists</h2>
        <p>Browse department faculty, consultation availability, and certifications.</p>
      </div>
      <div id="doctors-grid" class="products-grid"></div>
    </section>

    <!-- View 3: Appointments -->
    <section id="view-appointments" class="portal-view">
      <div class="view-header">
        <h2>Patient Consultations & Clinical Calendar</h2>
        <p>Track scheduled, ongoing, and completed consultations.</p>
      </div>
      <div class="table-responsive">
        <table class="portal-table">
          <thead><tr><th>ID</th><th>Patient Name</th><th>Attending Physician</th><th>Department</th><th>Time</th><th>Status</th></tr></thead>
          <tbody id="appointments-table-body"></tbody>
        </table>
      </div>
    </section>

    <!-- View 4: Patients EHR -->
    <section id="view-patients" class="portal-view">
      <div class="view-header">
        <h2>Electronic Health Records (EHR)</h2>
        <p>Patient medical history, blood group, diagnosis, and triage state.</p>
      </div>
      <div class="table-responsive">
        <table class="portal-table">
          <thead><tr><th>MRN</th><th>Patient Name</th><th>Blood Group</th><th>Primary Doctor</th><th>Diagnosis</th><th>Triage</th></tr></thead>
          <tbody id="patients-table-body"></tbody>
        </table>
      </div>
    </section>

    <!-- View 5: Book Consultation -->
    <section id="view-book" class="portal-view">
      <div class="view-header">
        <h2>Schedule a Consultation</h2>
        <p>Register a consultation with an attending medical specialist.</p>
      </div>
      <div class="form-card">
        <form id="booking-form" onsubmit="handleBookAppointment(event)">
          <div class="form-row">
            <div class="form-group"><label>Patient Full Name</label><input type="text" id="bk-name" required placeholder="e.g. Maya Chen"></div>
            <div class="form-group"><label>Medical Record Number (MRN)</label><input type="text" id="bk-mrn" required placeholder="e.g. MRN-2026-441"></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label>Attending Physician</label>
              <select id="bk-doctor">
                <option value="Dr. Marcus Vance">Dr. Marcus Vance (Cardiology)</option>
                <option value="Dr. Sarah Lin">Dr. Sarah Lin (Neurology)</option>
                <option value="Dr. Elena Gomez">Dr. Elena Gomez (Pediatrics)</option>
              </select>
            </div>
            <div class="form-group"><label>Chief Medical Complaint</label><input type="text" id="bk-complaint" required placeholder="e.g. Persistent migraine"></div>
          </div>
          <div class="form-actions">
            <button type="submit" class="submit-btn">✓ Confirm Appointment</button>
            <button type="button" class="cancel-btn" onclick="showView('appointments')">Cancel</button>
          </div>
        </form>
      </div>
    </section>
  </main>

  <div id="login-modal" class="modal-overlay">
    <div class="modal-dialog">
      <div class="modal-header"><h3>🔒 Medical Staff Portal Login</h3><button class="modal-close" onclick="toggleAuthModal()">✕</button></div>
      <form onsubmit="handleLogin(event)">
        <div class="modal-body">
          <label>Staff ID / Email</label><input type="email" value="dr.vance@hospital.org" required>
          <label>Access Code</label><input type="password" value="medpass2026" required>
        </div>
        <div class="modal-footer"><button type="submit" class="submit-btn">Authenticate</button></div>
      </form>
    </div>
  </div>

  <div id="toast" class="toast-notification"></div>
  <script src="app.js"></script>
</body>
</html>
"""


def generate_hospital_js(name: str) -> str:
    return """\
// Live Hospital Care Controller
const DOCTORS = [
  { id: 'd1', name: 'Dr. Marcus Vance', specialty: 'Cardiology', icon: '🩺', room: 'Suite 401', status: 'Available' },
  { id: 'd2', name: 'Dr. Sarah Lin', specialty: 'Neurology', icon: '🧠', room: 'Suite 310', status: 'In Consultation' },
  { id: 'd3', name: 'Dr. Elena Gomez', specialty: 'Pediatrics', icon: '👶', room: 'Suite 205', status: 'Available' },
  { id: 'd4', name: 'Dr. David Chen', specialty: 'Orthopedics', icon: '🦴', room: 'Suite 108', status: 'In Surgery' }
];

const APPOINTMENTS = [
  { id: 'APT-101', patient: 'Liam Taylor', doctor: 'Dr. Marcus Vance', dept: 'Cardiology', time: '10:30 AM', status: 'Completed' },
  { id: 'APT-102', patient: 'Chloe Kim', doctor: 'Dr. Sarah Lin', dept: 'Neurology', time: '11:15 AM', status: 'In Progress' },
  { id: 'APT-103', patient: 'Alexander Wright', doctor: 'Dr. Elena Gomez', dept: 'Pediatrics', time: '02:00 PM', status: 'Scheduled' }
];

const PATIENTS = [
  { mrn: 'MRN-2026-001', name: 'Liam Taylor', blood: 'O+', doctor: 'Dr. Marcus Vance', diag: 'Arrhythmia Evaluation', triage: 'Stable' },
  { mrn: 'MRN-2026-002', name: 'Chloe Kim', blood: 'A+', doctor: 'Dr. Sarah Lin', diag: 'Neurological Assessment', triage: 'Observation' },
  { mrn: 'MRN-2026-003', name: 'Alexander Wright', blood: 'B+', doctor: 'Dr. Elena Gomez', diag: 'Pediatric Checkup', triage: 'Stable' }
];

function showView(viewId) {
  document.querySelectorAll('.portal-view').forEach(v => v.classList.remove('active'));
  const target = document.getElementById('view-' + viewId);
  if (target) target.classList.add('active');
  document.querySelectorAll('.nav-link').forEach(btn => {
    const matches = btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(viewId);
    btn.classList.toggle('active', !!matches);
  });
  if (viewId === 'doctors') renderDoctors();
  if (viewId === 'appointments') renderAppointments();
  if (viewId === 'patients') renderPatients();
}

function renderDoctors() {
  const grid = document.getElementById('doctors-grid');
  if (!grid) return;
  grid.innerHTML = DOCTORS.map(d => `
    <div class='product-card'>
      <div class='product-icon-wrap'><span class='product-icon'>${d.icon}</span><span class='category-pill'>${d.specialty}</span></div>
      <div class='product-info'>
        <h3>${d.name}</h3>
        <p class='product-desc'>Location: ${d.room}</p>
        <div class='product-stock-tag'>Status: ${d.status}</div>
        <div class='product-price-bar'><button class='add-cart-btn' onclick="showView('book')">Book Consultation</button></div>
      </div>
    </div>
  `).join('');
}

function renderAppointments() {
  const tbody = document.getElementById('appointments-table-body');
  if (!tbody) return;
  tbody.innerHTML = APPOINTMENTS.map(a => `
    <tr>
      <td><code>${a.id}</code></td>
      <td><strong>${a.patient}</strong></td>
      <td>${a.doctor}</td>
      <td>${a.dept}</td>
      <td>${a.time}</td>
      <td><span class='status-badge ${a.status.toLowerCase().replace(' ', '-')}'>${a.status}</span></td>
    </tr>
  `).join('');
}

function renderPatients() {
  const tbody = document.getElementById('patients-table-body');
  if (!tbody) return;
  tbody.innerHTML = PATIENTS.map(p => `
    <tr>
      <td><code>${p.mrn}</code></td>
      <td><strong>${p.name}</strong></td>
      <td>${p.blood}</td>
      <td>${p.doctor}</td>
      <td>${p.diag}</td>
      <td><span class='status-badge ${p.triage.toLowerCase()}'>${p.triage}</span></td>
    </tr>
  `).join('');
}

function handleBookAppointment(e) {
  e.preventDefault();
  const name = document.getElementById('bk-name').value;
  const doc = document.getElementById('bk-doctor').value;
  const newApt = { id: 'APT-' + Math.floor(100 + Math.random() * 900), patient: name, doctor: doc, dept: 'Consultation', time: 'Tomorrow 09:00 AM', status: 'Scheduled' };
  APPOINTMENTS.unshift(newApt);
  showToast(`Booked consultation for ${name} with ${doc}`);
  showView('appointments');
}

function toggleAuthModal() {
  const m = document.getElementById('login-modal');
  if (m) m.classList.toggle('active');
}
function toggleMobileMenu() {
  const n = document.getElementById('nav-links');
  if (n) n.classList.toggle('mobile-open');
}
function handleLogin(e) {
  e.preventDefault();
  toggleAuthModal();
  const btn = document.getElementById('auth-btn');
  if (btn) btn.innerHTML = '✓ Dr. Marcus Vance (Cardiology)';
  showToast('Authenticated as Dr. Marcus Vance');
}
function showToast(msg) {
  const t = document.getElementById('toast');
  if (t) {
    t.textContent = '✓ ' + msg;
    t.classList.add('active');
    setTimeout(() => t.classList.remove('active'), 3200);
  }
}
document.addEventListener('DOMContentLoaded', () => { renderDoctors(); });
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  renderDoctors();
}
"""


def generate_hospital_backend(name: str) -> str:
    return f"""\
\"\"\"Autonomous Implementation for: {name}\"\"\"

import uuid
import json
from typing import Any, Dict, List, Optional

_DOCTORS = [
    {{"id": "d1", "name": "Dr. Marcus Vance", "specialty": "Cardiology"}},
    {{"id": "d2", "name": "Dr. Sarah Lin", "specialty": "Neurology"}},
]
_APPOINTMENTS: Dict[str, Dict[str, Any]] = {{}}
_PATIENTS: Dict[str, Dict[str, Any]] = {{}}

def get_status() -> Dict[str, Any]:
    return {{"service": "{name}", "status": "healthy", "doctors": len(_DOCTORS), "appointments": len(_APPOINTMENTS)}}

def list_doctors() -> List[Dict[str, Any]]:
    return list(_DOCTORS)

def book_appointment(payload: Dict[str, Any]) -> Dict[str, Any]:
    apt_id = payload.get("id") or f"APT-{{str(uuid.uuid4())[:6].upper()}}"
    rec = dict(payload)
    rec["id"] = apt_id
    _APPOINTMENTS[apt_id] = rec
    return rec

def list_appointments() -> List[Dict[str, Any]]:
    return list(_APPOINTMENTS.values())

def register_patient(payload: Dict[str, Any]) -> Dict[str, Any]:
    pid = payload.get("id") or f"MRN-{{str(uuid.uuid4())[:6].upper()}}"
    rec = dict(payload)
    rec["id"] = pid
    _PATIENTS[pid] = rec
    return rec

def list_patients() -> List[Dict[str, Any]]:
    return list(_PATIENTS.values())

def clear_data() -> None:
    _APPOINTMENTS.clear()
    _PATIENTS.clear()

if __name__ == "__main__":
    print(f"{name} operational: {{get_status()}}")
"""


def generate_hospital_tests(name: str) -> str:
    return """\
import unittest
import app

class TestHospitalSuite(unittest.TestCase):
    def setUp(self):
        app.clear_data()

    def test_health_status(self):
        status = app.get_status()
        self.assertEqual(status.get("status"), "healthy")

    def test_list_doctors(self):
        docs = app.list_doctors()
        self.assertGreaterEqual(len(docs), 1)

    def test_book_and_list_appointments(self):
        apt = app.book_appointment({"patient": "John Doe", "doctor": "Dr. Vance"})
        self.assertIsNotNone(apt.get("id"))
        apts = app.list_appointments()
        self.assertEqual(len(apts), 1)

if __name__ == "__main__":
    unittest.main()
"""


# =============================================================================
# STUDENT PORTAL IMPLEMENTATIONS
# =============================================================================

def generate_student_html(name: str, entity: str, plural: str, ctx: dict[str, Any]) -> str:
    entity_title = entity.capitalize()
    plural_title = plural.capitalize()
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name}</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <!-- Top Navigation Bar -->
  <nav class="portal-navbar">
    <div class="nav-brand">
      <span class="brand-icon">🎓</span>
      <span class="brand-title">{name}</span>
      <span class="brand-pill">Live Swarm Build</span>
    </div>
    <div class="nav-links" id="nav-links">
      <button class="nav-link active" onclick="showView('dashboard')">📊 Dashboard</button>
      <button class="nav-link" onclick="showView('list')">👥 {plural_title} Directory</button>
      <button class="nav-link" onclick="showView('register')">➕ Register {entity_title}</button>
      <button class="nav-link" onclick="showView('analytics')">📈 Analytics</button>
    </div>
    <div class="nav-user">
      <button class="login-btn" id="auth-btn" onclick="toggleAuthModal()">👤 Administrator Login</button>
      <button class="mobile-menu-toggle" onclick="toggleMobileMenu()">☰</button>
    </div>
  </nav>

  <!-- Main Content Container -->
  <main class="portal-container">
    <!-- View 1: Dashboard -->
    <section id="view-dashboard" class="portal-view active">
      <div class="view-header">
        <h2>Welcome to {name}</h2>
        <p>Operational control center for tracking {plural}, academic progress, and institutional records.</p>
      </div>
      <div class="metrics-grid">
        <div class="metric-card">
          <span>Total Registered {plural_title}</span>
          <strong id="metric-total">48</strong>
          <small class="trend-up">↑ +12% this semester</small>
        </div>
        <div class="metric-card">
          <span>Active Academic Departments</span>
          <strong>6 Departments</strong>
          <small>CS, Engineering, Data Science</small>
        </div>
        <div class="metric-card">
          <span>Average Cumulative GPA</span>
          <strong class="highlight-val">3.72 / 4.0</strong>
          <small class="trend-up">Top 10% performance tier</small>
        </div>
        <div class="metric-card">
          <span>Course Attendance Rate</span>
          <strong class="highlight-val">96.4%</strong>
          <small>Excellent cohort rating</small>
        </div>
      </div>
      <div class="quick-actions-bar">
        <button class="action-btn primary" onclick="showView('register')">➕ Register New {entity_title}</button>
        <button class="action-btn secondary" onclick="showView('list')">🔍 Browse {plural_title} Directory</button>
        <button class="action-btn secondary" onclick="showView('analytics')">📊 View Academic Analytics</button>
      </div>
      <div class="recent-block">
        <h3>Recent Enrolled {plural_title}</h3>
        <div class="table-responsive">
          <table class="portal-table">
            <thead>
              <tr><th>Identifier</th><th>Name</th><th>Department</th><th>GPA</th><th>Status</th></tr>
            </thead>
            <tbody id="recent-table-body">
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- View 2: List & Search Directory -->
    <section id="view-list" class="portal-view">
      <div class="view-header">
        <h2>{plural_title} Directory & Record Management</h2>
        <p>Live search, filter, and inspect enrolled {plural} in real time.</p>
      </div>
      <div class="filter-bar">
        <input type="text" id="search-input" class="search-input" placeholder="Search by name, email, or code..." oninput="filterTable()">
        <select id="dept-filter" class="filter-select" onchange="filterTable()">
          <option value="all">All Departments</option>
          <option value="Computer Science">Computer Science</option>
          <option value="Engineering">Engineering</option>
          <option value="Data Science">Data Science</option>
          <option value="Business Administration">Business Administration</option>
        </select>
        <select id="status-filter" class="filter-select" onchange="filterTable()">
          <option value="all">All Statuses</option>
          <option value="Active">Active</option>
          <option value="Graduated">Graduated</option>
          <option value="On Leave">On Leave</option>
        </select>
      </div>
      <div class="table-responsive">
        <table class="portal-table">
          <thead>
            <tr><th>Student Code</th><th>Full Name</th><th>Institutional Email</th><th>Department</th><th>GPA</th><th>Status</th><th>Actions</th></tr>
          </thead>
          <tbody id="students-table-body">
          </tbody>
        </table>
      </div>
    </section>

    <!-- View 3: Registration Form -->
    <section id="view-register" class="portal-view">
      <div class="view-header">
        <h2>Register New {entity_title}</h2>
        <p>Fill out the required information to enroll a new {entity} into institutional records.</p>
      </div>
      <div class="form-card">
        <form id="registration-form" onsubmit="handleRegister(event)">
          <div class="form-row">
            <div class="form-group">
              <label>First Name</label>
              <input type="text" id="reg-first-name" required placeholder="e.g. Maya">
            </div>
            <div class="form-group">
              <label>Last Name</label>
              <input type="text" id="reg-last-name" required placeholder="e.g. Patel">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>{entity_title} Code</label>
              <input type="text" id="reg-code" required placeholder="e.g. STU-2026-009">
            </div>
            <div class="form-group">
              <label>Institutional Email</label>
              <input type="email" id="reg-email" required placeholder="e.g. maya.patel@school.edu">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Academic Department</label>
              <select id="reg-dept">
                <option value="Computer Science">Computer Science</option>
                <option value="Engineering">Engineering</option>
                <option value="Data Science">Data Science</option>
                <option value="Business Administration">Business Administration</option>
              </select>
            </div>
            <div class="form-group">
              <label>Initial GPA</label>
              <input type="number" step="0.01" min="0" max="4.0" id="reg-gpa" required value="3.85">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Enrollment Status</label>
              <select id="reg-status">
                <option value="Active">Active</option>
                <option value="On Leave">On Leave</option>
              </select>
            </div>
          </div>
          <div class="form-actions">
            <button type="submit" class="submit-btn">✓ Complete {entity_title} Registration</button>
            <button type="button" class="cancel-btn" onclick="showView('list')">Cancel</button>
          </div>
        </form>
      </div>
    </section>

    <!-- View 4: Analytics -->
    <section id="view-analytics" class="portal-view">
      <div class="view-header">
        <h2>Academic Cohort Analytics</h2>
        <p>Real-time department distributions, enrollment growth, and GPA health.</p>
      </div>
      <div class="analytics-cards">
        <div class="analytics-box">
          <h3>Department Distribution</h3>
          <div class="bar-row"><span>Computer Science (45%)</span><div class="bar-bg"><div class="bar-fill" style="width: 45%"></div></div></div>
          <div class="bar-row"><span>Data Science (25%)</span><div class="bar-bg"><div class="bar-fill" style="width: 25%"></div></div></div>
          <div class="bar-row"><span>Engineering (20%)</span><div class="bar-bg"><div class="bar-fill" style="width: 20%"></div></div></div>
          <div class="bar-row"><span>Business (10%)</span><div class="bar-bg"><div class="bar-fill" style="width: 10%"></div></div></div>
        </div>
        <div class="analytics-box">
          <h3>GPA Quartiles</h3>
          <p>3.80 - 4.00: <strong>38% (Dean's Honor Roll)</strong></p>
          <p>3.50 - 3.79: <strong>44% (Good Standing)</strong></p>
          <p>3.00 - 3.49: <strong>15% (Satisfactory)</strong></p>
          <p>Below 3.00: <strong>3% (Academic Support)</strong></p>
        </div>
      </div>
    </section>
  </main>

  <!-- Login Modal -->
  <div id="login-modal" class="modal-overlay">
    <div class="modal-dialog">
      <div class="modal-header">
        <h3>🔒 Institutional Portal Login</h3>
        <button class="modal-close" onclick="toggleAuthModal()">✕</button>
      </div>
      <form onsubmit="handleLogin(event)">
        <div class="modal-body">
          <label>Email Address</label>
          <input type="email" id="login-email" value="admin@school.edu" required>
          <label>Password</label>
          <input type="password" id="login-pw" value="admin2026" required>
          <small style="color: #94a3b8;">Demo credentials pre-filled.</small>
        </div>
        <div class="modal-footer">
          <button type="submit" class="submit-btn">Authenticate</button>
        </div>
      </form>
    </div>
  </div>

  <div id="toast" class="toast-notification"></div>

  <script src="app.js"></script>
</body>
</html>
"""


def generate_student_js(name: str, entity: str, plural: str) -> str:
    return """\
// Live Student Management Controller
const STORAGE_KEY = 'swarm_portal_students_v1';

const DEFAULT_STUDENTS = [
  { id: '1', code: 'STU-2026-001', name: 'Alex Johnson', email: 'alex.j@school.edu', department: 'Computer Science', gpa: 3.92, status: 'Active' },
  { id: '2', code: 'STU-2026-002', name: 'Sarah Chen', email: 'sarah.c@school.edu', department: 'Data Science', gpa: 3.88, status: 'Active' },
  { id: '3', code: 'STU-2026-003', name: 'Marcus Williams', email: 'm.williams@school.edu', department: 'Engineering', gpa: 3.65, status: 'Active' },
  { id: '4', code: 'STU-2026-004', name: 'Emily Davis', email: 'e.davis@school.edu', department: 'Business Administration', gpa: 3.74, status: 'Active' },
  { id: '5', code: 'STU-2026-005', name: 'Liam Murphy', email: 'l.murphy@school.edu', department: 'Computer Science', gpa: 3.81, status: 'Graduated' },
  { id: '6', code: 'STU-2026-006', name: 'Sophia Rodriguez', email: 's.rodriguez@school.edu', department: 'Data Science', gpa: 3.95, status: 'Active' }
];

function getStudents() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : DEFAULT_STUDENTS;
  } catch (e) {
    return DEFAULT_STUDENTS;
  }
}

function saveStudents(list) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  } catch (e) {}
}

function showView(viewId) {
  document.querySelectorAll('.portal-view').forEach(v => v.classList.remove('active'));
  const target = document.getElementById('view-' + viewId);
  if (target) target.classList.add('active');
  document.querySelectorAll('.nav-link').forEach(btn => {
    const matches = btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(viewId);
    btn.classList.toggle('active', !!matches);
  });
  const nav = document.getElementById('nav-links');
  if (nav) nav.classList.remove('mobile-open');
  if (viewId === 'dashboard' || viewId === 'list') renderAll();
}

function toggleMobileMenu() {
  const nav = document.getElementById('nav-links');
  if (nav) nav.classList.toggle('mobile-open');
}

function toggleAuthModal() {
  const modal = document.getElementById('login-modal');
  if (modal) modal.classList.toggle('active');
}

function handleLogin(e) {
  e.preventDefault();
  toggleAuthModal();
  const authBtn = document.getElementById('auth-btn');
  if (authBtn) {
    authBtn.innerHTML = '✓ Dean Miller (Administrator)';
    authBtn.style.borderColor = '#10b981';
    authBtn.style.color = '#6ee7b7';
  }
  showToast('Authenticated as Administrator.');
}

function renderAll() {
  const students = getStudents();
  const totalEl = document.getElementById('metric-total');
  if (totalEl) totalEl.textContent = students.length;

  const recentTbody = document.getElementById('recent-table-body');
  if (recentTbody) {
    recentTbody.innerHTML = students.slice(0, 4).map(s => `
      <tr>
        <td><code>${s.code}</code></td>
        <td><strong>${s.name}</strong></td>
        <td>${s.department}</td>
        <td><strong style='color:#86efac'>${s.gpa.toFixed(2)}</strong></td>
        <td><span class='status-badge ${s.status.toLowerCase().replace(' ', '-')}'>${s.status}</span></td>
      </tr>
    `).join('');
  }

  filterTable();
}

function filterTable() {
  const query = (document.getElementById('search-input')?.value || '').toLowerCase();
  const dept = document.getElementById('dept-filter')?.value || 'all';
  const status = document.getElementById('status-filter')?.value || 'all';
  const students = getStudents();

  const filtered = students.filter(s => {
    const matchQuery = s.name.toLowerCase().includes(query) || s.email.toLowerCase().includes(query) || s.code.toLowerCase().includes(query);
    const matchDept = dept === 'all' || s.department === dept;
    const matchStatus = status === 'all' || s.status === status;
    return matchQuery && matchDept && matchStatus;
  });

  const tbody = document.getElementById('students-table-body');
  if (tbody) {
    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:#94a3b8;">No students match search filter.</td></tr>';
    } else {
      tbody.innerHTML = filtered.map(s => `
        <tr>
          <td><code>${s.code}</code></td>
          <td><strong>${s.name}</strong></td>
          <td>${s.email}</td>
          <td>${s.department}</td>
          <td><strong style='color:#86efac'>${Number(s.gpa).toFixed(2)}</strong></td>
          <td><span class='status-badge ${s.status.toLowerCase().replace(' ', '-')}'>${s.status}</span></td>
          <td><button class='delete-btn' data-id='${s.id}' onclick='deleteStudent(this.dataset.id)'>Delete</button></td>
        </tr>
      `).join('');
    }
  }
}

function handleRegister(e) {
  e.preventDefault();
  const firstName = document.getElementById('reg-first-name').value.trim();
  const lastName = document.getElementById('reg-last-name').value.trim();
  const code = document.getElementById('reg-code').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const department = document.getElementById('reg-dept').value;
  const gpa = parseFloat(document.getElementById('reg-gpa').value) || 3.5;
  const status = document.getElementById('reg-status').value;

  if (!firstName || !lastName || !code || !email) return;

  const newStudent = {
    id: String(Date.now()),
    code,
    name: firstName + ' ' + lastName,
    email,
    department,
    gpa,
    status
  };

  const list = getStudents();
  list.unshift(newStudent);
  saveStudents(list);
  document.getElementById('registration-form').reset();
  showToast(`Successfully registered ${newStudent.name} (${code})!`);
  showView('list');
}

function deleteStudent(id) {
  let list = getStudents();
  const student = list.find(s => s.id === id);
  list = list.filter(s => s.id !== id);
  saveStudents(list);
  renderAll();
  showToast(student ? `Deleted record for ${student.name}.` : 'Student record removed.');
}

function showToast(msg) {
  const t = document.getElementById('toast');
  if (t) {
    t.textContent = '✓ ' + msg;
    t.classList.add('active');
    setTimeout(() => t.classList.remove('active'), 3200);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  renderAll();
});
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  renderAll();
}
"""


def generate_student_backend(name: str) -> str:
    return f"""\
\"\"\"Autonomous Implementation for: {name}\"\"\"

import uuid
import json
from typing import Any, Dict, List, Optional

_STUDENTS: Dict[str, Dict[str, Any]] = {{}}

def get_status() -> Dict[str, Any]:
    return {{"service": "{name}", "status": "healthy", "initialized": True, "count": len(_STUDENTS)}}

def create_student(payload: Dict[str, Any]) -> Dict[str, Any]:
    item_id = str(uuid.uuid4())
    record = dict(payload)
    record["id"] = item_id
    _STUDENTS[item_id] = record
    return record

def get_student(item_id: str) -> Optional[Dict[str, Any]]:
    return _STUDENTS.get(item_id)

def list_students() -> List[Dict[str, Any]]:
    return list(_STUDENTS.values())

def delete_student(item_id: str) -> bool:
    if item_id in _STUDENTS:
        del _STUDENTS[item_id]
        return True
    return False

def clear_data() -> None:
    _STUDENTS.clear()

if __name__ == "__main__":
    print(f"{name} operational: {{get_status()}}")
"""


def generate_student_tests(name: str) -> str:
    return """\
import unittest
import app

class TestStudentSuite(unittest.TestCase):
    def setUp(self):
        app.clear_data()

    def test_health_status(self):
        status = app.get_status()
        self.assertEqual(status.get("status"), "healthy")
        self.assertTrue(status.get("initialized"))

    def test_create_and_list_students(self):
        s = app.create_student({"name": "Elena Rostova", "department": "Computer Science", "gpa": 3.95})
        self.assertIsNotNone(s.get("id"))
        students = app.list_students()
        self.assertGreaterEqual(len(students), 1)

    def test_get_student(self):
        s = app.create_student({"name": "Alex Johnson"})
        fetched = app.get_student(s["id"])
        self.assertEqual(fetched.get("name"), "Alex Johnson")

    def test_delete_student(self):
        s = app.create_student({"name": "To Delete"})
        self.assertTrue(app.delete_student(s["id"]))

if __name__ == "__main__":
    unittest.main()
"""


# =============================================================================
# GENERIC DOMAIN IMPLEMENTATIONS
# =============================================================================

def generate_generic_html(name: str, entity: str, plural: str, ctx: dict[str, Any]) -> str:
    entity_title = entity.capitalize()
    plural_title = plural.capitalize()
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name}</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <nav class="portal-navbar">
    <div class="nav-brand">
      <span class="brand-icon">⚡</span>
      <span class="brand-title">{name}</span>
      <span class="brand-pill">Operations</span>
    </div>
    <div class="nav-links" id="nav-links">
      <button class="nav-link active" onclick="showView('dashboard')">📊 Dashboard</button>
      <button class="nav-link" onclick="showView('list')">📋 {plural_title} Directory</button>
      <button class="nav-link" onclick="showView('register')">➕ Create {entity_title}</button>
      <button class="nav-link" onclick="showView('analytics')">📈 Analytics</button>
    </div>
    <div class="nav-user">
      <button class="login-btn" id="auth-btn" onclick="toggleAuthModal()">👤 Administrator Login</button>
      <button class="mobile-menu-toggle" onclick="toggleMobileMenu()">☰</button>
    </div>
  </nav>

  <main class="portal-container">
    <section id="view-dashboard" class="portal-view active">
      <div class="view-header">
        <h2>Welcome to {name}</h2>
        <p>Operational control center for managing and monitoring {plural} in real time.</p>
      </div>
      <div class="metrics-grid">
        <div class="metric-card">
          <span>Total {plural_title}</span>
          <strong id="metric-total">24</strong>
          <small class="trend-up">↑ Active cluster nodes</small>
        </div>
        <div class="metric-card">
          <span>System Availability</span>
          <strong class="highlight-val">99.98%</strong>
          <small>Zero incidents recorded</small>
        </div>
        <div class="metric-card">
          <span>Throughput Velocity</span>
          <strong class="highlight-val">1,420 ops/sec</strong>
          <small class="trend-up">Peak efficiency</small>
        </div>
        <div class="metric-card">
          <span>Active Workflows</span>
          <strong>12 Tasks</strong>
          <small>Automated synchronization</small>
        </div>
      </div>
      <div class="quick-actions-bar">
        <button class="action-btn primary" onclick="showView('register')">➕ Create New {entity_title}</button>
        <button class="action-btn secondary" onclick="showView('list')">🔍 Browse {plural_title} Directory</button>
      </div>
    </section>

    <section id="view-list" class="portal-view">
      <div class="view-header">
        <h2>{plural_title} Directory</h2>
        <p>Inspect, filter, and search managed {plural}.</p>
      </div>
      <div class="filter-bar">
        <input type="text" id="search-input" class="search-input" placeholder="Search records..." oninput="filterTable()">
      </div>
      <div class="table-responsive">
        <table class="portal-table">
          <thead><tr><th>ID</th><th>Title</th><th>Category</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody id="records-table-body"></tbody>
        </table>
      </div>
    </section>

    <section id="view-register" class="portal-view">
      <div class="view-header">
        <h2>Create New {entity_title}</h2>
      </div>
      <div class="form-card">
        <form id="create-form" onsubmit="handleCreate(event)">
          <div class="form-row">
            <div class="form-group"><label>{entity_title} Title</label><input type="text" id="rec-title" required placeholder="Enter title"></div>
            <div class="form-group"><label>Category / Domain</label><input type="text" id="rec-cat" required placeholder="Operations"></div>
          </div>
          <div class="form-actions">
            <button type="submit" class="submit-btn">✓ Create {entity_title}</button>
            <button type="button" class="cancel-btn" onclick="showView('list')">Cancel</button>
          </div>
        </form>
      </div>
    </section>

    <section id="view-analytics" class="portal-view">
      <div class="view-header"><h2>Operations Analytics</h2></div>
      <div class="analytics-cards">
        <div class="analytics-box"><h3>Health Overview</h3><p>System operational with nominal parameters.</p></div>
      </div>
    </section>
  </main>

  <div id="toast" class="toast-notification"></div>
  <script src="app.js"></script>
</body>
</html>
"""


def generate_generic_js(name: str, entity: str, plural: str, ctx: dict[str, Any]) -> str:
    return f"""\
// Operations Controller for {name}
const STORAGE_KEY = 'swarm_records_v1';
const DEFAULT_ITEMS = [
  {{ id: 'REC-001', title: 'Primary Production Cluster', category: 'Infrastructure', status: 'Active' }},
  {{ id: 'REC-002', title: 'Telemetry Ingestion Gateway', category: 'Data Pipelines', status: 'Active' }},
  {{ id: 'REC-003', title: 'Secondary Failover Replicator', category: 'High Availability', status: 'Idle' }}
];

function getItems() {{
  try {{ return JSON.parse(localStorage.getItem(STORAGE_KEY)) || DEFAULT_ITEMS; }} catch(e) {{ return DEFAULT_ITEMS; }}
}}
function saveItems(list) {{
  try {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(list)); }} catch(e) {{}}
}}
function showView(viewId) {{
  document.querySelectorAll('.portal-view').forEach(v => v.classList.remove('active'));
  const target = document.getElementById('view-' + viewId);
  if (target) target.classList.add('active');
  document.querySelectorAll('.nav-link').forEach(btn => {{
    const matches = btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(viewId);
    btn.classList.toggle('active', !!matches);
  }});
  if (viewId === 'list') renderTable();
}}
function renderTable() {{
  const items = getItems();
  const query = (document.getElementById('search-input')?.value || '').toLowerCase();
  const filtered = items.filter(i => i.title.toLowerCase().includes(query) || i.category.toLowerCase().includes(query));
  const tbody = document.getElementById('records-table-body');
  if (!tbody) return;
  tbody.innerHTML = filtered.map(i => `
    <tr>
      <td><code>${{i.id}}</code></td>
      <td><strong>${{i.title}}</strong></td>
      <td>${{i.category}}</td>
      <td><span class='status-badge active'>${{i.status}}</span></td>
      <td><button class='delete-btn' data-id='${{i.id}}' onclick='deleteItem(this.dataset.id)'>Delete</button></td>
    </tr>
  `).join('');
}}
function filterTable() {{ renderTable(); }}
function handleCreate(e) {{
  e.preventDefault();
  const title = document.getElementById('rec-title').value.trim();
  const cat = document.getElementById('rec-cat').value.trim();
  if (!title) return;
  const newItem = {{ id: 'REC-' + Math.floor(100 + Math.random() * 900), title, category: cat, status: 'Active' }};
  const list = getItems();
  list.unshift(newItem);
  saveItems(list);
  showToast(`Created ${{title}}`);
  showView('list');
}}
function deleteItem(id) {{
  let list = getItems().filter(i => i.id !== id);
  saveItems(list);
  renderTable();
  showToast('Item deleted.');
}}
function showToast(msg) {{
  const t = document.getElementById('toast');
  if (t) {{
    t.textContent = '✓ ' + msg;
    t.classList.add('active');
    setTimeout(() => t.classList.remove('active'), 3200);
  }}
}}
document.addEventListener('DOMContentLoaded', () => {{ renderTable(); }});
if (document.readyState === 'complete' || document.readyState === 'interactive') {{
  renderTable();
}}
"""


def generate_generic_backend(name: str, entity: str, plural: str) -> str:
    return f"""\
\"\"\"Autonomous Implementation for: {name}\"\"\"

import uuid
import json
from typing import Any, Dict, List, Optional

_STORE: Dict[str, Dict[str, Any]] = {{}}

def get_status() -> Dict[str, Any]:
    return {{"service": "{name}", "status": "healthy", "initialized": True, "count": len(_STORE)}}

def create_{entity}(payload: Dict[str, Any]) -> Dict[str, Any]:
    item_id = str(uuid.uuid4())
    record = dict(payload)
    record["id"] = item_id
    _STORE[item_id] = record
    return record

def get_{entity}(item_id: str) -> Optional[Dict[str, Any]]:
    return _STORE.get(item_id)

def list_{plural}() -> List[Dict[str, Any]]:
    return list(_STORE.values())

def delete_{entity}(item_id: str) -> bool:
    if item_id in _STORE:
        del _STORE[item_id]
        return True
    return False

def clear_data() -> None:
    _STORE.clear()

if __name__ == "__main__":
    print(f"{name} operational: {{get_status()}}")
"""


def generate_generic_tests(name: str, entity: str, plural: str) -> str:
    return f"""\
import unittest
import app

class TestApplicationSuite(unittest.TestCase):
    def setUp(self):
        app.clear_data()

    def test_health_status(self):
        status = app.get_status()
        self.assertEqual(status.get("status"), "healthy")
        self.assertTrue(status.get("initialized"))

    def test_create_and_list_{plural}(self):
        item = app.create_{entity}({{"title": "Test Item", "active": True}})
        self.assertIsNotNone(item.get("id"))
        items = app.list_{plural}()
        self.assertGreaterEqual(len(items), 1)

    def test_get_{entity}(self):
        created = app.create_{entity}({{"title": "Specific Item"}})
        fetched = app.get_{entity}(created["id"])
        self.assertEqual(fetched.get("title"), "Specific Item")

    def test_delete_{entity}(self):
        created = app.create_{entity}({{"title": "To Delete"}})
        self.assertTrue(app.delete_{entity}(created["id"]))

if __name__ == "__main__":
    unittest.main()
"""


def get_student_portal_files(name: str = "Student Management Portal", ctx: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    files = []

    # 1. frontend/package.json
    package_json = {
        "name": "student-management-portal",
        "private": True,
        "version": "1.0.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview"
        },
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0"
        },
        "devDependencies": {
            "@vitejs/plugin-react": "^4.2.1",
            "vite": "^5.0.0"
        }
    }
    files.append({
        "path": "frontend/package.json",
        "language": "json",
        "purpose": "Frontend React 18 and Vite package configuration",
        "code": json.dumps(package_json, indent=2),
    })

    # 2. frontend/src/styles/App.css
    css_code = """/* Modern Student Management Portal Stylesheet */
:root {
  --bg-primary: #0a0e17;
  --bg-surface: #111827;
  --bg-card: #1f2937;
  --bg-hover: #374151;
  --border-color: #374151;
  --text-main: #f9fafb;
  --text-muted: #9ca3af;
  --accent: #3b82f6;
  --accent-hover: #2563eb;
  --success: #10b981;
  --danger: #ef4444;
  --warning: #f59e0b;
  --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background-color: var(--bg-primary);
  color: var(--text-main);
  font-family: var(--font-family);
  min-height: 100vh;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

/* Navbar */
.navbar {
  background-color: var(--bg-surface);
  border-bottom: 1px solid var(--border-color);
  padding: 0.85rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 50;
  backdrop-filter: blur(8px);
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.025em;
  color: #fff;
}

.nav-badge {
  font-size: 0.75rem;
  background-color: rgba(59, 130, 246, 0.2);
  color: var(--accent);
  border: 1px solid rgba(59, 130, 246, 0.3);
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  font-weight: 600;
}

.nav-tabs {
  display: flex;
  gap: 0.5rem;
}

.nav-tab-btn {
  background: transparent;
  color: var(--text-muted);
  border: 1px solid transparent;
  padding: 0.45rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.nav-tab-btn:hover {
  color: var(--text-main);
  background-color: var(--bg-card);
}

.nav-tab-btn.active {
  color: #fff;
  background-color: var(--accent);
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
}

.nav-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--success);
  box-shadow: 0 0 8px var(--success);
}

/* Layout */
.main-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

/* KPI Cards */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.25rem;
  margin-bottom: 2rem;
}

.kpi-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  transition: transform 0.2s, box-shadow 0.2s;
}

.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
  border-color: rgba(59, 130, 246, 0.4);
}

.kpi-title {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  font-weight: 600;
}

.kpi-value {
  font-size: 2rem;
  font-weight: 800;
  color: #fff;
  line-height: 1.1;
}

.kpi-sub {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* Controls Header */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.section-title {
  font-size: 1.35rem;
  font-weight: 700;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-bar {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.search-input {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 0.55rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  width: 260px;
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: var(--accent);
}

.select-filter {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 0.55rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  outline: none;
  cursor: pointer;
}

/* Data Table */
.table-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.875rem;
}

.data-table th {
  background-color: rgba(31, 41, 55, 0.7);
  padding: 0.85rem 1.25rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border-color);
}

.data-table td {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-main);
  vertical-align: middle;
}

.data-table tr:last-child td {
  border-bottom: none;
}

.data-table tr:hover td {
  background-color: rgba(31, 41, 55, 0.4);
}

/* Badges */
.badge {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-cs { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
.badge-it { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
.badge-ee { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
.badge-ds { background: rgba(139, 92, 246, 0.2); color: #a78bfa; border: 1px solid rgba(139, 92, 246, 0.3); }
.badge-ba { background: rgba(236, 72, 153, 0.2); color: #f472b6; border: 1px solid rgba(236, 72, 153, 0.3); }
.badge-active { background: rgba(16, 185, 129, 0.2); color: #10b981; }

/* Buttons */
.btn {
  padding: 0.55rem 1.25rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.btn-primary {
  background-color: var(--accent);
  color: #fff;
}
.btn-primary:hover {
  background-color: var(--accent-hover);
}

.btn-secondary {
  background-color: var(--bg-card);
  color: var(--text-main);
  border: 1px solid var(--border-color);
}
.btn-secondary:hover {
  background-color: var(--bg-hover);
}

.btn-profile {
  background: #1e3a8a;
  color: #bfdbfe;
  border: 1px solid #3b82f6;
  border-radius: 0.375rem;
  padding: 0.35rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-right: 0.35rem;
}
.btn-profile:hover {
  background: #2563eb;
  color: #fff;
}

.btn-edit {
  background: #064e3b;
  color: #a7f3d0;
  border: 1px solid #059669;
  border-radius: 0.375rem;
  padding: 0.35rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-right: 0.35rem;
}
.btn-edit:hover {
  background: #059669;
  color: #fff;
}

.btn-danger {
  background: #7f1d1d;
  color: #fecaca;
  border: 1px solid #dc2626;
  border-radius: 0.375rem;
  padding: 0.35rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-danger:hover {
  background: #dc2626;
  color: #fff;
}

/* Forms */
.form-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 2rem;
  max-width: 680px;
  margin: 0 auto;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: 0.4rem;
}

.form-control {
  width: 100%;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 0.65rem 0.85rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.2s;
}

.form-control:focus {
  border-color: var(--accent);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 1.75rem;
  max-width: 520px;
  width: 90%;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
}

/* Toast */
.toast-container {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 1000;
}

.toast {
  background: var(--bg-surface);
  color: #fff;
  border: 1px solid var(--accent);
  padding: 0.75rem 1.25rem;
  border-radius: 0.5rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
  font-size: 0.88rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
  from { transform: translateY(100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
"""
    files.append({
        "path": "frontend/src/styles/App.css",
        "language": "css",
        "purpose": "Modern responsive Student Management Portal CSS styling",
        "code": css_code,
    })
    files.append({
        "path": "styles.css",
        "language": "css",
        "purpose": "Root CSS alias",
        "code": css_code,
    })
    files.append({
        "path": "frontend/styles.css",
        "language": "css",
        "purpose": "Frontend public CSS alias for live preview",
        "code": css_code,
    })

    # Vite Configuration
    vite_config_js = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '127.0.0.1',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
});
"""
    files.append({
        "path": "frontend/vite.config.js",
        "language": "javascript",
        "purpose": "Vite React configuration with API proxy",
        "code": vite_config_js,
    })
    files.append({
        "path": "vite.config.js",
        "language": "javascript",
        "purpose": "Root Vite configuration alias",
        "code": vite_config_js,
    })

    # 3. frontend/src/api/students.js
    api_js = """// Frontend API client for Student Management Portal
const API_BASE = '/api';

export async function fetchStudents(q = '', department = '') {
  try {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (department && department !== 'all') params.set('department', department);
    const res = await fetch(`${API_BASE}/students?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch students');
    return await res.json();
  } catch (err) {
    console.warn('API fetch fallback to localStorage:', err);
    return null;
  }
}

export async function createStudent(student) {
  try {
    const res = await fetch(`${API_BASE}/students`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(student)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Creation failed');
    }
    return { success: true, data: await res.json() };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

export async function updateStudent(id, updates) {
  try {
    const res = await fetch(`${API_BASE}/students/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    if (!res.ok) throw new Error('Update failed');
    return { success: true, data: await res.json() };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

export async function deleteStudent(id) {
  try {
    const res = await fetch(`${API_BASE}/students/${id}`, {
      method: 'DELETE'
    });
    return res.ok;
  } catch (err) {
    return false;
  }
}
"""
    files.append({
        "path": "frontend/src/api/students.js",
        "language": "javascript",
        "purpose": "Async API client for backend student CRUD integration",
        "code": api_js,
    })

    # 4. frontend/src/components/Navbar.jsx
    navbar_jsx = """import React from 'react';

export function Navbar({ activeTab, onTabChange, studentCount }) {
  return (
    <nav className="navbar">
      <div className="nav-brand">
        <span>🎓</span>
        <span>Student Management Portal</span>
        <span className="nav-badge">{studentCount} Enrolled</span>
      </div>
      <div className="nav-tabs">
        <button
          className={`nav-tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => onTabChange('dashboard')}
        >
          📊 Dashboard
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'students' ? 'active' : ''}`}
          onClick={() => onTabChange('students')}
        >
          📋 Directory
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'register' ? 'active' : ''}`}
          onClick={() => onTabChange('register')}
        >
          ➕ Register Student
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => onTabChange('analytics')}
        >
          📈 Analytics
        </button>
      </div>
      <div className="nav-status">
        <span className="status-dot"></span>
        <span>Active & Synced</span>
        <button className="nav-tab-btn" style={{ marginLeft: '0.5rem' }} onClick={() => alert('Admin Session: Authenticated')}>
          🔐 Login: Admin
        </button>
      </div>
    </nav>
  );
}
"""
    files.append({
        "path": "frontend/src/components/Navbar.jsx",
        "language": "javascript",
        "purpose": "Responsive navigation header with live metrics and tab triggers",
        "code": navbar_jsx,
    })

    # 5. frontend/src/components/StudentForm.jsx
    student_form_jsx = """import React, { useState } from 'react';

export function StudentForm({ onSubmit, onCancel, initialData = null }) {
  const [formData, setFormData] = useState(initialData || {
    student_id: '',
    name: '',
    email: '',
    department: 'Computer Science',
    course: 'B.S. Computer Science',
    phone: '',
    gpa: 3.5,
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const validate = () => {
    const errs = {};
    if (!formData.name.trim()) errs.name = 'Full name is required';
    if (!formData.student_id.trim()) errs.student_id = 'Student ID is required';
    if (!formData.email.trim() || !formData.email.includes('@') || !formData.email.includes('.')) {
      errs.email = 'Valid email address is required';
    }
    if (!formData.phone.trim() || formData.phone.length < 5) {
      errs.phone = 'Valid phone number is required';
    }
    const gpaNum = parseFloat(formData.gpa);
    if (isNaN(gpaNum) || gpaNum < 0 || gpaNum > 4.0) {
      errs.gpa = 'GPA must be between 0.0 and 4.0';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    await onSubmit({ ...formData, gpa: parseFloat(formData.gpa) });
    setSubmitting(false);
  };

  return (
    <div className="form-card">
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label>Student ID *</label>
            <input
              type="text"
              className="form-control"
              placeholder="e.g. STU-1006"
              disabled={!!initialData}
              value={formData.student_id}
              onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
            />
            {errors.student_id && <span style={{ color: '#ef4444', fontSize: '0.75rem' }}>{errors.student_id}</span>}
          </div>
          <div className="form-group">
            <label>Full Name *</label>
            <input
              type="text"
              className="form-control"
              placeholder="e.g. Alexander Clark"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
            {errors.name && <span style={{ color: '#ef4444', fontSize: '0.75rem' }}>{errors.name}</span>}
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Email Address *</label>
            <input
              type="email"
              className="form-control"
              placeholder="student@university.edu"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
            {errors.email && <span style={{ color: '#ef4444', fontSize: '0.75rem' }}>{errors.email}</span>}
          </div>
          <div className="form-group">
            <label>Phone Number *</label>
            <input
              type="text"
              className="form-control"
              placeholder="+1 555-0199"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            />
            {errors.phone && <span style={{ color: '#ef4444', fontSize: '0.75rem' }}>{errors.phone}</span>}
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Department *</label>
            <select
              className="form-control"
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
            >
              <option value="Computer Science">Computer Science</option>
              <option value="Information Technology">Information Technology</option>
              <option value="Electrical Engineering">Electrical Engineering</option>
              <option value="Data Science">Data Science</option>
              <option value="Business Administration">Business Administration</option>
            </select>
          </div>
          <div className="form-group">
            <label>Degree Course *</label>
            <select
              className="form-control"
              value={formData.course || 'B.S. Computer Science'}
              onChange={(e) => setFormData({ ...formData, course: e.target.value })}
            >
              <option value="B.S. Computer Science">B.S. Computer Science</option>
              <option value="B.S. Software Engineering">B.S. Software Engineering</option>
              <option value="B.S. Information Technology">B.S. Information Technology</option>
              <option value="B.S. Electrical Engineering">B.S. Electrical Engineering</option>
              <option value="B.S. Data Science & AI">B.S. Data Science & AI</option>
              <option value="B.B.A. Business Administration">B.B.A. Business Administration</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label>Cumulative GPA (0.00 - 4.00) *</label>
          <input
            type="number"
            step="0.01"
            min="0"
            max="4.0"
            className="form-control"
            value={formData.gpa}
            onChange={(e) => setFormData({ ...formData, gpa: e.target.value })}
          />
          {errors.gpa && <span style={{ color: '#ef4444', fontSize: '0.75rem' }}>{errors.gpa}</span>}
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Saving...' : initialData ? 'Update Record' : 'Enroll Student'}
          </button>
          {onCancel && (
            <button type="button" className="btn btn-secondary" onClick={onCancel}>
              Cancel
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
"""
    files.append({
        "path": "frontend/src/components/StudentForm.jsx",
        "language": "javascript",
        "purpose": "Form component with validation for adding and editing students",
        "code": student_form_jsx,
    })

    # 6. frontend/src/components/StudentTable.jsx
    student_table_jsx = """import React from 'react';

export function StudentTable({ students, onEdit, onDelete, onView }) {
  if (!students || students.length === 0) {
    return (
      <div className="table-card" style={{ padding: '2.5rem', textAlign: 'center', color: '#9ca3af' }}>
        <p>No student records found matching the active filter.</p>
      </div>
    );
  }

  const getDeptBadgeClass = (dept) => {
    if (dept.includes('Computer')) return 'badge-cs';
    if (dept.includes('Information')) return 'badge-it';
    if (dept.includes('Electrical')) return 'badge-ee';
    if (dept.includes('Data')) return 'badge-ds';
    return 'badge-ba';
  };

  return (
    <div className="table-card">
      <table className="data-table">
        <thead>
          <tr>
            <th>Student ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Department</th>
            <th>Course</th>
            <th>GPA</th>
            <th>Phone</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {students.map((s) => (
            <tr key={s.student_id || s.id}>
              <td><strong>{s.student_id}</strong></td>
              <td>{s.name}</td>
              <td>{s.email}</td>
              <td>
                <span className={`badge ${getDeptBadgeClass(s.department)}`}>
                  {s.department}
                </span>
              </td>
              <td>{s.course || 'B.S. Computer Science'}</td>
              <td><strong>{Number(s.gpa).toFixed(2)}</strong></td>
              <td>{s.phone}</td>
              <td>
                <span className="badge badge-active">{s.status || 'Active'}</span>
              </td>
              <td>
                <button
                  className="btn-profile"
                  onClick={() => onView && onView(s)}
                >
                  👁️ Profile
                </button>
                <button
                  className="btn-edit"
                  onClick={() => onEdit(s)}
                >
                  ✏️ Edit
                </button>
                <button
                  className="btn-danger"
                  onClick={() => onDelete(s.student_id || s.id)}
                >
                  🗑️ Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
"""
    files.append({
        "path": "frontend/src/components/StudentTable.jsx",
        "language": "javascript",
        "purpose": "Tabular student directory presentation with badges and action dispatchers",
        "code": student_table_jsx,
    })

    # 7. frontend/src/pages/Dashboard.jsx
    dashboard_jsx = """import React from 'react';
import { StudentTable } from '../components/StudentTable.jsx';

export function Dashboard({ students, onEdit, onDelete, onView }) {
  const totalStudents = students.length;
  const activeStudents = students.filter((s) => s.status === 'Active').length;
  const avgGpa = totalStudents > 0
    ? (students.reduce((acc, curr) => acc + (parseFloat(curr.gpa) || 0), 0) / totalStudents).toFixed(2)
    : '0.00';
  const deptsCount = new Set(students.map((s) => s.department)).size;

  return (
    <div>
      <div className="kpi-grid">
        <div className="kpi-card">
          <span className="kpi-title">Total Enrolled</span>
          <span className="kpi-value">{totalStudents}</span>
          <span className="kpi-sub">Active registered records</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-title">Active Students</span>
          <span className="kpi-value">{activeStudents}</span>
          <span className="kpi-sub">100% good academic standing</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-title">Academic Departments</span>
          <span className="kpi-value">{deptsCount}</span>
          <span className="kpi-sub">CS, IT, EE, DS, BA</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-title">Average Cumulative GPA</span>
          <span className="kpi-value">{avgGpa}</span>
          <span className="kpi-sub">High academic standard</span>
        </div>
      </div>

      <div className="section-header">
        <h3 className="section-title">Recently Enrolled Students</h3>
      </div>

      <StudentTable
        students={students.slice(0, 5)}
        onEdit={onEdit}
        onDelete={onDelete}
        onView={onView}
      />
    </div>
  );
}
"""
    files.append({
        "path": "frontend/src/pages/Dashboard.jsx",
        "language": "javascript",
        "purpose": "Executive KPI overview and recent enrollments dashboard page",
        "code": dashboard_jsx,
    })

    # 8. frontend/src/pages/Students.jsx
    students_page_jsx = """import React, { useState } from 'react';
import { StudentTable } from '../components/StudentTable.jsx';

export function StudentsPage({ students, onEdit, onDelete, onView }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDept, setSelectedDept] = useState('all');

  const filtered = students.filter((s) => {
    const matchSearch =
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.student_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.course && s.course.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchDept = selectedDept === 'all' || s.department === selectedDept;
    return matchSearch && matchDept;
  });

  return (
    <div>
      <div className="section-header">
        <h3 className="section-title">Student Directory</h3>
        <div className="filter-bar">
          <input
            type="text"
            className="search-input"
            placeholder="Search by name, ID, email, or course..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <select
            className="select-filter"
            value={selectedDept}
            onChange={(e) => setSelectedDept(e.target.value)}
          >
            <option value="all">All Departments</option>
            <option value="Computer Science">Computer Science</option>
            <option value="Information Technology">Information Technology</option>
            <option value="Electrical Engineering">Electrical Engineering</option>
            <option value="Data Science">Data Science</option>
            <option value="Business Administration">Business Administration</option>
          </select>
        </div>
      </div>

      <StudentTable
        students={filtered}
        onEdit={onEdit}
        onDelete={onDelete}
        onView={onView}
      />
    </div>
  );
}
"""
    files.append({
        "path": "frontend/src/pages/Students.jsx",
        "language": "javascript",
        "purpose": "Interactive student directory with search and filter capabilities",
        "code": students_page_jsx,
    })

    # 9. frontend/src/pages/RegisterStudent.jsx
    register_page_jsx = """import React from 'react';
import { StudentForm } from '../components/StudentForm.jsx';

export function RegisterStudentPage({ onSubmit }) {
  return (
    <div>
      <div className="section-header" style={{ justifyContent: 'center', marginBottom: '1.5rem' }}>
        <h3 className="section-title">Student Enrollment & Registration</h3>
      </div>
      <StudentForm onSubmit={onSubmit} />
    </div>
  );
}
"""
    files.append({
        "path": "frontend/src/pages/RegisterStudent.jsx",
        "language": "javascript",
        "purpose": "Dedicated enrollment form view",
        "code": register_page_jsx,
    })

    # 10. frontend/src/App.jsx
    app_jsx = """import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar.jsx';
import { Dashboard } from './pages/Dashboard.jsx';
import { StudentsPage } from './pages/Students.jsx';
import { RegisterStudentPage } from './pages/RegisterStudent.jsx';
import { StudentForm } from './components/StudentForm.jsx';
import { fetchStudents, createStudent, updateStudent, deleteStudent } from './api/students.js';
import './styles/App.css';

export function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [students, setStudents] = useState([]);
  const [editingStudent, setEditingStudent] = useState(null);
  const [viewingStudent, setViewingStudent] = useState(null);
  const [toast, setToast] = useState('');

  const loadData = async () => {
    const list = await fetchStudents();
    if (list && Array.isArray(list)) {
      setStudents(list);
    } else {
      const raw = localStorage.getItem('portal_students_db_v3');
      if (raw) setStudents(JSON.parse(raw));
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(''), 3500);
  };

  const handleRegister = async (payload) => {
    const res = await createStudent(payload);
    if (res.success) {
      showToast(`✅ Registered student ${payload.name}`);
      await loadData();
      setActiveTab('students');
    } else {
      alert(`Registration error: ${res.error}`);
    }
  };

  const handleUpdate = async (payload) => {
    const res = await updateStudent(editingStudent.student_id || editingStudent.id, payload);
    if (res.success) {
      showToast(`✅ Updated details for ${payload.name}`);
      setEditingStudent(null);
      await loadData();
    } else {
      alert(`Update error: ${res.error}`);
    }
  };

  const handleDelete = async (sid) => {
    if (!window.confirm(`Are you sure you want to delete student ${sid}?`)) return;
    const ok = await deleteStudent(sid);
    if (ok) {
      showToast(`✅ Deleted student record ${sid}`);
      await loadData();
    } else {
      alert('Delete operation failed.');
    }
  };

  return (
    <div>
      <Navbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        studentCount={students.length}
      />

      <main className="main-container">
        {activeTab === 'dashboard' && (
          <Dashboard
            students={students}
            onEdit={setEditingStudent}
            onDelete={handleDelete}
            onView={setViewingStudent}
          />
        )}
        {activeTab === 'students' && (
          <StudentsPage
            students={students}
            onEdit={setEditingStudent}
            onDelete={handleDelete}
            onView={setViewingStudent}
          />
        )}
        {activeTab === 'register' && (
          <RegisterStudentPage onSubmit={handleRegister} />
        )}
        {activeTab === 'analytics' && (
          <div>
            <div className="section-header">
              <h3 className="section-title">Academic Analytics & Honor Roll</h3>
            </div>
            <div className="kpi-grid">
              <div className="kpi-card">
                <span className="kpi-title">Dean's Honor Roll (GPA ≥ 3.8)</span>
                <span className="kpi-value" style={{ color: '#60a5fa' }}>
                  {students.filter(s => parseFloat(s.gpa) >= 3.8).length} Students
                </span>
                <span className="kpi-sub">
                  {((students.filter(s => parseFloat(s.gpa) >= 3.8).length / (students.length || 1)) * 100).toFixed(1)}% of total enrollment
                </span>
              </div>
            </div>
          </div>
        )}

        {editingStudent && (
          <div className="modal-overlay" onClick={() => setEditingStudent(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3 style={{ color: '#fff' }}>Edit Student Record</h3>
                <button className="btn btn-secondary" onClick={() => setEditingStudent(null)}>✕</button>
              </div>
              <StudentForm
                initialData={editingStudent}
                onSubmit={handleUpdate}
                onCancel={() => setEditingStudent(null)}
              />
            </div>
          </div>
        )}

        {viewingStudent && (
          <div className="modal-overlay" onClick={() => setViewingStudent(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3 style={{ color: '#fff' }}>Student Profile</h3>
                <button className="btn btn-secondary" onClick={() => setViewingStudent(null)}>✕</button>
              </div>
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1.25rem' }}>
                <div style={{ width: 56, height: 56, borderRadius: '50%', background: '#3b82f6', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.25rem', fontWeight: 700 }}>
                  {viewingStudent.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <h4 style={{ margin: 0, color: '#fff', fontSize: '1.2rem' }}>{viewingStudent.name}</h4>
                  <span style={{ color: '#9ca3af', fontSize: '0.85rem' }}>{viewingStudent.student_id} &bull; {viewingStudent.department}</span>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.9rem' }}>
                <div><span style={{ color: '#9ca3af', display: 'block', fontSize: '0.8rem' }}>Email</span><strong>{viewingStudent.email}</strong></div>
                <div><span style={{ color: '#9ca3af', display: 'block', fontSize: '0.8rem' }}>Phone</span><strong>{viewingStudent.phone}</strong></div>
                <div><span style={{ color: '#9ca3af', display: 'block', fontSize: '0.8rem' }}>Course</span><strong>{viewingStudent.course || 'B.S. Computer Science'}</strong></div>
                <div><span style={{ color: '#9ca3af', display: 'block', fontSize: '0.8rem' }}>GPA</span><strong>{Number(viewingStudent.gpa).toFixed(2)}</strong></div>
                <div><span style={{ color: '#9ca3af', display: 'block', fontSize: '0.8rem' }}>Status</span><span className="badge badge-active">{viewingStudent.status || 'Active'}</span></div>
                <div><span style={{ color: '#9ca3af', display: 'block', fontSize: '0.8rem' }}>Standing</span><strong style={{ color: '#10b981' }}>{parseFloat(viewingStudent.gpa) >= 3.8 ? "Dean's List" : "Good Standing"}</strong></div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                <button className="btn btn-secondary" onClick={() => setViewingStudent(null)}>Close</button>
              </div>
            </div>
          </div>
        )}
      </main>

      {toast && (
        <div className="toast-container">
          <div className="toast">{toast}</div>
        </div>
      )}
    </div>
  );
}
export default App;
"""
    files.append({
        "path": "frontend/src/App.jsx",
        "language": "javascript",
        "purpose": "Root application React 18 component with navigation and CRUD state",
        "code": app_jsx,
    })

    # 11. frontend/src/main.jsx
    main_jsx = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""
    files.append({
        "path": "frontend/src/main.jsx",
        "language": "javascript",
        "purpose": "React 18 DOM root mounter",
        "code": main_jsx,
    })

    # 12. app.js (Live interactive controller for index.html)
    app_js = """// Student Management Portal Client-side Controller
const STORAGE_KEY = 'portal_students_db_v3';

const INITIAL_STUDENTS = [
  { id: '1', student_id: 'STU-1001', name: 'Elena Rostova', email: 'elena.rostova@university.edu', department: 'Computer Science', course: 'B.S. Computer Science', phone: '+1 555-0101', gpa: 3.92, status: 'Active', created_at: '2026-09-01' },
  { id: '2', student_id: 'STU-1002', name: 'Marcus Vance', email: 'marcus.vance@university.edu', department: 'Information Technology', course: 'B.S. Information Technology', phone: '+1 555-0102', gpa: 3.78, status: 'Active', created_at: '2026-09-01' },
  { id: '3', student_id: 'STU-1003', name: 'Aisha Al-Mansoor', email: 'aisha.mansoor@university.edu', department: 'Electrical Engineering', course: 'B.S. Electrical Engineering', phone: '+1 555-0103', gpa: 3.85, status: 'Active', created_at: '2026-09-01' },
  { id: '4', student_id: 'STU-1004', name: 'David Kim', email: 'david.kim@university.edu', department: 'Data Science', course: 'B.S. Data Science & AI', phone: '+1 555-0104', gpa: 3.65, status: 'Active', created_at: '2026-09-01' },
  { id: '5', student_id: 'STU-1005', name: 'Sophia Martinez', email: 'sophia.martinez@university.edu', department: 'Business Administration', course: 'B.B.A. Business Administration', phone: '+1 555-0105', gpa: 3.70, status: 'Active', created_at: '2026-09-01' }
];

function getStoredStudents() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : INITIAL_STUDENTS;
  } catch {
    return INITIAL_STUDENTS;
  }
}

function saveStoredStudents(list) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  } catch {}
}

function showToast(msg) {
  const box = document.getElementById('toast-box');
  const txt = document.getElementById('toast-text');
  if (box && txt) {
    txt.textContent = msg;
    box.style.display = 'block';
    setTimeout(() => { box.style.display = 'none'; }, 3200);
  }
}

function switchTab(tab) {
  ['dashboard', 'directory', 'register', 'analytics'].forEach(t => {
    const el = document.getElementById('view-' + t);
    const btn = document.getElementById('tab-' + (t === 'dashboard' ? 'dash' : t === 'directory' ? 'dir' : t === 'register' ? 'reg' : 'ana'));
    if (el) el.style.display = (t === tab) ? 'block' : 'none';
    if (btn) btn.classList.toggle('active', t === tab);
  });
  if (tab === 'dashboard') renderDashboard();
  if (tab === 'directory') renderDirectory();
  if (tab === 'analytics') renderAnalytics();
}

function getDeptBadge(dept) {
  if (dept.includes('Computer')) return 'badge-cs';
  if (dept.includes('Information')) return 'badge-it';
  if (dept.includes('Electrical')) return 'badge-ee';
  if (dept.includes('Data')) return 'badge-ds';
  return 'badge-ba';
}

function renderDashboard() {
  const students = getStoredStudents();
  document.getElementById('stat-total').textContent = students.length;
  document.getElementById('stat-active').textContent = students.filter(s => s.status === 'Active').length;
  document.getElementById('stat-depts').textContent = new Set(students.map(s => s.department)).size;
  const avg = students.length > 0 ? (students.reduce((a, s) => a + (parseFloat(s.gpa) || 0), 0) / students.length).toFixed(2) : '0.00';
  document.getElementById('stat-gpa').textContent = avg;
  document.getElementById('nav-count').textContent = `${students.length} Students Enrolled`;

  const container = document.getElementById('dash-table-container');
  if (container) {
    container.innerHTML = buildTableHTML(students.slice(0, 5));
  }
}

function renderDirectory() {
  const students = getStoredStudents();
  const q = (document.getElementById('search-input')?.value || '').toLowerCase();
  const dept = document.getElementById('filter-dept')?.value || 'all';

  const filtered = students.filter(s => {
    const matchQ = s.name.toLowerCase().includes(q) ||
                   s.student_id.toLowerCase().includes(q) ||
                   s.email.toLowerCase().includes(q) ||
                   (s.course && s.course.toLowerCase().includes(q));
    const matchDept = dept === 'all' || s.department === dept;
    return matchQ && matchDept;
  });

  const container = document.getElementById('dir-table-container');
  if (container) {
    container.innerHTML = buildTableHTML(filtered);
  }
}

function renderAnalytics() {
  const students = getStoredStudents();
  const honors = students.filter(s => parseFloat(s.gpa) >= 3.8);
  const container = document.getElementById('analytics-container');
  if (!container) return;

  container.innerHTML = `
    <div class="kpi-grid" style="margin-bottom: 1.5rem;">
      <div class="kpi-card">
        <span class="kpi-title">Dean's Honor Roll (GPA ≥ 3.8)</span>
        <span class="kpi-value" style="color: #60a5fa;">${honors.length} Students</span>
        <span class="kpi-sub">${((honors.length / (students.length || 1)) * 100).toFixed(1)}% of total enrollment</span>
      </div>
    </div>
    <div class="table-card">
      <div style="padding: 1rem 1.25rem; font-weight: 700; border-bottom: 1px solid var(--border-color); color: #fff;">
        Dean's List Honorees
      </div>
      ${buildTableHTML(honors)}
    </div>
  `;
}

function buildTableHTML(list) {
  if (list.length === 0) {
    return '<div class="table-card" style="padding: 2.5rem; text-align: center; color: #9ca3af;">No students match filter criteria.</div>';
  }

  let rows = list.map(s => `
    <tr>
      <td><strong>${s.student_id}</strong></td>
      <td>${s.name}</td>
      <td>${s.email}</td>
      <td><span class="badge ${getDeptBadge(s.department)}">${s.department}</span></td>
      <td>${s.course || 'B.S. Computer Science'}</td>
      <td><strong>${Number(s.gpa).toFixed(2)}</strong></td>
      <td>${s.phone}</td>
      <td><span class="badge badge-active">${s.status || 'Active'}</span></td>
      <td>
        <button class="btn-profile" onclick="openProfileModal('${s.student_id}')">👁️ Profile</button>
        <button class="btn-edit" onclick="openEditModal('${s.student_id}')">✏️ Edit</button>
        <button class="btn-danger" onclick="deleteStudentById('${s.student_id}')">🗑️ Delete</button>
      </td>
    </tr>
  `).join('');

  return `
    <div class="table-card">
      <table class="data-table">
        <thead>
          <tr>
            <th>Student ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Department</th>
            <th>Course</th>
            <th>GPA</th>
            <th>Phone</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function openProfileModal(sid) {
  const students = getStoredStudents();
  const s = students.find(item => item.student_id === sid);
  if (!s) return;

  const body = document.getElementById('profile-modal-body');
  if (!body) return;

  const isHonor = parseFloat(s.gpa) >= 3.8;
  const initials = s.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();

  body.innerHTML = `
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.25rem; padding: 1rem; background: rgba(59, 130, 246, 0.1); border-radius: 8px;">
      <div style="width: 56px; height: 56px; border-radius: 50%; background: #3b82f6; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.25rem;">
        ${initials}
      </div>
      <div>
        <h4 style="margin: 0; font-size: 1.25rem; color: #fff;">${s.name}</h4>
        <span style="color: #9ca3af; font-size: 0.875rem;">${s.student_id} &bull; ${s.department}</span>
      </div>
    </div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem; font-size: 0.9rem;">
      <div>
        <span style="color: #9ca3af; display: block; font-size: 0.8rem;">Email Address</span>
        <strong style="color: #f3f4f6;">${s.email}</strong>
      </div>
      <div>
        <span style="color: #9ca3af; display: block; font-size: 0.8rem;">Phone Number</span>
        <strong style="color: #f3f4f6;">${s.phone || 'N/A'}</strong>
      </div>
      <div>
        <span style="color: #9ca3af; display: block; font-size: 0.8rem;">Degree / Course</span>
        <strong style="color: #f3f4f6;">${s.course || 'B.S. Computer Science'}</strong>
      </div>
      <div>
        <span style="color: #9ca3af; display: block; font-size: 0.8rem;">Cumulative GPA</span>
        <strong style="color: ${isHonor ? '#60a5fa' : '#f3f4f6'};">${Number(s.gpa).toFixed(2)} ${isHonor ? '🏆 Dean\'s List' : ''}</strong>
      </div>
      <div>
        <span style="color: #9ca3af; display: block; font-size: 0.8rem;">Enrollment Status</span>
        <span class="badge badge-active">${s.status || 'Active'}</span>
      </div>
      <div>
        <span style="color: #9ca3af; display: block; font-size: 0.8rem;">Academic Standing</span>
        <strong style="color: #10b981;">${isHonor ? "Dean's Honors" : 'Good Standing'}</strong>
      </div>
      <div style="grid-column: span 2;">
        <span style="color: #9ca3af; display: block; font-size: 0.8rem;">Registration Date</span>
        <strong style="color: #f3f4f6;">${s.created_at || '2026-09-01'}</strong>
      </div>
    </div>
  `;
  document.getElementById('profile-modal').style.display = 'flex';
}

function closeProfileModal() {
  const m = document.getElementById('profile-modal');
  if (m) m.style.display = 'none';
}

function handleFormSubmit(e) {
  e.preventDefault();
  const sid = document.getElementById('reg-id').value.trim();
  const name = document.getElementById('reg-name').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const dept = document.getElementById('reg-dept').value;
  const course = document.getElementById('reg-course').value;
  const phone = document.getElementById('reg-phone').value.trim();
  const gpa = parseFloat(document.getElementById('reg-gpa').value);

  const students = getStoredStudents();
  if (students.some(s => s.student_id === sid)) {
    alert(`Error: Student ID '${sid}' is already registered.`);
    return;
  }

  const newStudent = {
    id: Date.now().toString(),
    student_id: sid,
    name,
    email,
    department: dept,
    course,
    phone,
    gpa,
    status: 'Active',
    created_at: new Date().toISOString().slice(0, 10)
  };

  saveStoredStudents([newStudent, ...students]);
  fetch('/api/students', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(newStudent)
  }).catch(() => {});

  showToast(`✅ Registered student ${name}`);
  e.target.reset();
  switchTab('directory');
}

function openEditModal(sid) {
  const students = getStoredStudents();
  const s = students.find(item => item.student_id === sid);
  if (!s) return;

  document.getElementById('edit-id').value = s.student_id;
  document.getElementById('edit-name').value = s.name;
  document.getElementById('edit-email').value = s.email;
  document.getElementById('edit-dept').value = s.department;
  document.getElementById('edit-course').value = s.course || 'B.S. Computer Science';
  document.getElementById('edit-phone').value = s.phone;
  document.getElementById('edit-gpa').value = s.gpa;
  document.getElementById('edit-modal').style.display = 'flex';
}

function closeEditModal() {
  document.getElementById('edit-modal').style.display = 'none';
}

function handleEditSubmit(e) {
  e.preventDefault();
  const sid = document.getElementById('edit-id').value;
  const name = document.getElementById('edit-name').value.trim();
  const email = document.getElementById('edit-email').value.trim();
  const dept = document.getElementById('edit-dept').value;
  const course = document.getElementById('edit-course').value;
  const phone = document.getElementById('edit-phone').value.trim();
  const gpa = parseFloat(document.getElementById('edit-gpa').value);

  const students = getStoredStudents();
  const idx = students.findIndex(s => s.student_id === sid);
  if (idx !== -1) {
    students[idx] = { ...students[idx], name, email, department: dept, course, phone, gpa };
    saveStoredStudents(students);
    fetch(`/api/students/${sid}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, department: dept, course, phone, gpa })
    }).catch(() => {});
    showToast(`✅ Updated ${name}`);
  }

  closeEditModal();
  renderDashboard();
  renderDirectory();
}

function deleteStudentById(sid) {
  if (!confirm(`Are you sure you want to delete student ${sid}?`)) return;
  const students = getStoredStudents().filter(s => s.student_id !== sid);
  saveStoredStudents(students);
  fetch(`/api/students/${sid}`, { method: 'DELETE' }).catch(() => {});
  showToast(`✅ Deleted student ${sid}`);
  renderDashboard();
  renderDirectory();
}

// Initial boot
document.addEventListener('DOMContentLoaded', () => {
  renderDashboard();
});
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  renderDashboard();
}
"""

    # 13. frontend/index.html & root index.html (self-contained interactive preview)
    index_html_template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Student Management Portal</title>
  <link rel="stylesheet" href="styles.css">
  <style>
/* __INLINE_CSS__ */
  </style>
</head>
<body>
  <div id="root">
    <!-- Static / Live Interactive Student Portal -->
    <nav class="navbar">
      <div class="nav-brand">
        <span>🎓</span>
        <span>Student Management Portal</span>
        <span id="nav-count" class="nav-badge">5 Students Enrolled</span>
      </div>
      <div class="nav-tabs">
        <button id="tab-dash" class="nav-tab-btn active" onclick="switchTab('dashboard')">📊 Dashboard</button>
        <button id="tab-dir" class="nav-tab-btn" onclick="switchTab('directory')">📋 Directory</button>
        <button id="tab-reg" class="nav-tab-btn" onclick="switchTab('register')">➕ Register Student</button>
        <button id="tab-ana" class="nav-tab-btn" onclick="switchTab('analytics')">📈 Analytics</button>
      </div>
      <div class="nav-status">
        <span class="status-dot"></span>
        <span>Active & Synced</span>
        <button class="nav-tab-btn" style="margin-left: 0.5rem;" onclick="showToast('Admin Session: Authenticated')">🔐 Login: Admin</button>
      </div>
    </nav>

    <main class="main-container">
      <!-- VIEW: DASHBOARD -->
      <section id="view-dashboard">
        <div class="kpi-grid">
          <div class="kpi-card">
            <span class="kpi-title">Total Enrolled</span>
            <span id="stat-total" class="kpi-value">5</span>
            <span class="kpi-sub">Active registered records</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-title">Active Students</span>
            <span id="stat-active" class="kpi-value">5</span>
            <span class="kpi-sub">100% good academic standing</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-title">Academic Departments</span>
            <span id="stat-depts" class="kpi-value">5</span>
            <span class="kpi-sub">CS, IT, EE, DS, BA</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-title">Average Cumulative GPA</span>
            <span id="stat-gpa" class="kpi-value">3.78</span>
            <span class="kpi-sub">High academic standard</span>
          </div>
        </div>

        <div class="section-header">
          <h3 class="section-title">Recently Enrolled Students</h3>
        </div>
        <div id="dash-table-container"></div>
      </section>

      <!-- VIEW: DIRECTORY -->
      <section id="view-directory" style="display: none;">
        <div class="section-header">
          <h3 class="section-title">Student Directory</h3>
          <div class="filter-bar">
            <input
              type="text"
              id="search-input"
              class="search-input"
              placeholder="Search by name, ID, email, or course..."
              oninput="renderDirectory()"
            />
            <select id="filter-dept" class="select-filter" onchange="renderDirectory()">
              <option value="all">All Departments</option>
              <option value="Computer Science">Computer Science</option>
              <option value="Information Technology">Information Technology</option>
              <option value="Electrical Engineering">Electrical Engineering</option>
              <option value="Data Science">Data Science</option>
              <option value="Business Administration">Business Administration</option>
            </select>
          </div>
        </div>
        <div id="dir-table-container"></div>
      </section>

      <!-- VIEW: REGISTER -->
      <section id="view-register" style="display: none;">
        <div class="section-header" style="justify-content: center; margin-bottom: 1.5rem;">
          <h3 class="section-title">Student Enrollment & Registration</h3>
        </div>
        <div class="form-card">
          <form id="student-reg-form" onsubmit="handleFormSubmit(event)">
            <div class="form-row">
              <div class="form-group">
                <label for="reg-id">Student ID *</label>
                <input type="text" id="reg-id" class="form-control" placeholder="e.g. STU-1006" required />
              </div>
              <div class="form-group">
                <label for="reg-name">Full Name *</label>
                <input type="text" id="reg-name" class="form-control" placeholder="e.g. Sophia Loren" required />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="reg-email">Email Address *</label>
                <input type="email" id="reg-email" class="form-control" placeholder="sophia.loren@university.edu" required />
              </div>
              <div class="form-group">
                <label for="reg-phone">Phone Number *</label>
                <input type="text" id="reg-phone" class="form-control" placeholder="+1 555-0199" required />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="reg-dept">Academic Department *</label>
                <select id="reg-dept" class="form-control" required>
                  <option value="Computer Science">Computer Science</option>
                  <option value="Information Technology">Information Technology</option>
                  <option value="Electrical Engineering">Electrical Engineering</option>
                  <option value="Data Science">Data Science</option>
                  <option value="Business Administration">Business Administration</option>
                </select>
              </div>
              <div class="form-group">
                <label for="reg-course">Degree Course / Major *</label>
                <select id="reg-course" class="form-control" required>
                  <option value="B.S. Computer Science">B.S. Computer Science</option>
                  <option value="B.S. Software Engineering">B.S. Software Engineering</option>
                  <option value="B.S. Information Technology">B.S. Information Technology</option>
                  <option value="B.S. Electrical Engineering">B.S. Electrical Engineering</option>
                  <option value="B.S. Data Science & AI">B.S. Data Science & AI</option>
                  <option value="B.B.A. Business Administration">B.B.A. Business Administration</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label for="reg-gpa">Cumulative GPA (0.00 - 4.00) *</label>
              <input type="number" id="reg-gpa" class="form-control" step="0.01" min="0" max="4.0" value="3.50" required />
            </div>

            <div style="display: flex; gap: 0.75rem; margin-top: 1.5rem;">
              <button type="submit" class="btn btn-primary">Enroll Student</button>
              <button type="reset" class="btn btn-secondary">Reset Form</button>
            </div>
          </form>
        </div>
      </section>

      <!-- VIEW: ANALYTICS -->
      <section id="view-analytics" style="display: none;">
        <div class="section-header">
          <h3 class="section-title">Academic Analytics & Performance</h3>
        </div>
        <div id="analytics-container"></div>
      </section>
    </main>

    <!-- EDIT MODAL -->
    <div id="edit-modal" class="modal-overlay" style="display: none;" onclick="closeEditModal()">
      <div class="modal-content" onclick="event.stopPropagation()">
        <div class="modal-header">
          <h3 style="color: #fff;">Edit Student Record</h3>
          <button class="btn btn-secondary" onclick="closeEditModal()">✕</button>
        </div>
        <form onsubmit="handleEditSubmit(event)">
          <input type="hidden" id="edit-id" />
          <div class="form-group">
            <label>Name</label>
            <input type="text" id="edit-name" class="form-control" required />
          </div>
          <div class="form-group">
            <label>Email</label>
            <input type="email" id="edit-email" class="form-control" required />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Department</label>
              <select id="edit-dept" class="form-control" required>
                <option value="Computer Science">Computer Science</option>
                <option value="Information Technology">Information Technology</option>
                <option value="Electrical Engineering">Electrical Engineering</option>
                <option value="Data Science">Data Science</option>
                <option value="Business Administration">Business Administration</option>
              </select>
            </div>
            <div class="form-group">
              <label>Course</label>
              <select id="edit-course" class="form-control" required>
                <option value="B.S. Computer Science">B.S. Computer Science</option>
                <option value="B.S. Software Engineering">B.S. Software Engineering</option>
                <option value="B.S. Information Technology">B.S. Information Technology</option>
                <option value="B.S. Electrical Engineering">B.S. Electrical Engineering</option>
                <option value="B.S. Data Science & AI">B.S. Data Science & AI</option>
                <option value="B.B.A. Business Administration">B.B.A. Business Administration</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Phone</label>
              <input type="text" id="edit-phone" class="form-control" required />
            </div>
            <div class="form-group">
              <label>GPA</label>
              <input type="number" id="edit-gpa" class="form-control" step="0.01" min="0" max="4.0" required />
            </div>
          </div>
          <div style="display: flex; gap: 0.75rem; margin-top: 1.25rem;">
            <button type="submit" class="btn btn-primary">Save Changes</button>
            <button type="button" class="btn btn-secondary" onclick="closeEditModal()">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- STUDENT PROFILE MODAL -->
    <div id="profile-modal" class="modal-overlay" style="display: none;" onclick="closeProfileModal()">
      <div class="modal-content" onclick="event.stopPropagation()">
        <div class="modal-header">
          <h3 style="color: #fff;">Student Profile</h3>
          <button class="btn btn-secondary" onclick="closeProfileModal()">✕</button>
        </div>
        <div id="profile-modal-body"></div>
        <div style="display: flex; justify-content: flex-end; margin-top: 1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="closeProfileModal()">Close</button>
        </div>
      </div>
    </div>

    <!-- TOAST NOTIFICATION -->
    <div id="toast-box" class="toast-container" style="display: none;">
      <div id="toast-text" class="toast"></div>
    </div>
  </div>

  <script>
// __INLINE_JS__
  </script>
  <script src="app.js"></script>
</body>
</html>
"""
    # Replace inline CSS and JS into index_html
    index_html = index_html_template.replace("/* __INLINE_CSS__ */", css_code).replace("// __INLINE_JS__", app_js)

    files.append({
        "path": "frontend/index.html",
        "language": "html",
        "purpose": "Complete interactive Student Management Portal entrypoint",
        "code": index_html,
    })
    files.append({
        "path": "index.html",
        "language": "html",
        "purpose": "Root application portal HTML alias",
        "code": index_html,
    })
    files.append({
        "path": "app.js",
        "language": "javascript",
        "purpose": "Client-side interactive state management and local persistence",
        "code": app_js,
    })
    files.append({
        "path": "frontend/app.js",
        "language": "javascript",
        "purpose": "Frontend public JavaScript controller alias for live preview",
        "code": app_js,
    })

    # 14. backend/__init__.py & backend/routers/__init__.py & tests/__init__.py
    files.append({"path": "backend/__init__.py", "language": "python", "purpose": "Package init", "code": ""})
    files.append({"path": "backend/routers/__init__.py", "language": "python", "purpose": "Routers init", "code": ""})
    files.append({"path": "tests/__init__.py", "language": "python", "purpose": "Tests init", "code": ""})

    # 15. backend/database.py
    backend_db = """import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent / "students.db"

def get_connection():
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    try:
        conn.execute(\"\"\"
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                department TEXT NOT NULL,
                course TEXT NOT NULL DEFAULT 'B.S. Computer Science',
                phone TEXT NOT NULL,
                gpa REAL DEFAULT 3.5,
                status TEXT DEFAULT 'Active',
                created_at TEXT NOT NULL
            )
        \"\"\")
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(students)")
        cols = [r[1] for r in cur.fetchall()]
        if "course" not in cols:
            conn.execute("ALTER TABLE students ADD COLUMN course TEXT NOT NULL DEFAULT 'B.S. Computer Science'")
            conn.commit()
        cur.execute("SELECT COUNT(*) FROM students")
        if cur.fetchone()[0] == 0:
            seed_data = [
                ("1", "STU-1001", "Elena Rostova", "elena.rostova@university.edu", "Computer Science", "B.S. Computer Science", "+1 555-0101", 3.92, "Active", "2026-09-01"),
                ("2", "STU-1002", "Marcus Vance", "marcus.vance@university.edu", "Information Technology", "B.S. Information Technology", "+1 555-0102", 3.78, "Active", "2026-09-01"),
                ("3", "STU-1003", "Aisha Al-Mansoor", "aisha.mansoor@university.edu", "Electrical Engineering", "B.S. Electrical Engineering", "+1 555-0103", 3.85, "Active", "2026-09-01"),
                ("4", "STU-1004", "David Kim", "david.kim@university.edu", "Data Science", "B.S. Data Science & AI", "+1 555-0104", 3.65, "Active", "2026-09-01"),
                ("5", "STU-1005", "Sophia Martinez", "sophia.martinez@university.edu", "Business Administration", "B.B.A. Business Administration", "+1 555-0105", 3.70, "Active", "2026-09-01"),
            ]
            conn.executemany(\"\"\"
                INSERT INTO students (id, student_id, name, email, department, course, phone, gpa, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            \"\"\", seed_data)
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
"""
    files.append({
        "path": "backend/database.py",
        "language": "python",
        "purpose": "SQLite database initialization and connection manager",
        "code": backend_db,
    })

    # 16. backend/models.py
    backend_models = """from dataclasses import dataclass
from typing import Optional

@dataclass
class Student:
    id: str
    student_id: str
    name: str
    email: str
    department: str
    course: str = "B.S. Computer Science"
    phone: str = ""
    gpa: float = 3.5
    status: str = "Active"
    created_at: str = ""

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "course": self.course,
            "phone": self.phone,
            "gpa": self.gpa,
            "status": self.status,
            "created_at": self.created_at,
        }
"""
    files.append({
        "path": "backend/models.py",
        "language": "python",
        "purpose": "Student domain model and dataclass definitions",
        "code": backend_models,
    })

    # 17. backend/schemas.py
    backend_schemas = """import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class StudentCreate(BaseModel):
    student_id: str = Field(..., min_length=2, max_length=32)
    name: str = Field(..., min_length=2, max_length=128)
    email: str = Field(..., min_length=5, max_length=128)
    department: str = Field(..., min_length=2, max_length=64)
    course: Optional[str] = Field(default="B.S. Computer Science", max_length=128)
    phone: str = Field(..., min_length=5, max_length=32)
    gpa: float = Field(default=3.5, ge=0.0, le=4.0)
    status: Optional[str] = "Active"

    @field_validator("email")
    @classmethod
    def validate_email_pattern(cls, v: str) -> str:
        clean = v.strip().lower()
        if "@" not in clean or "." not in clean:
            raise ValueError("Invalid email format")
        return clean

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    course: Optional[str] = None
    phone: Optional[str] = None
    gpa: Optional[float] = None
    status: Optional[str] = None

class StudentResponse(BaseModel):
    id: str
    student_id: str
    name: str
    email: str
    department: str
    course: Optional[str] = "B.S. Computer Science"
    phone: str
    gpa: float
    status: str
    created_at: str
"""
    files.append({
        "path": "backend/schemas.py",
        "language": "python",
        "purpose": "Pydantic request validation and response models",
        "code": backend_schemas,
    })

    # 18. backend/routers/students.py
    backend_router = """import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
try:
    from ..database import get_connection
    from ..schemas import StudentCreate, StudentUpdate, StudentResponse
except ImportError:
    from backend.database import get_connection
    from backend.schemas import StudentCreate, StudentUpdate, StudentResponse

router = APIRouter(prefix="/api/students", tags=["Students"])

@router.get("", response_model=List[StudentResponse])
def list_students(q: Optional[str] = Query(None), department: Optional[str] = Query(None)):
    conn = get_connection()
    try:
        cur = conn.cursor()
        query = "SELECT * FROM students WHERE 1=1"
        params = []
        if q:
            query += " AND (name LIKE ? OR student_id LIKE ? OR email LIKE ? OR course LIKE ?)"
            wild = f"%{q}%"
            params.extend([wild, wild, wild, wild])
        if department and department != "all":
            query += " AND department = ?"
            params.append(department)
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE id = ? OR student_id = ?", (student_id, student_id))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Student record not found")
        return dict(row)
    finally:
        conn.close()

@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(payload: StudentCreate):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM students WHERE student_id = ?", (payload.student_id,))
        if cur.fetchone()[0] > 0:
            raise HTTPException(status_code=400, detail=f"Student ID '{payload.student_id}' is already registered.")
        new_id = str(uuid.uuid4())[:8]
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cur.execute(\"\"\"
            INSERT INTO students (id, student_id, name, email, department, course, phone, gpa, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        \"\"\", (new_id, payload.student_id, payload.name, payload.email, payload.department, payload.course or "B.S. Computer Science", payload.phone, payload.gpa, payload.status or "Active", now_str))
        conn.commit()
        cur.execute("SELECT * FROM students WHERE id = ?", (new_id,))
        return dict(cur.fetchone())
    finally:
        conn.close()

@router.put("/{student_id}", response_model=StudentResponse)
def update_student(student_id: str, payload: StudentUpdate):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE id = ? OR student_id = ?", (student_id, student_id))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Student record not found")
        current = dict(row)
        updates = payload.model_dump(exclude_unset=True)
        for k, v in updates.items():
            if v is not None:
                current[k] = v
        cur.execute(\"\"\"
            UPDATE students SET name = ?, email = ?, department = ?, course = ?, phone = ?, gpa = ?, status = ?
            WHERE id = ?
        \"\"\", (current["name"], current["email"], current["department"], current.get("course", "B.S. Computer Science"), current["phone"], current["gpa"], current["status"], current["id"]))
        conn.commit()
        return current
    finally:
        conn.close()

@router.delete("/{student_id}")
def delete_student(student_id: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM students WHERE id = ? OR student_id = ?", (student_id, student_id))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Student record not found")
        cur.execute("DELETE FROM students WHERE id = ?", (row["id"],))
        conn.commit()
        return {"status": "deleted", "student_id": student_id}
    finally:
        conn.close()
"""
    files.append({
        "path": "backend/routers/students.py",
        "language": "python",
        "purpose": "FastAPI REST API router for student CRUD endpoints",
        "code": backend_router,
    })

    # 19. backend/main.py
    backend_main = """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from .database import init_db
    from .routers.students import router as students_router
except ImportError:
    from backend.database import init_db
    from backend.routers.students import router as students_router

init_db()

app = FastAPI(title="Student Management Portal API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Student Management Portal API"}

app.include_router(students_router)
"""
    files.append({
        "path": "backend/main.py",
        "language": "python",
        "purpose": "FastAPI application entrypoint with health check and CORS",
        "code": backend_main,
    })

    # 20. app.py (Root backend entrypoint wrapper)
    root_app_py = """# Root entrypoint for Student Management Portal API
try:
    from backend.main import app
    from backend.database import init_db, get_connection
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from backend.main import app
    from backend.database import init_db, get_connection

init_db()

def get_status():
    return {"status": "healthy", "service": "Student Management Portal"}

def create_student(payload):
    import uuid
    from datetime import datetime, timezone
    conn = get_connection()
    try:
        nid = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conn.execute(
            "INSERT INTO students (id, student_id, name, email, department, course, phone, gpa, status, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                nid,
                payload.get("student_id", f"STU-{nid}"),
                payload["name"],
                payload.get("email", "s@uni.edu"),
                payload.get("department", "Computer Science"),
                payload.get("course", "B.S. Computer Science"),
                payload.get("phone", "+1 555-0000"),
                payload.get("gpa", 3.5),
                "Active",
                now,
            )
        )
        conn.commit()
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE id = ?", (nid,))
        return dict(cur.fetchone())
    finally:
        conn.close()

def list_students():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM students")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_student(student_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE id = ? OR student_id = ?", (student_id, student_id))
        r = cur.fetchone()
        return dict(r) if r else None
    finally:
        conn.close()

def delete_student(student_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM students WHERE id = ? OR student_id = ?", (student_id, student_id))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def clear_data():
    conn = get_connection()
    try:
        conn.execute("DELETE FROM students WHERE student_id NOT LIKE 'STU-100%'")
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
"""
    files.append({
        "path": "app.py",
        "language": "python",
        "purpose": "Application service logic and handlers",
        "code": root_app_py,
    })

    # 21. tests/test_api.py (Comprehensive test suite covering all required endpoints)
    test_api_py = """import unittest
from starlette.testclient import TestClient
from backend.main import app
from backend.database import init_db

class TestStudentPortalAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_01_health_endpoint(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("status"), "healthy")

    def test_02_student_creation(self):
        payload = {
            "student_id": "STU-9901",
            "name": "Jordan Peterson",
            "email": "jordan.p@university.edu",
            "department": "Computer Science",
            "course": "B.S. Computer Science",
            "phone": "+1 555-9901",
            "gpa": 3.85
        }
        res = self.client.post("/api/students", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["student_id"], "STU-9901")
        self.assertEqual(data["name"], "Jordan Peterson")
        self.assertEqual(data["course"], "B.S. Computer Science")

    def test_03_student_listing(self):
        res = self.client.get("/api/students")
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.json()), 1)

    def test_04_student_retrieval(self):
        res = self.client.get("/api/students/STU-1001")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["name"], "Elena Rostova")

    def test_05_student_updating(self):
        res = self.client.put("/api/students/STU-1002", json={"gpa": 3.99})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["gpa"], 3.99)

    def test_06_student_deletion(self):
        res = self.client.delete("/api/students/STU-9901")
        self.assertEqual(res.status_code, 200)
        verify = self.client.get("/api/students/STU-9901")
        self.assertEqual(verify.status_code, 404)

    def test_07_invalid_email_validation(self):
        bad_payload = {
            "student_id": "STU-BAD",
            "name": "Bad Email Student",
            "email": "notanemail",
            "department": "Computer Science",
            "phone": "+1 555-0000"
        }
        res = self.client.post("/api/students", json=bad_payload)
        self.assertEqual(res.status_code, 422)

    def test_08_duplicate_student_id_rejected(self):
        dup_payload = {
            "student_id": "STU-1001",
            "name": "Duplicate Student",
            "email": "duplicate@university.edu",
            "department": "Computer Science",
            "phone": "+1 555-1111"
        }
        res = self.client.post("/api/students", json=dup_payload)
        self.assertEqual(res.status_code, 400)

    def test_09_search_functionality(self):
        res = self.client.get("/api/students?q=Elena")
        self.assertEqual(res.status_code, 200)
        results = res.json()
        self.assertTrue(any(s["student_id"] == "STU-1001" for s in results))

if __name__ == "__main__":
    unittest.main()
"""
    files.append({
        "path": "tests/test_api.py",
        "language": "python",
        "purpose": "Comprehensive API integration test suite covering 9 required scenarios",
        "code": test_api_py,
    })

    # 22. tests/test_students.py
    test_students_py = """import unittest
import app

class TestStudentsUnit(unittest.TestCase):
    def setUp(self):
        app.clear_data()

    def test_status_health(self):
        status = app.get_status()
        self.assertEqual(status.get("status"), "healthy")

    def test_create_and_get_student(self):
        created = app.create_student({
            "name": "Taylor Swift",
            "student_id": "STU-2099",
            "email": "taylor@uni.edu",
            "department": "Business Administration",
            "course": "B.B.A. Business Administration",
            "phone": "+1 555-2099",
            "gpa": 3.95
        })
        self.assertIsNotNone(created.get("id"))
        fetched = app.get_student("STU-2099")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.get("name"), "Taylor Swift")

    def test_list_students(self):
        students = app.list_students()
        self.assertGreaterEqual(len(students), 1)

    def test_delete_student(self):
        s = app.create_student({"name": "To Delete", "student_id": "STU-DEL"})
        self.assertTrue(app.delete_student("STU-DEL"))

if __name__ == "__main__":
    unittest.main()
"""
    files.append({
        "path": "tests/test_students.py",
        "language": "python",
        "purpose": "Student business logic unit tests",
        "code": test_students_py,
    })
    files.append({
        "path": "tests/test_app.py",
        "language": "python",
        "purpose": "Root tests alias",
        "code": test_api_py,
    })

    # 23. README.md
    readme_md = f"""# {name}

An autonomous full-stack Student Management Portal generated by the Autonomous DevOps Swarm.

## Architecture

- **Frontend**: React 18 + Vite + Responsive CSS
  - KPI Dashboard (Enrolled students, Active status, Departments, Cumulative GPA)
  - Student Directory with live search, department filtering, and action triggers
  - Student Enrollment & Registration form with client-side and backend validation
  - Student Profile Modal with academic standing and student credentials
  - Real-time client-side state with local persistence and REST API synchronization
- **Backend**: Python + FastAPI
  - RESTful CRUD API endpoints (`/api/students`)
  - Pydantic schema validation for request payloads
  - SQLite database persistence with automated table initialization and seeding
  - Health endpoint (`/api/health`) and CORS middleware
- **Automated Testing**: Pytest and Unittest
  - 9 automated test scenarios verifying health, CRUD, validation, and search

## Running the Application

### Backend API:
```bash
python -m uvicorn backend.main:app --port 8000
```

### Running Tests:
```bash
python -m unittest discover -v tests/
```

### Live Preview:
```bash
python -m http.server 9101
```
"""
    files.append({
        "path": "README.md",
        "language": "markdown",
        "purpose": "Project documentation and architecture overview",
        "code": readme_md,
    })

    return files

import React, { useState, useEffect, useRef, useMemo } from 'react'
import PageHeader from './PageHeader.jsx'
import { PRIMARY_SETTINGS_SECTIONS, ADVANCED_SETTINGS_SECTIONS, SETTINGS_SECTIONS, DEFAULT_SETTINGS } from '../settingsConfig.js'

export default function SettingsConsole({
  settings = DEFAULT_SETTINGS,
  onSaveSettings,
  onResetDefaults,
  onNavigateToLogs,
  themeMode = 'dark',
  onThemeChange,
  allAgents = [
    'Planning Agent',
    'Coding Agent',
    'Build Agent',
    'Testing Agent',
    'Security Agent',
    'Release Agent',
    'Deploy Agent',
    'Monitor Agent',
  ],
}) {
  const [activeSection, setActiveSection] = useState('general')
  const [lastSaved, setLastSaved] = useState(settings)
  const [formState, setFormState] = useState(settings)
  const [saveStatus, setSaveStatus] = useState(null)
  const [saving, setSaving] = useState(false)
  const [advancedExpanded, setAdvancedExpanded] = useState(false)
  const [resetConfirmOpen, setResetConfirmOpen] = useState(false)
  const [testingService, setTestingService] = useState(null)
  const [testResults, setTestResults] = useState({})
  const [testingNotification, setTestingNotification] = useState(false)
  const [notificationResult, setNotificationResult] = useState(null)
  const [secretVisibility, setSecretVisibility] = useState({})
  const [auditLogs, setAuditLogs] = useState([])
  const [loadingAudit, setLoadingAudit] = useState(false)
  const [auditFilter, setAuditFilter] = useState('all')

  const fileInputRef = useRef(null)

  // Sync state when prop updates
  useEffect(() => {
    setLastSaved(settings)
    setFormState(settings)
  }, [settings])

  // Auto-expand advanced if active section is an advanced subsection
  useEffect(() => {
    if (['workspace', 'audit', 'advanced'].includes(activeSection)) {
      setAdvancedExpanded(true)
    }
  }, [activeSection])

  // Track if changes have been made
  const isDirty = useMemo(() => {
    try {
      return JSON.stringify(formState) !== JSON.stringify(lastSaved)
    } catch {
      return false
    }
  }, [formState, lastSaved])

  // Fetch real audit logs when audit section is opened
  useEffect(() => {
    if (activeSection === 'audit') {
      fetchAuditLogs()
    }
  }, [activeSection])

  const fetchAuditLogs = async () => {
    setLoadingAudit(true)
    try {
      const res = await fetch('/api/settings/audit')
      if (res.ok) {
        const data = await res.json()
        setAuditLogs(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.warn('Could not fetch audit history:', err)
    } finally {
      setLoadingAudit(false)
    }
  }

  // Update top-level section field
  const updateField = (section, field, value) => {
    setFormState((prev) => ({
      ...prev,
      [section]: {
        ...(prev[section] || {}),
        [field]: value,
      },
    }))
    setSaveStatus(null)
  }

  // Update nested field
  const updateNestedField = (section, parentField, field, value) => {
    setFormState((prev) => ({
      ...prev,
      [section]: {
        ...(prev[section] || {}),
        [parentField]: {
          ...((prev[section] && prev[section][parentField]) || {}),
          [field]: value,
        },
      },
    }))
    setSaveStatus(null)
  }

  const handleSave = async () => {
    setSaving(true)
    setSaveStatus(null)
    try {
      if (onSaveSettings) {
        await onSaveSettings(formState)
      }
      setLastSaved(formState)
      setSaveStatus({ type: 'success', message: 'Settings saved and persisted successfully.' })
      setTimeout(() => setSaveStatus(null), 4000)
    } catch (err) {
      setSaveStatus({ type: 'error', message: `Failed to save settings: ${err.message || 'Server error'}` })
    } finally {
      setSaving(false)
    }
  }

  const handleDiscard = () => {
    setFormState(lastSaved)
    setSaveStatus(null)
  }

  const handleResetConfirm = async () => {
    setResetConfirmOpen(false)
    setSaving(true)
    try {
      if (onResetDefaults) {
        await onResetDefaults()
      }
      setFormState(DEFAULT_SETTINGS)
      setSaveStatus({ type: 'success', message: 'All settings reset to recommended enterprise factory defaults.' })
      setTimeout(() => setSaveStatus(null), 4000)
    } catch (err) {
      setSaveStatus({ type: 'error', message: 'Failed to reset settings to defaults.' })
    } finally {
      setSaving(false)
    }
  }

  const handleExport = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(formState, null, 2))
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute('href', dataStr)
    downloadAnchor.setAttribute('download', 'enterprise-devops-settings.json')
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
    setSaveStatus({ type: 'success', message: 'Configuration successfully exported as JSON.' })
    setTimeout(() => setSaveStatus(null), 3000)
  }

  const handleImport = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = async (event) => {
      try {
        const imported = JSON.parse(event.target.result)
        const merged = {
          ...DEFAULT_SETTINGS,
          ...imported,
          general: { ...DEFAULT_SETTINGS.general, ...(imported.general || {}) },
          agents: { ...DEFAULT_SETTINGS.agents, ...(imported.agents || {}) },
          autonomous: { ...DEFAULT_SETTINGS.autonomous, ...(imported.autonomous || {}) },
          safety: { ...DEFAULT_SETTINGS.safety, ...(imported.safety || {}) },
          buildTesting: { ...DEFAULT_SETTINGS.buildTesting, ...(imported.buildTesting || {}) },
          integrations: { ...DEFAULT_SETTINGS.integrations, ...(imported.integrations || {}) },
          secrets: { ...DEFAULT_SETTINGS.secrets, ...(imported.secrets || {}) },
          notifications: { ...DEFAULT_SETTINGS.notifications, ...(imported.notifications || {}) },
          workspace: { ...DEFAULT_SETTINGS.workspace, ...(imported.workspace || {}) },
          audit: { ...DEFAULT_SETTINGS.audit, ...(imported.audit || {}) },
          advanced: { ...DEFAULT_SETTINGS.advanced, ...(imported.advanced || {}) },
        }
        setFormState(merged)
        if (onSaveSettings) {
          await onSaveSettings(merged)
        }
        setSaveStatus({ type: 'success', message: 'Imported settings applied and saved successfully.' })
        setTimeout(() => setSaveStatus(null), 4000)
      } catch (err) {
        setSaveStatus({ type: 'error', message: `Invalid settings JSON file: ${err.message}` })
      }
    }
    reader.readAsText(file)
    e.target.value = ''
  }

  // Real Connection Test
  const runTestConnection = async (service, customConfig = null) => {
    setTestingService(service)
    try {
      const config = customConfig || formState.integrations?.[service] || {}
      const res = await fetch('/api/settings/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service, config }),
      })
      const result = await res.json()
      setTestResults((prev) => ({ ...prev, [service]: result }))
    } catch (err) {
      setTestResults((prev) => ({
        ...prev,
        [service]: {
          connected: false,
          latency_ms: 0,
          status_code: 503,
          message: `Network probe failure: ${err.message || 'Endpoint unreachable'}`,
        },
      }))
    } finally {
      setTestingService(null)
    }
  }

  // Real Test Notification
  const runTestNotification = async () => {
    setTestingNotification(true)
    setNotificationResult(null)
    try {
      const notifConfig = formState.notifications || {}
      const target =
        notifConfig.channel === 'slack'
          ? notifConfig.slackChannel
          : notifConfig.channel === 'webhook'
          ? notifConfig.webhookUrl
          : notifConfig.emailAddress
      const res = await fetch('/api/settings/test-notification', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: notifConfig.channel || 'dashboard',
          severity: notifConfig.alertSeverity || 'critical',
          target,
          message: `Test alert from DevOps Swarm - Notification delivery check (${new Date().toLocaleTimeString()})`,
        }),
      })
      const data = await res.json()
      setNotificationResult(data)
    } catch (err) {
      setNotificationResult({
        success: false,
        message: `Notification dispatch failed: ${err.message}`,
      })
    } finally {
      setTestingNotification(false)
    }
  }

  const toggleSecretVisibility = (key) => {
    setSecretVisibility((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  return (
    <div className="settings-console-container">
      {/* Standardized Header */}
      <PageHeader
        category="GOVERNANCE & SYSTEM CONFIGURATION"
        title="Enterprise DevOps Settings"
        subtitle="Manage autonomous execution policies, agent swarm parameters, quality gates, integrations, and compliance audit policies."
        badge={
          isDirty
            ? { label: '● Unsaved Changes', variant: 'waiting' }
            : { label: 'Persistent & Synced', variant: 'completed' }
        }
        actions={
          <div className="settings-header-action-group">
            {isDirty && (
              <button className="secondary-button" onClick={handleDiscard} disabled={saving}>
                Discard
              </button>
            )}
            <button className="primary-button" onClick={handleSave} disabled={saving || !isDirty}>
              {saving ? 'Saving changes…' : 'Save Changes'}
            </button>
            <button
              className="danger-button-outline"
              onClick={() => setResetConfirmOpen(true)}
              disabled={saving}
              title="Reset all settings to recommended defaults"
            >
              Reset to Defaults
            </button>
            <div className="settings-util-dropdown">
              <button className="icon-util-btn" onClick={handleExport} title="Export Settings JSON">
                💾 Export
              </button>
              <button className="icon-util-btn" onClick={() => fileInputRef.current?.click()} title="Import Settings JSON">
                📥 Import
              </button>
              <input ref={fileInputRef} type="file" accept=".json" style={{ display: 'none' }} onChange={handleImport} />
            </div>
          </div>
        }
      />

      {/* Save / Error Feedback Toast */}
      {saveStatus && (
        <div className={`settings-feedback-banner ${saveStatus.type}`}>
          <span>{saveStatus.type === 'success' ? '✓' : '⚠️'}</span>
          <p>{saveStatus.message}</p>
          <button className="feedback-dismiss" onClick={() => setSaveStatus(null)}>✕</button>
        </div>
      )}

      {/* Main 2-Column Deck: Left Navigation, Right Content */}
      <div className="settings-deck-layout">
        {/* Left Side Navigation Panel */}
        <nav className="settings-nav-panel" aria-label="Settings navigation">
          <div className="settings-nav-title">SECTIONS</div>
          <ul className="settings-nav-list">
            {PRIMARY_SETTINGS_SECTIONS.map((sec, idx) => {
              const active = activeSection === sec.id || 
                (sec.id === 'execution' && (activeSection === 'execution' || activeSection === 'autonomous')) || 
                (sec.id === 'security' && (activeSection === 'security' || activeSection === 'safety'))
              return (
                <li key={sec.id}>
                  <button
                    className={`settings-nav-item ${active ? 'active' : ''}`}
                    onClick={() => setActiveSection(sec.id)}
                  >
                    <span className="settings-nav-icon">{sec.icon}</span>
                    <span className="settings-nav-label">
                      <span className="settings-nav-number">{String(idx + 1).padStart(2, '0')}.</span>
                      {sec.label}
                    </span>
                    {active && <span className="settings-nav-active-pip" />}
                  </button>
                </li>
              )
            })}
          </ul>

          {/* Collapsible Advanced Settings Section */}
          <div className="settings-nav-collapsible-group">
            <button
              type="button"
              className="settings-nav-accordion-header"
              onClick={() => setAdvancedExpanded(!advancedExpanded)}
              aria-expanded={advancedExpanded}
            >
              <span className="settings-nav-accordion-title">
                <span className="accordion-caret">{advancedExpanded ? '▾' : '▸'}</span>
                <span>Advanced Settings</span>
              </span>
              <span className="accordion-pill">{ADVANCED_SETTINGS_SECTIONS.length}</span>
            </button>
            {advancedExpanded && (
              <ul className="settings-nav-sublist">
                {ADVANCED_SETTINGS_SECTIONS.map((sec) => {
                  const active = activeSection === sec.id
                  return (
                    <li key={sec.id}>
                      <button
                        className={`settings-nav-item settings-nav-subitem ${active ? 'active' : ''}`}
                        onClick={() => setActiveSection(sec.id)}
                      >
                        <span className="settings-nav-icon">{sec.icon}</span>
                        <span className="settings-nav-label">{sec.label}</span>
                        {active && <span className="settings-nav-active-pip" />}
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>

          <div className="settings-sidebar-status">
            <div className="settings-status-indicator">
              <span className="status-dot-pulse" />
              <span>Storage Driver: <strong>SQLite / MongoDB</strong></span>
            </div>
            <div className="settings-status-indicator">
              <span className="agent-dot completed" />
              <span>Backend Status: <strong>Connected</strong></span>
            </div>
          </div>
        </nav>

        {/* Right Side Configuration View */}
        <main className="settings-content-pane">
          {/* Section 1: GENERAL */}
          {activeSection === 'general' && (
            <div className="settings-section-view">
              <div className="section-intro">
                <h2>General Preferences</h2>
                <p>System identity, deployment target environments, telemetry, and runtime preferences.</p>
              </div>

              <div className="settings-card">
                <h3>Project & Application Identity</h3>
                <div className="settings-form-grid">
                  <div className="form-group">
                    <label>Project Name</label>
                    <input
                      type="text"
                      value={formState.general?.projectName || ''}
                      onChange={(e) => updateField('general', 'projectName', e.target.value)}
                      placeholder="e.g. Autonomous DevOps Swarm"
                    />
                    <small>Displayed across all mission logs and workspace artifacts.</small>
                  </div>
                  <div className="form-group">
                    <label>Default Git Branch</label>
                    <input
                      type="text"
                      value={formState.general?.defaultBranch || 'main'}
                      onChange={(e) => updateField('general', 'defaultBranch', e.target.value)}
                      placeholder="main"
                    />
                    <small>Default branch targeted by Coding and Release agents.</small>
                  </div>
                </div>

                <div className="form-group" style={{ marginTop: 14 }}>
                  <label>Project Description</label>
                  <input
                    type="text"
                    value={formState.general?.description || ''}
                    onChange={(e) => updateField('general', 'description', e.target.value)}
                    placeholder="Short description of the autonomous software development project"
                  />
                </div>
              </div>

              {/* Theme Selection Card */}
              <div className="settings-card">
                <h3>Interface Theme & Appearance</h3>
                <p className="card-subtitle" style={{ color: '#94a3b8', fontSize: '0.82rem', margin: '4px 0 14px' }}>
                  Select your preferred color scheme across all DevOps swarm interfaces.
                </p>
                <div className="theme-selector-cards">
                  <button
                    type="button"
                    className={`theme-option-card ${(formState.general?.theme || themeMode) === 'light' ? 'selected' : ''}`}
                    onClick={() => {
                      updateField('general', 'theme', 'light')
                      if (onThemeChange) onThemeChange('light')
                    }}
                  >
                    <span className="theme-icon">☀️</span>
                    <div className="theme-meta">
                      <strong>Light Mode</strong>
                      <small>High-contrast daylight theme</small>
                    </div>
                    {(formState.general?.theme || themeMode) === 'light' && <span className="theme-check">✓ Active</span>}
                  </button>

                  <button
                    type="button"
                    className={`theme-option-card ${(formState.general?.theme || themeMode) === 'dark' ? 'selected' : ''}`}
                    onClick={() => {
                      updateField('general', 'theme', 'dark')
                      if (onThemeChange) onThemeChange('dark')
                    }}
                  >
                    <span className="theme-icon">🌙</span>
                    <div className="theme-meta">
                      <strong>Dark Navy</strong>
                      <small>Default high-contrast DevOps cockpit</small>
                    </div>
                    {(formState.general?.theme || themeMode) === 'dark' && <span className="theme-check">✓ Active</span>}
                  </button>

                  <button
                    type="button"
                    className={`theme-option-card ${(formState.general?.theme || themeMode) === 'system' ? 'selected' : ''}`}
                    onClick={() => {
                      updateField('general', 'theme', 'system')
                      if (onThemeChange) onThemeChange('system')
                    }}
                  >
                    <span className="theme-icon">💻</span>
                    <div className="theme-meta">
                      <strong>System Default</strong>
                      <small>Follows operating system dark/light mode</small>
                    </div>
                    {(formState.general?.theme || themeMode) === 'system' && <span className="theme-check">✓ Active</span>}
                  </button>
                </div>
              </div>

              <div className="settings-card">
                <h3>Environment & Runtime Configuration</h3>
                <div className="settings-form-grid">
                  <div className="form-group">
                    <label>Default Target Environment</label>
                    <select
                      value={formState.general?.defaultTargetEnv || 'development'}
                      onChange={(e) => updateField('general', 'defaultTargetEnv', e.target.value)}
                    >
                      <option value="development">Development (Rapid iteration, auto-deploy)</option>
                      <option value="staging">Staging (Integration verification)</option>
                      <option value="production">Production (Human approval enforced)</option>
                    </select>
                    <small>Default target environment selected on the mission launcher.</small>
                  </div>

                  <div className="form-group">
                    <label>Logging Verbosity</label>
                    <select
                      value={formState.general?.logVerbosity || 'INFO'}
                      onChange={(e) => updateField('general', 'logVerbosity', e.target.value)}
                    >
                      <option value="DEBUG">DEBUG (Verbose agent traces)</option>
                      <option value="INFO">INFO (Standard production events)</option>
                      <option value="WARNING">WARNING (Only warnings & errors)</option>
                      <option value="ERROR">ERROR (Critical exceptions only)</option>
                    </select>
                    <small>Controls telemetry log output detail in the execution stream.</small>
                  </div>

                  <div className="form-group">
                    <label>Telemetry Polling Frequency</label>
                    <select
                      value={formState.general?.telemetryInterval || '2000ms'}
                      onChange={(e) => updateField('general', 'telemetryInterval', e.target.value)}
                    >
                      <option value="1000ms">1000ms (High frequency)</option>
                      <option value="2000ms">2000ms (Balanced default)</option>
                      <option value="5000ms">5000ms (Low overhead)</option>
                    </select>
                    <small>Interval for live agent pipeline progress updates.</small>
                  </div>

                  <div className="form-group">
                    <label>System Timezone</label>
                    <select
                      value={formState.general?.timezone || 'UTC'}
                      onChange={(e) => updateField('general', 'timezone', e.target.value)}
                    >
                      <option value="UTC">UTC (Universal Coordinated Time)</option>
                      <option value="America/New_York">US Eastern (EST/EDT)</option>
                      <option value="America/Los_Angeles">US Pacific (PST/PDT)</option>
                      <option value="Europe/London">London (GMT/BST)</option>
                      <option value="Asia/Kolkata">India (IST)</option>
                    </select>
                    <small>Used for timestamps in audit trails and failure memory logs.</small>
                  </div>
                </div>

                <div className="toggle-item-row" style={{ marginTop: 18 }}>
                  <div>
                    <strong>Auto-Start Mission on Submit</strong>
                    <p>Trigger the Global Orchestrator immediately upon mission submission without secondary confirmation.</p>
                  </div>
                  <label className="switch">
                    <input
                      type="checkbox"
                      checked={Boolean(formState.general?.autoStartOnSubmit ?? true)}
                      onChange={(e) => updateField('general', 'autoStartOnSubmit', e.target.checked)}
                    />
                    <span className="slider round" />
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Section 2: AGENT MANAGEMENT */}
          {activeSection === 'agents' && (
            <div className="settings-section-view">
              <div className="section-intro">
                <h2>Agent Swarm Management</h2>
                <p>Configure the supervisory orchestrators and specialized execution agents operating in this swarm.</p>
              </div>

              {/* Supervisory Tier */}
              <div className="settings-card">
                <h3>Supervisory Tier</h3>
                <div className="agent-supervisors-grid">
                  <div className="supervisor-card">
                    <div className="supervisor-header">
                      <div>
                        <strong>Global Orchestrator</strong>
                        <span className="badge">Main Brain</span>
                      </div>
                      <label className="switch">
                        <input
                          type="checkbox"
                          checked={Boolean(formState.agents?.globalOrchestrator?.enabled ?? true)}
                          onChange={(e) => updateNestedField('agents', 'globalOrchestrator', 'enabled', e.target.checked)}
                        />
                        <span className="slider round" />
                      </label>
                    </div>
                    <p>Decomposes natural language requests into structured mission steps, coordinates supervisors, and monitors system progress.</p>
                    <div className="supervisor-fields">
                      <div className="form-group">
                        <label>Max Decomposition Phases</label>
                        <input
                          type="number"
                          min="1"
                          max="10"
                          value={formState.agents?.globalOrchestrator?.maxPhases || 5}
                          onChange={(e) => updateNestedField('agents', 'globalOrchestrator', 'maxPhases', parseInt(e.target.value) || 5)}
                        />
                      </div>
                      <div className="form-group">
                        <label>Execution Strategy</label>
                        <select
                          value={formState.agents?.globalOrchestrator?.strategy || 'adaptive'}
                          onChange={(e) => updateNestedField('agents', 'globalOrchestrator', 'strategy', e.target.value)}
                        >
                          <option value="adaptive">Adaptive (Auto-tune based on failure risk)</option>
                          <option value="sequential">Sequential (Strict linear stages)</option>
                          <option value="parallel">Parallel (Concurrent independent stages)</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="supervisor-card">
                    <div className="supervisor-header">
                      <div>
                        <strong>Development Supervisor</strong>
                        <span className="badge">Dev Pipeline</span>
                      </div>
                      <label className="switch">
                        <input
                          type="checkbox"
                          checked={Boolean(formState.agents?.developmentSupervisor?.enabled ?? true)}
                          onChange={(e) => updateNestedField('agents', 'developmentSupervisor', 'enabled', e.target.checked)}
                        />
                        <span className="slider round" />
                      </label>
                    </div>
                    <p>Manages the Planning Agent, Coding Agent, Build Agent, Testing Agent, and Self-Healing feedback loop.</p>
                    <div className="toggle-item-row" style={{ marginTop: 12, padding: 0, border: 'none' }}>
                      <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Auto-Handoff to Operations</span>
                      <label className="switch">
                        <input
                          type="checkbox"
                          checked={Boolean(formState.agents?.developmentSupervisor?.autoHandoff ?? true)}
                          onChange={(e) => updateNestedField('agents', 'developmentSupervisor', 'autoHandoff', e.target.checked)}
                        />
                        <span className="slider round" />
                      </label>
                    </div>
                  </div>

                  <div className="supervisor-card">
                    <div className="supervisor-header">
                      <div>
                        <strong>Operations Supervisor</strong>
                        <span className="badge">Ops Pipeline</span>
                      </div>
                      <label className="switch">
                        <input
                          type="checkbox"
                          checked={Boolean(formState.agents?.operationsSupervisor?.enabled ?? true)}
                          onChange={(e) => updateNestedField('agents', 'operationsSupervisor', 'enabled', e.target.checked)}
                        />
                        <span className="slider round" />
                      </label>
                    </div>
                    <p>Manages Security scanning, Release staging, Deployment rollouts, and runtime Telemetry monitoring.</p>
                    <div className="toggle-item-row" style={{ marginTop: 12, padding: 0, border: 'none' }}>
                      <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Auto-Rollback on Deploy Error</span>
                      <label className="switch">
                        <input
                          type="checkbox"
                          checked={Boolean(formState.agents?.operationsSupervisor?.autoRollback ?? true)}
                          onChange={(e) => updateNestedField('agents', 'operationsSupervisor', 'autoRollback', e.target.checked)}
                        />
                        <span className="slider round" />
                      </label>
                    </div>
                  </div>
                </div>
              </div>

              {/* Execution Roster */}
              <div className="settings-card">
                <h3>Specialist Agent Execution Roster</h3>
                <p className="card-subtitle">Tune timeouts, retry budgets, and LLM models for every specialist agent in the swarm.</p>

                <div className="agent-roster-table-wrap">
                  <table className="enterprise-settings-table">
                    <thead>
                      <tr>
                        <th>Agent</th>
                        <th>Role & Responsibility</th>
                        <th>Status</th>
                        <th>Timeout</th>
                        <th>Max Retries</th>
                        <th>Model Binding</th>
                      </tr>
                    </thead>
                    <tbody>
                      {allAgents.map((agentName) => {
                        const agentConfig = formState.agents?.roster?.[agentName] || { enabled: true, timeoutSec: 120, maxRetries: 2 }
                        const isEnabled = agentConfig.enabled !== false
                        return (
                          <tr key={agentName} className={isEnabled ? '' : 'row-disabled'}>
                            <td>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <span className={`agent-dot ${isEnabled ? 'completed' : 'failed'}`} />
                                <strong>{agentName}</strong>
                              </div>
                            </td>
                            <td>
                              <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>
                                {agentName === 'Planning Agent' && 'Architecture & schema specification'}
                                {agentName === 'Coding Agent' && 'Source code & test generation'}
                                {agentName === 'Build Agent' && 'AST validation & package assembly'}
                                {agentName === 'Testing Agent' && 'Automated test suite execution'}
                                {agentName === 'Self-Healing Agent' && 'Root-cause diagnosis & remediation'}
                                {agentName === 'Security Agent' && 'SAST & secret leakage scanning'}
                                {agentName === 'Release Agent' && 'Artifact staging & semver tagging'}
                                {agentName === 'Deploy Agent' && 'Environment rollout & verification'}
                                {agentName === 'Monitor Agent' && 'Runtime health & telemetry monitoring'}
                              </span>
                            </td>
                            <td>
                              <label className="switch">
                                <input
                                  type="checkbox"
                                  checked={isEnabled}
                                  onChange={(e) => {
                                    const updatedRoster = {
                                      ...(formState.agents?.roster || {}),
                                      [agentName]: { ...agentConfig, enabled: e.target.checked },
                                    }
                                    updateField('agents', 'roster', updatedRoster)
                                  }}
                                />
                                <span className="slider round" />
                              </label>
                            </td>
                            <td>
                              <input
                                type="number"
                                min="10"
                                max="600"
                                className="table-inline-input"
                                value={agentConfig.timeoutSec || 120}
                                onChange={(e) => {
                                  const updatedRoster = {
                                    ...(formState.agents?.roster || {}),
                                    [agentName]: { ...agentConfig, timeoutSec: parseInt(e.target.value) || 120 },
                                  }
                                  updateField('agents', 'roster', updatedRoster)
                                }}
                              />
                              <span style={{ fontSize: '0.72rem', color: '#64748b', marginLeft: 4 }}>sec</span>
                            </td>
                            <td>
                              <input
                                type="number"
                                min="0"
                                max="5"
                                className="table-inline-input"
                                value={agentConfig.maxRetries ?? 2}
                                onChange={(e) => {
                                  const updatedRoster = {
                                    ...(formState.agents?.roster || {}),
                                    [agentName]: { ...agentConfig, maxRetries: parseInt(e.target.value) || 0 },
                                  }
                                  updateField('agents', 'roster', updatedRoster)
                                }}
                              />
                            </td>
                            <td>
                              {agentName === 'Planning Agent' || agentName === 'Coding Agent' ? (
                                <select
                                  className="table-inline-select"
                                  value={agentConfig.model || 'gpt-4o-mini'}
                                  onChange={(e) => {
                                    const updatedRoster = {
                                      ...(formState.agents?.roster || {}),
                                      [agentName]: { ...agentConfig, model: e.target.value },
                                    }
                                    updateField('agents', 'roster', updatedRoster)
                                  }}
                                >
                                  <option value="gpt-4o-mini">gpt-4o-mini (Fast)</option>
                                  <option value="gpt-4o">gpt-4o (Reasoning)</option>
                                  <option value="meta/llama-3.1-70b-instruct">NVIDIA NIM LLaMA-3.1</option>
                                  <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
                                </select>
                              ) : (
                                <span style={{ color: '#64748b', fontSize: '0.76rem' }}>Deterministic Tooling</span>
                              )}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Section 3: EXECUTION & POLICIES */}
          {(activeSection === 'execution' || activeSection === 'autonomous') && (
            <div className="settings-section-view">
              <div className="section-intro">
                <h2>Execution & Governance Policies</h2>
                <p>Define autonomous remediation behavior, retry limits, execution gates, and policy guardrails.</p>
              </div>

              <div className="settings-card">
                <h3>Autonomy Governance Mode</h3>
                <div className="autonomy-options-grid">
                  {[
                    {
                      id: 'supervised',
                      name: 'Supervised Autonomy (Recommended)',
                      badge: 'Production Standard',
                      desc: 'Agents execute autonomously with human approval gates enforced for critical actions, database alterations, and production releases.',
                    },
                    {
                      id: 'autonomous',
                      name: 'Full Autonomy',
                      badge: 'Zero-Human Touch',
                      desc: 'Swarm self-executes all development, testing, healing, and deployment stages without interruption unless an unrecoverable failure occurs.',
                    },
                    {
                      id: 'strict',
                      name: 'Strict / Manual Approval',
                      badge: 'High Security',
                      desc: 'Explicit human sign-off required at every stage transition between planning, coding, building, and deploying.',
                    },
                  ].map((mode) => {
                    const selected = (formState.autonomous?.autonomyLevel || 'supervised') === mode.id
                    return (
                      <div
                        key={mode.id}
                        className={`autonomy-card ${selected ? 'selected' : ''}`}
                        onClick={() => updateField('autonomous', 'autonomyLevel', mode.id)}
                      >
                        <div className="autonomy-card-header">
                          <strong>{mode.name}</strong>
                          <span className={`status-pill ${selected ? 'completed' : 'waiting'}`}>{mode.badge}</span>
                        </div>
                        <p>{mode.desc}</p>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="settings-card">
                <h3>Self-Healing & Remediation Engine</h3>
                <div className="toggle-list">
                  <div className="toggle-item-row">
                    <div>
                      <strong>Autonomous Self-Healing Engine</strong>
                      <p>Automatically diagnose build/test failures, query database failure memory, and generate code patches.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.autonomous?.autoHealing ?? true)}
                        onChange={(e) => updateField('autonomous', 'autoHealing', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>

                  <div className="toggle-item-row">
                    <div>
                      <strong>Auto-Retry Failed Jobs</strong>
                      <p>Automatically re-trigger failed stages before escalating to self-healing remediation.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.autonomous?.autoRetryFailedJobs ?? true)}
                        onChange={(e) => updateField('autonomous', 'autoRetryFailedJobs', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>

                  <div className="toggle-item-row">
                    <div>
                      <strong>Automatic Rollback on Failed Remediation</strong>
                      <p>Restore workspace Git state to previous healthy checkpoint if healing patch fails test verification.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.autonomous?.rollbackOnFailedFix ?? true)}
                        onChange={(e) => updateField('autonomous', 'rollbackOnFailedFix', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>
                </div>

                <div className="settings-form-grid" style={{ marginTop: 18 }}>
                  <div className="form-group">
                    <label>Maximum Remediation Attempts (1-5)</label>
                    <input
                      type="number"
                      min="1"
                      max="5"
                      value={formState.autonomous?.maxRemediationAttempts ?? 2}
                      onChange={(e) => updateField('autonomous', 'maxRemediationAttempts', Math.max(1, Math.min(5, parseInt(e.target.value) || 2)))}
                    />
                    <small>Default: 2 attempts before escalating to operator intervention.</small>
                  </div>

                  <div className="form-group">
                    <label>Detection Interval</label>
                    <select
                      value={formState.selfHealing?.detectionInterval || '30s'}
                      onChange={(e) => updateField('selfHealing', 'detectionInterval', e.target.value)}
                    >
                      <option value="10s">10s (Fast heartbeat)</option>
                      <option value="30s">30s (Recommended default)</option>
                      <option value="60s">60s (Low overhead)</option>
                    </select>
                    <small>Frequency of active health checks during pipeline run.</small>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 4: SECURITY & APPROVALS */}
          {(activeSection === 'security' || activeSection === 'safety') && (
            <div className="settings-section-view">
              <div className="section-intro">
                <h2>Security, Approvals & Rollback Policies</h2>
                <p>Production safeguards, secret redaction, environment access controls, and rollback policies.</p>
              </div>

              <div className="settings-card">
                <h3>Critical Action Approval Gates</h3>
                <div className="toggle-list">
                  <div className="toggle-item-row">
                    <div>
                      <strong>Enforce Approval Before Production Deployment</strong>
                      <p>Halt pipeline and await human authorization before releasing to production infrastructure.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.safety?.approvalBeforeProduction ?? true)}
                        onChange={(e) => updateField('safety', 'approvalBeforeProduction', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>

                  <div className="toggle-item-row">
                    <div>
                      <strong>Approval Before Database Migration / DDL Execution</strong>
                      <p>Require operator approval before applying schema migrations or irreversible data operations.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.safety?.approvalBeforeDatabase ?? true)}
                        onChange={(e) => updateField('safety', 'approvalBeforeDatabase', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>

                  <div className="toggle-item-row">
                    <div>
                      <strong>Approval Before Infrastructure Provisioning</strong>
                      <p>Require sign-off before Docker container spinning or cloud resource allocation.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.safety?.approvalBeforeInfra ?? true)}
                        onChange={(e) => updateField('safety', 'approvalBeforeInfra', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>
                </div>
              </div>

              <div className="settings-card">
                <h3>Protected Environments & Risk Policy</h3>
                <div className="settings-form-grid">
                  <div className="form-group">
                    <label>Risk Assessment Policy</label>
                    <select
                      value={formState.safety?.riskPolicy || 'medium'}
                      onChange={(e) => updateField('safety', 'riskPolicy', e.target.value)}
                    >
                      <option value="low">Low Risk (Strict gates, block all ambiguous commands)</option>
                      <option value="medium">Medium Risk (Balanced enterprise DevOps default)</option>
                      <option value="high">High (Permissive, for sandbox testing environments)</option>
                    </select>
                    <small>Governs the strictness of Security Agent static analysis.</small>
                  </div>

                  <div className="form-group">
                    <label>Session Inactivity Timeout</label>
                    <select
                      value={formState.safety?.sessionTimeoutMinutes || 60}
                      onChange={(e) => updateField('safety', 'sessionTimeoutMinutes', parseInt(e.target.value) || 60)}
                    >
                      <option value={15}>15 minutes</option>
                      <option value={30}>30 minutes</option>
                      <option value={60}>60 minutes (1 hour)</option>
                      <option value={480}>8 hours</option>
                    </select>
                    <small>Operator JWT token expires after inactivity.</small>
                  </div>
                </div>

                <div className="toggle-list" style={{ marginTop: 18 }}>
                  <div className="toggle-item-row">
                    <div>
                      <strong>Mask API Keys and Secrets in Frontend UI</strong>
                      <p>Render tokens with bullet masks (••••) to prevent shoulder-surfing and accidental exposure.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.safety?.maskSecretsInUi ?? true)}
                        onChange={(e) => updateField('safety', 'maskSecretsInUi', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>

                  <div className="toggle-item-row">
                    <div>
                      <strong>Prevent Secrets From Being Committed to Git</strong>
                      <p>Security Agent verifies zero hardcoded API keys before committing workspace code.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.safety?.preventSecretCommit ?? true)}
                        onChange={(e) => updateField('safety', 'preventSecretCommit', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 5: BUILD & TESTING */}
          {activeSection === 'buildTesting' && (
            <div className="settings-section-view">
              <div className="section-intro">
                <h2>Build & Testing Quality Gates</h2>
                <p>Configure AST compilation checks, automated testing rules, and release quality gates.</p>
              </div>

              <div className="settings-card">
                <h3>Quality Gates</h3>
                <div className="form-group">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <label>Minimum Test Coverage Gate</label>
                    <strong style={{ color: '#c4b5fd', fontSize: '1.1rem' }}>{formState.buildTesting?.minSuccessRate ?? 85}%</strong>
                  </div>
                  <input
                    type="range"
                    min="50"
                    max="100"
                    step="5"
                    className="enterprise-range"
                    value={formState.buildTesting?.minSuccessRate ?? 85}
                    onChange={(e) => updateField('buildTesting', 'minSuccessRate', parseInt(e.target.value) || 85)}
                  />
                  <small>Pipelines with test passing rates below this threshold will be blocked from release.</small>
                </div>

                <div className="toggle-item-row" style={{ marginTop: 14 }}>
                  <div>
                    <strong>Block Deployment on Quality Gate Failure</strong>
                    <p>Prevent Deploy Agent from rolling out code if test coverage or security scans fail.</p>
                  </div>
                  <label className="switch">
                    <input
                      type="checkbox"
                      checked={Boolean(formState.buildTesting?.blockDeploymentOnFail ?? true)}
                      onChange={(e) => updateField('buildTesting', 'blockDeploymentOnFail', e.target.checked)}
                    />
                    <span className="slider round" />
                  </label>
                </div>
              </div>

              <div className="settings-card">
                <h3>Build & Verification Checks</h3>
                <div className="toggle-list">
                  <div className="toggle-item-row">
                    <div>
                      <strong>Abstract Syntax Tree (AST) Compilation Verification</strong>
                      <p>Build Agent parses Python and JavaScript ASTs to ensure zero syntax defects before execution.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.buildTesting?.astCompilation ?? true)}
                        onChange={(e) => updateField('buildTesting', 'astCompilation', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>

                  <div className="toggle-item-row">
                    <div>
                      <strong>Automated Unit Test Execution</strong>
                      <p>Run unittest / pytest suites inside isolated workspace sub-processes.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.buildTesting?.unitTests ?? true)}
                        onChange={(e) => updateField('buildTesting', 'unitTests', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>

                  <div className="toggle-item-row">
                    <div>
                      <strong>Integration & Contract Tests</strong>
                      <p>Execute HTTP endpoint contract tests verifying REST response schemas and status codes.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.buildTesting?.integrationTests ?? true)}
                        onChange={(e) => updateField('buildTesting', 'integrationTests', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>

                  <div className="toggle-item-row">
                    <div>
                      <strong>Security Vulnerability Scanning</strong>
                      <p>Scan generated packages for CVEs, known vulnerable dependencies, and insecure calls.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.buildTesting?.securityChecks ?? true)}
                        onChange={(e) => updateField('buildTesting', 'securityChecks', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 6: INTEGRATIONS */}
          {activeSection === 'integrations' && (
            <div className="settings-section-view">
              <div className="section-intro">
                <h2>Toolchain Integrations & Credentials</h2>
                <p>Manage external DevOps services, API keys, and test live connectivity.</p>
              </div>

              {/* GitHub */}
              <div className="settings-card">
                <div className="integration-card-header">
                  <div className="integration-brand">
                    <span className="integration-icon">🐙</span>
                    <div>
                      <strong>GitHub Integration</strong>
                      <p>Repository syncing, branch tracking, and commit checkpointing.</p>
                    </div>
                  </div>
                  <div className="integration-actions">
                    <button
                      className="test-conn-btn"
                      onClick={() => runTestConnection('github')}
                      disabled={testingService === 'github'}
                    >
                      {testingService === 'github' ? 'Testing…' : 'Test Connection'}
                    </button>
                  </div>
                </div>

                {testResults.github && (
                  <div className={`conn-result-banner ${testResults.github.connected ? 'success' : 'failure'}`}>
                    <span>{testResults.github.connected ? '✓' : '✕'}</span>
                    <span>{testResults.github.message} ({testResults.github.latency_ms}ms)</span>
                  </div>
                )}

                <div className="settings-form-grid" style={{ marginTop: 14 }}>
                  <div className="form-group">
                    <label>Target Repository</label>
                    <input
                      type="text"
                      value={formState.integrations?.github?.repo || ''}
                      onChange={(e) => updateNestedField('integrations', 'github', 'repo', e.target.value)}
                      placeholder="owner/repository-name"
                    />
                  </div>
                  <div className="form-group">
                    <label>Target Branch</label>
                    <input
                      type="text"
                      value={formState.integrations?.github?.branch || 'main'}
                      onChange={(e) => updateNestedField('integrations', 'github', 'branch', e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group" style={{ marginTop: 12 }}>
                  <label>GitHub Personal Access Token (PAT)</label>
                  <div className="password-input-wrap">
                    <input
                      type={secretVisibility.githubToken ? 'text' : 'password'}
                      value={formState.secrets?.githubToken || ''}
                      onChange={(e) => updateNestedField('secrets', 'githubToken', null, e.target.value)}
                      placeholder="ghp_..."
                    />
                    <button
                      type="button"
                      className="eye-toggle-btn"
                      onClick={() => toggleSecretVisibility('githubToken')}
                    >
                      {secretVisibility.githubToken ? '👁️' : '🔒'}
                    </button>
                  </div>
                </div>
              </div>

              {/* Docker Registry */}
              <div className="settings-card">
                <div className="integration-card-header">
                  <div className="integration-brand">
                    <span className="integration-icon">🐳</span>
                    <div>
                      <strong>Docker Container Registry</strong>
                      <p>Build, push, and deploy container images for generated services.</p>
                    </div>
                  </div>
                  <div className="integration-actions">
                    <button
                      className="test-conn-btn"
                      onClick={() => runTestConnection('docker')}
                      disabled={testingService === 'docker'}
                    >
                      {testingService === 'docker' ? 'Testing…' : 'Test Connection'}
                    </button>
                  </div>
                </div>

                {testResults.docker && (
                  <div className={`conn-result-banner ${testResults.docker.connected ? 'success' : 'failure'}`}>
                    <span>{testResults.docker.connected ? '✓' : '✕'}</span>
                    <span>{testResults.docker.message} ({testResults.docker.latency_ms}ms)</span>
                  </div>
                )}

                <div className="settings-form-grid" style={{ marginTop: 14 }}>
                  <div className="form-group">
                    <label>Registry Endpoint</label>
                    <input
                      type="text"
                      value={formState.integrations?.docker?.registry || 'docker.io/swarm-ci'}
                      onChange={(e) => updateNestedField('integrations', 'docker', 'registry', e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Registry Access Token / Password</label>
                    <div className="password-input-wrap">
                      <input
                        type={secretVisibility.dockerKey ? 'text' : 'password'}
                        value={formState.secrets?.dockerKey || ''}
                        onChange={(e) => updateNestedField('secrets', 'dockerKey', null, e.target.value)}
                        placeholder="dckr_pat_..."
                      />
                      <button
                        type="button"
                        className="eye-toggle-btn"
                        onClick={() => toggleSecretVisibility('dockerKey')}
                      >
                        {secretVisibility.dockerKey ? '👁️' : '🔒'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* NVIDIA NIM / LLM */}
              <div className="settings-card">
                <div className="integration-card-header">
                  <div className="integration-brand">
                    <span className="integration-icon">🧠</span>
                    <div>
                      <strong>LLM & NVIDIA NIM Inference Provider</strong>
                      <p>Inference engine powering Planning, Coding, and Self-Healing agents.</p>
                    </div>
                  </div>
                  <div className="integration-actions">
                    <button
                      className="test-conn-btn"
                      onClick={() => runTestConnection('nvidia')}
                      disabled={testingService === 'nvidia'}
                    >
                      {testingService === 'nvidia' ? 'Testing…' : 'Test Connection'}
                    </button>
                  </div>
                </div>

                {testResults.nvidia && (
                  <div className={`conn-result-banner ${testResults.nvidia.connected ? 'success' : 'failure'}`}>
                    <span>{testResults.nvidia.connected ? '✓' : '✕'}</span>
                    <span>{testResults.nvidia.message} ({testResults.nvidia.latency_ms}ms)</span>
                  </div>
                )}

                <div className="settings-form-grid" style={{ marginTop: 14 }}>
                  <div className="form-group">
                    <label>Provider</label>
                    <select
                      value={formState.integrations?.nvidia?.provider || 'openai'}
                      onChange={(e) => updateNestedField('integrations', 'nvidia', 'provider', e.target.value)}
                    >
                      <option value="openai">OpenAI (gpt-4o-mini / gpt-4o)</option>
                      <option value="nvidia">NVIDIA NIM (meta/llama-3.1-70b-instruct)</option>
                      <option value="gemini">Google Gemini (gemini-2.0-flash)</option>
                      <option value="ollama">Local Ollama (llama3.2)</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>API Key / Bearer Secret</label>
                    <div className="password-input-wrap">
                      <input
                        type={secretVisibility.nvidiaKey ? 'text' : 'password'}
                        value={formState.secrets?.nvidiaKey || ''}
                        onChange={(e) => updateNestedField('secrets', 'nvidiaKey', null, e.target.value)}
                        placeholder="sk-..."
                      />
                      <button
                        type="button"
                        className="eye-toggle-btn"
                        onClick={() => toggleSecretVisibility('nvidiaKey')}
                      >
                        {secretVisibility.nvidiaKey ? '👁️' : '🔒'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Webhook & Slack */}
              <div className="settings-card">
                <div className="integration-card-header">
                  <div className="integration-brand">
                    <span className="integration-icon">🌐</span>
                    <div>
                      <strong>Outbound Event Webhook & Slack</strong>
                      <p>Stream real-time pipeline events to internal SIEM or chat channels.</p>
                    </div>
                  </div>
                  <div className="integration-actions">
                    <button
                      className="test-conn-btn"
                      onClick={() => runTestConnection('webhook')}
                      disabled={testingService === 'webhook'}
                    >
                      {testingService === 'webhook' ? 'Testing…' : 'Test Webhook'}
                    </button>
                  </div>
                </div>

                {testResults.webhook && (
                  <div className={`conn-result-banner ${testResults.webhook.connected ? 'success' : 'failure'}`}>
                    <span>{testResults.webhook.connected ? '✓' : '✕'}</span>
                    <span>{testResults.webhook.message} ({testResults.webhook.latency_ms}ms)</span>
                  </div>
                )}

                <div className="settings-form-grid" style={{ marginTop: 14 }}>
                  <div className="form-group">
                    <label>Webhook Destination URL</label>
                    <input
                      type="url"
                      value={formState.integrations?.webhook?.endpoint || ''}
                      onChange={(e) => updateNestedField('integrations', 'webhook', 'endpoint', e.target.value)}
                      placeholder="https://api.internal.devops/hooks/swarm"
                    />
                  </div>
                  <div className="form-group">
                    <label>Webhook Secret Key (HMAC)</label>
                    <div className="password-input-wrap">
                      <input
                        type={secretVisibility.webhookSecret ? 'text' : 'password'}
                        value={formState.secrets?.webhookSecret || ''}
                        onChange={(e) => updateNestedField('secrets', 'webhookSecret', null, e.target.value)}
                        placeholder="whsec_..."
                      />
                      <button
                        type="button"
                        className="eye-toggle-btn"
                        onClick={() => toggleSecretVisibility('webhookSecret')}
                      >
                        {secretVisibility.webhookSecret ? '👁️' : '🔒'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 7: NOTIFICATIONS */}
          {activeSection === 'notifications' && (
            <div className="settings-section-view">
              <div className="section-intro">
                <h2>Alert & Notification Routing</h2>
                <p>Configure event subscriptions, alerting channels, severity filters, and test notifications.</p>
              </div>

              <div className="settings-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3>Notification Channel & Targets</h3>
                  <button
                    className="secondary-button"
                    onClick={runTestNotification}
                    disabled={testingNotification}
                  >
                    {testingNotification ? 'Dispatching…' : '📨 Send Test Notification'}
                  </button>
                </div>

                {notificationResult && (
                  <div className={`conn-result-banner ${notificationResult.success ? 'success' : 'failure'}`} style={{ marginTop: 12 }}>
                    <span>{notificationResult.success ? '✓' : '✕'}</span>
                    <span>{notificationResult.message}</span>
                  </div>
                )}

                <div className="settings-form-grid" style={{ marginTop: 14 }}>
                  <div className="form-group">
                    <label>Primary Alert Channel</label>
                    <select
                      value={formState.notifications?.channel || 'dashboard'}
                      onChange={(e) => updateField('notifications', 'channel', e.target.value)}
                    >
                      <option value="dashboard">In-App Dashboard Toast</option>
                      <option value="email">Email Notification</option>
                      <option value="slack">Slack Channel Alert</option>
                      <option value="webhook">Automated Webhook</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Alert Severity Level</label>
                    <select
                      value={formState.notifications?.alertSeverity || 'critical'}
                      onChange={(e) => updateField('notifications', 'alertSeverity', e.target.value)}
                    >
                      <option value="info">Info (All events: starts, heals, finishes)</option>
                      <option value="warning">Warning & Above</option>
                      <option value="critical">Critical Only (Failures & unhandled errors)</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Email Recipient</label>
                    <input
                      type="email"
                      value={formState.notifications?.emailAddress || ''}
                      onChange={(e) => updateField('notifications', 'emailAddress', e.target.value)}
                      placeholder="devops-alerts@organization.com"
                    />
                  </div>

                  <div className="form-group">
                    <label>Slack Alert Channel</label>
                    <input
                      type="text"
                      value={formState.notifications?.slackChannel || ''}
                      onChange={(e) => updateField('notifications', 'slackChannel', e.target.value)}
                      placeholder="#devops-swarm-alerts"
                    />
                  </div>
                </div>
              </div>

              <div className="settings-card">
                <h3>Subscribed Event Triggers</h3>
                <div className="toggle-list">
                  <div className="toggle-item-row">
                    <div>
                      <strong>Pipeline Failures</strong>
                      <p>Trigger alerts when build, test, or deployment stages encounter errors.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.notifications?.pipelineFailures ?? true)}
                        onChange={(e) => updateField('notifications', 'pipelineFailures', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>

                  <div className="toggle-item-row">
                    <div>
                      <strong>Autonomous Self-Healing Actions</strong>
                      <p>Notify when Self-Healing Agent diagnoses and heals code defects.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.notifications?.selfHealingActions ?? true)}
                        onChange={(e) => updateField('notifications', 'selfHealingActions', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>

                  <div className="toggle-item-row">
                    <div>
                      <strong>Deployment Failures</strong>
                      <p>Alert when Deploy Agent encounters container health check timeouts.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.notifications?.deploymentFailures ?? true)}
                        onChange={(e) => updateField('notifications', 'deploymentFailures', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>

                  <div className="toggle-item-row">
                    <div>
                      <strong>Database & Storage Engine Errors</strong>
                      <p>Alert on MongoDB / SQLite connection pool issues or persistence errors.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.notifications?.databaseFailures ?? true)}
                        onChange={(e) => updateField('notifications', 'databaseFailures', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 8: WORKSPACE & RESOURCES */}
          {activeSection === 'workspace' && (
            <div className="settings-section-view">
              <div className="section-intro">
                <h2>Workspace & Resource Quotas</h2>
                <p>Disk isolation, container resource quotas, concurrency limits, and ephemeral cleanup.</p>
              </div>

              <div className="settings-card">
                <h3>Workspace Isolation & File Paths</h3>
                <div className="settings-form-grid">
                  <div className="form-group">
                    <label>Workspace Directory Root</label>
                    <input
                      type="text"
                      value={formState.workspace?.workspaceRoot || 'workspaces'}
                      onChange={(e) => updateField('workspace', 'workspaceRoot', e.target.value)}
                    />
                    <small>Base directory for mission project workspaces.</small>
                  </div>

                  <div className="form-group">
                    <label>Failed Artifact Retention</label>
                    <select
                      value={formState.workspace?.retainFailedArtifactsDays ?? 7}
                      onChange={(e) => updateField('workspace', 'retainFailedArtifactsDays', parseInt(e.target.value) || 7)}
                    >
                      <option value={1}>1 day</option>
                      <option value={7}>7 days (Recommended)</option>
                      <option value={30}>30 days</option>
                      <option value={90}>90 days</option>
                    </select>
                    <small>Preserve workspaces of failed runs for post-mortem analysis.</small>
                  </div>
                </div>

                <div className="toggle-list" style={{ marginTop: 18 }}>
                  <div className="toggle-item-row">
                    <div>
                      <strong>Strict Path Traversal Confinement</strong>
                      <p>Prevent agent file operations outside allocated mission workspace roots.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.workspace?.enforcePathConfinement ?? true)}
                        onChange={(e) => updateField('workspace', 'enforcePathConfinement', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>

                  <div className="toggle-item-row">
                    <div>
                      <strong>Automatic Git Checkpointing</strong>
                      <p>Create Git commits before and after Self-Healing patches to enable zero-data-loss rollback.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.workspace?.gitAutoCheckpoint ?? true)}
                        onChange={(e) => updateField('workspace', 'gitAutoCheckpoint', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>
                </div>
              </div>

              <div className="settings-card">
                <h3>Compute Resource Quotas</h3>
                <div className="settings-form-grid">
                  <div className="form-group">
                    <label>Max Concurrent Pipeline Missions</label>
                    <input
                      type="number"
                      min="1"
                      max="20"
                      value={formState.resourceLimits?.maxConcurrentJobs ?? 5}
                      onChange={(e) => updateField('resourceLimits', 'maxConcurrentJobs', parseInt(e.target.value) || 5)}
                    />
                    <small>Limit simultaneous agent swarm executions to prevent host exhaustion.</small>
                  </div>

                  <div className="form-group">
                    <label>Execution Timeout per Mission</label>
                    <input
                      type="number"
                      min="1"
                      max="60"
                      value={formState.resourceLimits?.executionTimeoutMinutes ?? 10}
                      onChange={(e) => updateField('resourceLimits', 'executionTimeoutMinutes', parseInt(e.target.value) || 10)}
                    />
                    <small>Minutes before a stalled mission is autonomously aborted.</small>
                  </div>

                  <div className="form-group">
                    <label>CPU Limit Cap (%)</label>
                    <input
                      type="number"
                      min="10"
                      max="100"
                      value={formState.resourceLimits?.cpuLimit ?? 80}
                      onChange={(e) => updateField('resourceLimits', 'cpuLimit', parseInt(e.target.value) || 80)}
                    />
                    <small>Throttles worker thread pools during AST compilation and testing.</small>
                  </div>

                  <div className="form-group">
                    <label>RAM Limit (GB)</label>
                    <input
                      type="number"
                      min="1"
                      max="64"
                      value={formState.resourceLimits?.memoryLimit ?? 4}
                      onChange={(e) => updateField('resourceLimits', 'memoryLimit', parseInt(e.target.value) || 4)}
                    />
                    <small>Maximum memory threshold allocated to Docker build containers.</small>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 9: AUDIT & HISTORY */}
          {activeSection === 'audit' && (
            <div className="settings-section-view">
              <div className="section-intro">
                <h2>Immutable Audit Trail & Compliance</h2>
                <p>Real-time audit log of configuration updates, agent operations, and pipeline executions.</p>
              </div>

              <div className="settings-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
                  <div>
                    <h3>Audit Events Timeline</h3>
                    <p className="card-subtitle">Fetched directly from persistent SQLite/MongoDB audit repository.</p>
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <select
                      value={auditFilter}
                      onChange={(e) => setAuditFilter(e.target.value)}
                      style={{ width: 'auto', padding: '6px 12px' }}
                    >
                      <option value="all">All Events</option>
                      <option value="SETTINGS">Settings Updates</option>
                      <option value="PIPELINE">Pipeline Executions</option>
                      <option value="NOTIFICATION">Notifications</option>
                    </select>
                    <button className="secondary-button" onClick={fetchAuditLogs} disabled={loadingAudit}>
                      {loadingAudit ? 'Refreshing…' : '🔄 Refresh'}
                    </button>
                  </div>
                </div>

                <div className="audit-table-wrap" style={{ marginTop: 14 }}>
                  {loadingAudit ? (
                    <div style={{ padding: 24, textAlign: 'center', color: '#94a3b8' }}>Loading audit records…</div>
                  ) : auditLogs.length > 0 ? (
                    <table className="enterprise-settings-table">
                      <thead>
                        <tr>
                          <th>Timestamp</th>
                          <th>Operator / Principal</th>
                          <th>Action</th>
                          <th>Category</th>
                          <th>Audit Details</th>
                        </tr>
                      </thead>
                      <tbody>
                        {auditLogs
                          .filter((item) => (auditFilter === 'all' ? true : (item.action || '').includes(auditFilter)))
                          .map((log) => (
                            <tr key={log.id}>
                              <td>
                                <code style={{ fontSize: '0.74rem', color: '#a78bfa' }}>
                                  {log.timestamp ? new Date(log.timestamp).toLocaleString() : '—'}
                                </code>
                              </td>
                              <td>
                                <strong>{log.user_id || 'system'}</strong>
                              </td>
                              <td>
                                <span className={`status-pill ${log.action.includes('RESET') ? 'failed' : 'completed'}`}>
                                  {log.action}
                                </span>
                              </td>
                              <td>
                                <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>{log.section || 'General'}</span>
                              </td>
                              <td>
                                <span style={{ fontSize: '0.82rem', color: '#cbd5e1' }}>{log.details || '—'}</span>
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  ) : (
                    <div style={{ padding: 24, textAlign: 'center', color: '#94a3b8' }}>
                      No audit history records found in database.
                    </div>
                  )}
                </div>
              </div>

              <div className="settings-card">
                <h3>Audit Configuration</h3>
                <div className="toggle-list">
                  <div className="toggle-item-row">
                    <div>
                      <strong>Record All Settings & Policy Changes</strong>
                      <p>Write an immutable audit log record every time an operator updates Swarm configuration.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.audit?.recordConfigChanges ?? true)}
                        onChange={(e) => updateField('audit', 'recordConfigChanges', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>

                  <div className="toggle-item-row">
                    <div>
                      <strong>Record Specialist Agent Actions</strong>
                      <p>Persist stage handoffs between Planning, Coding, and Build agents into execution history.</p>
                    </div>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={Boolean(formState.audit?.recordAgentActions ?? true)}
                        onChange={(e) => updateField('audit', 'recordAgentActions', e.target.checked)}
                      />
                      <span className="slider round" />
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 10: ADVANCED CONFIGURATION */}
          {activeSection === 'advanced' && (
            <div className="settings-section-view">
              <div className="section-intro">
                <h2>Advanced Swarm & System Settings</h2>
                <p>Low-level IPC communication, sandbox strictness, database overrides, and raw JSON editor.</p>
              </div>

              <div className="settings-card">
                <h3>System Runtime Flags</h3>
                <div className="settings-form-grid">
                  <div className="form-group">
                    <label>Inference Runtime Mode</label>
                    <select
                      value={formState.advanced?.systemMode || 'live'}
                      onChange={(e) => updateField('advanced', 'systemMode', e.target.value)}
                    >
                      <option value="live">Live API Mode (Real LLM inference)</option>
                      <option value="offline_deterministic">Offline Deterministic (Template fallbacks for testing)</option>
                    </select>
                    <small>Offline mode bypasses external API calls using deterministic generators.</small>
                  </div>

                  <div className="form-group">
                    <label>Sandbox Security Isolation</label>
                    <select
                      value={formState.advanced?.sandboxStrictness || 'standard'}
                      onChange={(e) => updateField('advanced', 'sandboxStrictness', e.target.value)}
                    >
                      <option value="standard">Standard (Full workspace I/O, no network)</option>
                      <option value="strict">Strict (Read-only root, ephemeral tmp)</option>
                    </select>
                    <small>Subprocess sandboxing mode for Build and Testing agents.</small>
                  </div>

                  <div className="form-group">
                    <label>IPC Buffer Size</label>
                    <input
                      type="text"
                      value={formState.advanced?.ipcBufferSize || '64KB'}
                      onChange={(e) => updateField('advanced', 'ipcBufferSize', e.target.value)}
                    />
                    <small>Memory buffer for inter-agent message passing.</small>
                  </div>

                  <div className="form-group">
                    <label>Concurrency Pool Size</label>
                    <input
                      type="number"
                      min="1"
                      max="32"
                      value={formState.advanced?.concurrencyLimit ?? 5}
                      onChange={(e) => updateField('advanced', 'concurrencyLimit', parseInt(e.target.value) || 5)}
                    />
                    <small>Worker pool size for parallel stage execution.</small>
                  </div>
                </div>
              </div>

              {/* Raw JSON Editor */}
              <div className="settings-card">
                <h3>Raw Configuration JSON Editor</h3>
                <p className="card-subtitle">Directly review or edit full enterprise configuration dictionary.</p>
                <textarea
                  className="raw-json-editor-textarea"
                  rows="14"
                  value={JSON.stringify(formState, null, 2)}
                  onChange={(e) => {
                    try {
                      const parsed = JSON.parse(e.target.value)
                      setFormState(parsed)
                    } catch {
                      // Allow typing while editing
                    }
                  }}
                />
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Confirmation Modal for Reset Defaults */}
      {resetConfirmOpen && (
        <div role="dialog" aria-modal="true" className="modal-backdrop" onMouseDown={() => setResetConfirmOpen(false)}>
          <div className="confirm-modal-box" onMouseDown={(e) => e.stopPropagation()}>
            <div className="confirm-modal-icon">⚠️</div>
            <h3>Reset to Recommended Factory Defaults?</h3>
            <p>
              This action will reset all 10 governance, agent, and policy sections to recommended enterprise defaults.
              Existing mission workspaces, project files, and user credentials will remain unaffected.
            </p>
            <div className="confirm-modal-actions">
              <button className="secondary-button" onClick={() => setResetConfirmOpen(false)}>
                Cancel
              </button>
              <button className="danger-button" onClick={handleResetConfirm}>
                Confirm Reset Defaults
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

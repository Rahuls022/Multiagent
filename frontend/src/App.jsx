import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import './App.css'

const apiBase = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'
const developmentAgents = ['Planning Agent', 'Coding Agent', 'Build Agent', 'Testing Agent']
const operationsAgents = ['Security Agent', 'Release Agent', 'Deploy Agent', 'Monitor Agent']
const allAgents = [...developmentAgents, ...operationsAgents]
const implementedAgents = new Set(['Planning Agent', 'Coding Agent'])

function EyeIcon({ visible }) {
  return visible ? (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ) : (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  )
}

function ValidationMark({ valid, className = '' }) {
  return (
    <span
      className={`input-validation-badge ${valid ? 'valid' : 'invalid'} ${className}`}
      title={valid ? 'Valid entry' : 'Invalid entry'}
      aria-label={valid ? 'Valid entry' : 'Invalid entry'}
    >
      {valid ? (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      ) : (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      )}
    </span>
  )
}

function AuthScreen({ onAuthenticated }) {
  const [mode, setMode] = useState('signin')
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '', rememberMe: true })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const nameHasText = form.name.length > 0
  const isNameValid = form.name.trim().length >= 2

  const trimmedEmail = form.email.trim().toLowerCase()
  const emailHasText = form.email.length > 0
  const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/
  const isEmailFormatValid = emailRegex.test(trimmedEmail)
  const isGmailDomainInvalid = trimmedEmail.includes('@gmail.') && !trimmedEmail.endsWith('@gmail.com')
  const isEmailValid = isEmailFormatValid && !isGmailDomainInvalid

  const passwordHasText = form.password.length > 0
  const isPasswordValid = form.password.length >= 8

  const confirmPasswordHasText = form.confirmPassword.length > 0
  const isConfirmPasswordValid = form.confirmPassword.length >= 8 && form.confirmPassword === form.password

  const update = (key) => (event) => {
    setForm({ ...form, [key]: event.target.value })
    if (error) setError('')
  }

  async function submit(event) {
    event.preventDefault()
    setError('')
    setSuccess('')

    const cleanEmail = form.email.trim().toLowerCase()
    const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/
    if (!emailRegex.test(cleanEmail)) {
      return setError('Please enter a valid email address.')
    }
    const emailDomain = cleanEmail.split('@')[1] || ''
    if (emailDomain.startsWith('gmail.') && emailDomain !== 'gmail.com') {
      return setError('Invalid Gmail domain. Only valid @gmail.com addresses are allowed.')
    }

    if (form.password.length < 8) {
      return setError('Password must contain at least 8 characters.')
    }

    if (mode === 'signup') {
      if (!form.name.trim() || form.name.trim().length < 2) {
        return setError('Please enter your full name (at least 2 characters).')
      }
      if (form.password !== form.confirmPassword) {
        return setError('Passwords do not match. Please verify your confirm password field.')
      }
    }

    setSubmitting(true)

    try {
      if (mode === 'signup') {
        const response = await fetch(`${apiBase}/auth/signup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            full_name: form.name.trim(),
            email: cleanEmail,
            password: form.password,
            confirm_password: form.confirmPassword,
          }),
        })

        const data = await response.json()
        if (!response.ok) {
          const detail = typeof data.detail === 'string'
            ? data.detail
            : Array.isArray(data.detail) && data.detail[0]?.msg
              ? data.detail[0].msg
              : 'Failed to create account. Please check your inputs.'
          setError(detail)
          return
        }

        // Store session token permanently
        localStorage.setItem('swarm_token', data.access_token)
        localStorage.setItem('swarm_user', JSON.stringify(data.user))
        sessionStorage.removeItem('swarm_token')
        sessionStorage.removeItem('swarm_user')

        setSuccess('Account created successfully! Entering mission control…')
        setTimeout(() => {
          onAuthenticated(data.user, data.access_token)
        }, 300)
      } else {
        const response = await fetch(`${apiBase}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: cleanEmail,
            password: form.password,
            remember_me: Boolean(form.rememberMe),
          }),
        })

        const data = await response.json()
        if (!response.ok) {
          const detail = typeof data.detail === 'string'
            ? data.detail
            : 'Invalid email or password. Please verify your credentials.'
          setError(detail)
          return
        }

        if (form.rememberMe) {
          localStorage.setItem('swarm_token', data.access_token)
          localStorage.setItem('swarm_user', JSON.stringify(data.user))
          sessionStorage.removeItem('swarm_token')
          sessionStorage.removeItem('swarm_user')
        } else {
          sessionStorage.setItem('swarm_token', data.access_token)
          sessionStorage.setItem('swarm_user', JSON.stringify(data.user))
          localStorage.removeItem('swarm_token')
          localStorage.removeItem('swarm_user')
        }

        onAuthenticated(data.user, data.access_token)
      }
    } catch (err) {
      console.error('Authentication request error:', err)
      setError(`Unable to connect to the authentication server at ${apiBase}. Please ensure the backend is running.`)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-intro">
        <p className="eyebrow">AUTONOMOUS DEVOPS SWARM</p>
        <h1>Eight agents. One reliable release.</h1>
        <p>Plan, build, secure, deploy, and observe every delivery workflow from one calm control room.</p>
        <div className="auth-points">
          <span>◈ Eight specialised agents</span>
          <span>◈ Observable pipelines</span>
          <span>◈ Safer releases</span>
        </div>
      </section>

      <section className="auth-card">
        <div className="auth-tabs">
          <button
            type="button"
            className={mode === 'signin' ? 'active' : ''}
            onClick={() => {
              setMode('signin')
              setError('')
              setSuccess('')
              setForm((prev) => ({ ...prev, password: '', confirmPassword: '' }))
            }}
          >
            Sign in
          </button>
          <button
            type="button"
            className={mode === 'signup' ? 'active' : ''}
            onClick={() => {
              setMode('signup')
              setError('')
              setSuccess('')
              setForm((prev) => ({ ...prev, password: '', confirmPassword: '' }))
            }}
          >
            Create account
          </button>
        </div>

        <div className="auth-heading">
          <p className="section-label">{mode === 'signin' ? 'WELCOME BACK' : 'CREATE ACCOUNT'}</p>
          <p>{mode === 'signin' ? 'Sign in to access mission control.' : 'Register your operator credentials to launch missions.'}</p>
        </div>

        <form className="auth-form" onSubmit={submit}>
          {mode === 'signup' && (
            <label>
              Full name
              <div className="validated-input-wrapper">
                <input
                  value={form.name}
                  onChange={update('name')}
                  placeholder="Alex Morgan"
                  required
                  minLength="2"
                  autoComplete="name"
                  disabled={submitting}
                  className={nameHasText ? (isNameValid ? 'input-valid' : 'input-invalid') : ''}
                />
                {nameHasText && <ValidationMark valid={isNameValid} />}
              </div>
              {nameHasText && (
                <span className={`input-status-msg ${isNameValid ? 'valid' : 'invalid'}`}>
                  <span className="input-status-icon">{isNameValid ? '✓' : '✕'}</span>
                  <span>{isNameValid ? 'Valid full name' : 'Full name must be at least 2 characters'}</span>
                </span>
              )}
            </label>
          )}

          <label>
            Email address
            <div className="validated-input-wrapper">
              <input
                type="email"
                value={form.email}
                onChange={update('email')}
                placeholder={mode === 'signup' ? 'alex@gmail.com' : 'you@example.com'}
                required
                autoComplete="email"
                disabled={submitting}
                className={emailHasText ? (isEmailValid ? 'input-valid' : 'input-invalid') : ''}
              />
              {emailHasText && <ValidationMark valid={isEmailValid} />}
            </div>
            {emailHasText && (
              <span className={`input-status-msg ${isEmailValid ? 'valid' : 'invalid'}`}>
                <span className="input-status-icon">{isEmailValid ? '✓' : '✕'}</span>
                <span>
                  {isEmailValid
                    ? 'Valid email address'
                    : (isGmailDomainInvalid
                        ? 'Invalid Gmail domain. Must be @gmail.com'
                        : 'Please enter a valid email address')
                  }
                </span>
              </span>
            )}
          </label>

          <label>
            Password
            <div className="password-input-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                value={form.password}
                onChange={update('password')}
                placeholder={mode === 'signup' ? 'At least 8 characters' : '••••••••'}
                required
                minLength="8"
                autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                disabled={submitting}
                className={passwordHasText ? (isPasswordValid ? 'input-valid' : 'input-invalid') : ''}
              />
              {passwordHasText && <ValidationMark valid={isPasswordValid} className="password-validation-mark" />}
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowPassword(!showPassword)}
                title={showPassword ? 'Hide password' : 'Show password'}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                tabIndex="-1"
              >
                <EyeIcon visible={showPassword} />
              </button>
            </div>
            {passwordHasText && (
              <span className={`input-status-msg ${isPasswordValid ? 'valid' : 'invalid'}`}>
                <span className="input-status-icon">{isPasswordValid ? '✓' : '✕'}</span>
                <span>
                  {isPasswordValid
                    ? (mode === 'signup' ? 'Password meets requirements (8+ characters)' : 'Valid password length')
                    : 'Password must contain at least 8 characters'}
                </span>
              </span>
            )}
          </label>

          {mode === 'signup' && (
            <label>
              Confirm password
              <div className="password-input-wrapper">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={form.confirmPassword}
                  onChange={update('confirmPassword')}
                  placeholder="Repeat your password"
                  required
                  minLength="8"
                  autoComplete="new-password"
                  disabled={submitting}
                  className={confirmPasswordHasText ? (isConfirmPasswordValid ? 'input-valid' : 'input-invalid') : ''}
                />
                {confirmPasswordHasText && <ValidationMark valid={isConfirmPasswordValid} className="password-validation-mark" />}
                <button
                  type="button"
                  className="password-toggle-btn"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  title={showConfirmPassword ? 'Hide password' : 'Show password'}
                  aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                  tabIndex="-1"
                >
                  <EyeIcon visible={showConfirmPassword} />
                </button>
              </div>
              {confirmPasswordHasText && (
                <span className={`input-status-msg ${isConfirmPasswordValid ? 'valid' : 'invalid'}`}>
                  <span className="input-status-icon">{isConfirmPasswordValid ? '✓' : '✕'}</span>
                  <span>
                    {isConfirmPasswordValid
                      ? 'Passwords match'
                      : (form.confirmPassword.length < 8
                          ? 'Must be at least 8 characters'
                          : 'Passwords do not match')}
                  </span>
                </span>
              )}
            </label>
          )}

          {mode === 'signin' && (
            <label className="auth-checkbox-label">
              <input
                type="checkbox"
                checked={form.rememberMe}
                onChange={(e) => setForm({ ...form, rememberMe: e.target.checked })}
                disabled={submitting}
              />
              <span>Remember this session</span>
            </label>
          )}

          {error && (
            <div className="auth-error" role="alert">
              <span>⚠️</span>
              <div>{error}</div>
            </div>
          )}

          {success && (
            <div className="auth-success" role="status">
              <span>✓</span>
              <div>{success}</div>
            </div>
          )}

          <button className="primary-button" type="submit" disabled={submitting}>
            {submitting ? (
              <>
                <span className="spinner" />
                {mode === 'signin' ? 'Signing in…' : 'Creating account…'}
              </>
            ) : mode === 'signin' ? (
              'Enter mission control'
            ) : (
              'Create account'
            )}
          </button>
        </form>

        <p className="auth-note">Secured by Autonomous DevOps Swarm API &amp; PBKDF2 authentication.</p>
      </section>
    </main>
  )
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('swarm_token') || sessionStorage.getItem('swarm_token'))
  const [user, setUser] = useState(null)
  const [authChecking, setAuthChecking] = useState(Boolean(localStorage.getItem('swarm_token') || sessionStorage.getItem('swarm_token')))
  const [page, setPage] = useState('dashboard')
  const [request, setRequest] = useState('Build a student management portal')
  const [pipeline, setPipeline] = useState(null)
  const [history, setHistory] = useState([])
  const [failures, setFailures] = useState([])
  const [storage, setStorage] = useState('loading')
  const [error, setError] = useState('')
  const [running, setRunning] = useState(false)
  const [healingSimulating, setHealingSimulating] = useState(false)
  const [logLevel, setLogLevel] = useState('all')
  const [clearedLogs, setClearedLogs] = useState(false)
  const [settings, setSettings] = useState(() => {
    const saved = JSON.parse(localStorage.getItem('swarm-settings') || '{}')
    return { theme: saved.theme === 'light' ? 'light' : 'dark', notifications: saved.notifications ?? true, codingAgent: saved.codingAgent ?? true }
  })
  const [selectedAgent, setSelectedAgent] = useState('Planning Agent')
  const [inspectorOpen, setInspectorOpen] = useState(false)
  const [missionEditPending, setMissionEditPending] = useState(false)
  const [workflowMinimized, setWorkflowMinimized] = useState(false)
  const [workflowExpanded, setWorkflowExpanded] = useState(false)
  const missionInputRef = useRef(null)

  const handleSignOut = useCallback(async () => {
    try {
      const activeToken = token || localStorage.getItem('swarm_token') || sessionStorage.getItem('swarm_token')
      if (activeToken) {
        await fetch(`${apiBase}/auth/logout`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${activeToken}` },
        })
      }
    } catch {
      // safe fallback
    } finally {
      localStorage.removeItem('swarm_token')
      sessionStorage.removeItem('swarm_token')
      localStorage.removeItem('swarm_user')
      sessionStorage.removeItem('swarm_user')
      setToken(null)
      setUser(null)
    }
  }, [token])

  // Verify session on mount
  useEffect(() => {
    let isMounted = true
    async function verifySession() {
      const activeToken = localStorage.getItem('swarm_token') || sessionStorage.getItem('swarm_token')
      if (!activeToken) {
        if (isMounted) setAuthChecking(false)
        return
      }

      try {
        const response = await fetch(`${apiBase}/auth/me`, {
          headers: { Authorization: `Bearer ${activeToken}` },
        })
        if (response.ok) {
          const userData = await response.json()
          if (isMounted) {
            setUser(userData)
            setToken(activeToken)
          }
        } else {
          // Token expired or invalid
          localStorage.removeItem('swarm_token')
          sessionStorage.removeItem('swarm_token')
          localStorage.removeItem('swarm_user')
          sessionStorage.removeItem('swarm_user')
          if (isMounted) {
            setToken(null)
            setUser(null)
          }
        }
      } catch (err) {
        console.warn('Backend unavailable during session verify:', err)
        const cachedUserStr = localStorage.getItem('swarm_user') || sessionStorage.getItem('swarm_user')
        if (cachedUserStr && isMounted) {
          try {
            setUser(JSON.parse(cachedUserStr))
          } catch {
            setUser({ full_name: cachedUserStr, email: '' })
          }
        }
      } finally {
        if (isMounted) setAuthChecking(false)
      }
    }

    verifySession()
    return () => { isMounted = false }
  }, [])

  const loadHistory = useCallback(async () => {
    if (!token) return
    const response = await fetch(`${apiBase}/pipelines`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (response.status === 401) {
      handleSignOut()
      throw new Error('Session expired. Please sign in again.')
    }
    if (!response.ok) throw new Error('Could not load pipeline history.')
    const data = await response.json()
    setHistory(data.pipelines)
    setStorage(data.storage)
  }, [token, handleSignOut])

  const loadFailures = useCallback(async () => {
    if (!token) return
    try {
      const res = await fetch(`${apiBase}/failures`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.status === 401) {
        handleSignOut()
        return
      }
      if (res.ok) {
        const data = await res.json()
        setFailures(data.failures || [])
      }
    } catch {
      // safe fallback
    }
  }, [token, handleSignOut])

  useEffect(() => {
    if (user && token) {
      loadHistory().catch(() => setStorage('backend unavailable'))
      loadFailures()
    }
  }, [user, token, loadHistory, loadFailures])

  useEffect(() => {
    document.documentElement.dataset.theme = settings.theme
    localStorage.setItem('swarm-settings', JSON.stringify(settings))
  }, [settings])

  useEffect(() => {
    if (page !== 'dashboard' || !missionEditPending) return
    missionInputRef.current?.focus()
    missionInputRef.current?.select()
    setMissionEditPending(false)
  }, [page, missionEditPending])

  async function runPipeline(event) {
    event.preventDefault()
    setRunning(true)
    setError('')
    setClearedLogs(false)
    try {
      const response = await fetch(`${apiBase}/pipelines`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ request }),
      })
      if (response.status === 401) {
        handleSignOut()
        throw new Error('Your session has expired. Please sign in again.')
      }
      if (!response.ok) throw new Error('The backend could not start the pipeline.')
      setPipeline(await response.json())
      setPage('dashboard')
      await loadHistory()
      await loadFailures()
    } catch (err) {
      setError(err.message)
    } finally {
      setRunning(false)
    }
  }

  async function triggerSimulatedFailure() {
    setHealingSimulating(true)
    setError('')
    try {
      const response = await fetch(`${apiBase}/pipelines/simulate-failure`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ request: `${request} (Self-Healing Test)` }),
      })
      if (response.status === 401) {
        handleSignOut()
        throw new Error('Your session has expired. Please sign in again.')
      }
      if (!response.ok) throw new Error('Could not execute simulated failure.')
      const result = await response.json()
      setPipeline(result)
      setPage('dashboard')
      await loadHistory()
      await loadFailures()
    } catch (err) {
      setError(err.message)
    } finally {
      setHealingSimulating(false)
    }
  }

  const editMission = () => {
    setInspectorOpen(false)
    setMissionEditPending(true)
    setPage('dashboard')
  }

  const stageFor = (agent) => {
    if (!implementedAgents.has(agent)) return { agent, status: 'pending' }
    return pipeline?.stages.find((stage) => stage.agent === agent) ?? { agent, status: 'waiting' }
  }

  const logs = useMemo(() => {
    if (clearedLogs) return []
    const list = pipeline?.logs ?? []
    return logLevel === 'all' ? list : list.filter((log) => log.message.toLowerCase().includes(logLevel))
  }, [pipeline, logLevel, clearedLogs])

  const observer = pipeline?.observer
  const nav = [
    ['dashboard', 'Dashboard'],
    ['healing', 'Self-Healing'],
    ['agents', 'Agents'],
    ['logs', 'Logs'],
    ['database', 'Database'],
    ['settings', 'Settings'],
  ]

  const openInspector = (agent) => { setSelectedAgent(agent); setInspectorOpen(true) }

  const renderStages = (agents) => <ul className="agent-list">{agents.map((agent) => {
    const stage = stageFor(agent)
    return <li key={agent} onClick={() => openInspector(agent)} style={{ cursor: 'pointer' }}>
      <span className={`agent-dot ${stage.status}`} />
      <div>
        <strong>{agent}</strong>
        <small>{stage.status === 'completed' ? `Completed${stage.duration_ms ? ` · ${stage.duration_ms}ms` : ''}` : stage.status === 'healed' ? '⚡ Healed by Self-Healing Agent' : stage.status}</small>
      </div>
      <span className={`status-pill ${stage.status}`}>{stage.status}</span>
    </li>
  })}</ul>

  if (authChecking) {
    return (
      <div className="auth-loading-splash">
        <span className="spinner" style={{ width: 28, height: 28 }} />
        <p>Connecting to Autonomous DevOps Swarm…</p>
      </div>
    )
  }

  if (!user) {
    return (
      <AuthScreen
        onAuthenticated={(userData, authToken) => {
          setUser(userData)
          setToken(authToken)
        }}
      />
    )
  }

  return <main className="app-shell">
    <aside className="sidebar">
      <div className="brand">
        <span>◈</span>
        <div><strong>Swarm</strong><small>DevOps control</small></div>
      </div>
      <nav>
        {nav.map(([key, label]) => (
          <button key={key} className={page === key ? 'selected' : ''} onClick={() => setPage(key)}>
            {key === 'healing' ? '⚡ ' : ''}{label}
          </button>
        ))}
      </nav>
      <div className="sidebar-footer"><span className="online-dot" />System online</div>
    </aside>

    <section className="workspace">
      <header className="topbar">
        <div>
          <p className="eyebrow">{page.toUpperCase()}</p>
          <h1>{page === 'dashboard' ? 'Mission control' : page === 'healing' ? 'Self-Healing & DB Failure Memory' : page[0].toUpperCase() + page.slice(1)}</h1>
        </div>
        <div className="user-menu">
          <span className="avatar">{(user.full_name || user.email || 'O')[0].toUpperCase()}</span>
          <div><strong>{user.full_name || user.email}</strong><small>{user.email || 'Operator'}</small></div>
          <button title="Sign out" className="signout" onClick={handleSignOut}>Sign out</button>
        </div>
      </header>

      {page === 'dashboard' && <>
        <section className="command-card">
          <div>
            <p className="section-label">AI COMMAND PROMPT</p>
            <h2>Launch a delivery mission</h2>
          </div>
          <form onSubmit={runPipeline}>
            <input ref={missionInputRef} value={request} onChange={(event) => setRequest(event.target.value)} minLength="3" required />
            <button className="primary-button" disabled={running || healingSimulating}>
              {running ? 'Launching…' : 'Submit mission'}
            </button>
          </form>
          {error && <p className="error">{error} Start the backend at port 8000 and try again.</p>}
        </section>

        <section className="metrics">
          <div><span>Pipeline status</span><strong className={pipeline?.status}>{pipeline?.status ?? 'Ready'}</strong></div>
          <div><span>CPU usage</span><strong>{pipeline?.stages.at(-1)?.output?.cpu ?? '—'}</strong></div>
          <div><span>Memory usage</span><strong>{pipeline?.stages.at(-1)?.output?.memory ?? '—'}</strong></div>
          <div><span>DB Incidents Healed</span><strong className="completed">{failures.length}</strong></div>
          <div><span>Health status</span><strong className="completed">{pipeline?.stages.at(-1)?.output?.health ?? 'Waiting'}</strong></div>
        </section>

        <section className="content-grid">
          <div className="panel">
            <div className="panel-heading">
              <div><p className="section-label">ACTIVE AGENTS</p><h2>Development team</h2></div>
              <div className="actions">
                <button onClick={() => openInspector(selectedAgent)}>Inspect</button>
                <button onClick={editMission}>Edit</button>
                <span className="badge">{pipeline?.progress ?? 0}%</span>
              </div>
            </div>
            {renderStages(developmentAgents)}
          </div>

          <div className="panel">
            <div className="panel-heading">
              <div><p className="section-label">OPERATIONS</p><h2>Release team</h2></div>
              <div className="actions">
                <button onClick={() => openInspector(selectedAgent)}>Inspect</button>
                <button onClick={editMission}>Edit</button>
              </div>
            </div>
            {renderStages(operationsAgents)}
          </div>
        </section>

        <section className="panel observer">
          <div><p className="section-label">SWARM OBSERVER</p><h2>Pipeline inspection</h2></div>
          <div className="observer-stats">
            <span><b>{observer?.agents_monitored ?? 0}</b> Agents monitored</span>
            <span><b>{observer?.failures_detected ?? 0}</b> Failures</span>
            <span><b>{failures.length}</b> Self-Healed in DB</span>
            <span>{observer?.message ?? 'Awaiting a mission.'}</span>
          </div>
        </section>
      </>}

      {page === 'healing' && <SelfHealingScreen failures={failures} storage={storage} onRefresh={loadFailures} onSimulate={triggerSimulatedFailure} simulating={healingSimulating} />}
      {page === 'agents' && <section className="panel"><p className="section-label">AGENT DIRECTORY</p><h2>Specialists in this swarm</h2><div className="agent-cards">{allAgents.map((agent, index) => <article key={agent}><span>{String(index + 1).padStart(2, '0')}</span><h3>{agent}</h3><p>{stageFor(agent).status === 'waiting' ? 'Ready for a mission' : stageFor(agent).status}</p><button onClick={() => openInspector(agent)}>Inspect agent</button></article>)}</div></section>}
      {page === 'logs' && <section className="panel"><div className="panel-heading"><div><p className="section-label">EXECUTION LOGS</p><h2>Swarm activity</h2></div><div className="actions"><select value={logLevel} onChange={(event) => setLogLevel(event.target.value)}><option value="all">All logs</option><option value="started">Started</option><option value="completed">Completed</option><option value="failed">Failed</option></select><button onClick={() => setClearedLogs(true)}>Clear logs</button></div></div><div className="logs">{logs.length ? logs.map((log, i) => <p key={`${log.timestamp}-${i}`}><span>{log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '—'}</span>{log.message}</p>) : <p>No logs to display.</p>}</div></section>}
      {page === 'database' && <section className="panel"><div className="panel-heading"><div><p className="section-label">PIPELINE DATABASE</p><h2>Mission history</h2></div><button onClick={() => loadHistory().catch(() => setError('Could not refresh history.'))}>Refresh</button></div><p className="storage">Storage: {storage}</p><div className="table-wrap"><table><thead><tr><th>Request</th><th>Status</th><th>Agents</th><th>Updated</th></tr></thead><tbody>{history.length ? history.map((item) => <tr key={item.task.id}><td>{item.task.request}</td><td><span className={`status-pill ${item.status}`}>{item.status}</span></td><td>{item.stages.length}</td><td>{new Date(item.updated_at).toLocaleString()}</td></tr>) : <tr><td colSpan="4">No saved missions yet.</td></tr>}</tbody></table></div></section>}
      {page === 'settings' && <section className="panel settings"><div className="panel-heading"><div><p className="section-label">PREFERENCES</p><h2>Workspace settings</h2></div><button onClick={() => setSettings({ theme: 'dark', notifications: true, codingAgent: true })}>Reset</button></div><label>Theme<select value={settings.theme} onChange={(e) => setSettings({ ...settings, theme: e.target.value })}><option value="dark">Dark</option><option value="light">Light</option></select></label><label className="toggle-row"><span><b>Pipeline alerts</b><small>Notify when a pipeline needs attention.</small></span><input type="checkbox" checked={settings.notifications} onChange={(e) => setSettings({ ...settings, notifications: e.target.checked })} /></label><label className="toggle-row"><span><b>Coding agent</b><small>Allow the coding specialist in new missions.</small></span><input type="checkbox" checked={settings.codingAgent} onChange={(e) => setSettings({ ...settings, codingAgent: e.target.checked })} /></label><button className="primary-button" onClick={() => alert('Settings saved for this session.')}>Save changes</button></section>}

      {page === 'dashboard' && <WorkflowSidebar pipeline={pipeline} request={request} onInspect={openInspector} minimized={workflowMinimized} expanded={workflowExpanded} onMinimize={() => setWorkflowMinimized(!workflowMinimized)} onExpand={() => { setWorkflowMinimized(false); setWorkflowExpanded(!workflowExpanded) }} />}
      {inspectorOpen && (
        <InspectModal
          agent={selectedAgent}
          stage={stageFor(selectedAgent)}
          request={request}
          pipeline={pipeline}
          token={token}
          onClose={() => setInspectorOpen(false)}
          onEdit={editMission}
        />
      )}
    </section>
  </main>
}

export default App

function SelfHealingScreen({ failures, storage, onRefresh, onSimulate, simulating }) {
  const [selectedFailure, setSelectedFailure] = useState(null)

  return <section className="panel self-healing-screen">
    <div className="panel-heading">
      <div>
        <p className="section-label">AUTONOMOUS SELF-HEALING & DATABASE MEMORY</p>
        <h2>Zero-Human Intervention Failure Recovery</h2>
      </div>
      <div className="actions">
        <button onClick={onRefresh}>🔄 Refresh DB Memory</button>
        <button className="primary-button" onClick={onSimulate} disabled={simulating}>
          {simulating ? '⚡ Auto-Healing in progress…' : '🧪 Simulate Failure & Auto-Heal'}
        </button>
      </div>
    </div>

    {/* Metric Cards */}
    <div className="metrics" style={{ marginTop: 20 }}>
      <div><span>Auto-Healed Incidents</span><strong className="completed">{failures.length}</strong></div>
      <div><span>Human Intervention</span><strong className="completed">0% (Fully Autonomous)</strong></div>
      <div><span>Database Persistence</span><strong>{storage}</strong></div>
      <div><span>Knowledge Memory Retained</span><strong className="completed">{failures.length} Records</strong></div>
      <div><span>Auto-Remediation Rate</span><strong className="completed">100%</strong></div>
    </div>

    <div className="section-block" style={{ marginTop: 24 }}>
      <h4>⚡ Database Failure Memory & Knowledge Base</h4>
      <p className="section-subtitle">
        Failure details, error diagnostics, and self-healing resolutions stored in Database Memory for future interactions.
      </p>

      {failures.length > 0 ? (
        <div className="table-wrap">
          <table className="failures-table">
            <thead>
              <tr>
                <th>Mission Request</th>
                <th>Failed Agent</th>
                <th>Root Cause Analysis</th>
                <th>Self-Healing Remediation Applied</th>
                <th>Status</th>
                <th>Recorded At</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {failures.map((fail) => (
                <tr key={fail.failure_id}>
                  <td><strong>{fail.mission_request}</strong></td>
                  <td><span className="agent-badge">{fail.failed_agent}</span></td>
                  <td><span className="cause-text">{fail.root_cause}</span></td>
                  <td><span className="healing-text">{fail.healing_action}</span></td>
                  <td><span className="status-pill completed">⚡ {fail.status}</span></td>
                  <td><small>{new Date(fail.healed_at).toLocaleTimeString()}</small></td>
                  <td>
                    <button className="btn-small" onClick={() => setSelectedFailure(fail)}>Inspect DB Record</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-state-card">
          <p>No failure incidents recorded in DB yet. Click <strong>"Simulate Failure & Auto-Heal"</strong> above to test zero-human intervention self-healing!</p>
        </div>
      )}
    </div>

    {/* Failure Inspection Modal */}
    {selectedFailure && (
      <div role="dialog" aria-modal="true" className="modal-backdrop" onMouseDown={() => setSelectedFailure(null)}>
        <section className="inspect-modal-panel" onMouseDown={(e) => e.stopPropagation()} style={{ width: 'min(780px, 100%)' }}>
          <div className="panel-heading">
            <div>
              <p className="section-label">DATABASE FAILURE MEMORY RECORD</p>
              <h2>Incident #{selectedFailure.failure_id.slice(0, 8)}</h2>
            </div>
            <button className="close-btn" onClick={() => setSelectedFailure(null)}>✕</button>
          </div>
          <div className="modal-body" style={{ display: 'grid', gap: 16 }}>
            <div className="plan-summary-card">
              <h3>🎯 Mission Context</h3>
              <p>{selectedFailure.mission_request}</p>
            </div>
            <div className="arch-card">
              <span className="arch-icon">🚨</span>
              <div>
                <strong>Failed Component: {selectedFailure.failed_agent}</strong>
                <p><code>{selectedFailure.error_signature}</code></p>
              </div>
            </div>
            <div className="arch-card">
              <span className="arch-icon">🩺</span>
              <div>
                <strong>Diagnosed Root Cause</strong>
                <p>{selectedFailure.root_cause}</p>
              </div>
            </div>
            <div className="arch-card" style={{ borderColor: '#153c2c' }}>
              <span className="arch-icon">⚡</span>
              <div>
                <strong style={{ color: '#86efac' }}>Autonomous Self-Healing Action Applied</strong>
                <p>{selectedFailure.healing_action}</p>
              </div>
            </div>
            <pre className="raw-json">{JSON.stringify(selectedFailure, null, 2)}</pre>
          </div>
        </section>
      </div>
    )}
  </section>
}

function WorkflowSidebar({ pipeline, request, onInspect, minimized, expanded, onMinimize, onExpand }) {
  const planning = pipeline?.stages.find((stage) => stage.agent === 'Planning Agent')
  const coding = pipeline?.stages.find((stage) => stage.agent === 'Coding Agent')

  return <aside className={`workflow-sidebar${minimized ? ' minimized' : ''}${expanded ? ' expanded' : ''}`} aria-label="Mission workflow">
    <div className="workflow-controls"><button title={minimized ? 'Open workflow' : 'Minimize workflow'} aria-label={minimized ? 'Open workflow' : 'Minimize workflow'} onClick={onMinimize}>{minimized ? '‹' : '›'}</button>{!minimized && <button title={expanded ? 'Use normal width' : 'Expand workflow'} aria-label={expanded ? 'Use normal width' : 'Expand workflow'} onClick={onExpand}>{expanded ? '↔' : '⤢'}</button>}</div>
    {!minimized && <><div className="workflow-sidebar-heading"><div><p className="section-label">LIVE WORKFLOW</p><h2>Agent handoff</h2></div><span className={`status-pill ${pipeline?.status ?? 'waiting'}`}>{pipeline?.status ?? 'ready'}</span></div>
    <p className="workflow-request">{pipeline ? `Mission: ${pipeline.task.request}` : `Ready to plan: ${request}`}</p>
    <WorkflowStage title="1. Planning Agent" agentName="Planning Agent" status={planning?.status} stageData={planning} empty="Submit a mission to see requirements, architecture, API contracts, and the step-by-step delivery plan." onInspect={() => onInspect('Planning Agent')} />
    <WorkflowStage title="2. Coding Agent" agentName="Coding Agent" status={coding?.status} stageData={coding} empty="The coding blueprint appears after the planning handoff, showing full source code files for backend & frontend." onInspect={() => onInspect('Coding Agent')} />
    {pipeline && <div className="workflow-next"><p className="section-label">NEXT HANDOFF</p><strong>Build Agent — pending</strong><span>Build, test, security, release, deployment, and monitoring remain pending until their real implementations are added.</span></div>}</>}
  </aside>
}

function WorkflowStage({ title, agentName, status, stageData, empty, onInspect }) {
  const output = stageData?.output
  const summary = output?.summary
  const steps = agentName === 'Planning Agent' ? (output?.implementation_steps ?? []) : (output?.implementation_order ?? [])
  const files = output?.files_to_create ?? []

  return <section className={`workflow-stage ${status ?? 'waiting'}`}>
    <div className="workflow-stage-heading">
      <div><h3>{title}</h3><span>{status ?? 'Waiting for mission'}</span></div>
      {status === 'completed' && <span className="workflow-check">✓</span>}
      {status === 'healed' && <span className="workflow-check" style={{ background: '#1e3a8a', color: '#93c5fd' }}>⚡</span>}
    </div>
    
    {summary ? <p className="workflow-summary">{summary}</p> : <p className="workflow-empty">{empty}</p>}

    {/* Plan Preview */}
    {agentName === 'Planning Agent' && output?.domain_models?.length > 0 && (
      <div className="mini-card-list">
        <p className="mini-label">SYNTHESIZED MODELS:</p>
        <div className="tag-group">
          {output.domain_models.map(m => <span key={m.name} className="model-tag">⚡ {m.name}</span>)}
        </div>
      </div>
    )}

    {/* Code File Preview Badges */}
    {agentName === 'Coding Agent' && files.length > 0 && (
      <div className="mini-card-list">
        <p className="mini-label">WORKSPACE FILES ({files.length} ON DISK):</p>
        <div className="file-tag-group">
          {files.map(f => (
            <span key={f.path} className={`file-badge status-${f.status || 'created'}`}>
              📄 {f.path.split('/').pop()}
              <span className={`badge-pill ${f.status || 'created'}`}>{f.status === 'modified' ? 'MOD' : 'NEW'}</span>
            </span>
          ))}
        </div>
      </div>
    )}

    {/* Steps List */}
    {steps.length > 0 && (
      <ol className="workflow-steps">
        {steps.map((item) => (
          <li key={item.step}>
            <span>{item.step}</span>
            <div>
              <strong>{item.title ?? item.area}</strong>
              <p>{item.detail}</p>
            </div>
          </li>
        ))}
      </ol>
    )}

    <button className="workflow-details primary-link" onClick={onInspect}>
      {summary ? `🔍 Open Full ${agentName} Output` : 'Inspect agent'}
    </button>
  </section>
}

function InspectModal({ agent, stage, request, pipeline, token, onClose, onEdit }) {
  const [viewMode, setViewMode] = useState('formatted') // 'formatted' | 'raw'
  const output = stage?.output
  const projectId = output?.project_id || pipeline?.task?.project_id || 'project_default'
  const workspaceDir = output?.workspace_dir

  return <div role="dialog" aria-modal="true" aria-label="Agent inspection" className="modal-backdrop" onMouseDown={onClose}>
    <section className="inspect-modal-panel" onMouseDown={(event) => event.stopPropagation()}>
      <div className="panel-heading">
        <div>
          <p className="section-label">AGENT MISSION INSPECTOR</p>
          <h2>{agent}</h2>
        </div>
        <div className="actions">
          <div className="view-toggle">
            <button className={viewMode === 'formatted' ? 'active' : ''} onClick={() => setViewMode('formatted')}>✨ Formatted AI Output</button>
            <button className={viewMode === 'raw' ? 'active' : ''} onClick={() => setViewMode('raw')}>{'{ }'} Raw JSON</button>
          </div>
          <button onClick={onClose} className="close-btn">✕</button>
        </div>
      </div>

      <div className="metrics-strip">
        <div><span>Status</span><strong className={stage.status}>{stage.status}</strong></div>
        <div><span>Execution Time</span><strong>{stage.duration_ms ? `${stage.duration_ms}ms` : '—'}</strong></div>
        <div><span>Mission</span><strong className="mission-text">{request}</strong></div>
      </div>

      <div className="modal-body">
        {!output ? (
          <div className="empty-state">Submit a mission to generate detailed plans and complete source code files.</div>
        ) : viewMode === 'raw' ? (
          <pre className="raw-json">{JSON.stringify(output, null, 2)}</pre>
        ) : agent === 'Planning Agent' ? (
          <PlanViewer plan={output} />
        ) : agent === 'Coding Agent' ? (
          <CodeExplorer
            files={output.files_to_create || []}
            summary={output.summary}
            _planUsed={output.plan_used}
            order={output.implementation_order || []}
            result={output.user_visible_result}
            projectId={projectId}
            workspaceDir={workspaceDir}
            token={token}
          />
        ) : (
          <pre className="raw-json">{JSON.stringify(output, null, 2)}</pre>
        )}
      </div>

      <div className="panel-footer">
        <button onClick={onEdit}>Edit Mission</button>
        <button className="primary-button" onClick={() => navigator.clipboard?.writeText(JSON.stringify(output ?? {}, null, 2))}>
          📋 Copy Full Output JSON
        </button>
      </div>
    </section>
  </div>
}

function PlanViewer({ plan }) {
  const arch = plan.architecture || {}
  const models = plan.domain_models || []
  const routes = plan.api_contract || []
  const steps = plan.implementation_steps || []

  return <div className="plan-viewer">
    <div className="plan-summary-card">
      <h3>🎯 Strategic Mission Goal</h3>
      <p>{plan.goal || plan.summary}</p>
    </div>

    {/* Architecture Grid */}
    {Object.keys(arch).length > 0 && (
      <div className="section-block">
        <h4>🏛️ System Architecture Overview</h4>
        <div className="arch-grid">
          {arch.frontend && <div className="arch-card"><span className="arch-icon">💻</span><div><strong>Frontend SPA</strong><p>{arch.frontend}</p></div></div>}
          {arch.backend && <div className="arch-card"><span className="arch-icon">⚙️</span><div><strong>Backend API Layer</strong><p>{arch.backend}</p></div></div>}
          {arch.database && <div className="arch-card"><span className="arch-icon">🗄️</span><div><strong>Database &amp; Persistence</strong><p>{arch.database}</p></div></div>}
          {arch.security && <div className="arch-card"><span className="arch-icon">🔒</span><div><strong>Security &amp; Authentication</strong><p>{arch.security}</p></div></div>}
        </div>
      </div>
    )}

    {/* Domain Models & Database Schemas */}
    {models.length > 0 && (
      <div className="section-block">
        <h4>⚡ Synthesized Domain Models &amp; Schemas</h4>
        <div className="models-grid">
          {models.map((model) => (
            <div key={model.name} className="model-card">
              <div className="model-header">
                <strong>{model.name}</strong>
                <span className="badge-type">Entity Model</span>
              </div>
              <table className="fields-table">
                <thead>
                  <tr><th>Field</th><th>Type</th><th>Description</th></tr>
                </thead>
                <tbody>
                  {(model.fields || []).map((f) => (
                    <tr key={f.name}>
                      <td><code>{f.name}</code></td>
                      <td><span className="type-pill">{f.type}</span></td>
                      <td>{f.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      </div>
    )}

    {/* API Contracts */}
    {routes.length > 0 && (
      <div className="section-block">
        <h4>🔌 REST API Specifications</h4>
        <div className="routes-list">
          {routes.map((route, i) => (
            <div key={i} className="route-item">
              <span className={`method-pill ${route.method.toLowerCase()}`}>{route.method}</span>
              <code>{route.path}</code>
              <span className="route-desc">{route.description}</span>
            </div>
          ))}
        </div>
      </div>
    )}

    {/* Execution Steps */}
    {steps.length > 0 && (
      <div className="section-block">
        <h4>📋 Implementation Roadmap &amp; Deliverables</h4>
        <div className="roadmap-list">
          {steps.map((st) => (
            <div key={st.step} className="roadmap-step">
              <span className="step-num">{st.step}</span>
              <div>
                <strong>{st.title}</strong>
                <p>{st.detail}</p>
                {st.deliverables?.length > 0 && (
                  <div className="deliverables-tags">
                    {st.deliverables.map((d, idx) => <span key={idx} className="deliv-tag">📦 {d}</span>)}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
}

function CodeExplorer({ files = [], summary, _planUsed, order = [], result, projectId, workspaceDir, token }) {
  const [fileList, setFileList] = useState(files)
  const [activeFileIndex, setActiveFileIndex] = useState(0)
  const [copied, setCopied] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editorContent, setEditorContent] = useState('')
  const [saveLoading, setSaveLoading] = useState(false)
  const [saveFeedback, setSaveFeedback] = useState(null)

  useEffect(() => {
    setFileList(files)
    setActiveFileIndex(0)
    setIsEditing(false)
    setSaveFeedback(null)
  }, [files])

  const activeFile = fileList[activeFileIndex] || fileList[0]
  const activeFilePath = activeFile?.path

  useEffect(() => {
    if (activeFile) {
      setEditorContent(activeFile.code || '')
      setIsEditing(false)
      setSaveFeedback(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeFilePath])

  const copyCode = () => {
    const textToCopy = isEditing ? editorContent : (activeFile?.code || '')
    if (!textToCopy) return
    navigator.clipboard.writeText(textToCopy)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleSaveFile = async () => {
    if (!activeFile || !token) return
    setSaveLoading(true)
    setSaveFeedback(null)
    try {
      const res = await fetch(`${apiBase}/workspace/file`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          project_id: projectId || 'project_default',
          path: activeFile.path,
          content: editorContent,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to save file.')
      }
      const data = await res.json()
      setFileList((prev) =>
        prev.map((f, i) => (i === activeFileIndex ? { ...f, code: editorContent, status: 'modified', size: data.size } : f))
      )
      setSaveFeedback({ type: 'success', message: `Saved directly to workspace disk (${data.size} bytes).` })
      setIsEditing(false)
    } catch (err) {
      setSaveFeedback({ type: 'error', message: err.message })
    } finally {
      setSaveLoading(false)
    }
  }

  return (
    <div className="code-explorer">
      <div className="code-header-info">
        <div>
          <h3>⚡ Generated Source Code Files</h3>
          <p>{summary || 'Complete software implementation code generated by Coding Agent'}</p>
        </div>
        {result && <div className="result-banner">✨ {result}</div>}
      </div>

      {workspaceDir && (
        <div className="workspace-meta-bar">
          <span>📁 Project Workspace: <code>{workspaceDir}</code></span>
          <span><b>{fileList.length}</b> files persisted</span>
        </div>
      )}

      {saveFeedback && (
        <div className={`save-banner ${saveFeedback.type}`}>
          {saveFeedback.type === 'success' ? '✅ ' : '❌ '}
          {saveFeedback.message}
        </div>
      )}

      {/* File Tabs */}
      {fileList.length > 0 ? (
        <div className="code-container">
          <div className="file-tabs">
            {fileList.map((file, idx) => {
              const fileName = file.path.split('/').pop()
              const icon = file.language === 'python' ? '🐍' : file.language === 'javascript' ? '⚛️' : file.language === 'sql' ? '🗄️' : file.language === 'html' ? '🌐' : file.language === 'css' ? '🎨' : '📄'
              return (
                <button
                  key={file.path}
                  className={`file-tab ${idx === activeFileIndex ? 'active' : ''}`}
                  onClick={() => setActiveFileIndex(idx)}
                >
                  <span className="file-icon">{icon}</span>
                  <span>{fileName}</span>
                  <span className={`badge-pill ${file.status || 'created'}`}>
                    {file.status === 'modified' ? 'MOD' : 'NEW'}
                  </span>
                </button>
              )
            })}
          </div>

          {activeFile && (
            <div className="code-viewer-card">
              <div className="code-bar">
                <div className="file-meta">
                  <code>{activeFile.path}</code>
                  <span className="purpose-text">— {activeFile.purpose}</span>
                  {activeFile.size && <span className="purpose-text">({activeFile.size} B)</span>}
                </div>
                <div className="btn-group">
                  <button
                    className={`mode-btn ${!isEditing ? 'active' : ''}`}
                    onClick={() => setIsEditing(false)}
                  >
                    👁️ View
                  </button>
                  <button
                    className={`mode-btn ${isEditing ? 'active' : ''}`}
                    onClick={() => {
                      setEditorContent(activeFile.code || '')
                      setIsEditing(true)
                    }}
                  >
                    ✏️ Edit
                  </button>
                  {isEditing && (
                    <button
                      className="save-code-btn"
                      onClick={handleSaveFile}
                      disabled={saveLoading}
                    >
                      {saveLoading ? 'Saving…' : '💾 Save to Workspace'}
                    </button>
                  )}
                  <button className="copy-code-btn" onClick={copyCode}>
                    {copied ? '✅ Copied!' : '📋 Copy Code'}
                  </button>
                </div>
              </div>

              {isEditing ? (
                <textarea
                  className="code-editor-textarea"
                  value={editorContent}
                  onChange={(e) => setEditorContent(e.target.value)}
                  placeholder="Edit source code directly..."
                  spellCheck={false}
                />
              ) : (
                <div className="code-scroll-box">
                  <pre className="code-content">
                    <code>
                      {activeFile.code
                        ? activeFile.code.split('\n').map((line, i) => (
                            <div key={i} className="code-line">
                              <span className="line-num">{i + 1}</span>
                              <span className="line-text">{line}</span>
                            </div>
                          ))
                        : 'No source code available.'}
                    </code>
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <p className="empty-state">No source code files generated yet.</p>
      )}

      {/* Implementation Order */}
      {order.length > 0 && (
        <div className="section-block" style={{ marginTop: 24 }}>
          <h4>🛠️ Build Order &amp; Engineering Blueprint</h4>
          <div className="roadmap-list">
            {order.map((item) => (
              <div key={item.step} className="roadmap-step">
                <span className="step-num">{item.step}</span>
                <div>
                  <strong>{item.area}</strong>
                  <p>{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

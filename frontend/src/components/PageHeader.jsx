import React from 'react'

/**
 * Standardized Enterprise DevOps Page Header
 * Used consistently across all pages: Dashboard, Self-Healing, Agents, Logs, Database, Settings.
 * Provides unified category label, page title, optional badge, subtitle, and action buttons.
 */
export default function PageHeader({
  category,
  title,
  subtitle,
  badge,
  actions,
}) {
  return (
    <header className="page-header-standard">
      <div className="page-header-text">
        {category && <div className="page-header-category">{category}</div>}
        <div className="page-header-title-row">
          <h1 className="page-header-title">{title}</h1>
          {badge && (
            <span className={`status-pill ${badge.variant || 'completed'}`}>
              {badge.label}
            </span>
          )}
        </div>
        {subtitle && <p className="page-header-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-header-actions">{actions}</div>}
    </header>
  )
}


/**
 * Enterprise DevOps Settings Configuration & Section Definitions
 * Inspired by GitLab, Harness, and Azure DevOps control planes.
 */

export const PRIMARY_SETTINGS_SECTIONS = [
  { id: 'general', label: 'General', icon: '⚙️', description: 'Application preferences, theme selection, and runtime defaults' },
  { id: 'agents', label: 'Agents', icon: '🤖', description: 'Orchestrators, supervisors, and specialist agent configurations' },
  { id: 'execution', label: 'Execution', icon: '⚡', description: 'Autonomy level, self-healing thresholds, retry budgets, and execution policies' },
  { id: 'security', label: 'Security', icon: '🛡️', description: 'Production gates, database safeguards, secret protection, and rollback controls' },
  { id: 'buildTesting', label: 'Build & Testing', icon: '🧪', description: 'AST validation, unit/integration testing suites, and quality gates' },
  { id: 'integrations', label: 'Integrations', icon: '🔗', description: 'Toolchain connections: GitHub, Docker Registry, NVIDIA NIM, Webhooks, and Slack' },
  { id: 'notifications', label: 'Notifications', icon: '🔔', description: 'Alert routing, severity filters, channels, and failure webhooks' },
]

export const ADVANCED_SETTINGS_SECTIONS = [
  { id: 'workspace', label: 'Resources & Quotas', icon: '📁', description: 'Workspace isolation, disk quotas, memory constraints, and cleanup routines' },
  { id: 'audit', label: 'Audit & History', icon: '📜', description: 'Immutable configuration audit trail, agent actions, and compliance logging' },
  { id: 'advanced', label: 'Advanced Configuration', icon: '🔧', description: 'System-level flags, IPC buffer sizing, database drivers, and raw JSON editor' },
]

export const SETTINGS_SECTIONS = [
  ...PRIMARY_SETTINGS_SECTIONS,
  ...ADVANCED_SETTINGS_SECTIONS,
]

export const DEFAULT_SETTINGS = {
  theme: 'dark',
  general: {
    projectName: 'Autonomous DevOps Swarm',
    description: 'Multi-Agent Autonomous DevOps & Continuous Healing Engine',
    theme: 'dark',                  // 'light' | 'dark' | 'system'
    defaultBranch: 'main',
    defaultTargetEnv: 'development', // 'development' | 'staging' | 'production'
    activeEnvironment: 'production',
    logVerbosity: 'INFO',            // 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
    timezone: 'UTC',
    telemetryInterval: '2000ms',
    autoStartOnSubmit: true,
  },
  agents: {
    globalOrchestrator: { enabled: true, maxPhases: 5, strategy: 'adaptive' },
    developmentSupervisor: { enabled: true, autoHandoff: true },
    operationsSupervisor: { enabled: true, autoRollback: true },
    observerAgent: { enabled: true, heartbeatIntervalSec: 5 },
    roster: {
      'Planning Agent': { enabled: true, timeoutSec: 120, maxRetries: 2, model: 'gpt-4o-mini' },
      'Coding Agent': { enabled: true, timeoutSec: 180, maxRetries: 2, model: 'gpt-4o-mini' },
      'Build Agent': { enabled: true, timeoutSec: 60, maxRetries: 3 },
      'Testing Agent': { enabled: true, timeoutSec: 90, maxRetries: 2 },
      'Self-Healing Agent': { enabled: true, timeoutSec: 120, maxRetries: 2 },
      'Security Agent': { enabled: true, timeoutSec: 45, maxRetries: 1 },
      'Release Agent': { enabled: true, timeoutSec: 60, maxRetries: 1 },
      'Deploy Agent': { enabled: true, timeoutSec: 120, maxRetries: 2 },
      'Monitor Agent': { enabled: true, timeoutSec: 30, maxRetries: 3 },
    },
  },
  autonomous: {
    autonomousMode: true,
    autonomyLevel: 'supervised', // Recommended default: Supervised
    autoHealing: true,           // Recommended default: Enabled
    autoRetryFailedJobs: true,   // Recommended default: Enabled
    requireHumanApproval: true,  // Recommended default: Enabled
    maxRemediationAttempts: 2,   // Recommended default: 2
    rollbackOnFailedFix: true,   // Recommended default: Enabled
    concurrencyLimit: 3,
    stopOnFirstCriticalFailure: false,
  },
  safety: {
    approvalBeforeProduction: true,
    approvalBeforeDatabase: true,
    approvalBeforeInfra: true,
    protectedEnvironments: {
      production: true,
      staging: false,
      development: false,
    },
    riskPolicy: 'medium', // 'low', 'medium', 'high'
    maskSecretsInUi: true,
    preventSecretCommit: true,
    sessionTimeoutMinutes: 60,
  },
  selfHealing: {
    autoDiagnosis: true,
    autoRemediation: true,
    runHealthChecks: true,
    detectionInterval: '30s',
    verifyAfterFix: true,
    rollbackIfVerifyFails: true,
  },
  buildTesting: {
    astCompilation: true,
    unitTests: true,
    integrationTests: true,
    securityChecks: true,
    dependencyChecks: true,
    qualityGates: true,
    minSuccessRate: 85,          // Recommended default: 85%
    blockDeploymentOnFail: true,
    testTimeoutSec: 180,
  },
  integrations: {
    github: { connected: true, repo: 'autonomous-devops-swarm', branch: 'main' },
    docker: { connected: true, registry: 'docker.io/swarm-ci' },
    nvidia: { connected: true, provider: 'openai', model: 'gpt-4o-mini' },
    kubernetes: { connected: false, cluster: 'k8s-prod-cluster-01' },
    jenkins: { connected: false, server: 'https://ci.devops.internal' },
    slack: { connected: false, channel: '#devops-swarm' },
    webhook: { connected: true, endpoint: 'https://api.internal.devops/hooks/swarm' },
  },
  secrets: {
    githubToken: 'ghp_••••••••••••••••••••••••••••••••',
    dockerKey: 'dckr_••••••••••••••••••••••••••••••',
    nvidiaKey: 'nvapi-••••••••••••••••••••••••••••',
    webhookSecret: 'whsec_••••••••••••••••••••••••••••',
  },
  notifications: {
    email: 'devops-team@enterprise.internal',
    slackAlerts: true,
    webhookAlerts: true,
    minSeverity: 'warning', // 'info' | 'warning' | 'error' | 'critical'
    notifyOnHeal: true,
    notifyOnSecurityRisk: true,
    channels: {
      criticalFailures: true,
      healingEvents: true,
      qualityGateViolations: true,
      deploymentApprovalRequests: true,
    },
  },
  workspace: {
    sandboxRoot: 'backend/workspaces',
    diskQuotaMb: 2048,
    memoryLimitMb: 1024,
    autoCleanupWorkspaces: true,
    maxRetainedWorkspaces: 10,
    enforceStrictIsolation: true,
  },
  audit: {
    retentionDays: 90,
    logAgentInvocations: true,
    logConfigMutations: true,
    immutabilityCheck: true,
    exportFormat: 'json',
  },
  advanced: {
    systemDebug: false,
    telemetryIpcBufferKb: 256,
    sqlitePragmas: 'WAL=ON, synchronous=NORMAL',
    databaseDriver: 'sqlite_local', // 'sqlite_local' | 'mongodb_cluster'
    enableExperimentalSandboxing: false,
    rawJson: '',
  },
}

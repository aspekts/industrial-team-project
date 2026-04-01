const navButtons = document.querySelectorAll("[data-screen-target]");
const screens = document.querySelectorAll(".screen");
const confirmActionButton = document.getElementById("confirm-action");
const confirmationCard = document.getElementById("confirmation-card");
const clickableCards = document.querySelectorAll(".metric-card-action[data-screen-target]");
const accessibilityToggle = document.getElementById("accessibility-toggle");
const globalSearchInput = document.querySelector('.search-field input[type="search"]');
const dateFilterForm = document.getElementById("date-filter-form");
const dateFilterInput = document.getElementById("dashboard-date-filter");
const dateFilterClearButton = document.getElementById("date-filter-clear");
const dateFilterStatus = document.getElementById("date-filter-status");
const dashboardMetricCards = document.querySelectorAll(".metric-grid .metric-card");
const anomalyTrendChart = document.querySelector(".panel-graph");
const hostPressureChart = document.querySelector(".mini-graph");
const dashboardRole = window.__dashboardRole || document.body.dataset.dashboardRole || "ops";
const dashboardRoleLabel = window.__dashboardRoleLabel || document.body.dataset.dashboardRoleLabel || "Ops";

const largeUiStorageKey = "atm-monitor-large-ui";
const uiStateModes = {
  LOADING: "loading",
  READY: "ready",
  UNAVAILABLE: "unavailable",
};

const roleViewConfig = {
  admin: {
    defaultScreen: "dashboard",
    allowedScreens: ["dashboard", "atm-list", "alerts", "data-flow", "settings"],
    dashboardTitle: "Admin platform view",
    dashboardDescription: "Review source readiness, access model, and platform health across all pipeline components.",
    dashboardStatus: "Platform",
    bannerEyebrow: "Admin focus",
    bannerTitle: "Platform health and policy exceptions will appear here.",
    primaryActionLabel: "Review exception groups",
  },
  manager: {
    defaultScreen: "dashboard",
    allowedScreens: ["dashboard", "atm-list", "alerts", "action-center", "settings"],
    dashboardTitle: "Manager summary view",
    dashboardDescription: "Review flagged ATM issues, business impact, and the actions that need follow-up across monitored ATMs.",
    dashboardStatus: "Loading...",
    bannerEyebrow: "Manager focus",
    bannerTitle: "Top operational anomaly will appear here.",
    primaryActionLabel: "Open action queue",
  },
  ops: {
    defaultScreen: "dashboard",
    allowedScreens: ["dashboard", "atm-detail", "atm-list", "alerts", "data-flow", "settings", "action-center"],
    dashboardTitle: "Operations",
    dashboardDescription: "",
    dashboardStatus: "Loading...",
    bannerEyebrow: "Ops focus",
    bannerTitle: "Highest-priority operational signal will appear here.",
    primaryActionLabel: "Open investigation queue",
  },
};

const roleCardContent = {
  admin: {
    observedAtms: {
      title: "Source readiness",
      note: "Pipeline data sources loaded",
      subnote: "Sources with records in atm_logs.db",
      hint: "View source readiness",
    },
    atmAppErrors: {
      title: "Policy exceptions",
      note: "Critical detection groups active",
      subnote: "CRITICAL-severity groups from analysis_detections",
      hint: "Review policy exceptions",
    },
    hardwareAlerts: {
      title: "Hardware exceptions",
      note: "ATMH WARNING and CRITICAL events",
      subnote: "Source-backed hardware sensor severity readings",
      hint: "Review hardware exceptions",
    },
    eventThroughput: {
      title: "Platform throughput",
      note: "Average KAFK transaction rate",
      subnote: "KAFK transaction_rate_tps rolling average",
      hint: "Inspect platform throughput",
    },
  },
  manager: {
    observedAtms: {
      title: "ATM coverage",
      note: "ATMs with activity in the ATM application logs (ATMA)",
      subnote: "Distinct ATM IDs observed in the current monitoring window",
      hint: "View ATM coverage",
    },
    atmAppErrors: {
      title: "Flagged issues",
      note: "Critical issue groups needing manager review",
      subnote: "Grouped detections that indicate a likely operational issue",
      hint: "Review flagged issues",
    },
    hardwareAlerts: {
      title: "Queue pressure",
      note: "Hardware warnings and critical alerts from ATMH",
      subnote: "Hardware signals contributing to the local action queue",
      hint: "Review queue pressure",
    },
    eventThroughput: {
      title: "Transaction summary",
      note: "Average transactions per second",
      subnote: "KAFK transaction_rate_tps rolling average",
      hint: "Open action queue",
    },
  },
  ops: {
    observedAtms: {
      title: "Observed ATMs",
      note: "ATMs with records in ATMA source",
      subnote: "Distinct ATM IDs active in the monitoring window",
      hint: "View ATM list",
    },
    atmAppErrors: {
      title: "ATM app errors",
      note: "ERROR, TIMEOUT, and DISCONNECT events",
      subnote: "Source-backed from ATMA application log records",
      hint: "Review application anomalies",
    },
    hardwareAlerts: {
      title: "Hardware alerts",
      note: "ATMH WARNING and CRITICAL events",
      subnote: "Source-backed hardware sensor severity readings",
      hint: "Open hardware anomalies",
    },
    eventThroughput: {
      title: "Event throughput",
      note: "Average transactions per second",
      subnote: "KAFK transaction_rate_tps rolling average",
      hint: "Inspect data flow",
    },
  },
};

const roleChartContent = {
  admin: {
    anomalyTrend: {
      ready: {
        titleSelector: "Source event volume — hourly trend",
        contextSelector: "Total ATMA event volume grouped by hour across all monitored ATMs.",
        captionSelector: "Loading trend data...",
        legendSelector: "Loading...",
      },
    },
    hostPressure: {
      ready: {
        headerLabelSelector: "WINOS host pressure",
        headerValueSelector: "Loading...",
      },
    },
  },
  manager: {
    anomalyTrend: {
      ready: {
        titleSelector: "ATM activity — hourly trend",
        contextSelector: "Hourly ATMA event distribution showing operational activity across all ATMs.",
        captionSelector: "Loading trend data...",
        legendSelector: "Loading...",
      },
    },
    hostPressure: {
      ready: {
        headerLabelSelector: "WINOS host pressure",
        headerValueSelector: "Loading...",
      },
    },
  },
  ops: {
    anomalyTrend: {
      ready: {
        titleSelector: "ATMA error events — hourly trend",
        contextSelector: "ERROR, TIMEOUT, and DISCONNECT events by hour — peak marks highest anomaly concentration.",
        captionSelector: "Loading trend data...",
        legendSelector: "Loading...",
      },
    },
    hostPressure: {
      ready: {
        headerLabelSelector: "WINOS host pressure",
        headerValueSelector: "Loading...",
      },
    },
  },
};

const roleScreenContent = {
  admin: {
    headerCopy: "Maintain cross-system visibility across source readiness, governance surfaces, and platform health.",
    searchPlaceholder: "Search source, ATM ID, anomaly type, or page name",
    searchHelper: "Search across fleet data, anomaly patterns, source coverage, and recommendation trends.",
    navLabels: {
      dashboard: "Overview",
      atmList: "ATM fleet",
      alerts: "Anomaly patterns",
      dataFlow: "Data flow",
      settings: "Settings",
    },
    listTitle: "Full ATM fleet",
    listDescription: "Platform-wide view of all monitored ATMs, their current status, and active anomaly counts.",
    filtersTitle: "Fleet filters",
    tableTitle: "ATM fleet overview",
    alertsTitle: "Anomaly pattern analysis",
    alertsDescription: "Review active anomaly type distribution, cross-source detection groups, and recommendation engine performance across the monitored fleet.",
    criticalGroupTitle: "Platform exceptions",
    warningGroupTitle: "Source watchlist",
    settingsTitle: "Platform settings",
    settingsDescription: "Review account details, detection thresholds, and source coverage.",
  },
  manager: {
    headerCopy: "Track immediate ATM issues, local operational pressure, and the next items that need action.",
    searchPlaceholder: "Search ATM ID, branch, issue type, or source",
    searchHelper: "Search across ATM queues, issue groups, incidents, and recommendations.",
    navLabels: {
      dashboard: "Overview",
      atmList: "ATM queue",
      alerts: "Action queue",
      actionCenter: "Record action",
      settings: "Settings",
    },
    listTitle: "ATMs needing attention",
    listDescription: "Review the ATM queue, local operational context, and the issues that need follow-up now.",
    filtersTitle: "Operational filters",
    tableTitle: "ATM action queue",
    alertsTitle: "Immediate action queue",
    alertsDescription: "Review grouped operational issues that need local follow-up, escalation, or manager visibility.",
    criticalGroupTitle: "Needs action now",
    warningGroupTitle: "Monitor locally",
    actionTitle: "Manager action center",
    actionDescription: "Acknowledge flagged issues, assign follow-up work, and leave an auditable note for the next handoff.",
    settingsTitle: "Account and configuration",
    settingsDescription: "Review account details, detection thresholds, and source coverage.",
  },
  ops: {
    headerCopy: "",
    searchPlaceholder: "Search ATM ID, branch, incident, source, or recommendation",
    searchHelper: "Search across ATM incidents, recommendations, and supporting issue groups.",
    navLabels: {
      dashboard: "Overview",
      atmList: "ATM list",
      alerts: "Incidents",
      actionCenter: "Action center",
      dataFlow: "Data flow",
      settings: "Settings",
    },
    detailTitle: "Technical incident detail",
    detailDescription: "Use this page for ATM-level evidence, failure sequence review, and system troubleshooting context.",
    listTitle: "ATM investigation queue",
    listDescription: "Review ATM-level incidents, failure states, and the technical items that need investigation.",
    filtersTitle: "Incident filters",
    tableTitle: "ATM incident table",
    alertsTitle: "Active incidents and telemetry spikes",
    alertsDescription: "Review outage clusters, anomaly spikes, and infrastructure signals that need frontline technical response.",
    criticalGroupTitle: "Critical incidents",
    warningGroupTitle: "Telemetry watchlist",
    actionTitle: "Technical action center",
    actionDescription: "Record operational decisions against active anomaly groups and generate an evidence-backed audit trail.",
    settingsTitle: "Account and configuration",
    settingsDescription: "Review account details, detection thresholds, and notification preferences.",
  },
};

// Role-specific metric card navigation targets — ensures every visible card on
// the dashboard screen links to a unique, relevant page for each role.
// null = card is shown as a read-only metric (no navigation).
const roleCardTargets = {
  admin: [
    { target: "atm-list",  hint: "View ATM fleet" },
    { target: "alerts",    hint: "Review policy exceptions" },
    { target: "alerts",    hint: "Review hardware exceptions" },
    { target: "data-flow", hint: "Inspect data flow" },
  ],
  manager: [
    { target: "atm-list",  hint: "View ATM queue" },
    { target: "alerts",    hint: "Review flagged issues" },
    { target: "alerts",    hint: "Review queue pressure" },
    { target: "action-center", hint: "Record manager action" },
  ],
  ops: [
    { target: "atm-list",      hint: "View ATM list" },
    { target: "alerts",        hint: "Review incidents" },
    { target: "action-center", hint: "Take action" },
    { target: "data-flow",     hint: "Inspect data flow" },
  ],
};

const metricCardState = createMetricCardStateRegistry();
const chartState = createChartStateRegistry();
const activeRoleConfig = roleViewConfig[dashboardRole] || roleViewConfig.ops;

let currentScreenId = "dashboard";
let activeDateFilter = "";
const validScreenIds = new Set(activeRoleConfig.allowedScreens);
let currentAtmId = null;
let currentPrioritySummary = null;
let currentRecommendations = [];
let currentActionContext = null;

function setLargeUi(isEnabled) {
  document.body.classList.toggle("large-ui", isEnabled);

  if (accessibilityToggle) {
    accessibilityToggle.setAttribute("aria-pressed", String(isEnabled));
    accessibilityToggle.textContent = isEnabled ? "Use standard display" : "Turn on larger display";
  }
}

function loadLargeUiPreference() {
  const savedPreference = window.localStorage.getItem(largeUiStorageKey);
  return savedPreference === "true";
}

function getTrimmedText(node) {
  return node ? node.textContent.trim() : "";
}

function createMetricCardStateRegistry() {
  const [observedAtmsCard, atmAppErrorsCard, hardwareAlertsCard, eventThroughputCard] = dashboardMetricCards;

  return {
    observedAtms: buildMetricCardState(observedAtmsCard),
    atmAppErrors: buildMetricCardState(atmAppErrorsCard),
    hardwareAlerts: buildMetricCardState(hardwareAlertsCard),
    eventThroughput: buildMetricCardState(eventThroughputCard),
  };
}

function buildMetricCardState(card) {
  if (!card) {
    return null;
  }

  const titleNode = card.querySelector("h3");
  const valueNode = card.querySelector(".metric-value");
  const noteNode = card.querySelector(".metric-note");
  const subnoteNode = card.querySelector(".metric-subnote");
  const hintNode = card.querySelector(".metric-link-hint");

  return {
    card,
    titleNode,
    valueNode,
    noteNode,
    subnoteNode,
    hintNode,
    fallback: {
      title: getTrimmedText(titleNode),
      value: getTrimmedText(valueNode),
      note: getTrimmedText(noteNode),
      subnote: getTrimmedText(subnoteNode),
      hint: getTrimmedText(hintNode),
      ariaLabel: card.getAttribute("aria-label") || "",
    },
  };
}

function createChartStateRegistry() {
  return {
    anomalyTrend: buildChartState(anomalyTrendChart, {
      titleSelector: "#trend-title",
      contextSelector: ".graph-context",
      captionSelector: ".chart-caption",
      legendSelector: ".legend",
    }),
    hostPressure: buildChartState(hostPressureChart, {
      headerLabelSelector: ".mini-graph-header span",
      headerValueSelector: ".mini-graph-header strong",
    }),
  };
}

function buildChartState(container, selectors) {
  if (!container) {
    return null;
  }

  const nodes = {};
  const fallback = {
    ariaLabel: container.getAttribute("aria-label") || "",
  };

  Object.entries(selectors).forEach(([key, selector]) => {
    const node = container.querySelector(selector);
    nodes[key] = node;
    fallback[key] = getTrimmedText(node);
  });

  return {
    container,
    nodes,
    fallback,
  };
}

function setMetricCardState(metricKey, mode, payload = {}) {
  const state = metricCardState[metricKey];
  if (!state) {
    return;
  }

  const fallback = state.fallback;
  const title = payload.title ?? fallback.title;
  const value = payload.value ?? fallback.value;
  const note = payload.note ?? fallback.note;
  const subnote = payload.subnote ?? fallback.subnote;
  const hint = payload.hint ?? fallback.hint;
  const ariaLabel = payload.ariaLabel ?? fallback.ariaLabel;

  state.card.dataset.uiState = mode;
  state.card.setAttribute("aria-busy", String(mode === uiStateModes.LOADING));
  state.card.setAttribute("aria-label", ariaLabel);

  if (state.titleNode) {
    state.titleNode.textContent = title;
  }

  if (state.valueNode) {
    if (mode === uiStateModes.LOADING) {
      state.valueNode.textContent = payload.loadingValue ?? "—";
    } else if (mode === uiStateModes.UNAVAILABLE) {
      state.valueNode.textContent = payload.unavailableValue ?? "—";
    } else {
      state.valueNode.textContent = value;
    }
  }

  if (state.noteNode) {
    if (mode === uiStateModes.LOADING) {
      state.noteNode.textContent = payload.loadingNote ?? "Loading...";
    } else if (mode === uiStateModes.UNAVAILABLE) {
      state.noteNode.textContent = payload.unavailableNote ?? "No data available";
    } else {
      state.noteNode.textContent = note;
    }
  }

  if (state.subnoteNode) {
    if (mode === uiStateModes.LOADING) {
      state.subnoteNode.textContent = payload.loadingSubnote ?? "";
    } else if (mode === uiStateModes.UNAVAILABLE) {
      state.subnoteNode.textContent = payload.unavailableSubnote ?? "";
    } else {
      state.subnoteNode.textContent = subnote;
    }
  }

  if (state.hintNode) {
    const isClickable = state.card.classList.contains("metric-card-action");
    if (!isClickable) {
      state.hintNode.textContent = "";
    } else if (mode === uiStateModes.LOADING) {
      state.hintNode.textContent = payload.loadingHint ?? "";
    } else if (mode === uiStateModes.UNAVAILABLE) {
      state.hintNode.textContent = payload.unavailableHint ?? "";
    } else {
      state.hintNode.textContent = hint;
    }
  }
}

function setChartState(chartKey, mode, payload = {}) {
  const state = chartState[chartKey];
  if (!state) {
    return;
  }

  state.container.dataset.uiState = mode;
  state.container.setAttribute("aria-busy", String(mode === uiStateModes.LOADING));
  state.container.setAttribute("aria-label", payload.ariaLabel ?? state.fallback.ariaLabel);

  Object.entries(state.nodes).forEach(([key, node]) => {
    if (!node) {
      return;
    }

    if (mode === uiStateModes.LOADING) {
      node.textContent = payload.loading?.[key] ?? getLoadingChartCopy(key);
      return;
    }

    if (mode === uiStateModes.UNAVAILABLE) {
      node.textContent = payload.unavailable?.[key] ?? getUnavailableChartCopy(key);
      return;
    }

    node.textContent = payload.ready?.[key] ?? state.fallback[key];
  });
}

function getLoadingChartCopy(key) {
  const copy = {
    titleSelector: "Loading chart...",
    contextSelector: "Fetching source-backed data from the pipeline.",
    captionSelector: "Loading trend data...",
    legendSelector: "Loading",
    headerLabelSelector: "Loading metric",
    headerValueSelector: "—",
  };

  return copy[key] ?? "Loading...";
}

function getUnavailableChartCopy(key) {
  const copy = {
    titleSelector: "Chart unavailable",
    contextSelector: "No dataset connected for this visual.",
    captionSelector: "No trend data available.",
    legendSelector: "—",
    headerLabelSelector: "Metric unavailable",
    headerValueSelector: "—",
  };

  return copy[key] ?? "—";
}

function initializeDashboardUiState() {
  Object.keys(metricCardState).forEach((metricKey) => {
    setMetricCardState(metricKey, uiStateModes.READY);
  });

  Object.keys(chartState).forEach((chartKey) => {
    setChartState(chartKey, uiStateModes.READY);
  });

  window.dashboardUiState = {
    modes: uiStateModes,
    setMetricCardState,
    setChartState,
  };
}

function setTextContent(selector, value) {
  const node = document.querySelector(selector);
  if (node && typeof value === "string") {
    node.textContent = value;
  }
}

function setInputPlaceholder(selector, value) {
  const node = document.querySelector(selector);
  if (node && typeof value === "string") {
    node.setAttribute("placeholder", value);
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function applyRoleDashboardCopy() {
  setTextContent("#dashboard-title", activeRoleConfig.dashboardTitle);
  setTextContent("#dashboard-title + p", activeRoleConfig.dashboardDescription);
  setTextContent(".critical-banner .critical-eyebrow", activeRoleConfig.bannerEyebrow);
  setTextContent("#critical-banner-title", activeRoleConfig.bannerTitle);

  const primaryActionButton = document.querySelector(".critical-button");
  if (primaryActionButton) {
    primaryActionButton.textContent = activeRoleConfig.primaryActionLabel;
  }

  const cardsForRole = roleCardContent[dashboardRole] || roleCardContent.ops;
  Object.entries(cardsForRole).forEach(([metricKey, payload]) => {
    setMetricCardState(metricKey, uiStateModes.READY, payload);
  });

  const chartsForRole = roleChartContent[dashboardRole] || roleChartContent.ops;
  Object.entries(chartsForRole).forEach(([chartKey, payload]) => {
    setChartState(chartKey, uiStateModes.READY, payload);
  });

  const screenContent = roleScreenContent[dashboardRole] || roleScreenContent.ops;
  setTextContent(".header-copy", screenContent.headerCopy);
  setInputPlaceholder('.search-field input[type="search"]', screenContent.searchPlaceholder);
  setTextContent("#search-helper-text", screenContent.searchHelper || "Search across the dashboard.");
  setTextContent("#list-title", screenContent.listTitle);
  setTextContent("#list-title + p", screenContent.listDescription);
  setTextContent("#filters-title", screenContent.filtersTitle);
  setTextContent("#table-title", screenContent.tableTitle);
  setTextContent("#alerts-title-page", screenContent.alertsTitle);
  setTextContent("#alerts-title-page + p", screenContent.alertsDescription);
  setTextContent("#group-critical-title", screenContent.criticalGroupTitle);
  setTextContent("#group-warning-title", screenContent.warningGroupTitle);
  setTextContent("#settings-title", screenContent.settingsTitle);
  setTextContent("#settings-title + p", screenContent.settingsDescription);
  setTextContent("#detail-title", screenContent.detailTitle);
  setTextContent("#detail-title + p", screenContent.detailDescription);
  setTextContent("#action-title", screenContent.actionTitle);
  setTextContent("#action-title + p", screenContent.actionDescription);

  const navLabelMap = {
    dashboard: document.querySelector('[data-screen-target="dashboard"] span'),
    atmList: document.querySelector('[data-screen-target="atm-list"] span'),
    alerts: document.querySelector('[data-screen-target="alerts"] span'),
    actionCenter: document.querySelector('[data-screen-target="action-center"] span'),
    dataFlow: document.querySelector('[data-screen-target="data-flow"] span'),
    settings: document.querySelector('[data-screen-target="settings"] span'),
  };

  Object.entries(screenContent.navLabels).forEach(([key, value]) => {
    const node = navLabelMap[key];
    if (node) {
      node.textContent = value;
    }
  });
}

function configureMetricCardTargets() {
  const targets = roleCardTargets[dashboardRole] || roleCardTargets.ops;
  dashboardMetricCards.forEach((card, i) => {
    const cfg = targets[i];
    if (!cfg) return;
    const hintNode = card.querySelector(".metric-link-hint");
    if (cfg.target) {
      card.dataset.screenTarget = cfg.target;
      card.classList.add("metric-card-action");
      card.setAttribute("tabindex", "0");
      card.setAttribute("role", "button");
      if (hintNode) hintNode.textContent = cfg.hint;
    } else {
      delete card.dataset.screenTarget;
      card.classList.remove("metric-card-action");
      card.removeAttribute("tabindex");
      card.removeAttribute("role");
      if (hintNode) hintNode.textContent = "";
    }
  });
}

function normalizeSearchValue(value) {
  return value.trim().toLowerCase();
}

function formatFilterDate(dateValue) {
  if (!dateValue) {
    return "";
  }

  const parsedDate = new Date(`${dateValue}T00:00:00`);
  if (Number.isNaN(parsedDate.getTime())) {
    return dateValue;
  }

  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(parsedDate);
}

function setDateFilterStatus(message) {
  if (dateFilterStatus) {
    dateFilterStatus.textContent = message;
  }
}

function buildApiUrl(path) {
  const url = new URL(path, window.location.origin);
  if (activeDateFilter) {
    url.searchParams.set("date", activeDateFilter);
  }
  return url.toString();
}

function updateDateFilterStatusFromState() {
  if (activeDateFilter) {
    setDateFilterStatus(`Filtering all dashboard data to ${formatFilterDate(activeDateFilter)}.`);
    return;
  }

  setDateFilterStatus("Showing all available dates.");
}

function setDashboardLoadingState() {
  Object.entries(roleCardContent[dashboardRole] || roleCardContent.ops).forEach(([metricKey, payload]) => {
    setMetricCardState(metricKey, uiStateModes.LOADING, payload);
  });
}

function filterAtmRows(query) {
  const atmRows = document.querySelectorAll("#atm-list tbody tr");
  if (!atmRows.length) {
    return 0;
  }

  let matchCount = 0;
  atmRows.forEach((row) => {
    const rowText = normalizeSearchValue(row.textContent);
    const isMatch = !query || rowText.includes(query);
    row.hidden = !isMatch;
    if (isMatch) {
      matchCount += 1;
    }
  });

  return matchCount;
}

function filterAnomalyItems(query) {
  const critItems = document.querySelectorAll("#alerts-critical-list li");
  const warnItems = document.querySelectorAll("#alerts-warning-list li");
  const recItems = document.querySelectorAll("#rec-list .rec-card");
  const incidentItems = document.querySelectorAll("#incidents-list li");
  let matchCount = 0;

  [critItems, warnItems].forEach((items) => {
    items.forEach((item) => {
      const text = normalizeSearchValue(item.textContent);
      const isMatch = !query || text.includes(query);
      item.hidden = !isMatch;
      if (isMatch) matchCount += 1;
    });
  });

  recItems.forEach((card) => {
    const text = normalizeSearchValue(card.textContent);
    const isMatch = !query || text.includes(query);
    card.hidden = !isMatch;
    if (isMatch) matchCount += 1;
  });

  incidentItems.forEach((item) => {
    const text = normalizeSearchValue(item.textContent);
    const isMatch = !query || text.includes(query);
    item.hidden = !isMatch;
    if (isMatch) matchCount += 1;
  });

  return matchCount;
}

function setSearchResultCount(count, context, query = "") {
  const el = document.getElementById("search-result-count");
  if (!el) return;
  if (!context) {
    el.hidden = true;
    el.textContent = "";
    return;
  }
  el.hidden = false;
  el.textContent = count > 0
    ? `${count} result${count !== 1 ? "s" : ""} in ${context}`
    : `No matches for "${query}". Try an ATM ID, branch, issue type, or source.`;
}

function clearSearchFilters() {
  filterAtmRows("");
  filterAnomalyItems("");
  setSearchResultCount(0, null);
}

function getSearchableScreenIds() {
  return Array.from(validScreenIds);
}

function findBestSearchTarget(query) {
  const searchableScreenIds = getSearchableScreenIds();

  for (const screenId of searchableScreenIds) {
    const navLabel = document.querySelector(`[data-screen-target="${screenId}"] span`);
    if (navLabel && normalizeSearchValue(navLabel.textContent).includes(query)) {
      return screenId;
    }
  }

  for (const screenId of searchableScreenIds) {
    const screen = document.getElementById(screenId);
    if (screen && normalizeSearchValue(screen.textContent).includes(query)) {
      return screenId;
    }
  }

  return null;
}

function applySearch(query) {
  const normalizedQuery = normalizeSearchValue(query);

  if (!normalizedQuery) {
    clearSearchFilters();
    return;
  }

  // 1. Filter ATM rows — if matches found, navigate to ATM list
  const atmMatchCount = filterAtmRows(normalizedQuery);
  if (atmMatchCount && validScreenIds.has("atm-list")) {
    navigateToScreen("atm-list");
    setSearchResultCount(atmMatchCount, "ATM list", normalizedQuery);
    return;
  }

  // 2. Filter anomaly items — if matches found, navigate to alerts
  const anomalyMatchCount = filterAnomalyItems(normalizedQuery);
  const alertsScreenId = validScreenIds.has("alerts") ? "alerts" : null;
  if (anomalyMatchCount && alertsScreenId) {
    navigateToScreen(alertsScreenId);
    setSearchResultCount(anomalyMatchCount, "issues, incidents, and recommendations", normalizedQuery);
    return;
  }

  // 3. Navigate to a screen whose content or nav label matches
  const targetScreenId = findBestSearchTarget(normalizedQuery);
  if (targetScreenId) {
    navigateToScreen(targetScreenId);
    setSearchResultCount(1, document.querySelector(`[data-screen-target="${targetScreenId}"] span`)?.textContent || targetScreenId, normalizedQuery);
    return;
  }

  setSearchResultCount(0, "dashboard", normalizedQuery);
}

function configureRoleView() {
  document.body.dataset.dashboardRole = dashboardRole;
  document.body.dataset.dashboardRoleLabel = dashboardRoleLabel;

  const sidebarEyebrow = document.querySelector(".sidebar-eyebrow");
  if (sidebarEyebrow) {
    sidebarEyebrow.textContent = `${dashboardRoleLabel} Console`;
  }

  screens.forEach((screen) => {
    screen.hidden = !validScreenIds.has(screen.id);
  });

  document.querySelectorAll("[data-screen-target]").forEach((element) => {
    const targetId = element.dataset.screenTarget;
    const isAllowed = validScreenIds.has(targetId);
    element.hidden = !isAllowed;

    if (!isAllowed) {
      element.setAttribute("aria-hidden", "true");
      element.setAttribute("tabindex", "-1");
    } else {
      element.removeAttribute("aria-hidden");
      if (element.classList.contains("metric-card")) {
        element.setAttribute("tabindex", "0");
      } else {
        element.removeAttribute("tabindex");
      }
    }
  });

  const adminAnalysisPanel = document.getElementById("admin-analysis-panel");
  if (adminAnalysisPanel) adminAnalysisPanel.hidden = dashboardRole !== "admin";
  const adminAnomalyBreakdown = document.getElementById("admin-anomaly-breakdown");
  if (adminAnomalyBreakdown) adminAnomalyBreakdown.hidden = dashboardRole !== "admin";
}

function showScreen(targetId) {
  if (!validScreenIds.has(targetId)) {
    return;
  }

  screens.forEach((screen) => {
    screen.classList.toggle("is-visible", screen.id === targetId);
  });

  navButtons.forEach((button) => {
    const isActive = button.dataset.screenTarget === targetId;
    button.classList.toggle("is-active", isActive);
    if (isActive) {
      button.setAttribute("aria-current", "page");
    } else {
      button.removeAttribute("aria-current");
    }
  });

  currentScreenId = targetId;

  const activeHeading = document.querySelector(`#${targetId} h2`);
  if (activeHeading) {
    activeHeading.setAttribute("tabindex", "-1");
    activeHeading.focus();
  }
}

function navigateToScreen(targetId) {
  if (!validScreenIds.has(targetId) || targetId === currentScreenId) {
    return;
  }

  window.location.hash = targetId;
}

navButtons.forEach((button) => {
  button.addEventListener("click", () => {
    navigateToScreen(button.dataset.screenTarget);
  });
});

clickableCards.forEach((card) => {
  card.addEventListener("click", () => {
    navigateToScreen(card.dataset.screenTarget);
  });

  card.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      navigateToScreen(card.dataset.screenTarget);
    }
  });
});

if (accessibilityToggle) {
  accessibilityToggle.addEventListener("click", () => {
    const nextValue = !document.body.classList.contains("large-ui");
    setLargeUi(nextValue);
    window.localStorage.setItem(largeUiStorageKey, String(nextValue));
  });
}

if (globalSearchInput) {
  globalSearchInput.addEventListener("input", (event) => {
    if (!event.target.value.trim()) clearSearchFilters();
    else applySearch(event.target.value);
  });

  globalSearchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      applySearch(event.target.value);
    }
  });
}

// ATM detail navigation — wire open buttons after ATM list renders
function wireAtmDetailButtons() {
  document.querySelectorAll(".atm-open-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const atmId = btn.dataset.atmId;
      if (atmId) {
        currentAtmId = atmId;
        navigateToScreen("atm-detail");
        fetchAtmDetail(atmId);
      }
    });
  });
}

// Filter chips on ATM list
document.querySelectorAll(".filter-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    document.querySelectorAll(".filter-chip").forEach((c) => c.classList.remove("is-active"));
    chip.classList.add("is-active");
    const filter = chip.dataset.filter || "all";
    const rows = document.querySelectorAll("#atm-list-tbody tr");
    rows.forEach((row) => {
      if (filter === "all") {
        row.hidden = false;
      } else {
        const pillEl = row.querySelector(".status-pill");
        const rowStatus = pillEl ? pillEl.className.includes(filter) : false;
        row.hidden = !rowStatus;
      }
    });
  });
});

function getQuickActionLabels() {
  if (dashboardRole === "manager") {
    return {
      primary: "Assign for review",
      secondary: "Acknowledge issue",
    };
  }

  return {
    primary: "Escalate to field support",
    secondary: "Acknowledge issue",
  };
}

async function recordAction(payload) {
  const response = await fetch("/api/actions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.json();
}

function populateActionHistory(actions) {
  const list = document.getElementById("action-history-list");
  if (!list) return;

  if (!actions || actions.length === 0) {
    list.innerHTML = "<li>No actions recorded yet.</li>";
    return;
  }

  list.innerHTML = actions
    .map((action) => {
      const atm = action.atm_id ? ` / ${escapeHtml(action.atm_id)}` : "";
      const anomaly = action.anomaly_name ? ` - ${escapeHtml(action.anomaly_name)}` : "";
      const notes = action.notes ? `<br><span class=\"metric-subnote\">${escapeHtml(action.notes)}</span>` : "";
      const owner = action.username || action.user_role || "team";
      return `<li><strong>${escapeHtml(action.action_label)}</strong> on ${escapeHtml(owner)}${atm}${anomaly}<br><span class=\"metric-subnote\">${escapeHtml((action.created_at || "").slice(0, 16))}</span>${notes}</li>`;
    })
    .join("");
}

// Confirm action button — dynamic based on priority summary context
if (confirmActionButton && confirmationCard) {
  confirmActionButton.addEventListener("click", async () => {
    const selected = document.querySelector('.radio-card input[type="radio"]:checked');
    const selectedLabel = selected
      ? selected.closest(".radio-card").querySelector("strong").textContent
      : "Review and monitor";
    const actionContext = currentActionContext || currentPrioritySummary || {};
    const atm = currentAtmId || actionContext.atm_id || "affected ATM";
    const anomaly = actionContext.anomaly_name || "active anomaly";
    const note = document.getElementById("action-textarea");
    const noteText = note && note.value.trim() ? note.value.trim() : "No additional notes.";
    confirmActionButton.disabled = true;

    try {
      const result = await recordAction({
        action_label: selectedLabel,
        notes: noteText === "No additional notes." ? "" : noteText,
        atm_id: atm === "affected ATM" ? "" : atm,
        anomaly_type: actionContext.anomaly_type || "",
        anomaly_name: anomaly,
      });

      if (result.status !== "ok") {
        confirmationCard.innerHTML = `<p><strong>Unable to record action.</strong></p><p class=\"metric-subnote\">${escapeHtml(result.reason || "Try again.")}</p>`;
        confirmationCard.focus();
        return;
      }

      confirmationCard.innerHTML = `
        <p><strong>Action recorded:</strong> ${escapeHtml(selectedLabel)}</p>
        <p>ATM: ${escapeHtml(atm)} - ${escapeHtml(anomaly)}.</p>
        <p class="metric-subnote" style="margin-top:0.5rem;">Note: ${escapeHtml(noteText)}</p>`;
      confirmationCard.focus();

      try {
        const history = await fetch("/api/actions").then((r) => r.json());
        if (history.status === "ok") populateActionHistory(history.actions);
      } catch {}
    } catch (error) {
      confirmationCard.innerHTML = "<p><strong>Unable to record action.</strong></p><p class=\"metric-subnote\">Please try again.</p>";
      confirmationCard.focus();
    } finally {
      confirmActionButton.disabled = false;
    }
  });
}

if (dateFilterForm) {
  dateFilterForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const value = dateFilterInput ? dateFilterInput.value.trim() : "";
    if (value) {
      activeDateFilter = value;
      updateDateFilterStatusFromState();
      fetchDashboardData();
    }
  });
}

if (dateFilterClearButton) {
  dateFilterClearButton.addEventListener("click", () => {
    activeDateFilter = "";
    if (dateFilterInput) dateFilterInput.value = "";
    updateDateFilterStatusFromState();
    fetchDashboardData();
  });
}

window.addEventListener("hashchange", () => {
  const targetId = window.location.hash.replace("#", "") || activeRoleConfig.defaultScreen;
  showScreen(validScreenIds.has(targetId) ? targetId : activeRoleConfig.defaultScreen);
});

setLargeUi(loadLargeUiPreference());
initializeDashboardUiState();
configureMetricCardTargets();
configureRoleView();
applyRoleDashboardCopy();

const initialTargetId = window.location.hash.replace("#", "") || activeRoleConfig.defaultScreen;
showScreen(validScreenIds.has(initialTargetId) ? initialTargetId : activeRoleConfig.defaultScreen);

const feedbackHistoryToggle = document.getElementById("feedback-history-toggle");
if (feedbackHistoryToggle) {
  feedbackHistoryToggle.addEventListener("click", () => {
    const histList = document.getElementById("feedback-history-list");
    if (!histList) return;
    const isHidden = histList.hidden;
    histList.hidden = !isHidden;
    feedbackHistoryToggle.textContent = isHidden ? "Hide history" : "Show history";
    feedbackHistoryToggle.setAttribute("aria-expanded", String(isHidden));
  });
}

// ─── Data layer ───────────────────────────────────────────────────────────────

async function fetchDashboardData() {
  setDashboardLoadingState();
  setDateFilterStatus(
    activeDateFilter
      ? `Loading data for ${formatFilterDate(activeDateFilter)}...`
      : "Loading data for all available dates..."
  );

  try {
    const [summary, scale, snapshot, atmList, alerts, trend, sourceChecks, prioritySummary, winosTrend, mlSummary, incidents, recommendations, feedbackHistory, actions] =
      await Promise.all([
        fetch(buildApiUrl("/api/summary")).then((r) => r.json()),
        fetch(buildApiUrl("/api/scale")).then((r) => r.json()),
        fetch(buildApiUrl("/api/source-snapshot")).then((r) => r.json()),
        fetch(buildApiUrl("/api/atm-list")).then((r) => r.json()),
        fetch(buildApiUrl("/api/alerts")).then((r) => r.json()),
        fetch("/api/trend").then((r) => r.json()),
        fetch("/api/source-checks").then((r) => r.json()),
        fetch("/api/priority-summary").then((r) => r.json()),
        fetch("/api/winos-trend").then((r) => r.json()),
        fetch("/api/ml-summary").then((r) => r.json()),
        fetch("/api/incidents").then((r) => r.json()),
        fetch("/api/recommendations").then((r) => r.json()),
        fetch("/api/feedback-history").then((r) => r.json()),
        fetch("/api/actions").then((r) => r.json()),
      ]);

    if (summary.status === "ok") populateSummary(summary);
    if (scale.status === "ok") populateScale(scale);
    if (snapshot.status === "ok") {
      populateSourceSnapshot(snapshot.sources);
      populateSettingsSourceList(snapshot.sources);
    }
    if (atmList.status === "ok") populateAtmList(atmList.atms);
    if (alerts.status === "ok") populateAlerts(alerts);
    if (trend.status === "ok") populateTrendChart(trend);
    if (winosTrend.status === "ok") populateWinosMiniGraph(winosTrend);
    if (sourceChecks.status === "ok") populateSourceChecks(sourceChecks.checks);
    if (mlSummary.status === "ok") populateMlSummary(mlSummary);
    if (incidents.status === "ok") populateIncidents(incidents);
    if (dashboardRole === "admin") {
      const mlData = mlSummary.status === "ok" ? mlSummary : { total_scored: 0, total_anomalies: 0, model_version: null, sources: [] };
      const fbData = feedbackHistory.status === "ok" ? feedbackHistory : { stats: [], history: [] };
      populateAdminAnalysisPanel(mlData, fbData);
      if (alerts.status === "ok" && recommendations.status === "ok") {
        populateAdminAnomalyBreakdown(alerts, recommendations.recommendations);
      }
    }
    if (validScreenIds.has("data-flow")) {
      const snapData = snapshot.status === "ok" ? snapshot : { sources: [] };
      const alertsData = alerts.status === "ok" ? alerts : { critical: [], warning: [] };
      const mlData = mlSummary.status === "ok" ? mlSummary : { total_scored: 0, total_anomalies: 0, model_version: null, sources: [] };
      const incData = incidents.status === "ok" ? incidents : { incidents: [], total: 0 };
      const recData = recommendations.status === "ok" ? recommendations : { recommendations: [] };
      populateDataFlow(snapData, alertsData, mlData, incData, recData);
    }
    if (recommendations.status === "ok") {
      currentRecommendations = recommendations.recommendations;
      populateRecommendations(recommendations.recommendations);
      if (dashboardRole === "ops" && recommendations.recommendations.length > 0) {
        populateActionCenterFromRec(recommendations.recommendations);
      }
    }
    if (feedbackHistory.status === "ok") populateFeedbackHistory(feedbackHistory);
    if (actions.status === "ok") populateActionHistory(actions.actions);
    if (prioritySummary.status === "ok") {
      currentPrioritySummary = prioritySummary;
      populatePrioritySummary(prioritySummary);
      if (validScreenIds.has("action-center")) populateActionCenter(prioritySummary);
    }
    populateSettingsAccount();
  } catch (err) {
    console.warn("[dashboard] data fetch failed:", err);
    setDateFilterStatus("Unable to load dashboard data for the selected date.");
  }
}

function populateSummary(data) {
  const isAdmin = dashboardRole === "admin";
  const isManager = dashboardRole === "manager";

  setMetricCardState("observedAtms", uiStateModes.READY, {
    value: String(data.observed_atms),
    note: isAdmin
      ? `${data.observed_atms} ATMs with active telemetry sources`
      : isManager
      ? `${data.observed_atms} ATMs in managed estate`
      : `${data.app_errors} app error events across ATMA`,
  });

  setMetricCardState("atmAppErrors", uiStateModes.READY, {
    value: isAdmin ? String(data.failure_windows) : String(data.app_errors),
    note: isAdmin
      ? `${data.failure_windows} critical detection group${data.failure_windows !== 1 ? "s" : ""}`
      : isManager
      ? `${data.failure_windows} critical detection group${data.failure_windows !== 1 ? "s" : ""}`
      : `${data.failure_windows} critical detection group${data.failure_windows !== 1 ? "s" : ""}`,
  });

  setMetricCardState("hardwareAlerts", uiStateModes.READY, {
    value: String(data.hardware_alerts),
    note: isAdmin
      ? "ATMH policy-impacting exceptions"
      : isManager
      ? `${data.hardware_alerts} ATMH alert${data.hardware_alerts !== 1 ? "s" : ""} in queue`
      : "ATMH WARNING + CRITICAL events",
  });

  setMetricCardState("eventThroughput", uiStateModes.READY, {
    value: `${data.avg_tps} TPS`,
    note: isAdmin
      ? "Platform-level KAFK ingestion rate"
      : isManager
      ? "Average KAFK transaction throughput"
      : "Average transactions per KAFK window",
  });

  const pill = document.getElementById("dashboard-status-pill");
  if (pill) {
    const hasCritical = data.failure_windows > 0;
    pill.textContent = hasCritical ? "Critical" : "Operational";
    pill.className = `status-pill ${hasCritical ? "status-critical" : "status-ok"}`;
  }
}

function populateScale(data) {
  const setText = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };
  setText("scale-sources", String(data.sources));
  setText("scale-atms", String(data.atms));
  setText("scale-window", data.filter_date ? formatFilterDate(data.filter_date) : data.time_window);
  setText("scale-avg-tps", String(data.avg_tps));
}

function populateSourceSnapshot(sources) {
  const tbody = document.getElementById("source-snapshot-tbody");
  if (!tbody) return;

  const backedMetric = {
    ATMA: "Application log events",
    ATMH: "Hardware sensor events",
    GCP: "Cloud runtime metrics",
    KAFK: "Transaction stream events",
    PROM: "Prometheus metrics",
    TERM: "Terminal handler logs",
    WINOS: "Windows OS metrics",
  };

  tbody.innerHTML = sources
    .map(
      (s) => `
    <tr>
      <th scope="row">${s.source}</th>
      <td>${backedMetric[s.source] || s.source}</td>
      <td>${s.signal === "present" ? "Live" : s.signal === "empty" ? "Empty" : "Absent"}</td>
      <td>${s.status}</td>
    </tr>`
    )
    .join("");
}

function populateAtmList(atms) {
  const tbody = document.getElementById("atm-list-tbody");
  if (!tbody) return;
  if (!atms.length) {
    tbody.innerHTML = `<tr><td colspan="6">${activeDateFilter ? `No ATM data available for ${formatFilterDate(activeDateFilter)}.` : "No ATM data available."}</td></tr>`;
    return;
  }
  tbody.innerHTML = atms
    .map((a) => {
      const pillClass =
        a.status === "critical"
          ? "status-critical"
          : a.status === "warning"
          ? "status-warning"
          : "status-ok";
      const pillLabel =
        a.status === "critical" ? "Critical" : a.status === "warning" ? "Warning" : "OK";
      const issue = a.issue || "No active anomaly";
      const lastUpdate = a.last_update ? a.last_update.slice(0, 16) : "Unknown";
      return `
    <tr>
      <th scope="row">${a.atm_id}</th>
      <td>${a.location}</td>
      <td><span class="status-pill ${pillClass}">${pillLabel}</span></td>
      <td>${issue}</td>
      <td>${lastUpdate}</td>
      <td>${
        validScreenIds.has("atm-detail")
          ? `<button class="text-button atm-open-btn" type="button" data-atm-id="${a.atm_id}" data-screen-target="atm-detail">Open</button>`
          : `<button class="text-button" type="button" data-screen-target="alerts">Alerts</button>`
      }</td>
    </tr>`;
    })
    .join("");

  wireAtmDetailButtons();
}

function populateAlerts(data) {
  const critSummary = document.getElementById("alerts-critical-summary");
  const critList = document.getElementById("alerts-critical-list");
  const warnSummary = document.getElementById("alerts-warning-summary");
  const warnList = document.getElementById("alerts-warning-list");

  if (critSummary) {
    critSummary.textContent = `${data.critical.length} critical anomaly group${data.critical.length !== 1 ? "s" : ""}${data.filter_date ? ` for ${formatFilterDate(data.filter_date)}` : ""}`;
  }
  if (critList) {
    critList.innerHTML = data.critical.length
      ? data.critical
          .map(
            (a) =>
              `<li><strong>${a.anomaly_name} (${a.anomaly_type})</strong> — ${a.source}${a.atm_id && a.atm_id !== "N/A" ? " / " + a.atm_id : ""}: ${a.description || ""} <em>(${a.event_count} event${a.event_count !== 1 ? "s" : ""})</em></li>`
          )
          .join("")
      : `<li>${data.filter_date ? `No critical anomalies detected for ${formatFilterDate(data.filter_date)}.` : "No critical anomalies detected."}</li>`;
  }

  if (warnSummary) {
    warnSummary.textContent = `${data.warning.length} warning anomaly group${data.warning.length !== 1 ? "s" : ""}${data.filter_date ? ` for ${formatFilterDate(data.filter_date)}` : ""}`;
  }
  if (warnList) {
    warnList.innerHTML = data.warning.length
      ? data.warning
          .map(
            (a) =>
              `<li><strong>${a.anomaly_name} (${a.anomaly_type})</strong> — ${a.source}${a.atm_id && a.atm_id !== "N/A" ? " / " + a.atm_id : ""}: ${a.description || ""} <em>(${a.event_count} event${a.event_count !== 1 ? "s" : ""})</em></li>`
          )
          .join("")
      : `<li>${data.filter_date ? `No warning anomalies detected for ${formatFilterDate(data.filter_date)}.` : "No warning anomalies detected."}</li>`;
  }

  const hostEl = document.getElementById("host-pressure-value");
  if (hostEl) {
    const winosWarning = data.warning.find((a) => a.source === "WINOS");
    hostEl.textContent = winosWarning ? "Elevated" : "Normal";
  }
}

function populateTrendChart(data) {
  if (!data.points || data.points.length < 2) return;

  const titleNode = document.getElementById("trend-title");
  const captionNode = document.querySelector(".chart-caption");
  const legendNode = document.querySelector(".panel-graph .legend");

  if (titleNode) {
    titleNode.textContent =
      dashboardRole === "ops"
        ? "ATMA error events — hourly trend"
        : dashboardRole === "manager"
        ? "ATM activity — hourly trend"
        : "Source event volume — hourly trend";
  }

  const useErrors = dashboardRole !== "admin";
  const values = data.points.map((p) => (useErrors ? p.errors : p.total));
  const maxVal = Math.max(...values, 1);
  const peakErrors = data.peak_errors || 0;

  if (captionNode) {
    captionNode.textContent =
      peakErrors > 0
        ? `${data.points.length} hourly buckets. Peak at ${data.peak_hour}:00 — ${peakErrors} error event${peakErrors !== 1 ? "s" : ""}.`
        : `${data.points.length} hourly buckets. No error events detected in the monitoring window.`;
  }
  if (legendNode) {
    legendNode.textContent = peakErrors > 0 ? `Peak: ${peakErrors} errors at ${data.peak_hour}:00` : "No errors detected";
  }

  const svgNS = "http://www.w3.org/2000/svg";
  const chartSvg = document.querySelector(".trend-chart-line svg");
  if (!chartSvg) return;

  const X_START = 20, X_END = 500, Y_BOTTOM = 200, Y_TOP = 30;
  const plotW = X_END - X_START;
  const plotH = Y_BOTTOM - Y_TOP;
  const n = data.points.length;

  const coords = values.map((v, i) => ({
    x: Math.round(X_START + (i / (n - 1)) * plotW),
    y: Math.round(Y_BOTTOM - (v / maxVal) * plotH),
    v,
    hour: data.points[i].hour,
  }));

  const pathD = coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c.x} ${c.y}`).join(" ");

  // Remove old static path and dynamic peak elements
  chartSvg.querySelectorAll("path, .dyn-peak").forEach((el) => el.remove());

  const pathEl = document.createElementNS(svgNS, "path");
  pathEl.setAttribute("d", pathD);
  chartSvg.appendChild(pathEl);

  if (peakErrors > 0 && data.peak_hour) {
    const peakIdx = data.points.findIndex((p) => p.hour === data.peak_hour);
    const peakCoord = peakIdx >= 0 ? coords[peakIdx] : null;

    if (peakCoord) {
      const circle = document.createElementNS(svgNS, "circle");
      circle.setAttribute("cx", peakCoord.x);
      circle.setAttribute("cy", peakCoord.y);
      circle.setAttribute("r", "8");
      circle.setAttribute("class", "anomaly-point dyn-peak");
      chartSvg.appendChild(circle);

      const guide = document.createElementNS(svgNS, "line");
      guide.setAttribute("x1", peakCoord.x);
      guide.setAttribute("y1", peakCoord.y);
      guide.setAttribute("x2", peakCoord.x);
      guide.setAttribute("y2", "200");
      guide.setAttribute("class", "anomaly-guide dyn-peak");
      chartSvg.appendChild(guide);

      const labelX = Math.min(peakCoord.x - 14, 375);
      const labelY = Math.max(peakCoord.y - 30, 4);

      const box = document.createElementNS(svgNS, "rect");
      box.setAttribute("x", labelX);
      box.setAttribute("y", labelY);
      box.setAttribute("width", "128");
      box.setAttribute("height", "24");
      box.setAttribute("rx", "8");
      box.setAttribute("class", "anomaly-label-box dyn-peak");
      chartSvg.appendChild(box);

      const txt = document.createElementNS(svgNS, "text");
      txt.setAttribute("x", labelX + 8);
      txt.setAttribute("y", labelY + 17);
      txt.setAttribute("class", "anomaly-text dyn-peak");
      txt.textContent = `${data.peak_hour}:00 — ${peakErrors} error${peakErrors !== 1 ? "s" : ""}`;
      chartSvg.appendChild(txt);
    }
  }

  // Update axis labels
  const axisContainer = document.querySelector(".chart-axis-labels");
  if (axisContainer && n >= 4) {
    const step = Math.floor((n - 1) / 3);
    const idxs = [0, step, step * 2, n - 1];
    const spans = axisContainer.querySelectorAll("span");
    idxs.forEach((idx, i) => {
      if (spans[i]) spans[i].textContent = `${data.points[idx].hour}:00`;
    });
  }
}

function populateSourceChecks(checks) {
  const list = document.getElementById("source-checks-list");
  if (!list) return;

  list.innerHTML = checks
    .map((c) => {
      const pillClass =
        c.severity === "critical"
          ? "status-critical"
          : c.severity === "warning"
          ? "status-warning"
          : c.severity === "absent"
          ? ""
          : "status-ok";
      const pillLabel =
        c.severity === "critical"
          ? "Critical"
          : c.severity === "warning"
          ? "Warning"
          : c.severity === "absent"
          ? "Absent"
          : "OK";
      const countLabel = c.value > 0 ? `${c.value.toLocaleString()} event${c.value !== 1 ? "s" : ""}` : "Clear";
      return `
      <li>
        <div>
          <strong>${c.label}</strong>
          <p>${c.detail}</p>
        </div>
        <span class="status-pill ${pillClass}">${pillLabel} — ${countLabel}</span>
      </li>`;
    })
    .join("");
}

function populatePrioritySummary(data) {
  const banner = document.querySelector(".critical-banner");
  if (dashboardRole === "admin") {
    if (banner) banner.hidden = true;
    const heroPanel = document.querySelector(".panel-hero");
    if (heroPanel) heroPanel.hidden = true;
    return;
  }
  if (!data.anomaly_name) {
    if (banner) banner.hidden = true;
    return;
  }

  // Critical banner
  const bannerTitle = document.getElementById("critical-banner-title");
  if (bannerTitle) {
    bannerTitle.textContent = `${data.anomaly_name}: ${data.total_critical} critical detection group${data.total_critical !== 1 ? "s" : ""} active across monitored ATMs.`;
  }

  // Hero panel title + pill
  const heroTitle = document.getElementById("priority-title");
  if (heroTitle) {
    heroTitle.textContent = data.anomaly_name;
  }

  const heroPill = document.querySelector(".panel-hero .status-pill");
  if (heroPill) {
    heroPill.textContent = data.severity || "Critical";
    heroPill.className = `status-pill ${data.has_critical ? "status-critical" : "status-warning"}`;
  }

  // Four incident-scan-items
  const fields = [
    data.primary_signal,
    data.secondary_signal,
    data.impact,
    data.next_review_area,
  ];
  const items = document.querySelectorAll(".incident-scan-item");
  fields.forEach((value, i) => {
    if (items[i]) {
      const strongEl = items[i].querySelector("strong");
      if (strongEl) strongEl.textContent = value || "—";
    }
  });

  // Next-best-action card
  const nextActionEl = document.getElementById("next-action-title");
  if (nextActionEl) {
    const strongEl = nextActionEl.querySelector("strong");
    if (strongEl) strongEl.textContent = data.next_best_action;
    else nextActionEl.textContent = data.next_best_action;
  }

  const nextActionNote = document.querySelector(".panel-hero .next-action-note");
  if (nextActionNote) {
    nextActionNote.textContent = `${data.event_count} event${data.event_count !== 1 ? "s" : ""} — detected ${(data.detection_timestamp || "").slice(0, 10) || "recently"}`;
  }
}

function populateActionCenter(data) {
  if (!data || !data.anomaly_name) return;

  currentActionContext = data;

  const atm = data.atm_id && data.atm_id !== "N/A" ? data.atm_id : "affected ATM";
  const recommendations = [
    {
      title: `Investigate ${data.anomaly_name} on ${atm}`,
      detail: `Review ${data.correlated_sources} evidence — ${data.event_count} supporting event${data.event_count !== 1 ? "s" : ""} across ${data.source}.`,
    },
    {
      title: `Escalate ${atm} to hardware team`,
      detail: "Raise service ticket for on-site inspection if ATMH hardware alerts are corroborated.",
    },
    {
      title: "Monitor and defer — no immediate action",
      detail: `Schedule follow-up review after next KAFK window for ${atm}.`,
    },
  ];

  const optionIds = ["action-option-1", "action-option-2", "action-option-3"];
  const detailIds = ["action-option-1-detail", "action-option-2-detail", "action-option-3-detail"];

  recommendations.forEach((rec, i) => {
    const titleEl = document.getElementById(optionIds[i]);
    const detailEl = document.getElementById(detailIds[i]);
    if (titleEl) titleEl.textContent = rec.title;
    if (detailEl) detailEl.textContent = rec.detail;
  });

  const textarea = document.getElementById("action-textarea");
  if (textarea) {
    textarea.placeholder = `Add notes for ${atm} — ${data.anomaly_name}`;
  }
}

async function fetchAtmDetail(atmId) {
  if (!atmId) return;
  try {
    const data = await fetch(`/api/atm-detail/${encodeURIComponent(atmId)}`).then((r) => r.json());
    if (data.status === "ok") populateAtmDetail(data);
    else if (data.status === "not_found") {
      setTextContent("#detail-title", `No data found for ${atmId}`);
      setTextContent("#detail-banner-title", `${atmId} not found in source data`);
    }
  } catch (err) {
    console.warn("[dashboard] ATM detail fetch failed:", err);
  }
}

function populateAtmDetail(data) {
  // Screen header
  setTextContent("#detail-title", `Incident detail — ${data.atm_id}`);

  const statusPill = document.getElementById("detail-status-pill");
  if (statusPill) {
    const hasCrit = data.top_detection && data.top_detection.severity === "CRITICAL";
    const hasWarn = data.hw_alerts > 0 || (data.top_detection && data.top_detection.severity === "WARNING");
    statusPill.textContent = hasCrit ? "Critical" : hasWarn ? "Warning" : "OK";
    statusPill.className = `status-pill ${hasCrit ? "status-critical" : hasWarn ? "status-warning" : "status-ok"}`;
  }

  // Banner
  const bannerTitle = document.getElementById("detail-banner-title");
  if (bannerTitle) {
    bannerTitle.textContent = data.top_detection
      ? `${data.top_detection.anomaly_name} — ${data.top_detection.description}`
      : `${data.atm_id} — ${data.atm_status}`;
  }
  const bannerNote = document.getElementById("detail-banner-note");
  if (bannerNote) {
    bannerNote.textContent = `${data.error_count} application error event${data.error_count !== 1 ? "s" : ""} recorded. Last update: ${(data.last_update || "").slice(0, 16)}.`;
  }

  // Diagnostic summary
  setTextContent("#detail-anomaly", data.top_detection ? data.top_detection.anomaly_name : "None detected");
  setTextContent("#detail-confidence", data.top_detection ? `${data.top_detection.event_count} supporting event${data.top_detection.event_count !== 1 ? "s" : ""} in ${data.top_detection.source}` : "N/A");
  setTextContent("#detail-impact", `${data.error_count} app error${data.error_count !== 1 ? "s" : ""}, ${data.hw_alerts} hardware alert${data.hw_alerts !== 1 ? "s" : ""}`);
  setTextContent("#detail-root-cause", data.kafk_summary ? `KAFK: ${data.kafk_summary.failure_reasons} (${data.kafk_summary.total_failures} failure${data.kafk_summary.total_failures !== 1 ? "s" : ""})` : "No KAFK failure events recorded");

  // Recommendation
  const recEl = document.getElementById("detail-recommended-action");
  if (recEl) {
    if (data.winos_summary) {
      recEl.textContent = `CPU: ${data.winos_summary.cpu_pct}%, Memory: ${data.winos_summary.mem_pct}%, Network errors: ${data.winos_summary.net_errors}. ${data.kafk_summary ? `KAFK failures: ${data.kafk_summary.total_failures}.` : ""} Review correlated sources: ${data.correlated_sources}.`;
    } else {
      recEl.textContent = `Review ${data.correlated_sources} for active anomaly evidence on ${data.atm_id}.`;
    }
  }

  // Next-best-action
  const nextActionEl = document.getElementById("detail-next-action-title");
  if (nextActionEl) {
    const strongEl = nextActionEl.querySelector("strong");
    const text = data.top_detection
      ? `Escalate ${data.top_detection.anomaly_name} — open action center for ${data.atm_id}`
      : `No active anomaly detected for ${data.atm_id}`;
    if (strongEl) strongEl.textContent = text;
    else nextActionEl.textContent = text;
  }
  const nextNoteEl = document.getElementById("detail-next-action-note");
  if (nextNoteEl) {
    nextNoteEl.textContent = `Location: ${data.location_code}. Last update: ${(data.last_update || "").slice(0, 16)}.`;
  }

  // Issue timeline
  const timeline = document.getElementById("detail-timeline");
  if (timeline) {
    if (data.timeline.length > 0) {
      timeline.innerHTML = data.timeline
        .map(
          (t) => `
        <li>
          <strong>${(t.timestamp || "").slice(11, 16)}</strong>
          <p>${t.event_type}${t.component ? " — " + t.component : ""}${t.error_code ? " [" + t.error_code + "]" : ""}: ${(t.message || "").slice(0, 80)}</p>
        </li>`
        )
        .join("");
    } else {
      timeline.innerHTML = `<li><strong>—</strong><p>No error events recorded for ${data.atm_id}.</p></li>`;
    }
  }

  // Evidence cards
  const appDet = data.detections.filter((d) => d.source === "ATMA");
  const hwDet = data.detections.filter((d) => d.source === "ATMH");
  const streamDet = data.detections.filter((d) => ["KAFK", "TERM", "WINOS", "PROM", "GCP"].includes(d.source));

  const appEl = document.getElementById("evidence-app");
  if (appEl) {
    appEl.innerHTML = `<p class="evidence-label">Application source (ATMA)</p><p>${
      appDet.length
        ? appDet.map((d) => `${d.anomaly_name}: ${d.description}`).join("; ")
        : `${data.error_count} application event${data.error_count !== 1 ? "s" : ""} recorded — no ATMA detection groups for this ATM.`
    }</p>`;
  }
  const hwEl = document.getElementById("evidence-hardware");
  if (hwEl) {
    hwEl.innerHTML = `<p class="evidence-label">Hardware source (ATMH)</p><p>${
      hwDet.length
        ? hwDet.map((d) => `${d.anomaly_name}: ${d.description}`).join("; ")
        : data.hw_alerts > 0
        ? `${data.hw_alerts} hardware alert event${data.hw_alerts !== 1 ? "s" : ""} — no ATMH detection groups for this ATM.`
        : "No hardware anomalies detected."
    }</p>`;
  }
  const streamEl = document.getElementById("evidence-stream");
  if (streamEl) {
    streamEl.innerHTML = `<p class="evidence-label">Stream and runtime sources (KAFK, PROM, GCP, TERM)</p><p>${
      streamDet.length
        ? streamDet.map((d) => `${d.source} — ${d.anomaly_name}: ${d.description}`).join("; ")
        : data.kafk_summary
        ? `KAFK: ${data.kafk_summary.total_failures} failure${data.kafk_summary.total_failures !== 1 ? "s" : ""} (${data.kafk_summary.failure_reasons}). Avg TPS: ${data.kafk_summary.avg_tps}.`
        : "No stream or runtime anomalies detected."
    }</p>`;
  }

  // Service impact
  setTextContent("#detail-observed-impact", data.top_detection ? data.top_detection.description : "None");
  setTextContent("#detail-location", data.location_code);
  setTextContent("#detail-last-event", (data.last_update || "").slice(0, 16));
  const sigCount = data.detections.length;
  setTextContent(
    "#detail-correlated-signals",
    sigCount > 0
      ? `${sigCount} detection group${sigCount !== 1 ? "s" : ""} across ${data.correlated_sources}`
      : "No correlated signals detected"
  );
}

async function populateSettingsAccount() {
  setTextContent("#settings-role", dashboardRoleLabel || dashboardRole);
  setTextContent("#settings-console", `${dashboardRoleLabel} Console`);
  try {
    const me = await fetch("/api/me").then((r) => r.json());
    if (me.status === "ok" && me.username) {
      setTextContent("#settings-username", me.username);
    } else {
      setTextContent("#settings-username", dashboardRoleLabel || dashboardRole);
    }
  } catch {
    setTextContent("#settings-username", dashboardRoleLabel || dashboardRole);
  }
}

function populateWinosMiniGraph(data) {
  if (!data.points || data.points.length < 2) return;

  const valueEl = document.getElementById("host-pressure-value");
  if (valueEl) {
    const peak = data.peak_cpu || 0;
    valueEl.textContent = peak > 80 ? `${peak}% — Elevated` : peak > 0 ? `${peak}% peak` : "Normal";
  }

  const svgEl = document.querySelector(".mini-graph svg");
  if (!svgEl) return;

  const X_START = 12, X_END = 308, Y_BOTTOM = 108, Y_TOP = 12;
  const plotW = X_END - X_START;
  const plotH = Y_BOTTOM - Y_TOP;
  const values = data.points.map((p) => p.avg_cpu);
  const maxVal = Math.max(...values, 1);
  const n = data.points.length;

  const coords = values.map((v, i) => ({
    x: Math.round(X_START + (i / (n - 1)) * plotW),
    y: Math.round(Y_BOTTOM - (v / maxVal) * plotH),
    v,
    hour: data.points[i].hour,
  }));

  const pathD = coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c.x} ${c.y}`).join(" ");
  const svgNS = "http://www.w3.org/2000/svg";

  svgEl.querySelectorAll("path, circle").forEach((el) => el.remove());

  const pathEl = document.createElementNS(svgNS, "path");
  pathEl.setAttribute("d", pathD);
  svgEl.appendChild(pathEl);

  const lastCoord = coords[coords.length - 1];
  const circle = document.createElementNS(svgNS, "circle");
  circle.setAttribute("cx", lastCoord.x);
  circle.setAttribute("cy", lastCoord.y);
  circle.setAttribute("r", "5");
  svgEl.appendChild(circle);
}

function populateIncidents(data) {
  const list = document.getElementById("incidents-list");
  const pill = document.getElementById("incidents-summary-pill");

  const total = data.total || 0;
  const critical = data.incidents.filter((i) => i.severity === "CRITICAL").length;

  if (pill) {
    pill.textContent = critical > 0 ? `${critical} Critical` : total > 0 ? `${total} grouped` : "None";
    pill.className = `status-pill ${critical > 0 ? "status-critical" : total > 0 ? "status-warning" : "status-ok"}`;
  }

  if (!list) return;
  if (!total) {
    list.innerHTML = "<li>No correlated incidents detected — run pipeline to generate data.</li>";
    return;
  }

  list.innerHTML = data.incidents
    .map((i) => {
      const strategyLabel = i.strategy === "correlation_id" ? "correlation_id match" : "time-window (±5 min)";
      const pillClass = i.severity === "CRITICAL" ? "status-critical" : "status-warning";
      return `<li>
        <strong>${i.incident_id}</strong>
        <span class="status-pill ${pillClass}" style="margin-left:0.5rem;">${i.severity}</span>
        <br><span class="metric-subnote">Sources: ${i.sources} — ATMs: ${i.atm_ids} — Types: ${i.anomaly_types}</span>
        <br><span class="metric-subnote">${i.description}</span>
        <br><span class="metric-subnote">${i.event_count} event${i.event_count !== 1 ? "s" : ""} · ${strategyLabel}${i.earliest_ts ? " · " + i.earliest_ts.slice(0, 16) : ""}</span>
      </li>`;
    })
    .join("");
}

function populateMlSummary(data) {
  const note = document.getElementById("ml-pipeline-note");
  if (!note) return;
  if (!data.total_scored) {
    note.textContent = "ML pipeline: no scores recorded yet.";
    return;
  }
  const sourceStr = data.sources
    .map((s) => `${s.source}: ${s.anomalies}/${s.scored}`)
    .join(", ");
  note.textContent = `ML (Isolation Forest) — ${data.total_anomalies} anomal${data.total_anomalies !== 1 ? "ies" : "y"} flagged from ${data.total_scored.toLocaleString()} scored rows across ${data.sources.length} source${data.sources.length !== 1 ? "s" : ""} (${sourceStr}). Model: ${data.model_version || "unknown"}.`;
}

function populateSettingsSourceList(sources) {
  const list = document.getElementById("settings-source-list");
  if (!list) return;
  list.innerHTML = sources
    .map(
      (s) =>
        `<li><strong>${s.source}:</strong> ${s.status}${s.signal === "present" ? " — active" : s.signal === "empty" ? " — empty" : " — not loaded"}</li>`
    )
    .join("");
}

function populateRecommendations(recs) {
  const list = document.getElementById("rec-list");
  const pill = document.getElementById("rec-summary-pill");
  const quickActionLabels = getQuickActionLabels();

  if (dashboardRole === "admin") {
    const h3 = document.getElementById("rec-panel-title");
    if (h3) h3.textContent = "Recommendation engine performance";
    const recPanel = document.querySelector(".rec-panel");
    const desc = recPanel ? recPanel.querySelector(".metric-subnote") : null;
    if (desc) desc.textContent = "Per-anomaly rule performance as seen by the operations team. Confidence reflects the base rule score adjusted by operator feedback.";
  }

  if (pill) {
    const critCount = recs.filter((r) => r.severity === "CRITICAL").length;
    pill.textContent = recs.length === 0 ? "None" : critCount > 0 ? `${critCount} Critical` : `${recs.length} active`;
    pill.className = `status-pill ${critCount > 0 ? "status-critical" : recs.length > 0 ? "status-warning" : "status-ok"}`;
  }

  if (!list) return;
  if (!recs.length) {
    list.innerHTML = "<li class=\"rec-card\"><div class=\"rec-card-header\"><strong>No active anomaly recommendations — run the pipeline to generate detections.</strong></div></li>";
    return;
  }

  list.innerHTML = recs
    .map((r) => {
      const confPct = Math.round(r.confidence * 100);
      const confClass = confPct >= 80 ? "rec-conf-high" : confPct >= 60 ? "rec-conf-mid" : "rec-conf-low";
      const sevClass = r.severity === "CRITICAL" ? "status-critical" : "status-warning";
      const atm = r.atm_id && r.atm_id !== "N/A" ? ` / ${r.atm_id}` : "";
      const stepsHtml = r.steps
        .map((s, i) => `<li>${s}</li>`)
        .join("");
      const quickActionsHtml = dashboardRole === "admin"
        ? ""
        : `
        <div class="rec-actions" role="group" aria-label="Recommendation actions">
          <button class="button quick-action-btn" type="button" data-action-label="${quickActionLabels.primary}" data-anomaly-type="${r.anomaly_type}" data-anomaly-name="${r.anomaly_name}" data-atm-id="${r.atm_id || ""}">${quickActionLabels.primary}</button>
          <button class="button-secondary quick-action-btn" type="button" data-action-label="${quickActionLabels.secondary}" data-anomaly-type="${r.anomaly_type}" data-anomaly-name="${r.anomaly_name}" data-atm-id="${r.atm_id || ""}">${quickActionLabels.secondary}</button>
          <button class="text-button open-action-center-btn" type="button" data-anomaly-type="${r.anomaly_type}" data-anomaly-name="${r.anomaly_name}" data-atm-id="${r.atm_id || ""}">Open action center</button>
        </div>
        <p class="quick-action-status" aria-live="polite"></p>`;
      return `
      <li class="rec-card" data-anomaly-type="${r.anomaly_type}" data-atm-id="${r.atm_id || ""}">
        <div class="rec-card-header">
          <div class="rec-card-title-row">
            <strong>${r.anomaly_name} (${r.anomaly_type})</strong>
            <span class="status-pill ${sevClass}" style="margin-left:0.5rem;">${r.severity}</span>
            <span class="rec-conf ${confClass}" style="margin-left:0.5rem;">${confPct}% confidence</span>
          </div>
          <p class="rec-source metric-subnote">${r.source}${atm}</p>
        </div>
        <div class="rec-card-body">
          <p class="rec-root-cause"><strong>Root cause:</strong> ${r.root_cause}</p>
          <ol class="rec-steps">${stepsHtml}</ol>
          <p class="rec-explanation metric-subnote"><em>Why triggered:</em> ${r.explanation}</p>
        </div>
        <div class="rec-feedback" role="group" aria-label="Rate this recommendation">
          <span class="rec-feedback-label">Was this recommendation helpful?</span>
          <div class="rec-feedback-buttons">
            <button class="feedback-btn feedback-like" type="button" data-vote="like" data-anomaly-type="${r.anomaly_type}" data-atm-id="${r.atm_id || ""}" aria-label="Mark recommendation as helpful">
              Helpful
            </button>
            <button class="feedback-btn feedback-dislike" type="button" data-vote="dislike" data-anomaly-type="${r.anomaly_type}" data-atm-id="${r.atm_id || ""}" aria-label="Mark recommendation as not helpful">
              Not helpful
            </button>
          </div>
        </div>
        ${quickActionsHtml}
      </li>`;
    })
    .join("");

  wireFeedbackButtons();
  wireRecommendationActionButtons();
}

function wireFeedbackButtons() {
  document.querySelectorAll(".feedback-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const vote = btn.dataset.vote;
      const anomalyType = btn.dataset.anomalyType;
      const atmId = btn.dataset.atmId || "";
      const card = btn.closest(".rec-card");

      // Optimistic UI
      card.querySelectorAll(".feedback-btn").forEach((b) => b.classList.remove("feedback-active"));
      btn.classList.add("feedback-active");
      btn.setAttribute("aria-pressed", "true");

      const result = await sendFeedback(anomalyType, atmId, vote);
      if (result && result.adjusted_confidence !== undefined) {
        const confEl = card.querySelector(".rec-conf");
        if (confEl) {
          const newPct = Math.round(result.adjusted_confidence * 100);
          confEl.textContent = `${newPct}% confidence`;
          confEl.className = `rec-conf ${newPct >= 80 ? "rec-conf-high" : newPct >= 60 ? "rec-conf-mid" : "rec-conf-low"}`;
        }
        // Refresh feedback history
        try {
          const hist = await fetch("/api/feedback-history").then((r) => r.json());
          if (hist.status === "ok") populateFeedbackHistory(hist);
        } catch {}
      }
    });
  });
}

function wireRecommendationActionButtons() {
  document.querySelectorAll(".quick-action-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const statusNode = btn.closest(".rec-card")?.querySelector(".quick-action-status");
      btn.disabled = true;

      try {
        const result = await recordAction({
          action_label: btn.dataset.actionLabel || "Review issue",
          anomaly_type: btn.dataset.anomalyType || "",
          anomaly_name: btn.dataset.anomalyName || "",
          atm_id: btn.dataset.atmId || "",
          notes: "",
        });

        if (statusNode) {
          statusNode.textContent = result.status === "ok"
            ? `${btn.dataset.actionLabel} recorded.`
            : `Unable to record action: ${result.reason || "try again"}.`;
        }

        if (result.status === "ok") {
          try {
            const history = await fetch("/api/actions").then((r) => r.json());
            if (history.status === "ok") populateActionHistory(history.actions);
          } catch {}
        }
      } catch {
        if (statusNode) statusNode.textContent = "Unable to record action right now.";
      } finally {
        btn.disabled = false;
      }
    });
  });

  document.querySelectorAll(".open-action-center-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      currentActionContext = {
        anomaly_type: btn.dataset.anomalyType || "",
        anomaly_name: btn.dataset.anomalyName || "",
        atm_id: btn.dataset.atmId || "",
      };

      if (!validScreenIds.has("action-center")) {
        return;
      }

      const matchingRecommendation = currentRecommendations.find(
        (rec) => rec.anomaly_type === currentActionContext.anomaly_type && (rec.atm_id || "") === currentActionContext.atm_id
      );
      if (matchingRecommendation) {
        populateActionCenterFromRec([
          matchingRecommendation,
          ...currentRecommendations.filter((rec) => rec !== matchingRecommendation),
        ]);
      }
      navigateToScreen("action-center");
    });
  });
}

async function sendFeedback(anomalyType, atmId, vote) {
  try {
    const resp = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ anomaly_type: anomalyType, atm_id: atmId, vote }),
    });
    return await resp.json();
  } catch (err) {
    console.warn("[dashboard] feedback submit failed:", err);
    return null;
  }
}

function populateFeedbackHistory(data) {
  const statsList = document.getElementById("feedback-stats-list");
  const histList = document.getElementById("feedback-history-list");

  if (statsList) {
    if (!data.stats || data.stats.length === 0) {
      statsList.innerHTML = "<p class=\"metric-subnote\">No feedback recorded yet — use the like/dislike buttons above to start training the model.</p>";
    } else {
      statsList.innerHTML = data.stats
        .map((s) => {
          const total = s.likes + s.dislikes;
          const likeRate = total > 0 ? Math.round((s.likes / total) * 100) : 0;
          return `
          <div class="feedback-stat-item">
            <strong>${s.anomaly_type}</strong>
            <span class="metric-subnote">${s.likes} helpful / ${s.dislikes} not helpful</span>
            <span class="rec-conf ${likeRate >= 60 ? "rec-conf-high" : likeRate >= 40 ? "rec-conf-mid" : "rec-conf-low"}">${likeRate}% approval</span>
          </div>`;
        })
        .join("");
    }
  }

  if (histList) {
    const toggleBtn = document.getElementById("feedback-history-toggle");
    if (!data.history || data.history.length === 0) {
      histList.innerHTML = "<li>No feedback recorded yet.</li>";
      return;
    }
    histList.innerHTML = data.history
      .map((h) => {
        const voteLabel = h.vote === "like" ? "Helpful" : "Not helpful";
        const atm = h.atm_id ? ` / ${h.atm_id}` : "";
        const roleLabel = h.user_role ? ` (${h.user_role})` : "";
        return `<li><strong>${h.anomaly_type}${atm}</strong> — ${voteLabel}${roleLabel} <span class="metric-subnote">${(h.created_at || "").slice(0, 16)}</span></li>`;
      })
      .join("");
  }
}

function populateActionCenterFromRec(recs) {
  if (!recs || recs.length === 0) return;
  const top = recs[0];
  currentActionContext = top;
  const atm = top.atm_id && top.atm_id !== "N/A" ? top.atm_id : "affected ATM";

  const recommendations = [
    {
      title: top.steps[0] || `Investigate ${top.anomaly_name} on ${atm}`,
      detail: `Root cause: ${top.root_cause.slice(0, 100)}${top.root_cause.length > 100 ? "..." : ""}`,
    },
    {
      title: recs.length > 1 ? (recs[1].steps[0] || `Address ${recs[1].anomaly_name}`) : `Escalate ${atm} for on-site inspection`,
      detail: recs.length > 1
        ? `Root cause: ${recs[1].root_cause.slice(0, 100)}${recs[1].root_cause.length > 100 ? "..." : ""}`
        : "Raise service ticket if hardware evidence is corroborated by ATMH alerts.",
    },
    {
      title: "Monitor and defer — no immediate action",
      detail: `Schedule follow-up after next KAFK window for ${atm}.`,
    },
  ];

  ["action-option-1", "action-option-2", "action-option-3"].forEach((id, i) => {
    const titleEl = document.getElementById(id);
    const detailEl = document.getElementById(`${id}-detail`);
    if (titleEl) titleEl.textContent = recommendations[i].title;
    if (detailEl) detailEl.textContent = recommendations[i].detail;
  });

  const textarea = document.getElementById("action-textarea");
  if (textarea) textarea.placeholder = `Add notes for ${atm} — ${top.anomaly_name}`;
}

fetchDashboardData();

function populateAdminAnalysisPanel(mlSummary, feedbackHistory) {
  if (dashboardRole !== "admin") return;

  const pill = document.getElementById("admin-analysis-pill");
  if (pill) {
    const hasData = mlSummary.total_scored > 0;
    pill.textContent = hasData ? "Pipeline active" : "No ML data";
    pill.className = `status-pill ${hasData ? "status-ok" : ""}`;
  }

  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };
  set("admin-stat-scored", (mlSummary.total_scored || 0).toLocaleString());
  set("admin-stat-anomalies", (mlSummary.total_anomalies || 0).toLocaleString());
  set("admin-stat-model", mlSummary.model_version || "Not available");

  const srcList = document.getElementById("admin-ml-sources");
  if (srcList) {
    if (!mlSummary.sources || mlSummary.sources.length === 0) {
      srcList.innerHTML = `<li class="metric-subnote">No ML scoring data available — run the pipeline to generate scores.</li>`;
    } else {
      srcList.innerHTML = mlSummary.sources
        .map((s) => {
          const anomRate = s.scored > 0 ? Math.round((s.anomalies / s.scored) * 100) : 0;
          return `<li><strong>${s.source}</strong> — ${s.scored.toLocaleString()} scored, ${s.anomalies} anomal${s.anomalies !== 1 ? "ies" : "y"} (${anomRate}% flagged)</li>`;
        })
        .join("");
    }
  }

  const recStats = document.getElementById("admin-rec-stats");
  if (recStats) {
    if (!feedbackHistory.stats || feedbackHistory.stats.length === 0) {
      recStats.innerHTML = `<li class="metric-subnote">No operator feedback recorded yet. Ops-team feedback from the Anomaly patterns page adjusts rule confidence scores.</li>`;
    } else {
      recStats.innerHTML = feedbackHistory.stats
        .map((s) => {
          const total = s.likes + s.dislikes;
          const approvalPct = total > 0 ? Math.round((s.likes / total) * 100) : null;
          const confClass =
            approvalPct === null
              ? ""
              : approvalPct >= 60
              ? "rec-conf-high"
              : approvalPct >= 40
              ? "rec-conf-mid"
              : "rec-conf-low";
          const approvalBadge =
            approvalPct !== null
              ? `<span class="rec-conf ${confClass}" style="margin-left:0.4rem;">${approvalPct}% approval</span>`
              : "";
          return `<li><strong>${s.anomaly_type}</strong> — ${s.likes} helpful / ${s.dislikes} not helpful${approvalBadge}</li>`;
        })
        .join("");
    }
  }
}

function populateAdminAnomalyBreakdown(alerts, recommendations) {
  if (dashboardRole !== "admin") return;

  const pill = document.getElementById("admin-breakdown-pill");
  const tbody = document.getElementById("admin-anomaly-tbody");

  const all = [...(alerts.critical || []), ...(alerts.warning || [])];
  const byType = {};
  all.forEach((a) => {
    const key = a.anomaly_type;
    if (!byType[key]) {
      byType[key] = { name: a.anomaly_name, severity: a.severity, groups: 0, atms: new Set() };
    }
    byType[key].groups += 1;
    if (a.atm_id && a.atm_id !== "N/A") byType[key].atms.add(a.atm_id);
  });

  const recByType = {};
  recommendations.forEach((r) => {
    recByType[r.anomaly_type] = r.confidence;
  });

  const types = Object.entries(byType).sort((a, b) => {
    if (a[1].severity === "CRITICAL" && b[1].severity !== "CRITICAL") return -1;
    if (b[1].severity === "CRITICAL" && a[1].severity !== "CRITICAL") return 1;
    return b[1].groups - a[1].groups;
  });

  if (pill) {
    const critTypes = types.filter(([, v]) => v.severity === "CRITICAL").length;
    pill.textContent = `${types.length} type${types.length !== 1 ? "s" : ""} active`;
    pill.className = `status-pill ${critTypes > 0 ? "status-critical" : types.length > 0 ? "status-warning" : "status-ok"}`;
  }

  if (!tbody) return;
  if (!types.length) {
    tbody.innerHTML = `<tr><td colspan="6">No anomaly detections found — run the pipeline to generate data.</td></tr>`;
    return;
  }

  tbody.innerHTML = types
    .map(([type, info]) => {
      const sevClass = info.severity === "CRITICAL" ? "status-critical" : "status-warning";
      const atmsArr = Array.from(info.atms);
      const atmsLabel =
        atmsArr.length === 0
          ? "—"
          : atmsArr.length <= 2
          ? atmsArr.join(", ")
          : `${atmsArr.slice(0, 2).join(", ")} +${atmsArr.length - 2} more`;
      const conf = recByType[type];
      const confPct = conf !== undefined ? Math.round(conf * 100) : null;
      const confClass =
        confPct === null ? "" : confPct >= 80 ? "rec-conf-high" : confPct >= 60 ? "rec-conf-mid" : "rec-conf-low";
      const confCell = confPct !== null ? `<span class="rec-conf ${confClass}">${confPct}%</span>` : "—";
      return `
      <tr>
        <th scope="row">${type}</th>
        <td>${info.name}</td>
        <td><span class="status-pill ${sevClass}">${info.severity}</span></td>
        <td>${info.groups}</td>
        <td>${atmsLabel}</td>
        <td>${confCell}</td>
      </tr>`;
    })
    .join("");
}

// ─── Anomaly taxonomy ────────────────────────────────────────────────────────

async function fetchTaxonomy() {
  try {
    const data = await fetch("/api/taxonomy").then((r) => r.json());
    if (data.status === "ok") populateTaxonomy(data.entries || []);
  } catch (err) {
    console.warn("[dashboard] taxonomy fetch failed:", err);
  }
}

function populateTaxonomy(entries) {
  const tbody = document.getElementById("taxonomy-tbody");
  const pill = document.getElementById("taxonomy-pill");

  const staticCount = entries.filter((e) => e.discovery_method === "static").length;
  const dynamicCount = entries.filter((e) => e.discovery_method === "dynamic").length;

  if (pill) {
    pill.textContent = entries.length === 0 ? "No data" : `${staticCount} static${dynamicCount > 0 ? ` · ${dynamicCount} dynamic` : ""}`;
    pill.className = `status-pill ${entries.length > 0 ? "status-ok" : ""}`;
  }

  if (!tbody) return;
  if (!entries.length) {
    tbody.innerHTML = `<tr><td colspan="6">No taxonomy entries found — run the pipeline to seed static entries.</td></tr>`;
    return;
  }

  tbody.innerHTML = entries
    .map((e) => {
      const sevClass = e.severity === "CRITICAL" ? "status-critical" : e.severity === "WARNING" ? "status-warning" : "status-ok";
      const methodClass = e.discovery_method === "dynamic" ? "rec-conf-mid" : "";
      const registeredAt = e.registered_at ? e.registered_at.slice(0, 16) : "—";
      return `
      <tr>
        <th scope="row"><strong>${e.anomaly_type}</strong></th>
        <td>${e.anomaly_name}</td>
        <td><span class="status-pill ${sevClass}">${e.severity}</span></td>
        <td><code>${e.source}</code></td>
        <td><span class="${methodClass}" style="font-size:0.8rem;">${e.discovery_method}</span></td>
        <td class="metric-subnote">${e.description || "—"}</td>
      </tr>`;
    })
    .join("");
}

// ─── Live streaming agent ─────────────────────────────────────────────────────

let _liveAgentPollInterval = null;

async function fetchLiveAgentStatus() {
  try {
    const data = await fetch("/api/live-agent/status").then((r) => r.json());
    if (data.status === "ok") populateLiveAgentPanel(data);
    return data;
  } catch (err) {
    console.warn("[dashboard] live agent status fetch failed:", err);
    return null;
  }
}

function populateLiveAgentPanel(data) {
  const pill = document.getElementById("live-agent-pill");
  const statusText = document.getElementById("live-agent-status-text");
  const eventsEl = document.getElementById("live-agent-events");
  const lastEventEl = document.getElementById("live-agent-last-event");
  const intervalEl = document.getElementById("live-agent-interval-display");
  const startBtn = document.getElementById("live-agent-start-btn");
  const stopBtn = document.getElementById("live-agent-stop-btn");
  const injectStatus = document.getElementById("live-inject-status");

  if (pill) {
    pill.textContent = data.running ? (data.current_injection ? `Live — injecting ${data.current_injection}` : "Live") : "Idle";
    pill.className = `status-pill ${data.running ? (data.current_injection ? "status-warning" : "status-ok") : ""}`;
  }
  if (statusText) statusText.textContent = data.running ? "Running" : "Idle";
  if (eventsEl) eventsEl.textContent = (data.events_generated || 0).toLocaleString();
  if (lastEventEl) lastEventEl.textContent = data.last_event_ts ? data.last_event_ts.slice(11, 19) + " UTC" : "—";
  if (intervalEl) intervalEl.textContent = data.running ? `${data.interval_seconds}s` : "—";
  if (startBtn) startBtn.disabled = data.running;
  if (stopBtn) stopBtn.disabled = !data.running;

  if (injectStatus && data.current_injection) {
    injectStatus.textContent = `Injecting ${data.current_injection} — active for this batch.`;
  }

  if (data.running) {
    _startLiveAgentPoll();
  } else {
    _stopLiveAgentPoll();
  }
}

function _startLiveAgentPoll() {
  if (_liveAgentPollInterval) return;
  _liveAgentPollInterval = setInterval(async () => {
    const agentData = await fetchLiveAgentStatus();
    if (agentData && agentData.running) {
      // Refresh dashboard data panels to reflect new records
      fetchDashboardData();
    }
  }, 5000);
}

function _stopLiveAgentPoll() {
  if (!_liveAgentPollInterval) return;
  clearInterval(_liveAgentPollInterval);
  _liveAgentPollInterval = null;
}

async function _controlLiveAgent(action, body = {}) {
  try {
    const resp = await fetch(`/api/live-agent/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return await resp.json();
  } catch (err) {
    console.warn(`[dashboard] live agent ${action} failed:`, err);
    return null;
  }
}

// Wire live agent buttons after DOM is ready
(function wireLiveAgent() {
  const startBtn = document.getElementById("live-agent-start-btn");
  const stopBtn = document.getElementById("live-agent-stop-btn");
  const injectChips = document.querySelectorAll("[data-inject]");
  const injectStatus = document.getElementById("live-inject-status");
  const intervalInput = document.getElementById("live-agent-interval-input");

  if (startBtn) {
    startBtn.addEventListener("click", async () => {
      startBtn.disabled = true;
      const interval = intervalInput ? parseInt(intervalInput.value, 10) || 10 : 10;
      const data = await _controlLiveAgent("start", { interval });
      if (data) populateLiveAgentPanel(data);
    });
  }

  if (stopBtn) {
    stopBtn.addEventListener("click", async () => {
      stopBtn.disabled = true;
      const data = await _controlLiveAgent("stop");
      if (data) populateLiveAgentPanel(data);
    });
  }

  injectChips.forEach((chip) => {
    chip.addEventListener("click", async () => {
      const anomalyType = chip.dataset.inject;
      if (!anomalyType) return;
      const data = await _controlLiveAgent("inject", { anomaly_type: anomalyType });
      if (!data) return;
      if (data.status === "ok") {
        injectChips.forEach((c) => c.classList.remove("is-active"));
        chip.classList.add("is-active");
        if (injectStatus) injectStatus.textContent = `${anomalyType} injection scheduled — records will appear in the next batch.`;
      } else if (data.reason && injectStatus) {
        injectStatus.textContent = data.reason;
      }
    });
  });
})();

// Load taxonomy and live agent status when data-flow screen is accessible
if (validScreenIds.has("data-flow")) {
  fetchTaxonomy();
  fetchLiveAgentStatus();
}

function populateDataFlow(snapshot, alerts, mlSummary, incidents, recommendations) {
  const setStage = (n, { metric, details, pillText, pillClass }) => {
    const metricEl = document.getElementById(`stage-${n}-metric`);
    const detailEl = document.getElementById(`stage-${n}-detail`);
    const pillEl = document.getElementById(`stage-${n}-pill`);
    if (metricEl) metricEl.textContent = metric;
    if (detailEl) detailEl.innerHTML = details.map((d) => `<li>${d}</li>`).join("");
    if (pillEl) {
      pillEl.textContent = pillText;
      pillEl.className = `status-pill ${pillClass}`;
    }
  };

  // Stage 1 — Source ingestion
  const presentSources = snapshot.sources.filter((s) => s.signal === "present");
  const emptySources = snapshot.sources.filter((s) => s.signal === "empty");
  const absentSources = snapshot.sources.filter((s) => s.signal === "absent");
  setStage(1, {
    metric: `${presentSources.length} / ${snapshot.sources.length} sources`,
    details: [
      `Active: ${presentSources.map((s) => s.source).join(", ") || "None"}`,
      emptySources.length ? `Empty: ${emptySources.map((s) => s.source).join(", ")}` : "All loaded sources have records",
      absentSources.length ? `Absent: ${absentSources.map((s) => s.source).join(", ")}` : "No absent sources",
    ],
    pillText: presentSources.length === snapshot.sources.length ? "All active" : presentSources.length > 0 ? "Partial" : "No data",
    pillClass: presentSources.length === snapshot.sources.length ? "status-ok" : presentSources.length > 0 ? "status-warning" : "status-critical",
  });

  // Stage 2 — Rule detection
  const allDetections = [...(alerts.critical || []), ...(alerts.warning || [])];
  const detectedTypes = [...new Set(allDetections.map((d) => d.anomaly_type))];
  const affectedAtms = new Set(allDetections.map((d) => d.atm_id).filter(Boolean));
  setStage(2, {
    metric: `${allDetections.length} detection group${allDetections.length !== 1 ? "s" : ""}`,
    details: [
      `${(alerts.critical || []).length} critical, ${(alerts.warning || []).length} warning`,
      detectedTypes.length ? `Types: ${detectedTypes.join(", ")}` : "No anomaly types detected",
      `${affectedAtms.size} ATM${affectedAtms.size !== 1 ? "s" : ""} affected`,
    ],
    pillText: (alerts.critical || []).length > 0 ? "Critical active" : allDetections.length > 0 ? "Warnings only" : "Clean",
    pillClass: (alerts.critical || []).length > 0 ? "status-critical" : allDetections.length > 0 ? "status-warning" : "status-ok",
  });

  // Stage 3 — ML scoring
  const mlFlagRate = mlSummary.total_scored > 0
    ? Math.round((mlSummary.total_anomalies / mlSummary.total_scored) * 100)
    : 0;
  setStage(3, {
    metric: mlSummary.total_scored > 0 ? `${mlSummary.total_scored.toLocaleString()} scored` : "No scores",
    details: [
      mlSummary.total_scored > 0
        ? `${mlSummary.total_anomalies} flagged (${mlFlagRate}% anomaly rate)`
        : "Run pipeline to generate ML scores",
      mlSummary.model_version ? `Model: ${mlSummary.model_version}` : "Model version: unknown",
      mlSummary.sources && mlSummary.sources.length > 0
        ? `Sources scored: ${mlSummary.sources.map((s) => s.source).join(", ")}`
        : "No source breakdown available",
    ],
    pillText: mlSummary.total_scored > 0 ? (mlFlagRate > 10 ? "High anomaly rate" : "Normal") : "No data",
    pillClass: mlSummary.total_scored > 0 ? (mlFlagRate > 10 ? "status-warning" : "status-ok") : "",
  });

  // Stage 4 — Incident correlation
  const critIncidents = (incidents.incidents || []).filter((i) => i.severity === "CRITICAL").length;
  setStage(4, {
    metric: `${incidents.total || 0} incident group${incidents.total !== 1 ? "s" : ""}`,
    details: [
      `${critIncidents} critical, ${(incidents.total || 0) - critIncidents} warning`,
      incidents.total > 0
        ? `Strategies: ${[...new Set((incidents.incidents || []).map((i) => i.strategy === "correlation_id" ? "correlation_id" : "time-window"))].join(", ")}`
        : "No incidents grouped yet — run pipeline",
      incidents.total > 0
        ? `ATMs spanned: ${[...new Set((incidents.incidents || []).flatMap((i) => (i.atm_ids || "").split(",").map((s) => s.trim())))].filter(Boolean).length}`
        : "",
    ].filter(Boolean),
    pillText: critIncidents > 0 ? `${critIncidents} Critical` : incidents.total > 0 ? `${incidents.total} grouped` : "No incidents",
    pillClass: critIncidents > 0 ? "status-critical" : incidents.total > 0 ? "status-warning" : "status-ok",
  });

  // Stage 5 — Recommendations
  const recs = recommendations.recommendations || [];
  const critRecs = recs.filter((r) => r.severity === "CRITICAL");
  const avgConf = recs.length > 0
    ? Math.round((recs.reduce((s, r) => s + r.confidence, 0) / recs.length) * 100)
    : 0;
  setStage(5, {
    metric: `${recs.length} recommendation${recs.length !== 1 ? "s" : ""}`,
    details: [
      recs.length > 0 ? `${critRecs.length} critical priority` : "No active recommendations",
      recs.length > 0 ? `Average confidence: ${avgConf}%` : "Run pipeline to generate detections",
      recs.length > 0
        ? `Rules active: ${[...new Set(recs.map((r) => r.anomaly_type))].join(", ")}`
        : "",
    ].filter(Boolean),
    pillText: critRecs.length > 0 ? "Action required" : recs.length > 0 ? "Active" : "No data",
    pillClass: critRecs.length > 0 ? "status-critical" : recs.length > 0 ? "status-warning" : "",
  });

  // Overall status pill
  const overallPill = document.getElementById("data-flow-status-pill");
  if (overallPill) {
    const hasCrit = (alerts.critical || []).length > 0 || critIncidents > 0;
    overallPill.textContent = presentSources.length === 0 ? "No pipeline data" : hasCrit ? "Critical signals" : "Pipeline active";
    overallPill.className = `status-pill ${presentSources.length === 0 ? "" : hasCrit ? "status-critical" : "status-ok"}`;
  }

  // Source-level breakdown table
  const tbody = document.getElementById("flow-sources-tbody");
  if (!tbody) return;

  const mlBySource = {};
  (mlSummary.sources || []).forEach((s) => { mlBySource[s.source] = s; });

  const detBySource = {};
  allDetections.forEach((d) => {
    detBySource[d.source] = (detBySource[d.source] || 0) + 1;
  });

  if (!snapshot.sources.length) {
    tbody.innerHTML = `<tr><td colspan="6">No source data — run the pipeline to populate.</td></tr>`;
    return;
  }

  tbody.innerHTML = snapshot.sources
    .map((s) => {
      const ml = mlBySource[s.source];
      const dets = detBySource[s.source] || 0;
      const signalClass = s.signal === "present" ? "status-ok" : s.signal === "empty" ? "" : "";
      const signalLabel = s.signal === "present" ? "Active" : s.signal === "empty" ? "Empty" : "Absent";
      return `
      <tr>
        <th scope="row">${s.source}</th>
        <td>${s.status}</td>
        <td><span class="status-pill ${signalClass}">${signalLabel}</span></td>
        <td>${ml ? ml.scored.toLocaleString() : "—"}</td>
        <td>${ml ? ml.anomalies : "—"}</td>
        <td>${dets > 0 ? dets : "—"}</td>
      </tr>`;
    })
    .join("");
}

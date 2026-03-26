const navButtons = document.querySelectorAll("[data-screen-target]");
const screens = document.querySelectorAll(".screen");
const confirmActionButton = document.getElementById("confirm-action");
const confirmationCard = document.getElementById("confirmation-card");
const clickableCards = document.querySelectorAll(".metric-card-action[data-screen-target]");
const accessibilityToggle = document.getElementById("accessibility-toggle");
const globalSearchInput = document.querySelector('.search-field input[type="search"]');
const dashboardMetricCards = document.querySelectorAll(".metric-grid .metric-card");
const anomalyTrendChart = document.querySelector(".trend-chart");
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
    allowedScreens: ["dashboard", "alerts", "settings"],
    dashboardTitle: "Admin platform view",
    dashboardDescription: "Review source readiness, session access, and configuration surfaces before live data is connected.",
    dashboardStatus: "Unavailable",
    bannerEyebrow: "Admin focus",
    bannerTitle: "Configuration, policy, and source-health summaries will appear here.",
    primaryActionLabel: "Review alert surfaces",
  },
  manager: {
    defaultScreen: "dashboard",
    allowedScreens: ["dashboard", "atm-list", "alerts", "settings"],
    dashboardTitle: "Manager summary view",
    dashboardDescription: "Review summary-level operational posture, ATM coverage, and grouped anomaly demand.",
    dashboardStatus: "Loading...",
    bannerEyebrow: "Manager focus",
    bannerTitle: "Summary metrics and grouped exceptions will appear here.",
    primaryActionLabel: "Review grouped anomalies",
  },
  ops: {
    defaultScreen: "dashboard",
    allowedScreens: ["dashboard", "atm-detail", "atm-list", "alerts", "settings", "action-center"],
    dashboardTitle: "Ops investigation view",
    dashboardDescription: "Focus on anomaly triage, ATM detail, and action workflows as live signals become available.",
    dashboardStatus: "Loading...",
    bannerEyebrow: "Ops focus",
    bannerTitle: "The highest-priority operational signal will appear here.",
    primaryActionLabel: "Open investigation queue",
  },
};
const roleCardContent = {
  admin: {
    observedAtms: {
      title: "Source readiness",
      note: "Awaiting source availability summary from the backend.",
      subnote: "Use this card for pipeline readiness, not hardcoded estate counts.",
      hint: "View source readiness",
    },
    atmAppErrors: {
      title: "Access model",
      note: "Awaiting persona and entitlement summary from the backend.",
      subnote: "Admin views should expose controls and access state, not frontline incident detail.",
      hint: "Review role access",
    },
    hardwareAlerts: {
      title: "Policy exceptions",
      note: "Awaiting threshold and exception counts from the backend.",
      subnote: "Use this card for policy-impacting exceptions once a config endpoint exists.",
      hint: "Review policy exceptions",
    },
    eventThroughput: {
      title: "Backend status",
      note: "Awaiting runtime and ingestion summary from the backend.",
      subnote: "Use this card for platform health, restart signals, and service status.",
      hint: "Inspect backend status",
    },
  },
  manager: {
    observedAtms: {
      title: "ATM coverage",
      note: "Awaiting ATM coverage summary from the backend.",
      subnote: "Use this card for managed estate visibility once live summary data is available.",
      hint: "View ATM coverage",
    },
    atmAppErrors: {
      title: "Anomaly groups",
      note: "Awaiting grouped anomaly totals from the backend.",
      subnote: "Managers need grouped demand and summary counts rather than individual evidence events.",
      hint: "Review anomaly groups",
    },
    hardwareAlerts: {
      title: "Queue pressure",
      note: "Awaiting queue and escalation summary from the backend.",
      subnote: "Use this card for backlog pressure once queue endpoints are available.",
      hint: "Review queue pressure",
    },
    eventThroughput: {
      title: "Transaction summary",
      note: "Awaiting throughput summary from the backend.",
      subnote: "Use this card for reporting-level transaction flow rather than ATM-level event detail.",
      hint: "Inspect transaction summary",
    },
  },
  ops: {
    observedAtms: {
      title: "Assigned ATMs",
      note: "Awaiting ATM assignment or coverage summary from the backend.",
      subnote: "Use this card for the operator's current working set once that API exists.",
      hint: "View assigned ATMs",
    },
    atmAppErrors: {
      title: "ATM app errors",
      note: "Awaiting ATMA error totals from the backend.",
      subnote: "Use this card for frontline error counts and active ATM issues.",
      hint: "Review ATM errors",
    },
    hardwareAlerts: {
      title: "Hardware alerts",
      note: "Awaiting ATMH warning and critical totals from the backend.",
      subnote: "Use this card for hardware faults that need direct operational follow-up.",
      hint: "Open hardware alerts",
    },
    eventThroughput: {
      title: "Event throughput",
      note: "Awaiting KAFK throughput summary from the backend.",
      subnote: "Use this card for event and queue flow that affects operator response speed.",
      hint: "Inspect event throughput",
    },
  },
};
const roleChartContent = {
  admin: {
    anomalyTrend: {
      ready: {
        titleSelector: "Source readiness trend",
        contextSelector: "Awaiting platform-level readiness and runtime metrics from the backend.",
        captionSelector: "This chart should show source and backend readiness for the admin persona.",
        legendSelector: "Unavailable",
      },
    },
    hostPressure: {
      ready: {
        headerLabelSelector: "Backend health",
        headerValueSelector: "Unavailable",
      },
    },
  },
  manager: {
    anomalyTrend: {
      ready: {
        titleSelector: "Operational summary trend",
        contextSelector: "Awaiting grouped anomaly and throughput summary from the backend.",
        captionSelector: "This chart should show reporting-level operational movement for the manager persona.",
        legendSelector: "Loading...",
      },
    },
    hostPressure: {
      ready: {
        headerLabelSelector: "Summary health",
        headerValueSelector: "Loading...",
      },
    },
  },
  ops: {
    anomalyTrend: {
      ready: {
        titleSelector: "Investigation trend",
        contextSelector: "Awaiting triage-oriented anomaly data from the backend.",
        captionSelector: "This chart should show the active operational signal the ops user needs to investigate.",
        legendSelector: "Loading...",
      },
    },
    hostPressure: {
      ready: {
        headerLabelSelector: "Supporting metric",
        headerValueSelector: "Loading...",
      },
    },
  },
};
const roleScreenContent = {
  admin: {
    headerCopy: "Maintain cross-system visibility across source readiness, governance surfaces, and platform health.",
    searchPlaceholder: "Search source, service, role access, or exception",
    navLabels: {
      dashboard: "Overview",
      alerts: "Exceptions",
      settings: "Settings",
    },
    alertsTitle: "Cross-system exception groups",
    alertsDescription: "Review platform-wide exceptions, policy-impacting issues, and source-level concerns that need administrative visibility.",
    criticalGroupTitle: "Platform exceptions",
    warningGroupTitle: "Source watchlist",
    settingsTitle: "Platform settings",
    settingsDescription: "Review configuration areas, access controls, and operational policy surfaces.",
  },
  manager: {
    headerCopy: "Track immediate ATM issues, local operational pressure, and the next items that need action.",
    searchPlaceholder: "Search ATM, location, queue, or issue",
    navLabels: {
      dashboard: "Overview",
      atmList: "ATM queue",
      alerts: "Action queue",
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
    settingsTitle: "Operational settings",
    settingsDescription: "Review notifications and thresholds that affect local operational oversight.",
  },
  ops: {
    headerCopy: "Investigate outages, telemetry spikes, and infrastructure health without losing access to ATM-level workflows.",
    searchPlaceholder: "Search outage, telemetry, ATM, component, or error",
    navLabels: {
      dashboard: "Overview",
      atmDetail: "Incident detail",
      atmList: "ATM list",
      alerts: "Incidents",
      settings: "Settings",
      actionCenter: "Action center",
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
    actionDescription: "Use this page for immediate operational actions once live incident recommendations are available.",
    settingsTitle: "Tool settings",
    settingsDescription: "Review notification and threshold settings for technical operations.",
  },
};

const metricCardState = createMetricCardStateRegistry();
const chartState = createChartStateRegistry();
const activeRoleConfig = roleViewConfig[dashboardRole] || roleViewConfig.ops;

let currentScreenId = "dashboard";
const validScreenIds = new Set(activeRoleConfig.allowedScreens);

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
      state.valueNode.textContent = payload.loadingValue ?? "Loading...";
    } else if (mode === uiStateModes.UNAVAILABLE) {
      state.valueNode.textContent = payload.unavailableValue ?? "Unavailable";
    } else {
      state.valueNode.textContent = value;
    }
  }

  if (state.noteNode) {
    if (mode === uiStateModes.LOADING) {
      state.noteNode.textContent = payload.loadingNote ?? "Waiting for backend response.";
    } else if (mode === uiStateModes.UNAVAILABLE) {
      state.noteNode.textContent = payload.unavailableNote ?? "No source-backed data is available yet.";
    } else {
      state.noteNode.textContent = note;
    }
  }

  if (state.subnoteNode) {
    if (mode === uiStateModes.LOADING) {
      state.subnoteNode.textContent = payload.loadingSubnote ?? "The UI is ready to render live values when an endpoint is connected.";
    } else if (mode === uiStateModes.UNAVAILABLE) {
      state.subnoteNode.textContent =
        payload.unavailableSubnote ?? "Keep this panel hidden or disabled until the backend can provide a real value.";
    } else {
      state.subnoteNode.textContent = subnote;
    }
  }

  if (state.hintNode) {
    if (mode === uiStateModes.LOADING) {
      state.hintNode.textContent = payload.loadingHint ?? "Loading state";
    } else if (mode === uiStateModes.UNAVAILABLE) {
      state.hintNode.textContent = payload.unavailableHint ?? "Data unavailable";
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
    contextSelector: "Waiting for a source-backed response from the backend.",
    captionSelector: "This visual will render once live data is available.",
    legendSelector: "Loading",
    headerLabelSelector: "Loading metric",
    headerValueSelector: "Loading...",
  };

  return copy[key] ?? "Loading...";
}

function getUnavailableChartCopy(key) {
  const copy = {
    titleSelector: "Chart unavailable",
    contextSelector: "No real dataset is connected for this visual yet.",
    captionSelector: "Keep the visual hidden or clearly unavailable until an endpoint exists.",
    legendSelector: "Unavailable",
    headerLabelSelector: "Metric unavailable",
    headerValueSelector: "Unavailable",
  };

  return copy[key] ?? "Unavailable";
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

function applyRoleDashboardCopy() {
  setTextContent("#dashboard-title", activeRoleConfig.dashboardTitle);
  setTextContent("#dashboard-title + p", activeRoleConfig.dashboardDescription);
  setTextContent("#dashboard .screen-header .status-pill", activeRoleConfig.dashboardStatus);
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
  setTextContent('#list-title', screenContent.listTitle);
  setTextContent('#list-title + p', screenContent.listDescription);
  setTextContent('#filters-title', screenContent.filtersTitle);
  setTextContent('#table-title', screenContent.tableTitle);
  setTextContent('#alerts-title-page', screenContent.alertsTitle);
  setTextContent('#alerts-title-page + p', screenContent.alertsDescription);
  setTextContent('#group-critical-title', screenContent.criticalGroupTitle);
  setTextContent('#group-warning-title', screenContent.warningGroupTitle);
  setTextContent('#settings-title', screenContent.settingsTitle);
  setTextContent('#settings-title + p', screenContent.settingsDescription);
  setTextContent('#detail-title', screenContent.detailTitle);
  setTextContent('#detail-title + p', screenContent.detailDescription);
  setTextContent('#action-title', screenContent.actionTitle);
  setTextContent('#action-title + p', screenContent.actionDescription);

  const navLabelMap = {
    dashboard: document.querySelector('[data-screen-target="dashboard"] span'),
    atmDetail: document.querySelector('[data-screen-target="atm-detail"] span'),
    atmList: document.querySelector('[data-screen-target="atm-list"] span'),
    alerts: document.querySelector('[data-screen-target="alerts"] span'),
    settings: document.querySelector('[data-screen-target="settings"] span'),
    actionCenter: document.querySelector('[data-screen-target="action-center"] span'),
  };

  Object.entries(screenContent.navLabels).forEach(([key, value]) => {
    const node = navLabelMap[key];
    if (node) {
      node.textContent = value;
    }
  });
}

function normalizeSearchValue(value) {
  return value.trim().toLowerCase();
}

function filterAtmRows(query) {
  const atmRows = document.querySelectorAll("#atm-list tbody tr");
  if (!atmRows.length) {
    return false;
  }

  let hasMatch = false;
  atmRows.forEach((row) => {
    const rowText = normalizeSearchValue(row.textContent);
    const isMatch = !query || rowText.includes(query);
    row.hidden = !isMatch;
    if (isMatch) {
      hasMatch = true;
    }
  });

  return hasMatch;
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
    filterAtmRows("");
    if (globalSearchInput) {
      globalSearchInput.setCustomValidity("");
    }
    return;
  }

  const matchedAtmRows = filterAtmRows(normalizedQuery);
  if (matchedAtmRows && validScreenIds.has("atm-list")) {
    navigateToScreen("atm-list");
    if (globalSearchInput) {
      globalSearchInput.setCustomValidity("");
    }
    return;
  }

  const targetScreenId = findBestSearchTarget(normalizedQuery);
  if (targetScreenId) {
    navigateToScreen(targetScreenId);
    if (globalSearchInput) {
      globalSearchInput.setCustomValidity("");
    }
    return;
  }

  if (globalSearchInput) {
    globalSearchInput.setCustomValidity("No matching dashboard content found.");
    globalSearchInput.reportValidity();
  }
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
    if (globalSearchInput.validity.customError) {
      globalSearchInput.setCustomValidity("");
    }
    applySearch(event.target.value);
  });

  globalSearchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      applySearch(event.target.value);
    }
  });
}

if (confirmActionButton && confirmationCard) {
  confirmActionButton.addEventListener("click", () => {
    confirmationCard.innerHTML =
      "<p><strong>Action recorded:</strong> Source-backed review started for ATM-GB-0003.</p><p>Compare ATMH cassette depletion, KAFK host-unavailable windows, and the ATMA reconnect event before escalating runtime follow-up.</p>";
    confirmationCard.focus();
  });
}

window.addEventListener("hashchange", () => {
  const targetId = window.location.hash.replace("#", "") || activeRoleConfig.defaultScreen;
  showScreen(validScreenIds.has(targetId) ? targetId : activeRoleConfig.defaultScreen);
});

setLargeUi(loadLargeUiPreference());
initializeDashboardUiState();
configureRoleView();
applyRoleDashboardCopy();

const initialTargetId = window.location.hash.replace("#", "") || activeRoleConfig.defaultScreen;
showScreen(validScreenIds.has(initialTargetId) ? initialTargetId : activeRoleConfig.defaultScreen);

// ─── Data layer ───────────────────────────────────────────────────────────────

async function fetchDashboardData() {
  try {
    const [summary, scale, snapshot, atmList, alerts] = await Promise.all([
      fetch("/api/summary").then((r) => r.json()),
      fetch("/api/scale").then((r) => r.json()),
      fetch("/api/source-snapshot").then((r) => r.json()),
      fetch("/api/atm-list").then((r) => r.json()),
      fetch("/api/alerts").then((r) => r.json()),
    ]);

    if (summary.status === "ok") populateSummary(summary);
    if (scale.status === "ok") populateScale(scale);
    if (snapshot.status === "ok") populateSourceSnapshot(snapshot.sources);
    if (atmList.status === "ok") populateAtmList(atmList.atms);
    if (alerts.status === "ok") populateAlerts(alerts);
  } catch (err) {
    console.warn("[dashboard] data fetch failed:", err);
  }
}

function populateSummary(data) {
  setMetricCardState("observedAtms", uiStateModes.READY, {
    value: String(data.observed_atms),
    note: `${data.app_errors} app error events across ATMA`,
  });
  setMetricCardState("atmAppErrors", uiStateModes.READY, {
    value: String(data.app_errors),
    note: `${data.failure_windows} critical detection groups`,
  });
  setMetricCardState("hardwareAlerts", uiStateModes.READY, {
    value: String(data.hardware_alerts),
    note: "ATMH WARNING + CRITICAL events",
  });
  setMetricCardState("eventThroughput", uiStateModes.READY, {
    value: String(data.avg_tps),
    note: "Average transactions per KAFK window",
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
  setText("scale-window", data.time_window);
  setText("scale-avg-tps", String(data.avg_tps));
}

function populateSourceSnapshot(sources) {
  const tbody = document.getElementById("source-snapshot-tbody");
  if (!tbody) return;
  tbody.innerHTML = sources
    .map(
      (s) => `
    <tr>
      <th scope="row">${s.source}</th>
      <td>${s.status}</td>
      <td>${s.signal === "present" ? "Live" : s.signal === "empty" ? "Empty" : "Absent"}</td>
      <td>${s.signal === "present" ? "Source data available." : "No records ingested yet."}</td>
    </tr>`
    )
    .join("");
}

function populateAtmList(atms) {
  const tbody = document.getElementById("atm-list-tbody");
  if (!tbody) return;
  if (!atms.length) {
    tbody.innerHTML = '<tr><td colspan="6">No ATM data available.</td></tr>';
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
      <td><button class="text-button" type="button" data-screen-target="atm-detail">Open</button></td>
    </tr>`;
    })
    .join("");
}

function populateAlerts(data) {
  const critSummary = document.getElementById("alerts-critical-summary");
  const critList = document.getElementById("alerts-critical-list");
  const warnSummary = document.getElementById("alerts-warning-summary");
  const warnList = document.getElementById("alerts-warning-list");

  if (critSummary) {
    critSummary.textContent = `${data.critical.length} critical anomaly group${data.critical.length !== 1 ? "s" : ""}`;
  }
  if (critList) {
    critList.innerHTML = data.critical.length
      ? data.critical
          .map(
            (a) =>
              `<li><strong>${a.anomaly_name} (${a.anomaly_type})</strong> — ${a.source}${a.atm_id && a.atm_id !== "N/A" ? " / " + a.atm_id : ""}: ${a.description || ""} <em>(${a.event_count} event${a.event_count !== 1 ? "s" : ""})</em></li>`
          )
          .join("")
      : "<li>No critical anomalies detected.</li>";
  }

  if (warnSummary) {
    warnSummary.textContent = `${data.warning.length} warning anomaly group${data.warning.length !== 1 ? "s" : ""}`;
  }
  if (warnList) {
    warnList.innerHTML = data.warning.length
      ? data.warning
          .map(
            (a) =>
              `<li><strong>${a.anomaly_name} (${a.anomaly_type})</strong> — ${a.source}${a.atm_id && a.atm_id !== "N/A" ? " / " + a.atm_id : ""}: ${a.description || ""} <em>(${a.event_count} event${a.event_count !== 1 ? "s" : ""})</em></li>`
          )
          .join("")
      : "<li>No warning anomalies detected.</li>";
  }

  const hostEl = document.getElementById("host-pressure-value");
  if (hostEl) {
    const winosWarning = data.warning.find((a) => a.source === "WINOS");
    hostEl.textContent = winosWarning ? "Elevated" : "Normal";
  }
}

fetchDashboardData();

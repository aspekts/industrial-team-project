const navButtons = document.querySelectorAll("[data-screen-target]");
const screens = document.querySelectorAll(".screen");
const confirmActionButton = document.getElementById("confirm-action");
const confirmationCard = document.getElementById("confirmation-card");
const clickableCards = document.querySelectorAll(".metric-card-action[data-screen-target]");
const accessibilityToggle = document.getElementById("accessibility-toggle");
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
    allowedScreens: ["dashboard", "atm-list", "alerts"],
    dashboardTitle: "Manager summary view",
    dashboardDescription: "Review summary-level operational posture, ATM coverage, and grouped anomaly demand.",
    dashboardStatus: "Loading...",
    bannerEyebrow: "Manager focus",
    bannerTitle: "Summary metrics and grouped exceptions will appear here.",
    primaryActionLabel: "Review grouped anomalies",
  },
  ops: {
    defaultScreen: "alerts",
    allowedScreens: ["dashboard", "atm-detail", "atm-list", "alerts", "action-center"],
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

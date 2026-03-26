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
  },
  manager: {
    defaultScreen: "dashboard",
    allowedScreens: ["dashboard", "atm-list", "alerts"],
  },
  ops: {
    defaultScreen: "alerts",
    allowedScreens: ["dashboard", "atm-detail", "atm-list", "alerts", "action-center"],
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

  const valueNode = card.querySelector(".metric-value");
  const noteNode = card.querySelector(".metric-note");
  const subnoteNode = card.querySelector(".metric-subnote");
  const hintNode = card.querySelector(".metric-link-hint");

  return {
    card,
    valueNode,
    noteNode,
    subnoteNode,
    hintNode,
    fallback: {
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
  const value = payload.value ?? fallback.value;
  const note = payload.note ?? fallback.note;
  const subnote = payload.subnote ?? fallback.subnote;
  const hint = payload.hint ?? fallback.hint;
  const ariaLabel = payload.ariaLabel ?? fallback.ariaLabel;

  state.card.dataset.uiState = mode;
  state.card.setAttribute("aria-busy", String(mode === uiStateModes.LOADING));
  state.card.setAttribute("aria-label", ariaLabel);

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

const initialTargetId = window.location.hash.replace("#", "") || activeRoleConfig.defaultScreen;
showScreen(validScreenIds.has(initialTargetId) ? initialTargetId : activeRoleConfig.defaultScreen);

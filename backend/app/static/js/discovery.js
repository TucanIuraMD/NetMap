(function () {
  "use strict";

  const urls = window.NM_DISCOVERY || {};

  const networkEl = document.getElementById("discovery-network");
  const startBtn = document.getElementById("discovery-start");
  const cancelBtn = document.getElementById("discovery-cancel");
  const reloadBtn = document.getElementById("discovery-reload");
  const errorEl = document.getElementById("discovery-error");
  const idleEl = document.getElementById("discovery-idle");
  const runningEl = document.getElementById("discovery-running");
  const resultsEl = document.getElementById("discovery-results");
  const statusBadge = document.getElementById("discovery-status-badge");
  const phaseEl = document.getElementById("discovery-phase");
  const scannedEl = document.getElementById("discovery-scanned");
  const totalEl = document.getElementById("discovery-total");
  const discoveredEl = document.getElementById("discovery-discovered");
  const progressEl = document.getElementById("discovery-progress");
  const jobErrorEl = document.getElementById("discovery-job-error");
  const resultsCountEl = document.getElementById("discovery-results-count");
  const resultsBodyEl = document.getElementById("discovery-results-body");

  const POLL_INTERVAL_MS = 1000;

  let pollTimer = null;
  let activeNetworkId = null;
  let inFlight = false;

  function setError(message) {
    if (message) {
      errorEl.textContent = message;
      errorEl.classList.remove("d-none");
    } else {
      errorEl.textContent = "";
      errorEl.classList.add("d-none");
    }
  }

  function setRunningUi(job) {
    idleEl.classList.add("d-none");
    resultsEl.classList.add("d-none");
    runningEl.classList.remove("d-none");

    const status = job.status || "running";
    statusBadge.textContent = status;
    statusBadge.className =
      "badge " +
      (status === "running"
        ? "text-bg-primary"
        : status === "completed"
          ? "text-bg-success"
          : status === "cancelled"
            ? "text-bg-warning"
            : "text-bg-danger");

    phaseEl.textContent = job.phase || "";
    scannedEl.textContent = job.scanned_hosts || 0;
    totalEl.textContent = job.total_hosts || 0;
    discoveredEl.textContent = job.discovered || 0;

    const progress = typeof job.progress === "number" ? job.progress : 0;
    progressEl.style.width = progress + "%";
    progressEl.textContent = progress + "%";
    progressEl.classList.toggle("progress-bar-animated", status === "running");

    startBtn.disabled = status === "running";
    cancelBtn.disabled = status !== "running";

    if (job.error) {
      jobErrorEl.textContent = job.error;
      jobErrorEl.classList.remove("d-none");
    } else {
      jobErrorEl.classList.add("d-none");
    }
  }

  function renderResults(results) {
    resultsCountEl.textContent = results.length + " hosts";
    resultsBodyEl.innerHTML = "";

    if (!results.length) {
      const tr = document.createElement("tr");
      tr.innerHTML =
        '<td colspan="5" class="text-body-secondary">Хосты не найдены.</td>';
      resultsBodyEl.appendChild(tr);
      return;
    }

    results.forEach(function (host) {
      const tr = document.createElement("tr");
      const deviceLink = host.device_id
        ? '<a href="' + window.NM_DEVICES_BASE + "/" + host.device_id + '">' +
          host.device_id + "</a>"
        : '<span class="text-body-secondary">—</span>';

      tr.innerHTML =
        '<td class="nm-mono">' + escapeHtml(host.ip_address) + "</td>" +
        '<td>' + escapeHtml(host.hostname || "—") + "</td>" +
        '<td>' +
        (host.reachable
          ? '<span class="badge text-bg-success">yes</span>'
          : '<span class="badge text-bg-secondary">no</span>') +
        "</td>" +
        '<td class="nm-mono">' + escapeHtml((host.open_ports || []).join(", ") || "—") + "</td>" +
        "<td>" + deviceLink + "</td>";

      resultsBodyEl.appendChild(tr);
    });
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (c) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[c];
    });
  }

  function stopPolling() {
    if (pollTimer !== null) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function currentNetworkId() {
    const value = networkEl.value;
    return value ? parseInt(value, 10) : null;
  }

  async function fetchJson(url, options) {
    const res = await fetch(url, options);
    let payload = null;
    try {
      payload = await res.json();
    } catch (err) {
      payload = null;
    }
    if (!res.ok) {
      const message = payload && payload.error ? payload.error : "HTTP " + res.status;
      const err = new Error(message);
      err.status = res.status;
      err.payload = payload;
      throw err;
    }
    return payload;
  }

  async function loadResults(networkId) {
    try {
      const data = await fetchJson(
        urls.resultsUrl + "?network_id=" + encodeURIComponent(networkId)
      );
      resultsEl.classList.remove("d-none");
      renderResults(data.results || []);
    } catch (err) {
      if (err.status !== 404) {
        setError("Не удалось загрузить результаты: " + err.message);
      }
    }
  }

  async function pollOnce(networkId) {
    if (inFlight || networkId !== activeNetworkId) {
      return;
    }
    inFlight = true;
    try {
      const job = await fetchJson(
        urls.statusUrl + "?network_id=" + encodeURIComponent(networkId)
      );
      if (networkId !== activeNetworkId) {
        return;
      }
      setRunningUi(job);

      if (job.status === "completed") {
        stopPolling();
        await loadResults(networkId);
      } else if (job.status === "cancelled" || job.status === "failed") {
        stopPolling();
      }
    } catch (err) {
      if (err.status === 404) {
        stopPolling();
        setIdle();
      } else {
        setError("Не удалось получить статус: " + err.message);
        stopPolling();
      }
    } finally {
      inFlight = false;
    }
  }

  function setIdle() {
    stopPolling();
    activeNetworkId = null;
    runningEl.classList.add("d-none");
    resultsEl.classList.add("d-none");
    idleEl.classList.remove("d-none");
    startBtn.disabled = false;
    cancelBtn.disabled = true;
  }

  function startPolling(networkId) {
    stopPolling();
    activeNetworkId = networkId;
    idleEl.classList.add("d-none");
    runningEl.classList.remove("d-none");
    pollTimer = setInterval(function () {
      pollOnce(networkId);
    }, POLL_INTERVAL_MS);
    pollOnce(networkId);
  }

  // Restore the UI state for the selected network (used on page load
  // and when the selection changes). 404 means no job -> idle state.
  async function restoreState(networkId) {
    setError(null);
    stopPolling();
    activeNetworkId = networkId;

    if (!networkId) {
      setIdle();
      return;
    }

    try {
      const job = await fetchJson(
        urls.statusUrl + "?network_id=" + encodeURIComponent(networkId)
      );
      if (networkId !== activeNetworkId) {
        return;
      }
      setRunningUi(job);

      if (job.status === "running") {
        startPolling(networkId);
      } else if (job.status === "completed") {
        await loadResults(networkId);
      }
    } catch (err) {
      if (err.status === 404) {
        setIdle();
      } else {
        setIdle();
        setError("Не удалось восстановить состояние: " + err.message);
      }
    }
  }

  async function startDiscovery() {
    const networkId = currentNetworkId();
    if (!networkId) {
      setError("Сначала выберите сеть.");
      return;
    }

    setError(null);
    startBtn.disabled = true;

    try {
      const job = await fetchJson(urls.startUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ network_id: networkId }),
      });
      startPolling(networkId);
      setRunningUi(job);
    } catch (err) {
      startBtn.disabled = false;
      setError("Не удалось запустить discovery: " + err.message);
      // Still try to restore the actual state (a job may already run).
      restoreState(networkId);
    }
  }

  async function cancelDiscovery() {
    const networkId = currentNetworkId();
    if (!networkId) {
      return;
    }
    setError(null);
    cancelBtn.disabled = true;

    try {
      await fetchJson(urls.cancelUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ network_id: networkId }),
      });
      pollOnce(networkId);
    } catch (err) {
      cancelBtn.disabled = false;
      setError("Не удалось отменить: " + err.message);
    }
  }

  startBtn.addEventListener("click", startDiscovery);
  cancelBtn.addEventListener("click", cancelDiscovery);
  reloadBtn.addEventListener("click", function () {
    restoreState(currentNetworkId());
  });
  networkEl.addEventListener("change", function () {
    restoreState(currentNetworkId());
  });

  restoreState(currentNetworkId());
})();
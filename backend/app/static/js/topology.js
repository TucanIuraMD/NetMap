(function () {
  "use strict";

  const statusEl = document.getElementById("topology-status");
  const canvasEl = document.getElementById("topology-canvas");
  const panelEl = document.getElementById("topology-node-panel");
  const titleEl = document.getElementById("topology-node-title");
  const metaEl = document.getElementById("topology-node-meta");
  const linkEl = document.getElementById("topology-node-link");

  let cy = null;

  function nodeLabel(device) {
    return device.display_name || device.name;
  }

  function statusColor(isActive) {
    return isActive ? "#3fb950" : "#8b949e";
  }

  async function loadGraph() {
    statusEl.textContent = "Loading topology…";
    panelEl.classList.add("d-none");

    let devices, connections;

    try {
      const [devicesRes, connectionsRes] = await Promise.all([
        fetch(window.NM_DEVICES_URL),
        fetch(window.NM_CONNECTIONS_URL),
      ]);
      devices = await devicesRes.json();
      connections = await connectionsRes.json();
    } catch (err) {
      statusEl.textContent = "Не удалось загрузить данные топологии.";
      return;
    }

    const nodes = devices.map(function (device) {
      return {
        data: {
          id: "device-" + device.id,
          deviceId: device.id,
          label: nodeLabel(device),
          isActive: device.is_active,
        },
      };
    });

    const edges = connections
      .filter(function (c) {
        return (
          devices.some((d) => d.id === c.source_device_id) &&
          devices.some((d) => d.id === c.target_device_id)
        );
      })
      .map(function (c) {
        return {
          data: {
            id: "conn-" + c.id,
            source: "device-" + c.source_device_id,
            target: "device-" + c.target_device_id,
            type: c.connection_type,
          },
        };
      });

    if (cy) {
      cy.destroy();
    }

    cy = cytoscape({
      container: canvasEl,
      elements: { nodes: nodes, edges: edges },
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "background-color": function (ele) {
              return statusColor(ele.data("isActive"));
            },
            color: "#e6edf3",
            "font-size": 11,
            "text-valign": "bottom",
            "text-margin-y": 6,
            width: 28,
            height: 28,
            "border-width": 2,
            "border-color": "#30363d",
          },
        },
        {
          selector: "edge",
          style: {
            width: 2,
            "line-color": "#58a6ff",
            "curve-style": "bezier",
            "line-style": function (ele) {
              return ele.data("type") === "wifi" ? "dashed" : "solid";
            },
          },
        },
        {
          selector: "node:selected",
          style: {
            "border-color": "#58a6ff",
            "border-width": 3,
          },
        },
      ],
      layout: { name: "cose", animate: false },
      minZoom: 0.2,
      maxZoom: 3,
    });

    cy.on("tap", "node", function (evt) {
      const data = evt.target.data();
      const device = devices.find((d) => d.id === data.deviceId);
      if (!device) return;

      titleEl.textContent = nodeLabel(device);
      metaEl.textContent =
        (device.device_type || "unknown") +
        " · " +
        (device.is_active ? "Active" : "Inactive");
      linkEl.href = window.NM_DEVICE_DETAILS_BASE + "/" + device.id;
      panelEl.classList.remove("d-none");
    });

    statusEl.textContent =
      nodes.length + " devices, " + edges.length + " connections";
  }

  document.getElementById("topology-fit").addEventListener("click", function () {
    if (cy) cy.fit(undefined, 30);
  });

  document.getElementById("topology-reload").addEventListener("click", loadGraph);

  loadGraph();
})();

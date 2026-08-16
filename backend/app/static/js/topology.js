(function () {
  "use strict";

  const statusEl = document.getElementById("topology-status");
  const canvasEl = document.getElementById("topology-canvas");
  const panelEl = document.getElementById("topology-node-panel");
  const titleEl = document.getElementById("topology-node-title");
  const metaEl = document.getElementById("topology-node-meta");
  const linkEl = document.getElementById("topology-node-link");

  const GENERIC_IFACE_NAMES = ["discovered", "unknown", "iface", "interface", "eth"];

  let cy = null;
  let allDevices = [];
  let unlinkedNodes = [];
  let showUnlinked = false;

  function nodeLabel(device) {
    return device.display_name || device.name;
  }

  function statusColor(isActive) {
    return isActive ? "#3fb950" : "#8b949e";
  }

  function ifaceLabel(iface) {
    if (!iface) return null;
    const name = (iface.name || "").trim();
    if (name && GENERIC_IFACE_NAMES.indexOf(name.toLowerCase()) === -1) {
      return name;
    }
    return "iface " + iface.id;
  }

  async function loadGraph() {
    statusEl.textContent = "Loading topology…";
    panelEl.classList.add("d-none");

    let devices, connections, interfaces;

    try {
      const [devicesRes, connectionsRes, interfacesRes] = await Promise.all([
        fetch(window.NM_DEVICES_URL),
        fetch(window.NM_CONNECTIONS_URL),
        fetch(window.NM_INTERFACES_URL || "/api/v1/interfaces"),
      ]);
      devices = await devicesRes.json();
      connections = await connectionsRes.json();
      interfaces = await interfacesRes.json();
    } catch (err) {
      statusEl.textContent = "Не удалось загрузить данные топологии.";
      return;
    }

    allDevices = devices;

    const interfacesByDevice = {};
    (interfaces || []).forEach(function (iface) {
      (interfacesByDevice[iface.device_id] =
        interfacesByDevice[iface.device_id] || []).push(iface);
    });

    // Devices that participate in at least one connection are rendered in
    // the main graph; everything else is placed in a distinct side cluster
    // so it does not clutter the main view but stays accessible.
    const linkedIds = new Set();
    connections.forEach(function (c) {
      linkedIds.add(c.source_device_id);
      linkedIds.add(c.target_device_id);
    });

    const linked = devices.filter(function (d) {
      return linkedIds.has(d.id);
    });
    const unlinked = devices.filter(function (d) {
      return !linkedIds.has(d.id);
    });

    unlinkedNodes = unlinked.map(function (device) {
      return {
        data: {
          id: "device-" + device.id,
          deviceId: device.id,
          label: nodeLabel(device),
          isActive: device.is_active,
          linked: false,
        },
      };
    });

    const nodes = linked.map(function (device) {
      return {
        data: {
          id: "device-" + device.id,
          deviceId: device.id,
          label: nodeLabel(device),
          isActive: device.is_active,
          linked: true,
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
        const sourceIface = ifaceLabel(
          (interfacesByDevice[c.source_device_id] || []).find(
            function (i) {
              return i.id === c.source_interface_id;
            }
          )
        );
        const targetIface = ifaceLabel(
          (interfacesByDevice[c.target_device_id] || []).find(
            function (i) {
              return i.id === c.target_interface_id;
            }
          )
        );

        let label = null;
        if (sourceIface && targetIface) {
          label = sourceIface + " → " + targetIface;
        } else if (sourceIface) {
          label = sourceIface + " →";
        } else if (targetIface) {
          label = "→ " + targetIface;
        }

        return {
          data: {
            id: "conn-" + c.id,
            source: "device-" + c.source_device_id,
            target: "device-" + c.target_device_id,
            type: c.connection_type,
            label: label,
          },
        };
      });

    if (cy) {
      cy.destroy();
    }

    const initialNodes = showUnlinked
      ? nodes.concat(unlinkedNodes)
      : nodes;

    cy = cytoscape({
      container: canvasEl,
      elements: { nodes: initialNodes, edges: edges },
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
            "text-wrap": "wrap",
            "text-max-width": "120px",
            width: 28,
            height: 28,
            "border-width": 2,
            "border-color": "#30363d",
          },
        },
        {
          selector: "node[?linked]",
          style: {
            width: 34,
            height: 34,
            "border-color": "#58a6ff",
          },
        },
        {
          selector: "node[!linked]",
          style: {
            "background-color": "#21262d",
            "border-color": "#484f58",
            "border-style": "dashed",
            color: "#8b949e",
            "font-size": 10,
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
            label: "data(label)",
            color: "#8b949e",
            "font-size": 10,
            "text-background-color": "#0d1117",
            "text-background-opacity": 0.85,
            "text-background-padding": "2px",
            "text-rotation": "autorotate",
            "text-margin-y": -10,
          },
        },
        {
          selector: "node:selected",
          style: {
            "border-color": "#f0883e",
            "border-width": 3,
          },
        },
      ],
      layout: {
        name: "cose",
        animate: false,
        randomize: true,
        fit: true,
        padding: 60,
        nodeRepulsion: function (node) {
          return node.data("linked") ? 22000 : 12000;
        },
        idealEdgeLength: function (edge) {
          return 160;
        },
        edgeElasticity: function (edge) {
          return 90;
        },
        nodeOverlap: 50,
        componentSpacing: 120,
        gravity: 0.4,
        numIter: 2000,
      },
      minZoom: 0.15,
      maxZoom: 3,
    });

    cy.on("layoutstop", function () {
      // Keep the main graph in view by default; when unlinked devices are
      // toggled on, keep them visible too (no repositioning needed — cose
      // separates components with componentSpacing).
      if (showUnlinked) {
        cy.fit(undefined, 40);
      } else {
        cy.fit(cy.elements("node[?linked]"), 60);
      }
    });

    cy.on("tap", "node", function (evt) {
      const data = evt.target.data();
      const device = allDevices.find((d) => d.id === data.deviceId);
      if (!device) return;

      titleEl.textContent = nodeLabel(device);
      metaEl.textContent =
        (device.device_type || "unknown") +
        " · " +
        (device.is_active ? "Active" : "Inactive");
      linkEl.href = window.NM_DEVICE_DETAILS_BASE + "/" + device.id;
      panelEl.classList.remove("d-none");
    });

    const linkedCount = linked.length;
    const unlinkedCount = unlinked.length;
    statusEl.textContent =
      linkedCount +
      " linked devices, " +
      edges.length +
      " connections" +
      (unlinkedCount ? " · " + unlinkedCount + " without links" : "");
    toggleBtn.textContent = showUnlinked
      ? "Hide without links"
      : "Show without links (" + unlinkedCount + ")";
  }

  document.getElementById("topology-fit").addEventListener("click", function () {
    if (cy) cy.fit(undefined, 40);
  });

  document.getElementById("topology-reload").addEventListener("click", loadGraph);

  const toggleBtn = document.getElementById("topology-toggle-unlinked");
  toggleBtn.addEventListener("click", function () {
    showUnlinked = !showUnlinked;
    toggleBtn.classList.toggle("active", showUnlinked);
    loadGraph();
  });

  loadGraph();
})();
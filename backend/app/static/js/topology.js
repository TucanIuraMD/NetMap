(function () {
  "use strict";

  const statusEl = document.getElementById("topology-status");
  const canvasEl = document.getElementById("topology-canvas");
  const panelEl = document.getElementById("topology-node-panel");
  const titleEl = document.getElementById("topology-node-title");
  const metaEl = document.getElementById("topology-node-meta");
  const linkEl = document.getElementById("topology-node-link");

  const GENERIC_IFACE_NAMES = ["discovered", "unknown", "iface", "interface", "eth"];
  const LINK_COLOR = "#58a6ff";
  const WIFI_COLOR = "#d29922";

  let cy = null;
  let allNodes = [];
  let unlinkedNodes = [];
  let showUnlinked = false;

  function statusColor(isActive) {
    return isActive ? "#3fb950" : "#8b949e";
  }

  function deviceLabel(node) {
    const device = node.data.device || {};
    return device.display_name || device.hostname || device.name || "device " + device.id;
  }

  function primaryIp(node) {
    const interfaces = node.data.interfaces || [];
    for (const iface of interfaces) {
      for (const ip of iface.ip_addresses || []) {
        if (ip.is_primary) {
          return ip.address;
        }
      }
    }
    return null;
  }

  function interfaceLabel(iface) {
    if (!iface) {
      return null;
    }
    const name = (iface.name || "").trim();
    if (name && GENERIC_IFACE_NAMES.indexOf(name.toLowerCase()) === -1) {
      return name;
    }
    return "iface " + iface.id;
  }

  function portLabel(port) {
    if (!port) {
      return null;
    }
    let label = port.port_number + "/" + port.protocol;
    if (port.display_name) {
      label += " (" + port.display_name + ")";
    }
    return label;
  }

  // Interface + port (when present) for one end of a connection.
  function endpointLabel(node, interfaceId, portId) {
    const parts = [];
    if (interfaceId != null) {
      const iface = (node.data.interfaces || []).find(function (i) {
        return i.id === interfaceId;
      });
      const il = interfaceLabel(iface);
      if (il) {
        parts.push(il);
      }
    }
    if (portId != null) {
      const port = (node.data.ports || []).find(function (p) {
        return p.id === portId;
      });
      const pl = portLabel(port);
      if (pl) {
        parts.push(pl);
      }
    }
    return parts.length ? parts.join(" · ") : null;
  }

  function edgeLabel(edge, nodesById) {
    const conn = edge.data.connection || {};
    const sourceNode = nodesById.get(edge.data.source);
    const targetNode = nodesById.get(edge.data.target);
    const src = sourceNode
      ? endpointLabel(sourceNode, conn.source_interface_id, conn.source_port_id)
      : null;
    const tgt = targetNode
      ? endpointLabel(targetNode, conn.target_interface_id, conn.target_port_id)
      : null;

    if (src && tgt) {
      return src + " → " + tgt;
    }
    if (src) {
      return src + " →";
    }
    if (tgt) {
      return "→ " + tgt;
    }
    return null;
  }

  function filterParams() {
    const params = [];
    const network = document.getElementById("topology-network").value;
    const type = document.getElementById("topology-type").value;
    const status = document.getElementById("topology-status").value;
    if (network) {
      params.push("network_id=" + encodeURIComponent(network));
    }
    if (type) {
      params.push("device_type=" + encodeURIComponent(type));
    }
    if (status) {
      params.push("status=" + encodeURIComponent(status));
    }
    return params.join("&");
  }

  function showEmptyState() {
    if (cy) {
      cy.destroy();
      cy = null;
    }
    canvasEl.classList.add("d-none");
    statusEl.textContent = showUnlinked
      ? "Устройства не найдены."
      : "Нет устройств, связанных соединениями. Добавьте соединения, чтобы увидеть топологию.";
    toggleBtn.textContent = "Show without links";
    panelEl.classList.add("d-none");
  }

  async function loadGraph() {
    statusEl.textContent = "Loading topology…";
    panelEl.classList.add("d-none");

    let payload;
    try {
      const qs = filterParams();
      const url = window.NM_TOPOLOGY_URL + (qs ? "?" + qs : "");
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error("HTTP " + res.status);
      }
      payload = await res.json();
    } catch (err) {
      statusEl.textContent = "Не удалось загрузить данные топологии.";
      return;
    }

    const apiNodes = payload.nodes || [];
    const apiEdges = payload.edges || [];

    if (!apiNodes.length) {
      showEmptyState();
      return;
    }

    if (cy) {
      cy.destroy();
      cy = null;
    }
    canvasEl.classList.remove("d-none");

    allNodes = apiNodes;
    unlinkedNodes = apiNodes.filter(function (n) {
      return !n.data.linked;
    });

    const nodesById = new Map(
      apiNodes.map(function (n) {
        return [n.data.id, n];
      })
    );

    const nodes = apiNodes.map(function (node) {
      const label = deviceLabel(node);
      const ip = primaryIp(node);
      return {
        data: {
          id: node.data.id,
          deviceId: node.data.deviceId,
          label: label,
          subtitle: ip && ip !== label ? ip : null,
          isActive: node.data.isActive,
          linked: node.data.linked,
        },
      };
    });

    const edges = apiEdges
      .filter(function (e) {
        return nodesById.has(e.data.source) && nodesById.has(e.data.target);
      })
      .map(function (e) {
        return {
          data: {
            id: e.data.id,
            source: e.data.source,
            target: e.data.target,
            type: e.data.type,
            label: edgeLabel(e, nodesById),
          },
        };
      });

    const initialNodes = showUnlinked
      ? nodes
      : nodes.filter(function (n) {
          return n.data.linked;
        });

    if (!initialNodes.length) {
      showEmptyState();
      return;
    }

    cy = cytoscape({
      container: canvasEl,
      elements: { nodes: initialNodes, edges: edges },
      style: [
        {
          selector: "node",
          style: {
            label: function (ele) {
              const sub = ele.data("subtitle");
              return sub ? ele.data("label") + "\n" + sub : ele.data("label");
            },
            "background-color": function (ele) {
              return statusColor(ele.data("isActive"));
            },
            color: "#e6edf3",
            "font-size": 11,
            "text-valign": "bottom",
            "text-margin-y": 8,
            "text-wrap": "wrap",
            "text-max-width": "130px",
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
            "border-color": LINK_COLOR,
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
            "line-color": function (ele) {
              return ele.data("type") === "wifi" ? WIFI_COLOR : LINK_COLOR;
            },
            "curve-style": "bezier",
            "target-arrow-shape": "triangle",
            "target-arrow-color": function (ele) {
              return ele.data("type") === "wifi" ? WIFI_COLOR : LINK_COLOR;
            },
            "arrow-scale": 0.9,
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
      if (showUnlinked) {
        cy.fit(undefined, 40);
      } else {
        cy.fit(cy.elements("node[?linked]"), 60);
      }
    });

    cy.on("tap", "node", function (evt) {
      const data = evt.target.data();
      const node = allNodes.find(function (n) {
        return n.data.deviceId === data.deviceId;
      });
      if (!node) {
        return;
      }
      const device = node.data.device || {};
      const bits = [];
      if (device.device_type) {
        bits.push(device.device_type);
      }
      const ip = primaryIp(node);
      if (ip) {
        bits.push(ip);
      }
      bits.push(device.is_active ? "Active" : "Inactive");
      titleEl.textContent = deviceLabel(node);
      metaEl.textContent = bits.join(" · ");
      linkEl.href = window.NM_DEVICE_DETAILS_BASE + "/" + device.id;
      panelEl.classList.remove("d-none");
    });

    const linkedCount = apiNodes.length - unlinkedNodes.length;
    statusEl.textContent =
      linkedCount +
      " linked devices, " +
      edges.length +
      " connections" +
      (unlinkedNodes.length
        ? " · " + unlinkedNodes.length + " without links"
        : "");
    toggleBtn.textContent = showUnlinked
      ? "Hide without links"
      : "Show without links (" + unlinkedNodes.length + ")";
  }

  document.getElementById("topology-fit").addEventListener("click", function () {
    if (cy) {
      cy.fit(undefined, 40);
    }
  });

  document.getElementById("topology-reload").addEventListener("click", loadGraph);
  document.getElementById("topology-reset").addEventListener("click", function () {
    document.getElementById("topology-network").value = "";
    document.getElementById("topology-type").value = "";
    document.getElementById("topology-status").value = "";
    loadGraph();
  });

  var toggleBtn = document.getElementById("topology-toggle-unlinked");
  toggleBtn.addEventListener("click", function () {
    showUnlinked = !showUnlinked;
    toggleBtn.classList.toggle("active", showUnlinked);
    loadGraph();
  });

  ["topology-network", "topology-type", "topology-status"].forEach(function (id) {
    document.getElementById(id).addEventListener("change", loadGraph);
  });

  loadGraph();
})();
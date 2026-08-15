(function () {
  "use strict";

  const modalEl = document.getElementById("nm-modal");
  const bsModal = modalEl ? new bootstrap.Modal(modalEl) : null;

  // Any element with data-nm-modal-target="#nm-modal" opens the shared
  // modal once HTMX has swapped content into #nm-modal-content.
  document.body.addEventListener("htmx:afterSwap", function (evt) {
    if (evt.detail.target && evt.detail.target.id === "nm-modal-content") {
      bsModal && bsModal.show();
    }
  });

  // Custom HX-Trigger events fired by the server after a successful
  // create/update (see app/web/*.py) close the modal and show a toast.
  // On pages that don't have a live-updating table for this entity
  // (e.g. Device/Network Details, which render Identity/Overview as
  // static server-side HTML), there is nothing for the OOB swap to
  // update — so reload once to reflect the saved changes.
  const wrapperIdByEvent = {
    "device-saved": "devices-table-wrapper",
    "network-saved": "networks-table-wrapper",
    "connection-saved": "connections-table-wrapper",
  };

  Object.keys(wrapperIdByEvent).forEach(function (name) {
    document.body.addEventListener(name, function () {
      bsModal && bsModal.hide();
      showToast("Сохранено", "success");

      if (!document.getElementById(wrapperIdByEvent[name])) {
        window.location.reload();
      }
    });
  });

  window.showToast = function showToast(message, variant) {
    variant = variant || "success";
    const container = document.getElementById("toast-container");
    if (!container) return;

    const wrapper = document.createElement("div");
    wrapper.className =
      "toast align-items-center text-bg-" + variant + " border-0";
    wrapper.setAttribute("role", "alert");
    wrapper.innerHTML =
      '<div class="d-flex">' +
      '<div class="toast-body">' + message + "</div>" +
      '<button type="button" class="btn-close btn-close-white me-2 m-auto" ' +
      'data-bs-dismiss="toast"></button>' +
      "</div>";

    container.appendChild(wrapper);
    const toast = new bootstrap.Toast(wrapper, { delay: 3000 });
    toast.show();
    wrapper.addEventListener("hidden.bs.toast", function () {
      wrapper.remove();
    });
  };

  // Simple confirm-before-delete for any element with
  // data-nm-confirm="text". Works with hx-delete.
  document.body.addEventListener("htmx:confirm", function (evt) {
    const message = evt.detail.elt.getAttribute("data-nm-confirm");
    if (!message) return;

    evt.preventDefault();
    if (window.confirm(message)) {
      evt.detail.issueRequest(true);
    }
  });

  document.body.addEventListener("htmx:responseError", function (evt) {
    showToast("Ошибка запроса (" + evt.detail.xhr.status + ")", "danger");
  });
})();

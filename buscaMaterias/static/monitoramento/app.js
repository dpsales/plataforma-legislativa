"use strict";

(function () {
  const tableBody = document.querySelector("#results-table tbody");
  const emptyState = document.getElementById("empty-state");
  const btnRefresh = document.getElementById("btn-refresh");
  const btnExportXlsx = document.getElementById("btn-export-xlsx");
  const btnExportDocx = document.getElementById("btn-export-docx");
  const searchInput = document.getElementById("search-text");

  const selectCasas = document.getElementById("filter-casas");
  const selectSecretarias = document.getElementById("filter-secretarias");
  const selectPrioridades = document.getElementById("filter-prioridades");

  const multiSelectValues = (select) => Array.from(select.selectedOptions).map((option) => option.value);

  const buildUrl = (base, params) => {
    const url = new URL(base, window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
      if (Array.isArray(value) && value.length) {
        url.searchParams.set(key, value.join(","));
      } else if (typeof value === "string" && value.trim()) {
        url.searchParams.set(key, value.trim());
      }
    });
    return url;
  };

  const renderLink = (label, url) => {
    if (!url) {
      return "";
    }
    return `<a href="${url}" target="_blank" rel="noopener">${label}</a>`;
  };

  const applyFilters = () => {
    const params = {
      casas: multiSelectValues(selectCasas),
      secretarias: multiSelectValues(selectSecretarias),
      prioridades: multiSelectValues(selectPrioridades),
      busca: searchInput.value,
    };
    const apiUrl = buildUrl(window.MONITORAMENTO_ENDPOINTS.api, params);
    const exportXlsx = buildUrl(window.MONITORAMENTO_ENDPOINTS.exportXlsx, params);
    const exportDocx = buildUrl(window.MONITORAMENTO_ENDPOINTS.exportDocx, params);

    btnExportXlsx.href = exportXlsx.toString();
    btnExportDocx.href = exportDocx.toString();

    return fetch(apiUrl.toString(), { headers: { Accept: "application/json" } });
  };

  const fetchAndRender = async () => {
    btnRefresh.disabled = true;
    emptyState.classList.add("d-none");
    tableBody.innerHTML = "";

    try {
      const response = await applyFilters();
      if (!response.ok) {
        throw new Error(`Erro ao buscar dados (${response.status})`);
      }
      const payload = await response.json();
      const resultados = payload.results || [];
      if (!resultados.length) {
        emptyState.classList.remove("d-none");
        return;
      }
      resultados.forEach((item) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${item.casa || ""}</td>
          <td>${item.secretaria || ""}</td>
          <td>${item.titulo || ""}</td>
          <td>${item.autor || ""}</td>
          <td>${item.ementa || ""}</td>
          <td>${item.status || ""}</td>
          <td>${item.ultima_movimentacao || ""}</td>
          <td>${item.data_movimentacao || ""}</td>
          <td>${renderLink("Ficha", item.link_ficha)}</td>
          <td>${renderLink("Inteiro", item.link_inteiro_teor)}</td>
        `;
        tableBody.appendChild(tr);
      });
    } catch (error) {
      console.error(error);
      emptyState.classList.remove("d-none");
      emptyState.textContent = "Não foi possível carregar os dados agora. Tente novamente mais tarde.";
    } finally {
      btnRefresh.disabled = false;
    }
  };

  btnRefresh.addEventListener("click", fetchAndRender);
  searchInput.addEventListener("keyup", (event) => {
    if (event.key === "Enter") {
      fetchAndRender();
    }
  });

  [selectCasas, selectSecretarias, selectPrioridades].forEach((select) => {
    if (!select) {
      return;
    }
    select.addEventListener("change", fetchAndRender);
  });

  fetchAndRender();
})();

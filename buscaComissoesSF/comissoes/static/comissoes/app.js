"use strict";

(function () {
  const tableBody = document.querySelector("#results-table tbody");
  const emptyState = document.getElementById("empty-state");
  const btnRefresh = document.getElementById("btn-refresh");
  const btnExport = document.getElementById("btn-export");
  const searchInput = document.getElementById("search-text");

  const multiSelectValues = (select) => Array.from(select.selectedOptions).map((opt) => opt.value);

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

  const renderLinks = (links) => {
    if (!Array.isArray(links) || !links.length) {
      return "";
    }
    return links
      .filter((item) => item && item.url)
      .map((item) => {
        const label = item.label || "Documento";
        return `<a href="${item.url}" target="_blank" rel="noopener">${label}</a>`;
      })
      .join(" · ");
  };

  const fetchAndRender = async () => {
    btnRefresh.disabled = true;
    const params = {
      tipos: multiSelectValues(document.getElementById("filter-types")),
      comissoes: multiSelectValues(document.getElementById("filter-comissoes")),
      situacoes: multiSelectValues(document.getElementById("filter-situacoes")),
      busca: searchInput.value,
    };

    const apiUrl = buildUrl(window.COMISSOES_ENDPOINTS.api, params);
    const exportUrl = buildUrl(window.COMISSOES_ENDPOINTS.exportXlsx, params);
    btnExport.href = exportUrl.toString();

    try {
      const response = await fetch(apiUrl, { headers: { Accept: "application/json" } });
      if (!response.ok) {
        throw new Error(`Erro ao buscar dados: ${response.status}`);
      }
      const payload = await response.json();
      const rows = payload.results || [];
      tableBody.innerHTML = "";
      if (!rows.length) {
        emptyState.classList.remove("d-none");
        return;
      }
      emptyState.classList.add("d-none");
      rows.forEach((row) => {
        const tr = document.createElement("tr");
        const textos = renderLinks(row.textos_associados);
        const links = [];
        if (row.ficha_url) {
          links.push(`<a href="${row.ficha_url}" target="_blank" rel="noopener">Ficha</a>`);
        }
        tr.innerHTML = `
          <td>${row.proposicao || ""}</td>
          <td>${row.autor || ""}</td>
          <td>${row.ementa || ""}</td>
          <td>${row.situacao || ""}</td>
          <td>${row.comissao || ""}</td>
          <td>${row.data_ultima_tramitacao || ""}</td>
          <td>${textos || ""}</td>
          <td>${links.join(" · ")}</td>
        `;
        tableBody.appendChild(tr);
      });
    } catch (error) {
      console.error(error);
      tableBody.innerHTML = "";
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
  document.querySelectorAll("select[multiple]").forEach((select) => {
    select.addEventListener("change", fetchAndRender);
  });

  fetchAndRender();
})();

/**
 * TechDebt Radar // Application Logic & Visualizations
 * Pair Programming with Antigravity
 */

(function () {
  'use strict';

  // State
  let currentReport = null;
  let activeTab = 'tab-overview';
  let filesFilter = 'all';
  let filesSearchTerm = '';
  let filesSortCol = 'deuda_horas';
  let filesSortAsc = false;
  let violationsFilter = 'all';

  // Chart instances
  let chartTopDeuda = null;
  let chartHealthDoughnut = null;
  let chartModuleDebt = null;
  let chartViolationsDoughnut = null;
  let chartMartinScatter = null;

  // Chart.js global theme defaults (Mercado Pago Light Theme)
  if (window.Chart) {
    Chart.defaults.color = '#4b5563';
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(17, 24, 39, 0.95)';
    Chart.defaults.plugins.tooltip.titleColor = '#ffffff';
    Chart.defaults.plugins.tooltip.bodyColor = '#f3f4f6';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(0, 0, 0, 0.08)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
  }

  // DOM Elements
  const repoNameDisplay = document.getElementById('repo-name-display');
  const reportDateDisplay = document.getElementById('report-date-display');
  const badgeModel = document.getElementById('badge-model');
  const btnLoadDemo = document.getElementById('btn-load-demo');
  const btnUploadFile = document.getElementById('btn-upload-file');
  const fileInput = document.getElementById('file-input');
  const dropzoneBanner = document.getElementById('dropzone-banner');
  const dropStatusBadge = document.getElementById('drop-status-badge');

  // KPI elements
  const kpiDeudaHoras = document.getElementById('kpi-deuda-horas');
  const kpiDeudaMeses = document.getElementById('kpi-deuda-meses');
  const kpiCostoUsd = document.getElementById('kpi-costo-usd');
  const kpiInteresUsd = document.getElementById('kpi-interes-usd');
  const kpiTdrVal = document.getElementById('kpi-tdr-val');
  const kpiTdrBadge = document.getElementById('kpi-tdr-badge');
  const kpiTdrSub = document.getElementById('kpi-tdr-sub');

  // SQALE tab KPIs
  const sqaleCountViolations = document.getElementById('sqale-count-violations');
  const sqaleTotalRemediation = document.getElementById('sqale-total-remediation');
  const sqaleLTd = document.getElementById('sqale-l-td');
  const sqaleVA = document.getElementById('sqale-v-a');

  // Tables & Containers
  const modulesContainer = document.getElementById('modules-container');
  const filesTbody = document.getElementById('files-tbody');
  const filesSearch = document.getElementById('files-search');
  const btnExportCsv = document.getElementById('btn-export-csv');
  const violationsTbody = document.getElementById('violations-tbody');

  // Modal
  const fileModal = document.getElementById('file-modal');
  const modalCloseBtn = document.getElementById('modal-close-btn');
  const modalFileTitle = document.getElementById('modal-file-title');
  const modalFileBadge = document.getElementById('modal-file-badge');
  const modalBodyContent = document.getElementById('modal-body-content');

  // Formatters
  function formatNumber(num, decimals = 1) {
    if (num === null || num === undefined || isNaN(num)) return '0.0';
    return Number(num).toLocaleString('es-AR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  }

  function formatCurrency(num) {
    if (num === null || num === undefined || isNaN(num)) return '$0 USD';
    return '$' + Number(num).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }) + ' USD';
  }

  function cleanPathName(fullPath) {
    if (!fullPath) return '';
    return fullPath.replace(/\\/g, '/');
  }

  function getBaseFileName(filePath) {
    const clean = cleanPathName(filePath);
    const parts = clean.split('/');
    return parts[parts.length - 1];
  }

  function getProjectName(repoPath) {
    if (!repoPath) return 'Proyecto';
    const clean = cleanPathName(repoPath).replace(/\/+$/, '');
    const parts = clean.split('/');
    return parts[parts.length - 1] || 'Proyecto';
  }

  // Load Initial Data
  async function initData() {
    // Check if demo data was embedded via demo_data.js
    if (window.__DEFAULT_REPORT_DATA__) {
      loadReport(window.__DEFAULT_REPORT_DATA__);
      return;
    }

    // Try fetching latest_report.json
    try {
      const resp = await fetch('latest_report.json');
      if (resp.ok) {
        const data = await resp.json();
        loadReport(data);
        return;
      }
    } catch (e) {
      console.warn('Fetch fallback to demo:', e);
    }
  }

  // Main Report Loading & UI Update
  function loadReport(data) {
    currentReport = data;

    // Header info
    const projName = getProjectName(data.repo_path);
    repoNameDisplay.textContent = `Proyecto: ${projName}`;
    if (data.generado_en) {
      try {
        const d = new Date(data.generado_en);
        reportDateDisplay.textContent = d.toLocaleString('es-AR', {
          dateStyle: 'short',
          timeStyle: 'medium'
        });
      } catch {
        reportDateDisplay.textContent = data.generado_en;
      }
    }
    badgeModel.textContent = (data.modelo_calculo || 'dinámico').toUpperCase();

    // Top KPIs
    const deudaHoras = data.total_deuda_horas || 0;
    kpiDeudaHoras.textContent = `${formatNumber(deudaHoras, 1)} h`;
    kpiDeudaMeses.textContent = formatNumber(deudaHoras / 160, 1);
    kpiCostoUsd.textContent = formatCurrency(data.total_costo_reparacion_usd || 0);
    kpiInteresUsd.textContent = `${formatCurrency(data.total_interes_anual_usd || 0)}/año`;

    // SQALE metrics
    const sqale = data.sqale_report || {};
    const tdr = sqale.tdr !== undefined ? sqale.tdr : 0;
    kpiTdrVal.textContent = `${formatNumber(tdr, 2)}%`;
    
    // TDR Badge & Thresholds
    let tdrClass = 'badge-success';
    let tdrText = sqale.estado_tdr || 'BAJO';
    if (tdr > 20 || tdrText === 'CRITICO') {
      tdrClass = 'badge-critical';
      tdrText = 'CRÍTICO';
    } else if (tdr > 10 || tdrText === 'ALTO') {
      tdrClass = 'badge-warning';
      tdrText = 'ALTO';
    } else if (tdr > 5 || tdrText === 'MODERADO') {
      tdrClass = 'badge-warning';
      tdrText = 'MODERADO';
    } else {
      tdrClass = 'badge-success';
      tdrText = 'BAJO';
    }
    kpiTdrBadge.className = `kpi-badge ${tdrClass}`;
    kpiTdrBadge.textContent = tdrText;
    kpiTdrSub.textContent = `L_TD: ${formatNumber(sqale.l_td || 0, 0)} LOC`;

    // SQALE Tab KPIs
    const violaciones = sqale.violaciones || [];
    sqaleCountViolations.textContent = (sqale.total_violaciones || violaciones.length).toString();
    const totalRemedMinutes = violaciones.reduce((acc, v) => acc + (v.remediacion_minutos || 0), 0);
    sqaleTotalRemediation.textContent = `${formatNumber(totalRemedMinutes / 60, 1)} h`;
    sqaleLTd.textContent = `${formatNumber(sqale.l_td || 0, 0)} LOC`;
    sqaleVA.textContent = `${formatNumber(sqale.v_a || 0, 0)} LOC`;

    // Render components
    renderCharts(data);
    renderModules(sqale.modulos || []);
    renderFilesTable();
    renderViolationsTable(violaciones);

    dropStatusBadge.textContent = 'Reporte activo: ' + projName;
    dropStatusBadge.style.color = 'var(--color-success)';
  }

  // Render All Charts
  function renderCharts(data) {
    if (!window.Chart) return;
    const archivos = data.archivos || [];
    const sqale = data.sqale_report || {};
    const modulos = sqale.modulos || [];
    const violaciones = sqale.violaciones || [];

    // 1. Chart Top 10 Deuda (Horizontal Bar)
    const sortedByDebt = [...archivos]
      .sort((a, b) => (b.deuda_horas || 0) - (a.deuda_horas || 0))
      .slice(0, 10);

    const ctxTopDeuda = document.getElementById('chart-top-deuda');
    if (ctxTopDeuda) {
      if (chartTopDeuda) chartTopDeuda.destroy();
      chartTopDeuda = new Chart(ctxTopDeuda, {
        type: 'bar',
        data: {
          labels: sortedByDebt.map(f => getBaseFileName(f.ruta)),
          datasets: [{
            label: 'Deuda en Horas',
            data: sortedByDebt.map(f => f.deuda_horas || 0),
            backgroundColor: '#009ee3',
            borderColor: '#007eb5',
            borderWidth: 1,
            borderRadius: 4
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              grid: { color: '#f1f5f9' },
              ticks: { color: '#64748b' }
            },
            y: {
              grid: { display: false },
              ticks: { color: '#1f2937', font: { family: "'JetBrains Mono', monospace", size: 11 } }
            }
          },
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                afterLabel: function (context) {
                  const item = sortedByDebt[context.dataIndex];
                  return `Costo: ${formatCurrency(item.costo_reparacion_usd)} | MI: ${formatNumber(item.mi, 1)}`;
                }
              }
            }
          }
        }
      });
    }

    // 2. Chart Health Distribution (Doughnut)
    const countCritico = archivos.filter(f => f.estado_mi === 'CRITICO').length;
    const countRegular = archivos.filter(f => f.estado_mi === 'REGULAR').length;
    const countBueno = archivos.filter(f => f.estado_mi === 'BUENO').length;

    // Update filter counts
    document.getElementById('count-all').textContent = archivos.length;
    document.getElementById('count-critico').textContent = countCritico;
    document.getElementById('count-regular').textContent = countRegular;
    document.getElementById('count-bueno').textContent = countBueno;

    const ctxHealth = document.getElementById('chart-health-doughnut');
    if (ctxHealth) {
      if (chartHealthDoughnut) chartHealthDoughnut.destroy();
      chartHealthDoughnut = new Chart(ctxHealth, {
        type: 'doughnut',
        data: {
          labels: ['Crítico (MI < 20)', 'Regular (20 ≤ MI < 65)', 'Bueno (MI ≥ 65)'],
          datasets: [{
            data: [countCritico, countRegular, countBueno],
            backgroundColor: ['#f04438', '#f59e0b', '#00a650'],
            borderColor: '#ffffff',
            borderWidth: 2,
            hoverOffset: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '70%',
          plugins: {
            legend: {
              position: 'bottom',
              labels: { padding: 16, usePointStyle: true, pointStyle: 'circle', color: '#4b5563' }
            }
          }
        }
      });
    }

    // 3. Chart Deuda por Módulo
    const moduleDebtMap = {};
    archivos.forEach(f => {
      const clean = cleanPathName(f.ruta);
      let matched = 'Otros';
      for (const m of modulos) {
        if (clean.includes(cleanPathName(m.ruta)) || clean.includes(m.nombre)) {
          matched = m.nombre;
          break;
        }
      }
      moduleDebtMap[matched] = (moduleDebtMap[matched] || 0) + (f.deuda_horas || 0);
    });

    const modLabels = Object.keys(moduleDebtMap).sort((a, b) => moduleDebtMap[b] - moduleDebtMap[a]);
    const modValues = modLabels.map(l => moduleDebtMap[l]);

    const ctxModDebt = document.getElementById('chart-module-debt');
    if (ctxModDebt) {
      if (chartModuleDebt) chartModuleDebt.destroy();
      chartModuleDebt = new Chart(ctxModDebt, {
        type: 'bar',
        data: {
          labels: modLabels,
          datasets: [{
            label: 'Horas de Deuda',
            data: modValues,
            backgroundColor: 'rgba(0, 158, 227, 0.85)',
            borderColor: '#009ee3',
            borderWidth: 1,
            borderRadius: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: '#1f2937', font: { family: "'JetBrains Mono', monospace", size: 11 } }
            },
            y: {
              grid: { color: '#f1f5f9' },
              ticks: { color: '#64748b' }
            }
          },
          plugins: {
            legend: { display: false }
          }
        }
      });
    }

    // 4. Chart Violaciones SQALE por Regla
    const ruleCounts = {};
    violaciones.forEach(v => {
      ruleCounts[v.regla] = (ruleCounts[v.regla] || 0) + 1;
    });

    const ctxViolations = document.getElementById('chart-violations-doughnut');
    if (ctxViolations) {
      if (chartViolationsDoughnut) chartViolationsDoughnut.destroy();
      const vLabels = Object.keys(ruleCounts);
      const vData = vLabels.map(k => ruleCounts[k]);

      chartViolationsDoughnut = new Chart(ctxViolations, {
        type: 'doughnut',
        data: {
          labels: vLabels.length ? vLabels : ['Sin infracciones'],
          datasets: [{
            data: vData.length ? vData : [1],
            backgroundColor: ['#f04438', '#009ee3', '#f59e0b', '#7c3aed', '#00a650'],
            borderColor: '#ffffff',
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '65%',
          plugins: {
            legend: {
              position: 'bottom',
              labels: { padding: 14, usePointStyle: true, color: '#4b5563' }
            }
          }
        }
      });
    }

    // 5. Chart Robert C. Martin A vs I (Scatter Plot)
    const ctxMartin = document.getElementById('chart-martin-scatter');
    if (ctxMartin) {
      if (chartMartinScatter) chartMartinScatter.destroy();

      // Main sequence line data: (0, 1) to (1, 0)
      const mainSequenceLine = [
        { x: 0, y: 1 },
        { x: 1, y: 0 }
      ];

      // Points for modules
      const scatterPoints = modulos.map(m => {
        let color = '#00a650'; // Main sequence (green)
        if (m.zona === 'ZONA_DOLOR') color = '#f04438';
        else if (m.zona === 'ZONA_INUTILIDAD') color = '#f59e0b';

        return {
          x: m.inestabilidad,
          y: m.abstraccion,
          module: m,
          color: color
        };
      });

      chartMartinScatter = new Chart(ctxMartin, {
        type: 'scatter',
        data: {
          datasets: [
            {
              type: 'line',
              label: 'Secuencia Principal (A + I = 1)',
              data: mainSequenceLine,
              borderColor: '#00a650',
              borderWidth: 2,
              borderDash: [6, 6],
              pointRadius: 0,
              fill: false
            },
            {
              type: 'scatter',
              label: 'Módulos Analizados',
              data: scatterPoints.map(p => ({ x: p.x, y: p.y })),
              backgroundColor: scatterPoints.map(p => p.color),
              borderColor: '#ffffff',
              borderWidth: 2,
              pointRadius: 9,
              pointHoverRadius: 13
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              min: 0,
              max: 1,
              title: {
                display: true,
                text: 'Inestabilidad (I) →  [0 = Estable, 1 = Inestable]',
                color: '#374151',
                font: { weight: 600 }
              },
              grid: { color: '#f1f5f9' },
              ticks: { color: '#64748b' }
            },
            y: {
              min: 0,
              max: 1,
              title: {
                display: true,
                text: 'Abstracción (A) →  [0 = Concreto, 1 = Abstracto]',
                color: '#374151',
                font: { weight: 600 }
              },
              grid: { color: '#f1f5f9' },
              ticks: { color: '#64748b' }
            }
          },
          plugins: {
            legend: {
              position: 'top',
              labels: { usePointStyle: true, color: '#4b5563' }
            },
            tooltip: {
              callbacks: {
                label: function (context) {
                  if (context.datasetIndex === 0) return 'Secuencia Principal (A + I = 1)';
                  const m = modulos[context.dataIndex];
                  if (!m) return '';
                  return [
                    `Módulo: ${m.nombre}`,
                    `Zona: ${m.zona.replace('_', ' ')}`,
                    `Distancia D: ${formatNumber(m.distancia_d, 4)}`,
                    `Inestabilidad (I): ${formatNumber(m.inestabilidad, 2)} (Ca=${m.ca}, Ce=${m.ce})`,
                    `Abstracción (A): ${formatNumber(m.abstraccion, 2)} (Na=${m.na}, Nc=${m.nc})`
                  ];
                }
              }
            }
          }
        }
      });
    }
  }

  // Render Modules List (Tab 2)
  function renderModules(modulos) {
    if (!modulesContainer) return;
    if (!modulos || !modulos.length) {
      modulesContainer.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-dim);">
          No se encontraron métricas de módulos en este reporte. Corré el análisis con el flag <code>--arquitectura</code> para ver las métricas de Robert C. Martin.
        </div>
      `;
      return;
    }

    modulesContainer.innerHTML = modulos.map(m => {
      let zoneBadge = 'badge-success';
      let zoneText = 'SECUENCIA PRINCIPAL';
      if (m.zona === 'ZONA_DOLOR') {
        zoneBadge = 'badge-critical';
        zoneText = 'ZONA DE DOLOR';
      } else if (m.zona === 'ZONA_INUTILIDAD') {
        zoneBadge = 'badge-warning';
        zoneText = 'ZONA DE INUTILIDAD';
      }

      const depsIn = (m.dependencias_in || []).map(d => `<span class="dep-pill dep-in">← ${d}</span>`).join('');
      const depsOut = (m.dependencias_out || []).map(d => `<span class="dep-pill dep-out">→ ${d}</span>`).join('');

      return `
        <article class="module-card">
          <div class="module-header">
            <div>
              <div class="module-name">${m.nombre}</div>
              <div class="module-path">${cleanPathName(m.ruta)}</div>
            </div>
            <span class="kpi-badge ${zoneBadge}">${zoneText}</span>
          </div>

          <div class="module-metrics-row">
            <div class="metric-mini-box">
              <span class="metric-mini-label">Ca</span>
              <span class="metric-mini-value">${m.ca}</span>
            </div>
            <div class="metric-mini-box">
              <span class="metric-mini-label">Ce</span>
              <span class="metric-mini-value">${m.ce}</span>
            </div>
            <div class="metric-mini-box">
              <span class="metric-mini-label">I</span>
              <span class="metric-mini-value">${formatNumber(m.inestabilidad, 2)}</span>
            </div>
            <div class="metric-mini-box">
              <span class="metric-mini-label">A</span>
              <span class="metric-mini-value">${formatNumber(m.abstraccion, 2)}</span>
            </div>
          </div>

          <div style="display: flex; justify-content: space-between; font-size: 0.82rem; font-family: var(--font-mono); color: var(--text-muted);">
            <span>Distancia D: <strong style="color: var(--text-main);">${formatNumber(m.distancia_d, 3)}</strong></span>
            <span>Archivos: <strong style="color: var(--text-main);">${m.archivos}</strong></span>
          </div>

          <div class="module-deps-section">
            <div style="font-size: 0.72rem; text-transform: uppercase; color: var(--text-dim); margin-bottom: 2px;">
              Dependencias Entrantes (${(m.dependencias_in || []).length})
            </div>
            <div class="deps-pills">
              ${depsIn || '<span style="font-size: 0.75rem; color: var(--text-dim);">Ninguna</span>'}
            </div>
          </div>

          <div class="module-deps-section">
            <div style="font-size: 0.72rem; text-transform: uppercase; color: var(--text-dim); margin-bottom: 2px;">
              Dependencias Salientes (${(m.dependencias_out || []).length})
            </div>
            <div class="deps-pills">
              ${depsOut || '<span style="font-size: 0.75rem; color: var(--text-dim);">Ninguna</span>'}
            </div>
          </div>
        </article>
      `;
    }).join('');
  }

  // Render Files Table (Tab 3)
  function renderFilesTable() {
    if (!filesTbody || !currentReport) return;
    const archivos = currentReport.archivos || [];

    // Filter
    let filtered = archivos.filter(f => {
      // Status filter
      if (filesFilter !== 'all' && f.estado_mi !== filesFilter) return false;
      // Search filter
      if (filesSearchTerm) {
        const query = filesSearchTerm.toLowerCase();
        const path = (f.ruta || '').toLowerCase();
        const lang = (f.lenguaje || '').toLowerCase();
        if (!path.includes(query) && !lang.includes(query)) return false;
      }
      return true;
    });

    // Sort
    filtered.sort((a, b) => {
      let valA = a[filesSortCol];
      let valB = b[filesSortCol];
      if (typeof valA === 'string') {
        valA = valA.toLowerCase();
        valB = (valB || '').toLowerCase();
        return filesSortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      valA = Number(valA) || 0;
      valB = Number(valB) || 0;
      return filesSortAsc ? valA - valB : valB - valA;
    });

    if (filtered.length === 0) {
      filesTbody.innerHTML = `
        <tr>
          <td colspan="12" style="text-align: center; padding: 32px; color: var(--text-dim);">
            No se encontraron archivos que coincidan con la búsqueda.
          </td>
        </tr>
      `;
      return;
    }

    filesTbody.innerHTML = filtered.map((f, idx) => {
      let badgeClass = 'badge-success';
      if (f.estado_mi === 'CRITICO') badgeClass = 'badge-critical';
      else if (f.estado_mi === 'REGULAR') badgeClass = 'badge-warning';

      // MI color bar
      const miVal = Math.max(0, Math.min(100, f.mi || 0));
      let miColor = '#00a650';
      if (f.estado_mi === 'CRITICO') miColor = '#f04438';
      else if (f.estado_mi === 'REGULAR') miColor = '#f59e0b';

      const fileName = getBaseFileName(f.ruta);
      const dirPath = cleanPathName(f.ruta).replace(fileName, '');

      return `
        <tr data-file-idx="${idx}" style="cursor: pointer;" title="Haz clic para ver el desglose matemático detallado">
          <td class="file-cell">
            <strong>${fileName}</strong><br>
            <span>${dirPath}</span>
          </td>
          <td><span class="brand-badge" style="font-size: 0.7rem; background: var(--mp-blue-light); color: var(--mp-blue); border-color: var(--mp-blue-subtle);">${(f.lenguaje || 'gen').toUpperCase()}</span></td>
          <td class="numeric-cell">${formatNumber(f.loc, 0)}</td>
          <td class="numeric-cell">${f.complejidad_ciclomatica || 0}</td>
          <td>
            <div class="mi-bar-wrapper">
              <span style="font-family: var(--font-mono); font-weight: 700; width: 32px; text-align: right;">${formatNumber(f.mi, 1)}</span>
              <div class="mi-bar-track">
                <div class="mi-bar-fill" style="width: ${miVal}%; background: ${miColor};"></div>
              </div>
            </div>
          </td>
          <td><span class="kpi-badge ${badgeClass}" style="font-size: 0.7rem;">${f.estado_mi}</span></td>
          <td class="numeric-cell" style="font-weight: 700; color: var(--text-main);">${formatNumber(f.deuda_horas, 1)}</td>
          <td class="numeric-cell">${formatCurrency(f.costo_reparacion_usd)}</td>
          <td class="numeric-cell">${formatCurrency(f.interes_anual_usd)}</td>
          <td class="numeric-cell">${formatNumber(f.payback_anios, 2)} a</td>
          <td class="numeric-cell" style="color: ${f.roi_4_anios_porc >= 0 ? 'var(--color-success)' : 'var(--color-critical)'};">
            ${formatNumber(f.roi_4_anios_porc, 1)}%
          </td>
          <td class="numeric-cell">${formatNumber(f.factor_friccion, 1)}x</td>
        </tr>
      `;
    }).join('');

    // Attach click handlers to rows for modal details
    const rows = filesTbody.querySelectorAll('tr[data-file-idx]');
    rows.forEach(r => {
      r.addEventListener('click', () => {
        const fileData = filtered[parseInt(r.getAttribute('data-file-idx'), 10)];
        if (fileData) openFileModal(fileData);
      });
    });
  }

  // File Detail Drilldown Modal
  function openFileModal(f) {
    modalFileTitle.textContent = cleanPathName(f.ruta);
    let badgeClass = 'badge-success';
    if (f.estado_mi === 'CRITICO') badgeClass = 'badge-critical';
    else if (f.estado_mi === 'REGULAR') badgeClass = 'badge-warning';

    modalFileBadge.className = `kpi-badge ${badgeClass}`;
    modalFileBadge.textContent = `${f.estado_mi} (MI: ${formatNumber(f.mi, 1)})`;

    modalBodyContent.innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px;">
        <div class="formula-box">
          <div class="formula-box-title">Deuda en Horas</div>
          <div style="font-size: 1.4rem; font-weight: 800; font-family: var(--font-mono); color: var(--color-critical);">${formatNumber(f.deuda_horas, 1)} h</div>
          <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">Horas para llevar a MI de referencia</div>
        </div>
        <div class="formula-box">
          <div class="formula-box-title">Costo de Reparación</div>
          <div style="font-size: 1.4rem; font-weight: 800; font-family: var(--font-mono); color: var(--color-warning);">${formatCurrency(f.costo_reparacion_usd)}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">Inversión directa estimada</div>
        </div>
        <div class="formula-box">
          <div class="formula-box-title">Interés Anual</div>
          <div style="font-size: 1.4rem; font-weight: 800; font-family: var(--font-mono); color: var(--accent-purple);">${formatCurrency(f.interes_anual_usd)}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">Fricción anual recurrente</div>
        </div>
      </div>

      <h4 style="font-size: 0.9rem; font-weight: 700; color: var(--text-main); margin-bottom: 10px;">Desglose de Parámetros y Fórmulas</h4>
      <div class="formula-grid">
        <div class="formula-box">
          <div class="formula-box-title">Maintainability Index (MI)</div>
          <div class="formula-code">MI = 171 - 5.2*ln(V) - 0.23*CC - 16.2*ln(LOC)</div>
          <p style="font-size: 0.78rem; color: var(--text-dim);">
            LOC: <strong>${f.loc}</strong> | Complejidad Ciclomática (CC): <strong>${f.complejidad_ciclomatica || 0}</strong>
          </p>
        </div>

        <div class="formula-box">
          <div class="formula-box-title">Factor de Fricción F(MI)</div>
          <div class="formula-code">F(MI) = 1.0 + (75 - MI)/15  [elástico]</div>
          <p style="font-size: 0.78rem; color: var(--text-dim);">
            Factor Fricción: <strong>${formatNumber(f.factor_friccion, 2)}x</strong> | Delta T: <strong>${formatNumber(f.delta_t_horas, 2)}h</strong>
          </p>
        </div>

        <div class="formula-box">
          <div class="formula-box-title">Tiempos de Desarrollo</div>
          <div class="formula-code">T_real = T_clean * F(MI) = ${formatNumber(f.t_clean_horas, 1)}h * ${formatNumber(f.factor_friccion, 1)} = ${formatNumber(f.t_real_horas, 1)}h</div>
          <p style="font-size: 0.78rem; color: var(--text-dim);">
            ΔT (Sobrecosto por tarea): <strong>+${formatNumber(f.delta_t_horas, 2)} horas</strong>
          </p>
        </div>

        <div class="formula-box">
          <div class="formula-box-title">Retorno de Inversión (ROI) & Payback</div>
          <div class="formula-code">Payback = Costo / Interés = ${formatNumber(f.payback_anios, 2)} años</div>
          <p style="font-size: 0.78rem; color: var(--text-dim);">
            ROI a 4 años: <strong style="color: ${f.roi_4_anios_porc >= 0 ? 'var(--color-success)' : 'var(--color-critical)'};">${formatNumber(f.roi_4_anios_porc, 1)}%</strong>
          </p>
        </div>
      </div>
    `;

    fileModal.classList.add('open');
  }

  // Render SQALE Violations Table (Tab 4)
  function renderViolationsTable(violaciones) {
    if (!violationsTbody) return;
    if (!violaciones || !violaciones.length) {
      violationsTbody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; padding: 32px; color: var(--text-dim);">
            No se detectaron violaciones en el análisis SQALE.
          </td>
        </tr>
      `;
      return;
    }

    const filtered = violationsFilter === 'all'
      ? violaciones
      : violaciones.filter(v => v.regla === violationsFilter);

    violationsTbody.innerHTML = filtered.map(v => {
      let ruleBadge = 'badge-purple';
      if (v.regla === 'ZONA_DOLOR') ruleBadge = 'badge-critical';
      else if (v.regla === 'FUNCION_LARGA') ruleBadge = 'badge-warning';

      const remedHours = ((v.remediacion_minutos || 0) / 60).toFixed(1);

      return `
        <tr>
          <td><span class="kpi-badge ${ruleBadge}" style="font-size: 0.7rem;">${v.regla}</span></td>
          <td><span style="color: var(--text-muted); font-size: 0.8rem;">${v.categoria_sqale || 'Mantenibilidad'}</span></td>
          <td class="file-cell"><strong>${cleanPathName(v.archivo)}</strong></td>
          <td style="color: var(--text-main); font-size: 0.84rem;">${v.detalle}</td>
          <td class="numeric-cell" style="font-family: var(--font-mono); color: var(--color-warning); font-weight: 700;">
            ${v.remediacion_minutos} min (${remedHours}h)
          </td>
        </tr>
      `;
    }).join('');
  }

  // CSV Export
  function exportFilesToCsv() {
    if (!currentReport || !currentReport.archivos) return;
    const headers = [
      'ruta', 'lenguaje', 'loc', 'complejidad_ciclomatica', 'mi', 'estado_mi',
      'deuda_horas', 'costo_reparacion_usd', 'interes_anual_usd', 'payback_anios',
      'roi_4_anios_porc', 'factor_friccion', 'delta_t_horas'
    ];

    const rows = currentReport.archivos.map(f => [
      `"${cleanPathName(f.ruta)}"`,
      f.lenguaje || '',
      f.loc || 0,
      f.complejidad_ciclomatica || 0,
      f.mi || 0,
      f.estado_mi || '',
      f.deuda_horas || 0,
      f.costo_reparacion_usd || 0,
      f.interes_anual_usd || 0,
      f.payback_anios || 0,
      f.roi_4_anios_porc || 0,
      f.factor_friccion || 0,
      f.delta_t_horas || 0
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `techdebt_${getProjectName(currentReport.repo_path)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // Event Listeners Setup
  function setupEventListeners() {
    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const tabId = btn.getAttribute('data-tab');
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        const target = document.getElementById(tabId);
        if (target) target.classList.add('active');

        // Resize charts when switching tabs so they render properly
        if (tabId === 'tab-overview' && chartTopDeuda) {
          chartTopDeuda.resize();
          chartHealthDoughnut.resize();
        } else if (tabId === 'tab-architecture' && chartMartinScatter) {
          chartMartinScatter.resize();
        }
      });
    });

    // File Input Upload
    btnUploadFile.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) handleJsonFile(file);
    });

    // Demo Data Button
    btnLoadDemo.addEventListener('click', () => {
      if (window.__DEFAULT_REPORT_DATA__) {
        loadReport(window.__DEFAULT_REPORT_DATA__);
      } else {
        alert('Datos de demo no encontrados en assets/demo_data.js');
      }
    });

    // Drag and Drop
    ['dragenter', 'dragover'].forEach(eventName => {
      window.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzoneBanner.classList.add('drag-over');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      window.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzoneBanner.classList.remove('drag-over');
      }, false);
    });

    window.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const file = dt.files[0];
      if (file) handleJsonFile(file);
    });

    // Search & Filter
    if (filesSearch) {
      filesSearch.addEventListener('input', (e) => {
        filesSearchTerm = e.target.value;
        renderFilesTable();
      });
    }

    const filterBtns = document.querySelectorAll('.filter-btn[data-filter]');
    filterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        filesFilter = btn.getAttribute('data-filter');
        renderFilesTable();
      });
    });

    // Table sorting
    const tableHeaders = document.querySelectorAll('#files-table th[data-sort]');
    tableHeaders.forEach(th => {
      th.addEventListener('click', () => {
        const col = th.getAttribute('data-sort');
        if (filesSortCol === col) {
          filesSortAsc = !filesSortAsc;
        } else {
          filesSortCol = col;
          filesSortAsc = false;
        }
        tableHeaders.forEach(h => h.classList.remove('sorted-asc', 'sorted-desc'));
        th.classList.add(filesSortAsc ? 'sorted-asc' : 'sorted-desc');
        renderFilesTable();
      });
    });

    // Violations Filter Buttons
    const vFilterBtns = document.querySelectorAll('.filter-btn[data-vfilter]');
    vFilterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        vFilterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        violationsFilter = btn.getAttribute('data-vfilter');
        if (currentReport && currentReport.sqale_report) {
          renderViolationsTable(currentReport.sqale_report.violaciones || []);
        }
      });
    });

    // Export CSV Button
    if (btnExportCsv) {
      btnExportCsv.addEventListener('click', exportFilesToCsv);
    }

    // Modal close
    if (modalCloseBtn) {
      modalCloseBtn.addEventListener('click', () => fileModal.classList.remove('open'));
    }
    if (fileModal) {
      fileModal.addEventListener('click', (e) => {
        if (e.target === fileModal) fileModal.classList.remove('open');
      });
    }
  }

  // Handle uploaded JSON file
  function handleJsonFile(file) {
    if (!file.name.endsWith('.json')) {
      alert('Por favor selecciona un archivo con extensión .json');
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const parsed = JSON.parse(e.target.result);
        if (!parsed.archivos && !parsed.total_loc) {
          alert('El archivo no parece tener la estructura de un reporte de Tech-Debt-Tool.');
          return;
        }
        loadReport(parsed);
      } catch (err) {
        alert('Error al parsear el JSON: ' + err.message);
      }
    };
    reader.readAsText(file);
  }

  // Initialize
  document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    initData();
  });

})();

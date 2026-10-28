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

  // Plan & Sprint elements
  let currentSprintPlan = null;
  const inputDevsBe = document.getElementById('plan-devs-be');
  const inputDevsFe = document.getElementById('plan-devs-fe');
  const inputDevsFs = document.getElementById('plan-devs-fs');
  const selectSprintWeeks = document.getElementById('plan-sprint-weeks');
  const inputDedicationPct = document.getElementById('plan-dedication-pct');
  const selectSprintsCount = document.getElementById('plan-sprints-count');
  const selectStrategy = document.getElementById('plan-strategy');
  const selectSqalePriority = document.getElementById('plan-sqale-priority');
  const btnRecalculatePlan = document.getElementById('btn-recalculate-plan');
  const btnResetPlanDefaults = document.getElementById('btn-reset-plan-defaults');

  const valCapacityBeUsed = document.getElementById('val-capacity-be-used');
  const valCapacityBeTotal = document.getElementById('val-capacity-be-total');
  const fillCapacityBe = document.getElementById('fill-capacity-be');
  const badgeCapacityBe = document.getElementById('badge-capacity-be');
  const subCapacityBe = document.getElementById('sub-capacity-be');

  const valCapacityFeUsed = document.getElementById('val-capacity-fe-used');
  const valCapacityFeTotal = document.getElementById('val-capacity-fe-total');
  const fillCapacityFe = document.getElementById('fill-capacity-fe');
  const badgeCapacityFe = document.getElementById('badge-capacity-fe');
  const subCapacityFe = document.getElementById('sub-capacity-fe');

  const valCapacityFsUsed = document.getElementById('val-capacity-fs-used');
  const valCapacityFsTotal = document.getElementById('val-capacity-fs-total');
  const fillCapacityFs = document.getElementById('fill-capacity-fs');
  const badgeCapacityFs = document.getElementById('badge-capacity-fs');
  const subCapacityFs = document.getElementById('sub-capacity-fs');

  const valImpactHours = document.getElementById('val-impact-hours');
  const valImpactPct = document.getElementById('val-impact-pct');
  const valImpactSavings = document.getElementById('val-impact-savings');
  const badgePlanImpact = document.getElementById('badge-plan-impact');
  const subImpactSummary = document.getElementById('sub-impact-summary');

  const btnCopySgaPrompt = document.getElementById('btn-copy-sga-prompt');
  const btnDownloadPlanMd = document.getElementById('btn-download-plan-md');
  const btnDownloadPlanJson = document.getElementById('btn-download-plan-json');
  const planCopyFeedback = document.getElementById('plan-copy-feedback');
  const kanbanBoardContainer = document.getElementById('kanban-board-container');
  const forbiddenFilesBox = document.getElementById('forbidden-files-box');
  const forbiddenCountBadge = document.getElementById('forbidden-count-badge');
  const forbiddenTbody = document.getElementById('forbidden-tbody');
  const btnCopyChecklist = document.getElementById('btn-copy-checklist');

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
    generateSprintPlan(data);

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
    const countCritico = archivos.filter(f => (f.estado_mi || '').toUpperCase() === 'CRITICO').length;
    const countRegular = archivos.filter(f => {
      const e = (f.estado_mi || '').toUpperCase();
      return e === 'REGULAR' || e === 'APROBADO';
    }).length;
    const countBueno = archivos.filter(f => {
      const e = (f.estado_mi || '').toUpperCase();
      return e === 'BUENO' || e === 'EXCELENTE';
    }).length;

    // Update filter counts
    document.getElementById('count-all').textContent = archivos.length;
    document.getElementById('count-critico').textContent = countCritico;
    document.getElementById('count-regular').textContent = countRegular;
    document.getElementById('count-bueno').textContent = countBueno;

    const ctxHealth = document.getElementById('chart-health-doughnut');
    if (ctxHealth) {
      if (chartHealthDoughnut) chartHealthDoughnut.destroy();
      const isDinamico = (currentReport && currentReport.modelo_calculo === 'dinamico');
      const labelCritico = isDinamico ? 'Crítico (MI < 40)' : 'Crítico (MI < 20)';
      const labelRegular = isDinamico ? 'Regular / Aprobado (40 ≤ MI < 75)' : 'Regular / Aprobado (20 ≤ MI < 60)';
      const labelBueno = isDinamico ? 'Excelente (MI ≥ 75)' : 'Excelente (MI ≥ 60)';

      chartHealthDoughnut = new Chart(ctxHealth, {
        type: 'doughnut',
        data: {
          labels: [labelCritico, labelRegular, labelBueno],
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

      // Disperse points when modules share identical or near-identical coordinates
      function layoutScatterPoints(mods) {
        const threshold = 0.12; // wider grouping threshold to catch near-identical coords
        const groups = [];
        mods.forEach(m => {
          let placed = false;
          for (const g of groups) {
            const first = g[0];
            if (Math.hypot(m.inestabilidad - first.inestabilidad, m.abstraccion - first.abstraccion) < threshold) {
              g.push(m);
              placed = true;
              break;
            }
          }
          if (!placed) groups.push([m]);
        });

        const points = [];
        groups.forEach(g => {
          if (g.length === 1) {
            const m = g[0];
            points.push({
              x: m.inestabilidad,
              y: m.abstraccion,
              rawX: m.inestabilidad,
              rawY: m.abstraccion,
              module: m
            });
          } else {
            const centerX = g.reduce((s, m) => s + m.inestabilidad, 0) / g.length;
            const centerY = g.reduce((s, m) => s + m.abstraccion, 0) / g.length;
            // Scale radius with group size so larger clusters spread wider
            const radius = Math.min(0.12, 0.04 + g.length * 0.022);

            // Pick a start angle that avoids clipping chart boundaries
            let startAngle = -Math.PI / 2; // default: fan upward
            let angleSpan = 2 * Math.PI;   // full circle by default

            const nearLeft  = centerX <= 0.15;
            const nearRight = centerX >= 0.85;
            const nearBot   = centerY <= 0.15;
            const nearTop   = centerY >= 0.85;

            if (nearLeft && nearBot) {
              startAngle = 0;
              angleSpan = Math.PI * 0.55;
            } else if (nearRight && nearBot) {
              startAngle = Math.PI * 0.45;
              angleSpan = Math.PI * 0.55;
            } else if (nearRight && nearTop) {
              startAngle = Math.PI;
              angleSpan = Math.PI * 0.55;
            } else if (nearLeft && nearTop) {
              startAngle = Math.PI * 1.45;
              angleSpan = Math.PI * 0.55;
            } else if (nearLeft) {
              startAngle = -Math.PI * 0.4;
              angleSpan = Math.PI * 0.8;
            } else if (nearRight) {
              startAngle = Math.PI * 0.6;
              angleSpan = Math.PI * 0.8;
            } else if (nearBot) {
              startAngle = 0;
              angleSpan = Math.PI;
            } else if (nearTop) {
              startAngle = Math.PI;
              angleSpan = Math.PI;
            }

            g.forEach((m, idx) => {
              const step = g.length > 1 ? angleSpan / (g.length - 1) : 0;
              const angle = startAngle + idx * step;
              const offX = radius * Math.cos(angle);
              const offY = radius * Math.sin(angle);
              points.push({
                x: Math.max(0.01, Math.min(0.99, centerX + offX)),
                y: Math.max(0.01, Math.min(0.99, centerY + offY)),
                rawX: m.inestabilidad,
                rawY: m.abstraccion,
                module: m
              });
            });
          }
        });
        return points;
      }

      const allLaidOutPoints = layoutScatterPoints(modulos);

      // Separate points into datasets by zone
      const ptsMainSequence = allLaidOutPoints.filter(p => p.module.zona === 'SECUENCIA_PRINCIPAL');
      const ptsPainZone = allLaidOutPoints.filter(p => p.module.zona === 'ZONA_DOLOR');
      const ptsUselessZone = allLaidOutPoints.filter(p => p.module.zona === 'ZONA_INUTILIDAD');

      const datasets = [
        {
          type: 'line',
          label: 'Secuencia Principal (A + I = 1)',
          data: mainSequenceLine,
          borderColor: '#10b981',
          borderWidth: 2.5,
          borderDash: [6, 6],
          pointRadius: 0,
          fill: false,
          order: 99
        },
        {
          type: 'scatter',
          label: `Equilibrado (${ptsMainSequence.length})`,
          data: ptsMainSequence.map(p => ({ x: p.x, y: p.y, rawPoint: p })),
          backgroundColor: '#00a650',
          borderColor: '#ffffff',
          borderWidth: 2.5,
          pointRadius: 10,
          pointHoverRadius: 14,
          order: 1
        },
        {
          type: 'scatter',
          label: `Zona de Dolor (${ptsPainZone.length})`,
          data: ptsPainZone.map(p => ({ x: p.x, y: p.y, rawPoint: p })),
          backgroundColor: '#f04438',
          borderColor: '#ffffff',
          borderWidth: 2.5,
          pointRadius: 10,
          pointHoverRadius: 14,
          order: 2
        }
      ];

      if (ptsUselessZone.length > 0) {
        datasets.push({
          type: 'scatter',
          label: `Zona de Inutilidad (${ptsUselessZone.length})`,
          data: ptsUselessZone.map(p => ({ x: p.x, y: p.y, rawPoint: p })),
          backgroundColor: '#f59e0b',
          borderColor: '#ffffff',
          borderWidth: 2.5,
          pointRadius: 10,
          pointHoverRadius: 14,
          order: 3
        });
      }

      // Custom Plugins for Zone Backgrounds and Module Labels
      const martinZonesPlugin = {
        id: 'martinZones',
        beforeDraw(chart) {
          const { ctx, chartArea, scales } = chart;
          if (!chartArea || !scales.x || !scales.y) return;
          const { x, y } = scales;
          ctx.save();

          // 1. Zona de Dolor (bottom-left triangle: (0,0) - (0.5,0) - (0,0.5))
          const pOrigin = { x: x.getPixelForValue(0), y: y.getPixelForValue(0) };
          const pPainX = { x: x.getPixelForValue(0.5), y: y.getPixelForValue(0) };
          const pPainY = { x: x.getPixelForValue(0), y: y.getPixelForValue(0.5) };

          ctx.fillStyle = 'rgba(240, 68, 56, 0.08)';
          ctx.beginPath();
          ctx.moveTo(pOrigin.x, pOrigin.y);
          ctx.lineTo(pPainX.x, pPainX.y);
          ctx.lineTo(pPainY.x, pPainY.y);
          ctx.closePath();
          ctx.fill();

          ctx.font = '700 11px Inter, system-ui, sans-serif';
          ctx.fillStyle = 'rgba(220, 38, 38, 0.7)';
          ctx.textAlign = 'left';
          ctx.textBaseline = 'bottom';
          ctx.fillText('🔴 Zona de Dolor (Rígido / Estable)', pOrigin.x + 8, pOrigin.y - 8);

          // 2. Zona de Inutilidad (top-right triangle: (1,1) - (0.5,1) - (1,0.5))
          const pTopRight = { x: x.getPixelForValue(1), y: y.getPixelForValue(1) };
          const pInutilX = { x: x.getPixelForValue(0.5), y: y.getPixelForValue(1) };
          const pInutilY = { x: x.getPixelForValue(1), y: y.getPixelForValue(0.5) };

          ctx.fillStyle = 'rgba(245, 158, 11, 0.08)';
          ctx.beginPath();
          ctx.moveTo(pTopRight.x, pTopRight.y);
          ctx.lineTo(pInutilX.x, pInutilX.y);
          ctx.lineTo(pInutilY.x, pInutilY.y);
          ctx.closePath();
          ctx.fill();

          ctx.font = '700 11px Inter, system-ui, sans-serif';
          ctx.fillStyle = 'rgba(217, 119, 6, 0.7)';
          ctx.textAlign = 'right';
          ctx.textBaseline = 'top';
          ctx.fillText('🟡 Zona de Inutilidad (Volátil / Abstracto)', pTopRight.x - 8, pTopRight.y + 8);

          // 3. Secuencia Principal diagonal label
          const pMidLine = { x: x.getPixelForValue(0.5), y: y.getPixelForValue(0.5) };
          ctx.font = '600 11px Inter, system-ui, sans-serif';
          ctx.fillStyle = 'rgba(16, 185, 129, 0.85)';
          ctx.textAlign = 'left';
          ctx.textBaseline = 'bottom';
          ctx.fillText('Secuencia Principal (A + I = 1)', pMidLine.x + 12, pMidLine.y - 8);

          ctx.restore();
        }
      };

      const martinLabelsPlugin = {
        id: 'martinLabels',
        afterDatasetsDraw(chart) {
          const { ctx, chartArea } = chart;
          if (!chartArea) return;
          ctx.save();
          ctx.font = '600 11px "JetBrains Mono", Menlo, Consolas, monospace';

          // Collect all label rects first, then resolve collisions
          const labelRects = [];

          function tryPlace(px, py, badgeW, badgeH, preferRight) {
            const margin = 13;
            const candidates = preferRight
              ? [
                  [px + margin, py - badgeH / 2],
                  [px + margin, py - badgeH - 4],
                  [px + margin, py + 4],
                  [px - badgeW - margin, py - badgeH / 2],
                  [px - badgeW - margin, py - badgeH - 4],
                  [px - badgeW - margin, py + 4],
                  [px - badgeW / 2, py + margin],
                  [px - badgeW / 2, py - badgeH - margin]
                ]
              : [
                  [px - badgeW - margin, py - badgeH / 2],
                  [px - badgeW - margin, py - badgeH - 4],
                  [px - badgeW - margin, py + 4],
                  [px + margin, py - badgeH / 2],
                  [px + margin, py - badgeH - 4],
                  [px + margin, py + 4],
                  [px - badgeW / 2, py + margin],
                  [px - badgeW / 2, py - badgeH - margin]
                ];

            const pad = 2;
            for (const [cx, cy] of candidates) {
              // Clamp inside chart area
              const bx = Math.max(chartArea.left + 2, Math.min(cx, chartArea.right - badgeW - 2));
              const by = Math.max(chartArea.top + 2, Math.min(cy, chartArea.bottom - badgeH - 2));
              // Check overlap with already placed labels
              const overlaps = labelRects.some(r =>
                bx < r.x + r.w + pad && bx + badgeW + pad > r.x &&
                by < r.y + r.h + pad && by + badgeH + pad > r.y
              );
              if (!overlaps) return { x: bx, y: by };
            }
            // Fallback: take the first candidate clamped (may overlap, better than hiding)
            const [fx, fy] = candidates[0];
            return {
              x: Math.max(chartArea.left + 2, Math.min(fx, chartArea.right - badgeW - 2)),
              y: Math.max(chartArea.top + 2, Math.min(fy, chartArea.bottom - badgeH - 2))
            };
          }

          chart.data.datasets.forEach((ds, dsIndex) => {
            if (ds.type !== 'scatter') return;
            const meta = chart.getDatasetMeta(dsIndex);
            if (!meta || meta.hidden) return;

            meta.data.forEach((element, index) => {
              const item = ds.data[index];
              const m = item && item.rawPoint ? item.rawPoint.module : null;
              if (!m) return;

              const px = element.x;
              const py = element.y;
              const text = m.nombre;
              const textWidth = ctx.measureText(text).width;
              const padX = 6;
              const badgeW = textWidth + padX * 2;
              const badgeH = 18;

              // Prefer placing label on the side with more space
              const preferRight = (px - chartArea.left) < (chartArea.right - px);
              const pos = tryPlace(px, py, badgeW, badgeH, preferRight);
              labelRects.push({ x: pos.x, y: pos.y, w: badgeW, h: badgeH });

              const zoneColor = m.zona === 'ZONA_DOLOR' ? 'rgba(239, 68, 68, 0.5)' :
                                m.zona === 'ZONA_INUTILIDAD' ? 'rgba(245, 158, 11, 0.5)' : 'rgba(16, 185, 129, 0.5)';

              // Connector line from point to badge
              const connX = pos.x < px ? pos.x + badgeW : pos.x;
              const connY = pos.y + badgeH / 2;
              ctx.save();
              ctx.strokeStyle = zoneColor;
              ctx.lineWidth = 1;
              ctx.setLineDash([3, 3]);
              ctx.beginPath();
              ctx.moveTo(px, py);
              ctx.lineTo(connX, connY);
              ctx.stroke();
              ctx.setLineDash([]);
              ctx.restore();

              // Pill background
              ctx.shadowColor = 'rgba(0, 0, 0, 0.10)';
              ctx.shadowBlur = 5;
              ctx.shadowOffsetY = 1;
              ctx.fillStyle = 'rgba(255, 255, 255, 0.96)';
              ctx.strokeStyle = zoneColor;
              ctx.lineWidth = 1.2;

              ctx.beginPath();
              if (ctx.roundRect) {
                ctx.roundRect(pos.x, pos.y, badgeW, badgeH, 4);
              } else {
                ctx.rect(pos.x, pos.y, badgeW, badgeH);
              }
              ctx.fill();
              ctx.stroke();

              // Pill text
              ctx.shadowColor = 'transparent';
              ctx.fillStyle = m.zona === 'ZONA_DOLOR' ? '#b91c1c' :
                              m.zona === 'ZONA_INUTILIDAD' ? '#b45309' : '#047857';
              ctx.textAlign = 'left';
              ctx.textBaseline = 'middle';
              ctx.fillText(text, pos.x + padX, pos.y + badgeH / 2);
            });
          });

          ctx.restore();
        }
      };

      chartMartinScatter = new Chart(ctxMartin, {
        type: 'scatter',
        data: { datasets: datasets },
        plugins: [martinZonesPlugin, martinLabelsPlugin],
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              min: -0.06,
              max: 1.06,
              title: {
                display: true,
                text: 'Inestabilidad (I) →  [0 = Estable, 1 = Inestable]',
                color: '#1f2937',
                font: { weight: 700, size: 12 }
              },
              grid: {
                color: function (context) {
                  if (context.tick && (context.tick.value === 0 || context.tick.value === 1)) {
                    return 'rgba(100, 116, 139, 0.35)';
                  }
                  return '#f1f5f9';
                }
              },
              ticks: {
                stepSize: 0.2,
                callback: function (val) {
                  if (val >= 0 && val <= 1) return val.toFixed(1);
                  return '';
                },
                color: '#4b5563',
                font: { family: "'JetBrains Mono', monospace", size: 11, weight: 600 }
              }
            },
            y: {
              min: -0.06,
              max: 1.06,
              title: {
                display: true,
                text: 'Abstracción (A) →  [0 = Concreto, 1 = Abstracto]',
                color: '#1f2937',
                font: { weight: 700, size: 12 }
              },
              grid: {
                color: function (context) {
                  if (context.tick && (context.tick.value === 0 || context.tick.value === 1)) {
                    return 'rgba(100, 116, 139, 0.35)';
                  }
                  return '#f1f5f9';
                }
              },
              ticks: {
                stepSize: 0.2,
                callback: function (val) {
                  if (val >= 0 && val <= 1) return val.toFixed(1);
                  return '';
                },
                color: '#4b5563',
                font: { family: "'JetBrains Mono', monospace", size: 11, weight: 600 }
              }
            }
          },
          plugins: {
            legend: {
              position: 'top',
              labels: { usePointStyle: true, color: '#374151', padding: 14, font: { weight: 600 } }
            },
            tooltip: {
              callbacks: {
                label: function (context) {
                  if (context.dataset.type === 'line') return 'Secuencia Principal (A + I = 1)';
                  const item = context.raw;
                  const m = item && item.rawPoint ? item.rawPoint.module : null;
                  if (!m) return '';
                  const zoneName = m.zona === 'ZONA_DOLOR' ? 'Zona de Dolor' :
                                   m.zona === 'ZONA_INUTILIDAD' ? 'Zona de Inutilidad' : 'Secuencia Principal';
                  return [
                    `Módulo: ${m.nombre}`,
                    `Zona: ${zoneName}`,
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
      if (filesFilter !== 'all') {
        const est = (f.estado_mi || '').toUpperCase();
        if (filesFilter === 'CRITICO' && est !== 'CRITICO') return false;
        if ((filesFilter === 'REGULAR' || filesFilter === 'APROBADO') && (est !== 'REGULAR' && est !== 'APROBADO')) return false;
        if ((filesFilter === 'BUENO' || filesFilter === 'EXCELENTE') && (est !== 'BUENO' && est !== 'EXCELENTE')) return false;
      }
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
      const est = (f.estado_mi || '').toUpperCase();
      let badgeClass = 'badge-success';
      if (est === 'CRITICO') badgeClass = 'badge-critical';
      else if (est === 'REGULAR' || est === 'APROBADO') badgeClass = 'badge-warning';

      // MI color bar
      const miVal = Math.max(0, Math.min(100, f.mi || 0));
      let miColor = '#00a650';
      if (est === 'CRITICO') miColor = '#f04438';
      else if (est === 'REGULAR' || est === 'APROBADO') miColor = '#f59e0b';

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
    const est = (f.estado_mi || '').toUpperCase();
    let badgeClass = 'badge-success';
    if (est === 'CRITICO') badgeClass = 'badge-critical';
    else if (est === 'REGULAR' || est === 'APROBADO') badgeClass = 'badge-warning';

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
          <div class="formula-code">F(MI) = 1 + ((75 - MI) / 75)² × 3.0</div>
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

  // =========================================================================
  // Sprint Planner & Technical Debt Action Plan Engine
  // =========================================================================

  function resetPlanFormDefaults() {
    if (inputDevsBe) inputDevsBe.value = 4;
    if (inputDevsFe) inputDevsFe.value = 3;
    if (inputDevsFs) inputDevsFs.value = 0;
    if (selectSprintWeeks) selectSprintWeeks.value = 4;
    if (inputDedicationPct) inputDedicationPct.value = 100;
    if (selectSprintsCount) selectSprintsCount.value = 2;
    if (selectStrategy) selectStrategy.value = 'hybrid_zona_cc_roi';
    if (selectSqalePriority) selectSqalePriority.value = 'none';
    if (currentReport) generateSprintPlan(currentReport);
  }

  function getModuleInfoForFile(filePath, modulesList) {
    if (!filePath || !modulesList || modulesList.length === 0) {
      return { nombre: 'desconocido', zona: 'SECUENCIA_PRINCIPAL', distancia_d: 0.0 };
    }
    const clean = cleanPathName(filePath).toLowerCase();
    for (const m of modulesList) {
      const modName = (m.nombre || '').toLowerCase();
      const modRuta = cleanPathName(m.ruta || '').toLowerCase();
      if ((modRuta && (clean.startsWith(modRuta + '/') || clean.includes('/' + modRuta + '/'))) ||
          (modName && (clean.startsWith(modName + '/') || clean.includes('/' + modName + '/')))) {
        return m;
      }
    }
    return { nombre: 'general', zona: 'SECUENCIA_PRINCIPAL', distancia_d: 0.0 };
  }

  function getFileViolations(filePath, violationsList, modInfo) {
    if (!filePath || !violationsList) return [];
    const clean = cleanPathName(filePath).toLowerCase();
    const modRuta = cleanPathName(modInfo ? modInfo.ruta : '').toLowerCase();
    const modNombre = (modInfo ? modInfo.nombre : '').toLowerCase();

    return violationsList.filter(v => {
      const vPath = cleanPathName(v.archivo || '').toLowerCase();
      if (!vPath) return false;
      // Direct file match
      if (clean === vPath || clean.endsWith('/' + vPath) || vPath.endsWith('/' + clean) || clean.endsWith(vPath)) {
        return true;
      }
      // Module level architectural violation match (ZONA_DOLOR, IMPORT_CIRCULAR, ZONA_INUTILIDAD)
      if (modRuta && (vPath === modRuta || vPath === modNombre)) {
        return true;
      }
      return false;
    });
  }

  function generateSmartRefactorAdvice(file, role, modInfo, violations) {
    const p = cleanPathName(file.ruta).toLowerCase();
    const cc = file.complejidad_ciclomatica || 0;

    if (p.includes('handler') || p.includes('controller') || p.includes('api_datasource')) {
      return 'Extraer lógica de negocio del handler hacia la capa de aplicación/dominio; desacoplar de transporte HTTP y tipar DTOs.';
    }
    if (p.includes('screen') || p.includes('widget') || p.includes('panel')) {
      return 'Descomponer pantalla monolítica en sub-widgets especializados; desacoplar manejo de estado mediante BLoC/Clean Architecture.';
    }
    if (p.includes('repo') || p.includes('datasource') || p.includes('postgres')) {
      return 'Simplificar consultas complejas; extraer constructores de consultas (query builders) y aislar manejo de errores SQL.';
    }
    if (p.includes('domain') || p.includes('entities') || p.includes('entity')) {
      return 'Inmutabilizar entidades de dominio; extraer validaciones a Value Objects y desacoplar de librerías externas.';
    }
    if (p.includes('app') || p.includes('usecase') || p.includes('service')) {
      return 'Descomponer casos de uso monolíticos; aplicar patrón Strategy para reducir ramificaciones y simplificar orquestación.';
    }
    if (p.includes('test')) {
      return 'Modularizar suite de tests; extraer fixtures compartidas y helpers de prueba para eliminar código duplicado.';
    }
    if (p.includes('config') || p.includes('wiring') || p.includes('main.')) {
      return 'Introducir interfaces para desacoplar setup de dependencias concretas; simplificar inicialización de componentes.';
    }
    if (cc > 40) {
      return `Reducción prioritaria de complejidad ciclomática extrema (CC=${cc}); extraer submétodos y simplificar branches condicionales.`;
    }
    return 'Rediseñar componentes críticos y elevar Maintainability Index (MI) hacia nivel óptimo (≥ 75).';
  }

  function generateDefinitionOfDone(file, role) {
    const isDart = role === 'FE' || (file.lenguaje || '').toLowerCase() === 'dart' || (file.ruta || '').endsWith('.dart');
    const isGo = role === 'BE' || (file.lenguaje || '').toLowerCase() === 'go' || (file.ruta || '').endsWith('.go');
    const targetCc = isDart ? '≤ 4' : '≤ 7';

    const dod = [
      `CC ${targetCc} (máx 3 niveles de if anidados)`,
      'Maintainability Index (MI) ≥ 60%',
      'TDR ≤ 6% y cero imports/código muerto',
    ];

    if (isDart) {
      dod.push('Pattern matching / sealed classes en manejo de estado');
      dod.push('DIT ≤ 2 (Dart) y CBO ≤ 6');
    } else if (isGo) {
      dod.push('Parseo seguro de nulos en BD (sql.Null* o tipos seguros)');
      dod.push('Contratos de interfaz aislados en puertos de dominio/app');
    }

    dod.push('Al menos 1 test unitario/contrato nuevo pasando');
    dod.push('Ownership respetado (solo archivos asignados)');

    return dod;
  }

  function evaluarArchivoProhibido(f) {
    const clean = cleanPathName(f.ruta || '').toLowerCase();
    const loc = f.loc || 0;
    const cc = f.complejidad_ciclomatica || 0;
    const mi = f.mi !== undefined ? f.mi : 100;
    const deuda = f.deuda_horas || 0;
    const roiAdj = f.roi_ajustado_porc !== undefined ? f.roi_ajustado_porc : 0;
    const payback = f.payback_anios !== undefined ? f.payback_anios : null;

    // 1. Catálogo conocido estricto de monolitos arquitecturales vetados
    const vetados = [
      'cursos_screen.dart',
      'teachers_screen.dart',
      'configuracion_screen.dart',
      'api_datasource.dart',
      'sga_design_system.dart',
      'academic_repo.go'
    ];
    for (const v of vetados) {
      if (clean.endsWith(v) || clean.includes('/' + v) || clean === v) {
        return {
          isForbidden: true,
          motivo: 'Vetado estrictamente por requerir rediseño completo de arquitectura'
        };
      }
    }

    // 2. Hiper-Monolito inabarcable
    if (loc >= 1000 && cc >= 150) {
      return {
        isForbidden: true,
        motivo: `Hiper-monolito inabarcable (LOC=${loc}, CC=${cc}); requiere rediseño arquitectónico completo`
      };
    }

    // 3. Monolito crítico desproporcionado
    if (deuda >= 300 && mi <= 10 && cc >= 80) {
      return {
        isForbidden: true,
        motivo: `Monolito crítico desproporcionado (Deuda=${formatNumber(deuda, 1)}h, CC=${cc}, MI=${mi}); excede capacidad de sprint`
      };
    }

    // 4. Pérdida severa de retorno
    if (deuda >= 250 && roiAdj <= -40 && (payback === null || payback >= 7)) {
      return {
        isForbidden: true,
        motivo: `Retorno inviable para sprint incremental (ROI=${roiAdj}%, Payback=${payback}a); requiere reescritura`
      };
    }

    return { isForbidden: false, motivo: null };
  }

  function generateSprintPlan(reportData) {
    if (!reportData || !reportData.archivos) return;

    const devsBe = Math.max(0, parseInt(inputDevsBe ? inputDevsBe.value : 4) || 0);
    const devsFe = Math.max(0, parseInt(inputDevsFe ? inputDevsFe.value : 3) || 0);
    const devsFs = Math.max(0, parseInt(inputDevsFs ? inputDevsFs.value : 0) || 0);
    const weeks = Math.max(1, parseInt(selectSprintWeeks ? selectSprintWeeks.value : 4) || 4);
    const dedication = Math.max(0.1, (parseFloat(inputDedicationPct ? inputDedicationPct.value : 100) || 100) / 100.0);
    const sprintCount = Math.max(1, parseInt(selectSprintsCount ? selectSprintsCount.value : 2) || 2);
    const strategy = selectStrategy ? selectStrategy.value : 'hybrid_zona_cc_roi';
    const sqalePriority = selectSqalePriority ? selectSqalePriority.value : 'none';

    const hoursPerDev = weeks * 40 * dedication;
    const capBe = devsBe * hoursPerDev;
    const capFe = devsFe * hoursPerDev;
    const capFs = devsFs * hoursPerDev;

    const sqale = reportData.sqale_report || {};
    const modulos = sqale.modulos || [];
    const violaciones = sqale.violaciones || [];

    // Filter candidate files needing attention
    const candidateFiles = reportData.archivos.filter(f => {
      const debt = f.deuda_horas || 0;
      const mi = f.mi !== undefined ? f.mi : 100;
      const cleanPath = cleanPathName(f.ruta);
      const modInfo = getModuleInfoForFile(cleanPath, modulos);
      const fileViolations = getFileViolations(cleanPath, violaciones, modInfo);

      if (sqalePriority === 'only_with_violations' && fileViolations.length === 0) {
        return false;
      }

      return debt > 0.5 || mi < 75 || f.estado_mi === 'CRITICO' || f.estado_mi === 'REGULAR' || fileViolations.length > 0;
    });

    // Partition files: Forbidden Monoliths (DO NOT TOUCH) vs Eligible Sprint Tasks
    const forbiddenFiles = [];
    const eligibleFiles = [];

    candidateFiles.forEach(f => {
      const check = evaluarArchivoProhibido(f);
      if (check.isForbidden) {
        const cleanPath = cleanPathName(f.ruta);
        const isGo = (f.lenguaje || '').toLowerCase() === 'go' || cleanPath.endsWith('.go');
        forbiddenFiles.push({
          file: f,
          filePath: cleanPath,
          role: isGo ? 'BE' : 'FE',
          loc: f.loc || 0,
          cc: f.complejidad_ciclomatica || 0,
          mi: Math.round((f.mi || 0) * 10) / 10,
          deudaHoras: Math.round((f.deuda_horas || 0) * 10) / 10,
          motivo: check.motivo
        });
      } else {
        eligibleFiles.push(f);
      }
    });

    // Enrich eligible files with role, module, zone and cards info
    const enrichedCards = eligibleFiles.map(f => {
      const cleanPath = cleanPathName(f.ruta);
      const isGo = (f.lenguaje || '').toLowerCase() === 'go' || cleanPath.endsWith('.go');
      const isDart = (f.lenguaje || '').toLowerCase() === 'dart' || cleanPath.endsWith('.dart');
      const role = isGo ? 'BE' : (isDart ? 'FE' : 'FS');
      const modInfo = getModuleInfoForFile(cleanPath, modulos);
      const isPainZone = (modInfo.distancia_d !== undefined && modInfo.distancia_d > 0.5) || modInfo.zona === 'ZONA_DOLOR';
      const fileViolations = getFileViolations(cleanPath, violaciones, modInfo);
      const sqaleCount = fileViolations.length;
      const sqaleRemMinutes = fileViolations.reduce((sum, v) => sum + (v.remediacion_minutos || 0), 0);
      const sqaleRemHours = Math.round((sqaleRemMinutes / 60.0) * 10) / 10;
      const sqaleArchCount = fileViolations.filter(v => v.regla === 'ZONA_DOLOR' || v.regla === 'IMPORT_CIRCULAR' || v.regla === 'ZONA_INUTILIDAD').length;
      const sqaleCodeCount = fileViolations.filter(v => v.regla === 'CC_ALTA' || v.regla === 'FUNCION_LARGA' || v.regla === 'ARCHIVO_LARGO').length;
      const roiAdj = f.roi_ajustado_porc !== undefined ? f.roi_ajustado_porc : 0;
      const cc = f.complejidad_ciclomatica || 0;
      const debtHours = Math.round((f.deuda_horas || 0) * 10) / 10;

      return {
        id: '', // assigned below
        file: f,
        filePath: cleanPath,
        baseName: getBaseFileName(cleanPath),
        role: role,
        moduleName: modInfo.nombre || 'general',
        isPainZone: isPainZone,
        zona: modInfo.zona || (isPainZone ? 'ZONA_DOLOR' : 'SECUENCIA_PRINCIPAL'),
        distanciaD: modInfo.distancia_d || 0,
        loc: f.loc || 0,
        cc: cc,
        mi: Math.round((f.mi || 0) * 10) / 10,
        deudaHoras: debtHours,
        costoUsd: f.costo_reparacion_usd || 0,
        interesUsd: f.interes_anual_usd || 0,
        roiAjustado: roiAdj,
        violations: fileViolations,
        sqaleCount: sqaleCount,
        sqaleRemediationMinutes: sqaleRemMinutes,
        sqaleRemediationHours: sqaleRemHours,
        sqaleArchCount: sqaleArchCount,
        sqaleCodeCount: sqaleCodeCount,
        refactorAdvice: generateSmartRefactorAdvice(f, role, modInfo, fileViolations),
        dod: generateDefinitionOfDone(f, role),
        currentSprint: 1 // assigned below
      };
    });

    // Sort according to chosen strategy & SQALE prioritization
    enrichedCards.sort((a, b) => {
      // 1. Violaciones SQALE primero (por cantidad descendente)
      if (strategy === 'sqale_violations_first' || sqalePriority === 'count') {
        if (b.sqaleCount !== a.sqaleCount) return b.sqaleCount - a.sqaleCount;
        if (b.sqaleRemediationMinutes !== a.sqaleRemediationMinutes) return b.sqaleRemediationMinutes - a.sqaleRemediationMinutes;
        if (b.cc !== a.cc) return b.cc - a.cc;
        return b.deudaHoras - a.deudaHoras;
      }

      // 2. Remediación SQALE primero (por tiempo de remediación acumulado)
      if (strategy === 'sqale_remediation_first' || sqalePriority === 'remediation') {
        if (b.sqaleRemediationMinutes !== a.sqaleRemediationMinutes) return b.sqaleRemediationMinutes - a.sqaleRemediationMinutes;
        if (b.sqaleCount !== a.sqaleCount) return b.sqaleCount - a.sqaleCount;
        if (b.deudaHoras !== a.deudaHoras) return b.deudaHoras - a.deudaHoras;
        return b.cc - a.cc;
      }

      // 3. Híbrida SQALE (Infracciones + Arquitectura + CC + ROI)
      if (strategy === 'sqale_hybrid') {
        const scoreA = (a.sqaleCount * 2500) + (a.sqaleRemediationMinutes * 30) + (a.sqaleArchCount * 15000) + (a.isPainZone ? 15000 : 0) + (a.roiAjustado > 0 ? 8000 : 0) + (a.cc * 20) + Math.min(a.deudaHoras, 200);
        const scoreB = (b.sqaleCount * 2500) + (b.sqaleRemediationMinutes * 30) + (b.sqaleArchCount * 15000) + (b.isPainZone ? 15000 : 0) + (b.roiAjustado > 0 ? 8000 : 0) + (b.cc * 20) + Math.min(b.deudaHoras, 200);
        return scoreB - scoreA;
      }

      // Modificadores si sqalePriority está configurado en otras estrategias
      if (sqalePriority === 'arch_first' && (b.sqaleArchCount !== a.sqaleArchCount)) {
        return b.sqaleArchCount - a.sqaleArchCount;
      }
      if (sqalePriority === 'code_first' && (b.sqaleCodeCount !== a.sqaleCodeCount)) {
        return b.sqaleCodeCount - a.sqaleCodeCount;
      }

      if (strategy === 'roi_first') {
        if (b.roiAjustado !== a.roiAjustado) return b.roiAjustado - a.roiAjustado;
        return b.cc - a.cc;
      } else if (strategy === 'cc_first') {
        if (b.cc !== a.cc) return b.cc - a.cc;
        return b.deudaHoras - a.deudaHoras;
      } else if (strategy === 'debt_hours_first') {
        if (b.deudaHoras !== a.deudaHoras) return b.deudaHoras - a.deudaHoras;
        return b.cc - a.cc;
      } else {
        // hybrid_zona_cc_roi (default)
        const scoreA = (a.isPainZone ? 20000 : 0) + (a.roiAjustado > 0 ? 10000 : 0) + (a.cc * 25) + Math.min(a.deudaHoras, 300);
        const scoreB = (b.isPainZone ? 20000 : 0) + (b.roiAjustado > 0 ? 10000 : 0) + (b.cc * 25) + Math.min(b.deudaHoras, 300);
        return scoreB - scoreA;
      }
    });

    // Assign IDs (BE-01, FE-01, etc.)
    let beCounter = 1;
    let feCounter = 1;
    let fsCounter = 1;
    enrichedCards.forEach(c => {
      if (c.role === 'BE') {
        c.id = `BE-${String(beCounter++).padStart(2, '0')}`;
      } else if (c.role === 'FE') {
        c.id = `FE-${String(feCounter++).padStart(2, '0')}`;
      } else {
        c.id = `FS-${String(fsCounter++).padStart(2, '0')}`;
      }
    });

    // Sprints Bin-Packing
    const sprints = [];
    for (let i = 1; i <= sprintCount; i++) {
      sprints.push({
        id: `sprint-${i}`,
        number: i,
        name: `Sprint ${i}`,
        cards: [],
        beHours: 0,
        feHours: 0,
        fsHours: 0
      });
    }

    const backlog = {
      id: 'backlog',
      number: 0,
      name: 'Backlog de Deuda Técnica',
      cards: [],
      beHours: 0,
      feHours: 0,
      fsHours: 0
    };

    // Distribute cards into sprints based on capacity
    enrichedCards.forEach(card => {
      let placed = false;
      for (const sprint of sprints) {
        const dHours = card.deudaHoras;
        if (card.role === 'BE') {
          // Check if BE capacity has room or FS pool can absorb
          const remBe = capBe - sprint.beHours;
          const remFs = capFs - sprint.fsHours;
          if (remBe >= dHours || (remBe + remFs >= dHours && capFs > 0)) {
            sprint.cards.push(card);
            card.currentSprint = sprint.number;
            const useBe = Math.min(remBe, dHours);
            const useFs = Math.max(0, dHours - useBe);
            sprint.beHours += useBe;
            sprint.fsHours += useFs;
            placed = true;
            break;
          }
        } else if (card.role === 'FE') {
          const remFe = capFe - sprint.feHours;
          const remFs = capFs - sprint.fsHours;
          if (remFe >= dHours || (remFe + remFs >= dHours && capFs > 0)) {
            sprint.cards.push(card);
            card.currentSprint = sprint.number;
            const useFe = Math.min(remFe, dHours);
            const useFs = Math.max(0, dHours - useFe);
            sprint.feHours += useFe;
            sprint.fsHours += useFs;
            placed = true;
            break;
          }
        } else {
          // Fullstack task
          const remFs = capFs - sprint.fsHours;
          if (remFs >= dHours) {
            sprint.cards.push(card);
            card.currentSprint = sprint.number;
            sprint.fsHours += dHours;
            placed = true;
            break;
          }
        }
      }

      if (!placed) {
        backlog.cards.push(card);
        card.currentSprint = 0;
        if (card.role === 'BE') backlog.beHours += card.deudaHoras;
        else if (card.role === 'FE') backlog.feHours += card.deudaHoras;
        else backlog.fsHours += card.deudaHoras;
      }
    });

    currentSprintPlan = {
      sprints: sprints,
      backlog: backlog,
      forbiddenCards: forbiddenFiles,
      capBe: capBe,
      capFe: capFe,
      capFs: capFs,
      hoursPerDev: hoursPerDev,
      weeks: weeks,
      dedication: dedication,
      devsBe: devsBe,
      devsFe: devsFe,
      devsFs: devsFs,
      totalRepoDebt: reportData.total_deuda_horas || 1,
      totalRepoInterest: reportData.total_interes_anual_usd || 0
    };

    updateCapacityMeters();
    renderKanbanBoard();
    renderForbiddenFiles(forbiddenFiles);
  }

  function renderForbiddenFiles(forbiddenList) {
    if (!forbiddenFilesBox || !forbiddenTbody) return;
    if (!forbiddenList || forbiddenList.length === 0) {
      forbiddenFilesBox.style.display = 'none';
      return;
    }

    forbiddenFilesBox.style.display = 'block';
    if (forbiddenCountBadge) {
      forbiddenCountBadge.textContent = `${forbiddenList.length} archivos vetados`;
    }

    forbiddenTbody.innerHTML = forbiddenList.map((c, idx) => `
      <tr>
        <td style="font-weight: 700; color: #991b1b;">${idx + 1}</td>
        <td class="file-cell" style="color: #991b1b;">${c.filePath}</td>
        <td><span class="card-role-badge ${c.role === 'BE' ? 'card-role-be' : 'card-role-fe'}">${c.role}</span></td>
        <td style="font-family: var(--font-mono);">${c.loc}</td>
        <td style="font-family: var(--font-mono); font-weight: 700; color: var(--color-critical);">${c.cc}</td>
        <td style="font-family: var(--font-mono);">${c.mi}</td>
        <td style="font-family: var(--font-mono); font-weight: 700; color: #b91c1c;">${c.deudaHoras}h</td>
        <td style="font-size: 0.78rem; color: #7f1d1d;"><strong>${c.motivo}</strong></td>
      </tr>
    `).join('');
  }

  function copyChecklistMarkdown() {
    const checklistMd = `### 📋 CHECKLIST PR / REVIEWS (Viernes)
Al abrir la PR, incluir tildado:

* [ ] CC ≤ 4 (Dart) / ≤ 7 (Go)
* [ ] Maintainability Index ≥ 60%
* [ ] TDR ≤ 6%
* [ ] Máx 3 niveles de if
* [ ] Pattern matching / sealed classes en estado
* [ ] DIT ≤ 2 (Dart) y CBO ≤ 6
* [ ] Parseo seguro de nulos en BD
* [ ] Cero imports/variables/código muerto
* [ ] Al menos 1 test unitario/contrato nuevo pasando
* [ ] Ownership respetado (solo archivos asignados)
`;
    navigator.clipboard.writeText(checklistMd).then(() => {
      alert('¡Checklist de PR copiado al portapapeles!');
    }).catch(err => {
      alert('Error al copiar checklist: ' + err);
    });
  }

  function updateCapacityMeters() {
    if (!currentSprintPlan) return;

    const sprint1 = currentSprintPlan.sprints[0] || { beHours: 0, feHours: 0, fsHours: 0, cards: [] };
    // Recalculate Sprint 1 actual totals based on its current cards
    let s1Be = 0;
    let s1Fe = 0;
    let s1Fs = 0;
    (sprint1.cards || []).forEach(c => {
      if (c.role === 'BE') s1Be += c.deudaHoras;
      else if (c.role === 'FE') s1Fe += c.deudaHoras;
      else s1Fs += c.deudaHoras;
    });

    const capBe = currentSprintPlan.capBe || 1;
    const capFe = currentSprintPlan.capFe || 1;
    const capFs = currentSprintPlan.capFs || 0;

    // Backend
    const pctBe = Math.round((s1Be / capBe) * 100);
    if (valCapacityBeUsed) valCapacityBeUsed.textContent = `${formatNumber(s1Be, 1)}h`;
    if (valCapacityBeTotal) valCapacityBeTotal.textContent = `/ ${formatNumber(capBe, 0)}h disp.`;
    if (fillCapacityBe) {
      fillCapacityBe.style.width = `${Math.min(100, pctBe)}%`;
      fillCapacityBe.style.background = pctBe > 105 ? 'var(--color-critical)' : (pctBe > 90 ? 'var(--color-warning)' : 'var(--color-success)');
    }
    if (badgeCapacityBe) {
      badgeCapacityBe.className = `kpi-badge ${pctBe > 105 ? 'badge-critical' : (pctBe > 90 ? 'badge-warning' : 'badge-success')}`;
      badgeCapacityBe.textContent = `${pctBe}% USADO`;
    }
    if (subCapacityBe) {
      subCapacityBe.textContent = `Sprint 1: ${currentSprintPlan.devsBe} devs × ${formatNumber(currentSprintPlan.hoursPerDev, 0)}h`;
    }

    // Frontend
    const pctFe = Math.round((s1Fe / capFe) * 100);
    if (valCapacityFeUsed) valCapacityFeUsed.textContent = `${formatNumber(s1Fe, 1)}h`;
    if (valCapacityFeTotal) valCapacityFeTotal.textContent = `/ ${formatNumber(capFe, 0)}h disp.`;
    if (fillCapacityFe) {
      fillCapacityFe.style.width = `${Math.min(100, pctFe)}%`;
      fillCapacityFe.style.background = pctFe > 105 ? 'var(--color-critical)' : (pctFe > 90 ? 'var(--color-warning)' : 'var(--color-success)');
    }
    if (badgeCapacityFe) {
      badgeCapacityFe.className = `kpi-badge ${pctFe > 105 ? 'badge-critical' : (pctFe > 90 ? 'badge-warning' : 'badge-success')}`;
      badgeCapacityFe.textContent = `${pctFe}% USADO`;
    }
    if (subCapacityFe) {
      subCapacityFe.textContent = `Sprint 1: ${currentSprintPlan.devsFe} devs × ${formatNumber(currentSprintPlan.hoursPerDev, 0)}h`;
    }

    // Fullstack Pool
    if (valCapacityFsUsed) valCapacityFsUsed.textContent = `${formatNumber(s1Fs, 1)}h`;
    if (valCapacityFsTotal) valCapacityFsTotal.textContent = `/ ${formatNumber(capFs, 0)}h pool`;
    if (fillCapacityFs) {
      const pctFs = capFs > 0 ? Math.round((s1Fs / capFs) * 100) : 0;
      fillCapacityFs.style.width = `${Math.min(100, pctFs)}%`;
    }
    if (badgeCapacityFs) {
      badgeCapacityFs.textContent = capFs > 0 ? `${formatNumber(capFs, 0)}h DISP.` : 'INACTIVO';
    }
    if (subCapacityFs) {
      subCapacityFs.textContent = currentSprintPlan.devsFs > 0
        ? `${currentSprintPlan.devsFs} devs fullstack de apoyo dinámico`
        : '0 devs asignados a pool general';
    }

    // Overall Sprints Impact
    let totalPlannedHours = 0;
    let totalPlannedSavings = 0;
    let totalPlannedSqale = 0;
    currentSprintPlan.sprints.forEach(s => {
      (s.cards || []).forEach(c => {
        totalPlannedHours += c.deudaHoras;
        totalPlannedSavings += (c.interesUsd || 0);
        totalPlannedSqale += (c.sqaleCount || 0);
      });
    });

    const totalBacklogSqale = (currentSprintPlan.backlog.cards || []).reduce((acc, c) => acc + (c.sqaleCount || 0), 0);
    const totalSqaleAll = totalPlannedSqale + totalBacklogSqale;

    const repoTotalDebt = currentSprintPlan.totalRepoDebt || 1;
    const impactPct = Math.round((totalPlannedHours / repoTotalDebt) * 1000) / 10;
    if (valImpactHours) valImpactHours.textContent = `${formatNumber(totalPlannedHours, 1)}h`;
    if (valImpactPct) valImpactPct.textContent = `(${impactPct}% deuda total)`;
    if (valImpactSavings) valImpactSavings.textContent = `${formatCurrency(totalPlannedSavings)}/año`;
    if (subImpactSummary) {
      subImpactSummary.innerHTML = `
        Ahorro anual estimado en fricción: <strong style="color: var(--color-success);">${formatCurrency(totalPlannedSavings)}/año</strong>
        <span style="display: block; margin-top: 4px; font-size: 0.8rem; color: var(--text-secondary);">
          🛡️ Violaciones SQALE en sprints: <strong style="color: var(--mp-blue);">${totalPlannedSqale}</strong> de ${totalSqaleAll} detectadas
        </span>
      `;
    }
  }

  function renderKanbanBoard() {
    if (!kanbanBoardContainer || !currentSprintPlan) return;

    const allCols = [...currentSprintPlan.sprints, currentSprintPlan.backlog];

    kanbanBoardContainer.innerHTML = allCols.map(col => {
      const isBacklog = col.id === 'backlog';
      const colCards = col.cards || [];
      const totalColHours = colCards.reduce((acc, c) => acc + (c.deudaHoras || 0), 0);

      return `
        <div class="kanban-column" id="col-${col.id}" data-col-id="${col.id}">
          <div class="kanban-col-header">
            <div class="kanban-col-title-wrap">
              <span class="kanban-col-title">${isBacklog ? '📦 ' + col.name : '⚡ ' + col.name}</span>
              <span class="kanban-col-count" id="count-${col.id}">${colCards.length}</span>
            </div>
            <span class="kanban-col-hours" id="hours-${col.id}">${formatNumber(totalColHours, 1)}h</span>
          </div>

          <div class="kanban-cards-list" id="list-${col.id}" data-col-id="${col.id}">
            ${colCards.map(c => renderKanbanCardHtml(c, col.id)).join('')}
          </div>
        </div>
      `;
    }).join('');

    setupKanbanDragAndDrop();
    setupCardButtons();
  }

  function renderKanbanCardHtml(card, colId) {
    const isBacklog = colId === 'backlog';
    const roleBadgeClass = card.role === 'BE' ? 'card-role-be' : (card.role === 'FE' ? 'card-role-fe' : 'card-role-fs');
    const roleLabel = card.role === 'BE' ? 'Backend (Go)' : (card.role === 'FE' ? 'Frontend (Dart)' : 'Fullstack');
    const zoneBadgeClass = card.isPainZone ? 'zone-pain' : 'zone-main';
    const zoneLabel = card.isPainZone ? '🔴 ZONA DOLOR' : '🟢 SECUENCIA';
    const roiClass = card.roiAjustado > 0 ? 'highlight-roi' : '';
    const roiText = card.roiAjustado > 0 ? `ROI: +${card.roiAjustado}%` : `ROI: ${card.roiAjustado}%`;

    return `
      <div class="kanban-card" id="card-${card.id}" draggable="true" data-card-id="${card.id}" data-col-id="${colId}">
        <div class="kanban-card-top">
          <span class="card-id-tag">${card.id}</span>
          <div class="card-badges-group">
            <span class="card-role-badge ${roleBadgeClass}">${roleLabel}</span>
            <span class="card-zone-badge ${zoneBadgeClass}">${zoneLabel}</span>
          </div>
        </div>

        <div class="kanban-card-file" title="Clic para ver detalle del archivo" data-filepath="${card.filePath}">
          ${card.filePath}
        </div>

        <div class="kanban-card-metrics">
          <span class="card-metric-pill">LOC: ${card.loc}</span>
          <span class="card-metric-pill highlight-cc">CC: ${card.cc}</span>
          <span class="card-metric-pill">MI: ${card.mi}</span>
          <span class="card-metric-pill" style="font-weight: 700; color: var(--mp-blue-dark);">${card.deudaHoras}h</span>
          <span class="card-metric-pill ${roiClass}">${roiText}</span>
          ${card.sqaleCount > 0 ? `
            <span class="card-metric-pill highlight-sqale" title="Infracciones SQALE detectadas: ${card.violations.map(v => v.regla).join(', ')}">
              🛡️ SQALE: ${card.sqaleCount} (${card.sqaleRemediationHours}h)
            </span>
          ` : ''}
        </div>

        ${card.violations && card.violations.length > 0 ? `
          <div class="card-violation-tags">
            ${card.violations.slice(0, 3).map(v => {
              const isCrit = v.regla === 'ZONA_DOLOR' || v.regla === 'IMPORT_CIRCULAR';
              const isWarn = v.regla === 'CC_ALTA' || v.regla === 'ARCHIVO_LARGO';
              const tagClass = isCrit ? 'violation-critical' : (isWarn ? 'violation-warning' : '');
              return `<span class="card-violation-tag ${tagClass}" title="${v.detalle || ''}">${v.regla}</span>`;
            }).join('')}
            ${card.violations.length > 3 ? `<span class="card-violation-tag">+${card.violations.length - 3}</span>` : ''}
          </div>
        ` : ''}

        <div class="kanban-card-action">
          <strong>Acción:</strong> ${card.refactorAdvice}
        </div>

        <div class="kanban-card-dod">
          <strong style="color: var(--text-secondary); display: block; margin-bottom: 2px;">Criterios de Aceptación (DoD):</strong>
          <ul style="padding-left: 14px; margin: 0;">
            ${card.dod.slice(0, 2).map(item => `<li>${item}</li>`).join('')}
          </ul>
        </div>

        <div class="kanban-card-actions">
          ${!isBacklog ? `
            <button class="card-shift-btn btn-prev-sprint" data-card-id="${card.id}" title="Mover al sprint anterior">◀ Anterior</button>
            <button class="card-shift-btn discard-btn btn-send-backlog" data-card-id="${card.id}" title="Enviar al backlog">✕ Backlog</button>
            <button class="card-shift-btn btn-next-sprint" data-card-id="${card.id}" title="Mover al siguiente sprint">Siguiente ▶</button>
          ` : `
            <button class="card-shift-btn btn-to-sprint1" data-card-id="${card.id}" title="Priorizar en Sprint 1" style="color: var(--mp-blue-dark); font-weight: 700;">
              ▲ Mover a Sprint 1
            </button>
          `}
        </div>
      </div>
    `;
  }

  function setupCardButtons() {
    // Click on file path to open modal
    document.querySelectorAll('.kanban-card-file').forEach(el => {
      el.addEventListener('click', () => {
        const filePath = el.getAttribute('data-filepath');
        if (currentReport && currentReport.archivos) {
          const found = currentReport.archivos.find(f => cleanPathName(f.ruta) === filePath);
          if (found) openFileModal(found);
        }
      });
    });

    // Move Prev
    document.querySelectorAll('.btn-prev-sprint').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const cardId = btn.getAttribute('data-card-id');
        shiftCard(cardId, -1);
      });
    });

    // Move Next
    document.querySelectorAll('.btn-next-sprint').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const cardId = btn.getAttribute('data-card-id');
        shiftCard(cardId, 1);
      });
    });

    // Send Backlog
    document.querySelectorAll('.btn-send-backlog').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const cardId = btn.getAttribute('data-card-id');
        moveCard(cardId, 'backlog');
      });
    });

    // Backlog to Sprint 1
    document.querySelectorAll('.btn-to-sprint1').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const cardId = btn.getAttribute('data-card-id');
        moveCard(cardId, 'sprint-1');
      });
    });
  }

  function findCardAndCol(cardId) {
    if (!currentSprintPlan) return null;
    const allCols = [...currentSprintPlan.sprints, currentSprintPlan.backlog];
    for (const col of allCols) {
      const idx = col.cards.findIndex(c => c.id === cardId);
      if (idx !== -1) {
        return { col, card: col.cards[idx], index: idx };
      }
    }
    return null;
  }

  function shiftCard(cardId, delta) {
    const found = findCardAndCol(cardId);
    if (!found) return;

    const { col, card } = found;
    if (col.id === 'backlog') {
      moveCard(cardId, 'sprint-1');
      return;
    }

    const currentNum = col.number;
    const targetNum = currentNum + delta;

    if (targetNum < 1) {
      // already in Sprint 1, cannot go before
      return;
    }

    if (targetNum > currentSprintPlan.sprints.length) {
      // exceeded sprints, send to backlog
      moveCard(cardId, 'backlog');
      return;
    }

    moveCard(cardId, `sprint-${targetNum}`);
  }

  function moveCard(cardId, targetColId) {
    const found = findCardAndCol(cardId);
    if (!found) return;

    const { col: sourceCol, card, index } = found;
    if (sourceCol.id === targetColId) return;

    const allCols = [...currentSprintPlan.sprints, currentSprintPlan.backlog];
    const targetCol = allCols.find(c => c.id === targetColId);
    if (!targetCol) return;

    // Remove from source
    sourceCol.cards.splice(index, 1);
    // Add to target
    targetCol.cards.push(card);
    card.currentSprint = targetCol.number;

    updateCapacityMeters();
    renderKanbanBoard();
  }

  function setupKanbanDragAndDrop() {
    const cards = document.querySelectorAll('.kanban-card');
    const cols = document.querySelectorAll('.kanban-column');

    cards.forEach(cardEl => {
      cardEl.addEventListener('dragstart', (e) => {
        cardEl.classList.add('is-dragging');
        e.dataTransfer.setData('text/plain', cardEl.getAttribute('data-card-id'));
        e.dataTransfer.effectAllowed = 'move';
      });

      cardEl.addEventListener('dragend', () => {
        cardEl.classList.remove('is-dragging');
        cols.forEach(c => c.classList.remove('drag-over-col'));
      });
    });

    cols.forEach(colEl => {
      colEl.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        colEl.classList.add('drag-over-col');
      });

      colEl.addEventListener('dragleave', () => {
        colEl.classList.remove('drag-over-col');
      });

      colEl.addEventListener('drop', (e) => {
        e.preventDefault();
        colEl.classList.remove('drag-over-col');
        const cardId = e.dataTransfer.getData('text/plain');
        const targetColId = colEl.getAttribute('data-col-id');
        if (cardId && targetColId) {
          moveCard(cardId, targetColId);
        }
      });
    });
  }

  // =========================================================================
  // Exporters: SGA Agent Prompt, Markdown, and JSON
  // =========================================================================

  function copySgaPrompt() {
    if (!currentSprintPlan) {
      alert('Primero generá o cargá un plan de sprints.');
      return;
    }

    const s1 = currentSprintPlan.sprints[0];
    if (!s1 || s1.cards.length === 0) {
      alert('El Sprint 1 no contiene tarjetas asignadas.');
      return;
    }

    const repoName = getProjectName(currentReport ? currentReport.repo_path : '');
    const beCards = s1.cards.filter(c => c.role === 'BE');
    const feCards = s1.cards.filter(c => c.role === 'FE');
    const fsCards = s1.cards.filter(c => c.role === 'FS');

    const totalHours = s1.cards.reduce((acc, c) => acc + c.deudaHoras, 0);

    let promptText = `# 🤖 PLAN DE ACCIÓN DE DEUDA TÉCNICA — SPRINT 1 (${repoName.toUpperCase()})\n\n`;
    promptText += `**Objetivo del Sprint:** Reducir fricción operativa, mitigar violaciones SQALE (ISO/IEC 25010) y deuda técnica priorizando cuellos de botella en **Zona de Dolor (D > 0.5)** y **Quick Wins (ROI positivo)**.\n\n`;
    promptText += `### 👥 Capacidad y Asignación del Sprint 1:\n`;
    promptText += `- **Duración:** ${currentSprintPlan.weeks} semanas (${formatNumber(currentSprintPlan.hoursPerDev, 0)}h útiles/dev)\n`;
    promptText += `- **Equipo Backend (Go):** ${currentSprintPlan.devsBe} devs | ${formatNumber(currentSprintPlan.capBe, 0)}h disponibles\n`;
    promptText += `- **Equipo Frontend (Flutter):** ${currentSprintPlan.devsFe} devs | ${formatNumber(currentSprintPlan.capFe, 0)}h disponibles\n`;
    if (currentSprintPlan.devsFs > 0) {
      promptText += `- **Pool Fullstack:** ${currentSprintPlan.devsFs} devs | ${formatNumber(currentSprintPlan.capFs, 0)}h de apoyo flexible\n`;
    }
    promptText += `- **Total Horas Asignadas:** ${formatNumber(totalHours, 1)}h en ${s1.cards.length} tarjetas\n\n`;

    if (currentSprintPlan.forbiddenCards && currentSprintPlan.forbiddenCards.length > 0) {
      promptText += `🛑 *ARCHIVOS PROHIBIDOS (NO TOCAR)*\n`;
      promptText += `Quedan estrictamente vetados por requerir rediseño completo de arquitectura:\n\n`;
      currentSprintPlan.forbiddenCards.forEach((c, idx) => {
        promptText += `${idx + 1}. \`${c.filePath}\` (LOC: ${c.loc}, CC: ${c.cc}, Deuda: ${c.deudaHoras}h)\n`;
      });
      promptText += `\n`;
    }

    promptText += `---\n\n`;

    if (beCards.length > 0) {
      promptText += `## 🔧 Tarjetas Backend (Go) — Sprint 1\n\n`;
      beCards.forEach(c => {
        promptText += `### [${c.id}] \`${c.filePath}\`\n`;
        promptText += `- **Módulo:** \`${c.moduleName}\` (${c.zona})\n`;
        promptText += `- **Métricas:** LOC: ${c.loc} | CC: ${c.cc} | MI: ${c.mi} | Deuda: ${c.deudaHoras}h | ROI Ajustado: ${c.roiAjustado > 0 ? '+' : ''}${c.roiAjustado}%\n`;
        if (c.violations && c.violations.length > 0) {
          promptText += `- **Infracciones SQALE (${c.sqaleCount} violaciones, ~${c.sqaleRemediationHours}h remediación):**\n`;
          c.violations.forEach(v => {
            promptText += `  * [${v.regla}] ${v.detalle || ''} (${v.remediacion_minutos || 0} min)\n`;
          });
        }
        promptText += `- **Diagnóstico y Acción:** ${c.refactorAdvice}\n`;
        promptText += `- **Criterios de Aceptación (DoD):**\n`;
        c.dod.forEach(item => {
          promptText += `  - [ ] ${item}\n`;
        });
        promptText += `\n`;
      });
    }

    if (feCards.length > 0) {
      promptText += `## 🎨 Tarjetas Frontend (Flutter/Dart) — Sprint 1\n\n`;
      feCards.forEach(c => {
        promptText += `### [${c.id}] \`${c.filePath}\`\n`;
        promptText += `- **Módulo:** \`${c.moduleName}\` (${c.zona})\n`;
        promptText += `- **Métricas:** LOC: ${c.loc} | CC: ${c.cc} | MI: ${c.mi} | Deuda: ${c.deudaHoras}h | ROI Ajustado: ${c.roiAjustado > 0 ? '+' : ''}${c.roiAjustado}%\n`;
        if (c.violations && c.violations.length > 0) {
          promptText += `- **Infracciones SQALE (${c.sqaleCount} violaciones, ~${c.sqaleRemediationHours}h remediación):**\n`;
          c.violations.forEach(v => {
            promptText += `  * [${v.regla}] ${v.detalle || ''} (${v.remediacion_minutos || 0} min)\n`;
          });
        }
        promptText += `- **Diagnóstico y Acción:** ${c.refactorAdvice}\n`;
        promptText += `- **Criterios de Aceptación (DoD):**\n`;
        c.dod.forEach(item => {
          promptText += `  - [ ] ${item}\n`;
        });
        promptText += `\n`;
      });
    }

    if (fsCards.length > 0) {
      promptText += `## ⚡ Tarjetas Fullstack — Sprint 1\n\n`;
      fsCards.forEach(c => {
        promptText += `### [${c.id}] \`${c.filePath}\`\n`;
        promptText += `- **Módulo:** \`${c.moduleName}\` (${c.zona})\n`;
        promptText += `- **Métricas:** LOC: ${c.loc} | CC: ${c.cc} | MI: ${c.mi} | Deuda: ${c.deudaHoras}h\n`;
        if (c.violations && c.violations.length > 0) {
          promptText += `- **Infracciones SQALE (${c.sqaleCount} violaciones, ~${c.sqaleRemediationHours}h remediación):**\n`;
          c.violations.forEach(v => {
            promptText += `  * [${v.regla}] ${v.detalle || ''} (${v.remediacion_minutos || 0} min)\n`;
          });
        }
        promptText += `- **Diagnóstico y Acción:** ${c.refactorAdvice}\n`;
        promptText += `- **Criterios de Aceptación (DoD):**\n`;
        c.dod.forEach(item => {
          promptText += `  - [ ] ${item}\n`;
        });
        promptText += `\n`;
      });
    }

    promptText += `---\n\n`;
    promptText += `📋 *CHECKLIST PR / REVIEWS (Viernes)*\n`;
    promptText += `Al abrir la PR, incluir tildado:\n\n`;
    promptText += `* [ ] CC ≤ 4 (Dart) / ≤ 7 (Go)\n`;
    promptText += `* [ ] Maintainability Index ≥ 60%\n`;
    promptText += `* [ ] TDR ≤ 6%\n`;
    promptText += `* [ ] Máx 3 niveles de if\n`;
    promptText += `* [ ] Pattern matching / sealed classes en estado\n`;
    promptText += `* [ ] DIT ≤ 2 (Dart) y CBO ≤ 6\n`;
    promptText += `* [ ] Parseo seguro de nulos en BD\n`;
    promptText += `* [ ] Cero imports/variables/código muerto\n`;
    promptText += `* [ ] Al menos 1 test unitario/contrato nuevo pasando\n`;
    promptText += `* [ ] Ownership respetado (solo archivos asignados)\n\n`;

    promptText += `---\n\n`;
    promptText += `## ⚠️ Instrucciones Operativas de Ejecución para el Agente:\n`;
    promptText += `1. **Procesar secuencialmente:** Abordá una tarjeta a la vez siguiendo el orden numérico asignado.\n`;
    promptText += `2. **No omitir ningún archivo:** Cada tarjeta arriba listada debe tener su refactorización concreta.\n`;
    promptText += `3. **Cero regresiones:** Tras modificar cada archivo, ejecutá los tests unitarios correspondientes (\`go test ./...\` en backend o \`flutter test\` en frontend).\n`;
    promptText += `4. **Respetar contratos:** Si desacoplás un handler o controller, conservá el contrato de las APIs y no rompas los llamados existentes.\n`;
    promptText += `5. **Confirmación:** Al finalizar cada tarjeta, reportá los cambios realizados y la nueva complejidad ciclomática estimada.\n`;

    navigator.clipboard.writeText(promptText).then(() => {
      if (planCopyFeedback) {
        planCopyFeedback.style.display = 'inline-flex';
        setTimeout(() => {
          planCopyFeedback.style.display = 'none';
        }, 3500);
      }
    }).catch(err => {
      alert('Error al copiar al portapapeles: ' + err);
    });
  }

  function downloadPlanMarkdown() {
    if (!currentSprintPlan) {
      alert('Primero generá o cargá un plan de sprints.');
      return;
    }

    const repoName = getProjectName(currentReport ? currentReport.repo_path : '');
    let md = `# 🏗️ Plan de Acción — Reducción de Deuda Técnica ${repoName}\n\n`;
    md += `**Fecha de Generación:** ${new Date().toISOString().slice(0, 10)}  \n`;
    md += `**Equipo:** ${currentSprintPlan.devsBe} Backend Go + ${currentSprintPlan.devsFe} Frontend Flutter + ${currentSprintPlan.devsFs} Fullstack  \n`;
    md += `**Duración Sprint:** ${currentSprintPlan.weeks} semanas (~${formatNumber(currentSprintPlan.hoursPerDev, 0)}h útiles/dev)  \n`;
    md += `**Capacidad por Sprint:** Backend: ${formatNumber(currentSprintPlan.capBe, 0)}h | Frontend: ${formatNumber(currentSprintPlan.capFe, 0)}h | Fullstack: ${formatNumber(currentSprintPlan.capFs, 0)}h  \n`;
    const stratText = selectStrategy && selectStrategy.options[selectStrategy.selectedIndex] ? selectStrategy.options[selectStrategy.selectedIndex].text : 'Híbrida';
    md += `**Estrategia:** ${stratText}  \n`;
    if (selectSqalePriority && selectSqalePriority.value !== 'none') {
      const sqaleText = selectSqalePriority.options[selectSqalePriority.selectedIndex].text;
      md += `**Foco SQALE:** ${sqaleText}  \n`;
    }
    md += `\n`;

    if (currentSprintPlan.forbiddenCards && currentSprintPlan.forbiddenCards.length > 0) {
      md += `## 🛑 Archivos Prohibidos (No Tocar — Requieren Rediseño Completo)\n\n`;
      md += `Quedan estrictamente vetados por requerir rediseño completo de arquitectura:\n\n`;
      md += `| # | Archivo | Rol | LOC | CC | MI | Deuda (h) | Motivo |\n`;
      md += `|:---:|---|:---:|---:|---:|---:|---:|---|\n`;
      currentSprintPlan.forbiddenCards.forEach((c, idx) => {
        md += `| ${idx + 1} | \`${c.filePath}\` | ${c.role} | ${c.loc} | ${c.cc} | ${c.mi} | ${c.deudaHoras}h | ${c.motivo} |\n`;
      });
      md += `\n---\n\n`;
    }

    md += `## 📋 Checklist PR / Reviews (Viernes)\n\n`;
    md += `Al abrir la PR, incluir tildado:\n\n`;
    md += `* [ ] CC ≤ 4 (Dart) / ≤ 7 (Go)\n`;
    md += `* [ ] Maintainability Index ≥ 60%\n`;
    md += `* [ ] TDR ≤ 6%\n`;
    md += `* [ ] Máx 3 niveles de if\n`;
    md += `* [ ] Pattern matching / sealed classes en estado\n`;
    md += `* [ ] DIT ≤ 2 (Dart) y CBO ≤ 6\n`;
    md += `* [ ] Parseo seguro de nulos en BD\n`;
    md += `* [ ] Cero imports/variables/código muerto\n`;
    md += `* [ ] Al menos 1 test unitario/contrato nuevo pasando\n`;
    md += `* [ ] Ownership respetado (solo archivos asignados)\n\n`;
    md += `---\n\n`;

    currentSprintPlan.sprints.forEach(sprint => {
      const cards = sprint.cards || [];
      const totalHours = cards.reduce((acc, c) => acc + c.deudaHoras, 0);
      md += `## 🟢 ${sprint.name} (${formatNumber(totalHours, 1)}h asignadas)\n\n`;
      md += `| ID | Archivo | Rol | Módulo | Zona | LOC | CC | Deuda (h) | SQALE | ROI Adj. | Sugerencia de Refactorización |\n`;
      md += `|---|---|:---:|---|:---:|---:|---:|---:|:---:|---:|---|\n`;
      cards.forEach(c => {
        const sqaleStr = c.sqaleCount > 0 ? `🛡️ ${c.sqaleCount} (${c.sqaleRemediationHours}h)` : '—';
        md += `| ${c.id} | \`${c.filePath}\` | ${c.role} | ${c.moduleName} | ${c.isPainZone ? '🔴 DOLOR' : '🟢 SECUENCIA'} | ${c.loc} | ${c.cc} | ${c.deudaHoras}h | ${sqaleStr} | ${c.roiAjustado > 0 ? '+' : ''}${c.roiAjustado}% | ${c.refactorAdvice} |\n`;
      });
      md += `\n`;
    });

    if (currentSprintPlan.backlog && currentSprintPlan.backlog.cards.length > 0) {
      const bCards = currentSprintPlan.backlog.cards;
      const bHours = bCards.reduce((acc, c) => acc + c.deudaHoras, 0);
      md += `## 📦 Backlog de Deuda Técnica Restante (${bCards.length} tareas, ${formatNumber(bHours, 1)}h)\n\n`;
      md += `| ID | Archivo | Rol | Módulo | LOC | CC | Deuda (h) |\n`;
      md += `|---|---|:---:|---|---:|---:|---:|\n`;
      bCards.slice(0, 30).forEach(c => {
        md += `| ${c.id} | \`${c.filePath}\` | ${c.role} | ${c.moduleName} | ${c.loc} | ${c.cc} | ${c.deudaHoras}h |\n`;
      });
      if (bCards.length > 30) {
        md += `\n*... y ${bCards.length - 30} archivos más en backlog.*  \n`;
      }
    }

    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `plan_accion_${repoName}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  function downloadPlanJson() {
    if (!currentSprintPlan) {
      alert('Primero generá o cargá un plan de sprints.');
      return;
    }

    const repoName = getProjectName(currentReport ? currentReport.repo_path : '');
    const exportObj = {
      proyecto: repoName,
      fecha_plan: new Date().toISOString(),
      parametros: {
        devs_backend: currentSprintPlan.devsBe,
        devs_frontend: currentSprintPlan.devsFe,
        devs_fullstack: currentSprintPlan.devsFs,
        semanas_sprint: currentSprintPlan.weeks,
        dedicacion_pct: currentSprintPlan.dedication * 100,
        estrategia: selectStrategy ? selectStrategy.value : 'hybrid_zona_cc_roi',
        prioridad_sqale: selectSqalePriority ? selectSqalePriority.value : 'none',
        capacidad_be_horas: currentSprintPlan.capBe,
        capacidad_fe_horas: currentSprintPlan.capFe,
        capacidad_fs_horas: currentSprintPlan.capFs
      },
      sprints: currentSprintPlan.sprints.map(s => ({
        id: s.id,
        nombre: s.name,
        horas_totales: s.cards.reduce((acc, c) => acc + c.deudaHoras, 0),
        tareas: s.cards.map(c => ({
          id: c.id,
          archivo: c.filePath,
          rol: c.role,
          modulo: c.moduleName,
          zona: c.zona,
          loc: c.loc,
          cc: c.cc,
          mi: c.mi,
          deuda_horas: c.deudaHoras,
          roi_ajustado_porc: c.roiAjustado,
          sqale_violaciones_count: c.sqaleCount,
          sqale_remediacion_horas: c.sqaleRemediationHours,
          sqale_violaciones: (c.violations || []).map(v => ({
            regla: v.regla,
            categoria: v.categoria_sqale,
            detalle: v.detalle,
            minutos: v.remediacion_minutos
          })),
          diagnostico: c.refactorAdvice,
          criterios_aceptacion: c.dod
        }))
      })),
      backlog: {
        total_tareas: currentSprintPlan.backlog.cards.length,
        horas_totales: currentSprintPlan.backlog.cards.reduce((acc, c) => acc + c.deudaHoras, 0),
        tareas: currentSprintPlan.backlog.cards.map(c => ({
          id: c.id,
          archivo: c.filePath,
          rol: c.role,
          modulo: c.moduleName,
          zona: c.zona,
          loc: c.loc,
          cc: c.cc,
          mi: c.mi,
          deuda_horas: c.deudaHoras,
          roi_ajustado_porc: c.roiAjustado,
          sqale_violaciones_count: c.sqaleCount,
          sqale_remediacion_horas: c.sqaleRemediationHours
        }))
      }
    };

    const blob = new Blob([JSON.stringify(exportObj, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `plan_sprint_${repoName}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
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

    // Plan & Sprint Controls
    if (btnRecalculatePlan) {
      btnRecalculatePlan.addEventListener('click', () => {
        if (currentReport) generateSprintPlan(currentReport);
      });
    }

    if (btnResetPlanDefaults) {
      btnResetPlanDefaults.addEventListener('click', resetPlanFormDefaults);
    }

    if (btnCopySgaPrompt) {
      btnCopySgaPrompt.addEventListener('click', copySgaPrompt);
    }

    if (btnDownloadPlanMd) {
      btnDownloadPlanMd.addEventListener('click', downloadPlanMarkdown);
    }

    if (btnDownloadPlanJson) {
      btnDownloadPlanJson.addEventListener('click', downloadPlanJson);
    }

    if (btnCopyChecklist) {
      btnCopyChecklist.addEventListener('click', copyChecklistMarkdown);
    }

    // Auto-recalculate plan on input changes
    [inputDevsBe, inputDevsFe, inputDevsFs, selectSprintWeeks, inputDedicationPct, selectSprintsCount, selectStrategy, selectSqalePriority].forEach(elem => {
      if (elem) {
        elem.addEventListener('change', () => {
          if (currentReport) generateSprintPlan(currentReport);
        });
      }
    });

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

/**
 * Horizon B2B Services - Linear / Vercel Minimalist Dark Theme Chart Manager
 */

let serviceChartInstance = null;
let policyChartInstance = null;

function initCharts(stats) {
  if (typeof Chart === 'undefined') return;

  Chart.defaults.font.family = "'IBM Plex Sans Arabic', 'Plus Jakarta Sans', sans-serif";
  Chart.defaults.color = '#94A3B8';

  renderServiceChart(stats.service_distribution || []);
  renderPolicyChart(stats.policy_distribution || [], stats);
}

function renderServiceChart(serviceData) {
  const ctx = document.getElementById('serviceDistChart');
  if (!ctx) return;

  if (serviceChartInstance) {
    serviceChartInstance.destroy();
  }

  const labels = serviceData.map(d => {
    const name = d.service || 'Unknown';
    return name.length > 20 ? name.substring(0, 20) + '...' : name;
  });
  const dataValues = serviceData.map(d => d.count);

  const linearPalette = [
    '#F8FAFC', '#94A3B8', '#64748B', '#475569',
    '#10B981', '#F59E0B', '#6366F1', '#EC4899', '#38BDF8'
  ];

  serviceChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels.length ? labels : ['No data'],
      datasets: [{
        label: 'Requests',
        data: dataValues.length ? dataValues : [0],
        backgroundColor: linearPalette.slice(0, Math.max(labels.length, 1)),
        borderRadius: 4,
        barThickness: 20,
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.1)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#13151F',
          titleColor: '#FFFFFF',
          bodyColor: '#10B981',
          borderColor: 'rgba(255, 255, 255, 0.15)',
          borderWidth: 1,
          padding: 10,
          boxPadding: 4,
          callbacks: {
            title: function(items) {
              const idx = items[0].dataIndex;
              return serviceData[idx] ? serviceData[idx].service : '';
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { stepSize: 1, color: '#64748B', font: { size: 10 } }
        },
        x: {
          grid: { display: false },
          ticks: {
            autoSkip: false,
            maxRotation: 25,
            minRotation: 25,
            color: '#94A3B8',
            font: { size: 10 }
          }
        }
      }
    }
  });
}

function renderPolicyChart(policyData, stats) {
  const ctx = document.getElementById('policyDistChart');
  if (!ctx) return;

  if (policyChartInstance) {
    policyChartInstance.destroy();
  }

  const isAr = (typeof AppState !== 'undefined' && AppState.lang === 'ar');
  const labels = isAr ? ['متوافق', 'عاجل (موافقة)', 'مخالف وغير مكتمل', 'خارج النطاق'] : ['Compliant', 'Urgent', 'Violation', 'Out of Scope'];
  const values = [
    stats.approved_requests || (stats.total_requests - stats.urgent_requests - stats.policy_violations - stats.out_of_scope_requests) || 0,
    stats.urgent_requests || 0,
    stats.policy_violations || 0,
    stats.out_of_scope_requests || 0
  ];

  const total = values.reduce((a, b) => a + b, 0);
  const displayValues = total > 0 ? values : [1, 0, 0, 0];

  policyChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: displayValues,
        backgroundColor: [
          '#10B981', // Emerald
          '#F59E0B', // Amber
          '#F43F5E', // Rose
          '#6366F1'  // Indigo
        ],
        borderWidth: 2,
        borderColor: '#07080B',
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            padding: 12,
            font: { size: 10, weight: '600' },
            color: '#94A3B8'
          }
        },
        tooltip: {
          backgroundColor: '#13151F',
          titleColor: '#FFFFFF',
          bodyColor: '#E2E8F0',
          borderColor: 'rgba(255, 255, 255, 0.15)',
          borderWidth: 1,
          padding: 10
        }
      },
      cutout: '76%'
    }
  });
}

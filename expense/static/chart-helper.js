// chart-helper.js
async function fetchSummary(days = 30) {
  const resp = await fetch(`/api/summary?days=${days}`);
  return await resp.json();
}

function formatCurrency(x) {
  // simple currency formatter - change symbol if you want
  return "₹" + x.toFixed(2);
}

async function drawCharts(days = 30) {
  const data = await fetchSummary(days);

  // Category Pie Chart
  const catLabels = data.categories.map((c) => c.category);
  const catValues = data.categories.map((c) => c.total);

  const catCtx = document.getElementById("categoryChart").getContext("2d");
  // destroy existing chart on re-render (if any)
  if (catCtx._chart) {
    catCtx._chart.destroy();
  }
  catCtx._chart = new Chart(catCtx, {
    type: "doughnut",
    data: {
      labels: catLabels,
      datasets: [
        {
          data: catValues,
          backgroundColor: [
            '#44444E',
            '#6B6B75', 
            '#A67B7B',
            '#B87B7B',
            '#C8A8A8',
            '#D8B8B8',
            '#E8C8C8',
            '#F5F5F0'
          ],
          borderColor: '#F5F5F0',
          borderWidth: 2,
          hoverBorderWidth: 3,
          hoverBorderColor: '#44444E'
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: `🏷️ Spending by Category (Last ${data.days} Days)`,
          font: {
            size: 16,
            weight: 'bold',
            family: 'Inter, sans-serif'
          },
          color: '#44444E',
          padding: {
            top: 10,
            bottom: 20
          }
        },
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 20,
            font: {
              size: 12,
              family: 'Inter, sans-serif'
            },
            color: '#44444E'
          }
        },
        tooltip: {
          backgroundColor: 'rgba(68, 68, 78, 0.95)',
          titleColor: '#F5F5F0',
          bodyColor: '#F5F5F0',
          borderColor: '#A67B7B',
          borderWidth: 1,
          cornerRadius: 8,
          displayColors: true,
          titleFont: {
            size: 14,
            weight: 'bold'
          },
          bodyFont: {
            size: 13
          },
          callbacks: {
            label: function (context) {
              const val = context.raw || 0;
              const sum = context.dataset.data.reduce((a, b) => a + b, 0);
              const perc = sum ? ((100 * val) / sum).toFixed(1) : 0;
              return `${context.label}: ${formatCurrency(val)} (${perc}%)`;
            },
          },
        },
      },
      cutout: '50%',
      elements: {
        arc: {
          borderWidth: 2
        }
      }
    },
  });

  // Daily Trend Line Chart
  const dailyLabels = data.daily.map((d) => {
    const date = new Date(d.date);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });
  const dailyValues = data.daily.map((d) => d.total);

  const dailyCtx = document.getElementById("dailyChart").getContext("2d");
  if (dailyCtx._chart) {
    dailyCtx._chart.destroy();
  }
  dailyCtx._chart = new Chart(dailyCtx, {
    type: "line",
    data: {
      labels: dailyLabels,
      datasets: [
        {
          label: "Daily Spending",
          data: dailyValues,
          fill: true,
          tension: 0.4,
          backgroundColor: 'rgba(166, 123, 123, 0.1)',
          borderColor: '#A67B7B',
          borderWidth: 3,
          pointBackgroundColor: '#44444E',
          pointBorderColor: '#A67B7B',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8,
          pointHoverBackgroundColor: '#A67B7B',
          pointHoverBorderColor: '#44444E',
          pointHoverBorderWidth: 3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: `📊 Daily Spending Trend (Last ${data.days} Days)`,
          font: {
            size: 16,
            weight: 'bold',
            family: 'Inter, sans-serif'
          },
          color: '#44444E',
          padding: {
            top: 10,
            bottom: 20
          }
        },
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: 'rgba(68, 68, 78, 0.95)',
          titleColor: '#F5F5F0',
          bodyColor: '#F5F5F0',
          borderColor: '#A67B7B',
          borderWidth: 1,
          cornerRadius: 8,
          displayColors: false,
          titleFont: {
            size: 14,
            weight: 'bold'
          },
          bodyFont: {
            size: 13
          },
          callbacks: {
            title: function(context) {
              const date = new Date(data.daily[context[0].dataIndex].date);
              return date.toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              });
            },
            label: function (ctx) {
              const value = ctx.parsed.y || 0;
              return `💰 ${formatCurrency(value)}`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: {
            display: false
          },
          ticks: {
            maxRotation: 45,
            minRotation: 0,
            color: '#6B6B75',
            font: {
              size: 11,
              family: 'Inter, sans-serif'
            }
          },
          border: {
            display: false
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(107, 107, 117, 0.1)',
            drawBorder: false
          },
          ticks: {
            color: '#6B6B75',
            font: {
              size: 11,
              family: 'Inter, sans-serif'
            },
            callback: function(value) {
              return formatCurrency(value);
            }
          },
          border: {
            display: false
          }
        }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      },
      elements: {
        line: {
          borderCapStyle: 'round'
        }
      }
    },
  });
}

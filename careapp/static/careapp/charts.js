/* Dashboard charts (Chart.js). Single-hue series in brand teal; status bars are labelled on the axis. */
(function () {
  var dataEl = document.getElementById('chart-data');
  if (!dataEl || !window.Chart) return;
  var d = JSON.parse(dataEl.textContent);
  var TEAL = '#0C5A63', GOLD = '#BC8933', INK = '#5C6E70', GRID = '#E9EEEC';
  var STATUS = { scheduled: '#0C5A63', completed: '#2E7D4F', missed: '#B4232A', cancelled: '#9AA7A4' };

  Chart.defaults.font.family = "'Source Sans 3', 'Segoe UI', Arial, sans-serif";
  Chart.defaults.font.size = 13;
  Chart.defaults.color = INK;
  Chart.defaults.plugins.legend.display = false;
  Chart.defaults.plugins.tooltip.backgroundColor = '#002A2F';
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 8;
  Chart.defaults.maintainAspectRatio = false;

  var axes = function (horizontal) {
    var value = { beginAtZero: true, grid: { color: GRID }, border: { display: false }, ticks: { precision: 0 } };
    var cat = { grid: { display: false }, border: { color: GRID } };
    return horizontal ? { x: value, y: cat } : { x: cat, y: value };
  };
  var bar = { borderRadius: 4, borderSkipped: 'start', maxBarThickness: 36 };

  new Chart(document.getElementById('chart-hours'), {
    type: 'bar',
    data: { labels: d.hours.labels.map(function (l) { return 'w/c ' + l; }),
            datasets: [Object.assign({ label: 'Care hours', data: d.hours.values, backgroundColor: TEAL, hoverBackgroundColor: GOLD }, bar)] },
    options: { scales: axes(false), plugins: { tooltip: { callbacks: { label: function (c) { return ' ' + c.parsed.y + ' hours'; } } } } }
  });

  new Chart(document.getElementById('chart-shifts'), {
    type: 'bar',
    data: { labels: d.shifts.labels,
            datasets: [Object.assign({ label: 'Shifts', data: d.shifts.values,
              backgroundColor: d.shifts.keys.map(function (k) { return STATUS[k]; }) }, bar)] },
    options: { indexAxis: 'y', scales: axes(true) }
  });

  new Chart(document.getElementById('chart-services'), {
    type: 'bar',
    data: { labels: d.services.labels.length ? d.services.labels : ['No data yet'],
            datasets: [Object.assign({ label: 'Service users', data: d.services.values.length ? d.services.values : [0],
              backgroundColor: TEAL, hoverBackgroundColor: GOLD }, bar)] },
    options: { indexAxis: 'y', scales: axes(true) }
  });

  new Chart(document.getElementById('chart-enquiries'), {
    type: 'line',
    data: { labels: d.enquiries.labels,
            datasets: [{ label: 'Enquiries', data: d.enquiries.values, borderColor: GOLD, borderWidth: 2,
              backgroundColor: 'rgba(188,137,51,.12)', fill: true, tension: .3,
              pointRadius: 4, pointHoverRadius: 6, pointBackgroundColor: GOLD, pointBorderColor: '#fff', pointBorderWidth: 2 }] },
    options: { scales: axes(false), interaction: { mode: 'index', intersect: false } }
  });
})();

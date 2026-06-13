(function() {
  'use strict';

  if (typeof Chart === 'undefined') return;

  function safeJson(data, fallback) {
    if (typeof data === 'string') { try { return JSON.parse(data); } catch(e) { return fallback || []; } }
    return data || fallback || [];
  }

  var classPerfEl = document.getElementById('chart-class-performance');
  if (classPerfEl && typeof classPerfData !== 'undefined') {
    new Chart(classPerfEl.getContext('2d'), {
      type: 'bar',
      data: {
        labels: classPerfData.map(function(d) { return d.name; }),
        datasets: [
          { label: 'المتوسط', data: classPerfData.map(function(d) { return d.average; }), backgroundColor: '#4F46E5', borderRadius: 6 },
          { label: 'الحضور', data: classPerfData.map(function(d) { return d.attendance; }), backgroundColor: '#10B981', borderRadius: 6 },
        ],
      },
      options: { responsive: true, plugins: { legend: { position: 'bottom' } }, scales: { y: { beginAtZero: true, max: 100 } } },
    });
  }

  var attEl = document.getElementById('chart-attendance');
  if (attEl && typeof attRate !== 'undefined') {
    var attPresent = attRate || 0;
    var attAbsent = Math.max(0, 100 - attPresent);
    new Chart(attEl.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: ['حاضر', 'غائب'],
        datasets: [{ data: [attPresent, attAbsent], backgroundColor: ['#10B981', '#EF4444'] }],
      },
      options: { responsive: true, plugins: { legend: { position: 'bottom' } } },
    });
  }

  var compEl = document.getElementById('chart-completion');
  if (compEl && typeof perfRate !== 'undefined') {
    var compDone = perfRate || 0;
    var compRemain = Math.max(0, 100 - compDone);
    new Chart(compEl.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: ['مكتمل', 'متبقي'],
        datasets: [{ data: [compDone, compRemain], backgroundColor: ['#8B5CF6', '#E5E7EB'] }],
      },
      options: { responsive: true, plugins: { legend: { position: 'bottom' } } },
    });
  }

  var trendEl = document.getElementById('chart-trend');
  if (trendEl && typeof trendData !== 'undefined') {
    var td = safeJson(trendData);
    new Chart(trendEl.getContext('2d'), {
      type: 'line',
      data: {
        labels: ['الأسبوع 1', 'الأسبوع 2', 'الأسبوع 3', 'الأسبوع 4'],
        datasets: [{ label: 'الأداء', data: td, borderColor: '#4F46E5', backgroundColor: 'rgba(79,70,229,0.1)', fill: true, tension: 0.4 }],
      },
      options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, max: 100 } } },
    });
  }

  var subjEl = document.getElementById('chart-subjects');
  if (subjEl && typeof subjectData !== 'undefined') {
    var sd = safeJson(subjectData, {});
    var labels = Object.keys(sd);
    var values = labels.map(function(k) { return sd[k]; });
    new Chart(subjEl.getContext('2d'), {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{ label: 'المتوسط', data: values, backgroundColor: ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'], borderRadius: 6 }],
      },
      options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, max: 100 } }, indexAxis: 'y' },
    });
  }

  setInterval(function() {
    var alertBadges = document.querySelectorAll('.pulse-badge');
    alertBadges.forEach(function(b) {
      b.style.opacity = (parseFloat(b.style.opacity || 1) === 1) ? '0.4' : '1';
    });
  }, 800);
})();

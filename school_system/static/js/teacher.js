document.addEventListener('DOMContentLoaded', function () {
    initDurationCalculator();
    initCountdownTimers();
    initAttendanceGrid();
    initDeliveryToggle();
    initSessionPolling();
});

function initDurationCalculator() {
    const startInput = document.getElementById('id_start_time');
    const endInput = document.getElementById('id_end_time');
    const durationDisplay = document.getElementById('duration-display');

    if (!startInput || !endInput) return;

    function calcDuration() {
        if (startInput.value && endInput.value) {
            const [sh, sm] = startInput.value.split(':').map(Number);
            const [eh, em] = endInput.value.split(':').map(Number);
            const startMin = sh * 60 + sm;
            const endMin = eh * 60 + em;
            if (endMin > startMin) {
                const diff = endMin - startMin;
                const h = Math.floor(diff / 60);
                const m = diff % 60;
                if (durationDisplay) {
                    durationDisplay.textContent = (h ? h + 'h ' : '') + m + 'm';
                    durationDisplay.className = 'text-success fw-bold';
                }
            } else {
                if (durationDisplay) {
                    durationDisplay.textContent = 'Invalid';
                    durationDisplay.className = 'text-danger fw-bold';
                }
            }
        }
    }

    startInput.addEventListener('change', calcDuration);
    endInput.addEventListener('change', calcDuration);
}

function initCountdownTimers() {
    const timers = document.querySelectorAll('[data-countdown]');
    timers.forEach(function (el) {
        const endTime = new Date(el.getAttribute('data-countdown')).getTime();
        if (isNaN(endTime)) return;

        function tick() {
            const now = new Date().getTime();
            const diff = endTime - now;
            if (diff <= 0) {
                el.textContent = 'Live Now';
                el.className = 'badge bg-success pulse';
                return;
            }
            const h = Math.floor(diff / (1000 * 60 * 60));
            const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const s = Math.floor((diff % (1000 * 60)) / 1000);
            el.textContent = (h ? h + 'h ' : '') + m + 'm ' + s + 's';
        }

        tick();
        setInterval(tick, 1000);
    });
}

function initAttendanceGrid() {
    const grid = document.getElementById('attendance-grid');
    if (!grid) return;

    grid.addEventListener('keydown', function (e) {
        const rows = grid.querySelectorAll('tr[data-student-id]');
        let currentRow = e.target.closest('tr[data-student-id]');
        let idx = currentRow ? Array.from(rows).indexOf(currentRow) : -1;

        switch (e.key) {
            case '1':
                setAttendanceStatus(currentRow, 'PRESENT');
                e.preventDefault();
                break;
            case '2':
                setAttendanceStatus(currentRow, 'ABSENT');
                e.preventDefault();
                break;
            case '3':
                setAttendanceStatus(currentRow, 'LATE');
                e.preventDefault();
                break;
            case '4':
                setAttendanceStatus(currentRow, 'EXCUSED');
                e.preventDefault();
                break;
            case 'ArrowDown':
                if (idx < rows.length - 1) focusRow(rows[idx + 1]);
                e.preventDefault();
                break;
            case 'ArrowUp':
                if (idx > 0) focusRow(rows[idx - 1]);
                e.preventDefault();
                break;
        }
    });

    document.getElementById('mark-all-present')?.addEventListener('click', function () {
        document.querySelectorAll('#attendance-grid tr[data-student-id]').forEach(function (row) {
            setAttendanceStatus(row, 'PRESENT');
        });
    });

    document.getElementById('save-attendance')?.addEventListener('click', saveAttendance);
}

function setAttendanceStatus(row, status) {
    if (!row) return;
    const radio = row.querySelector('input[value="' + status + '"]');
    if (radio) radio.checked = true;
    row.classList.remove('table-success', 'table-danger', 'table-warning', 'table-info');
    if (status === 'PRESENT') row.classList.add('table-success');
    else if (status === 'ABSENT') row.classList.add('table-danger');
    else if (status === 'LATE') row.classList.add('table-warning');
    else if (status === 'EXCUSED') row.classList.add('table-info');
}

function focusRow(row) {
    if (!row) return;
    const firstInput = row.querySelector('input[type="radio"]');
    if (firstInput) firstInput.focus();
}

function saveAttendance() {
    const btn = document.getElementById('save-attendance');
    const indicator = document.getElementById('save-indicator');
    btn.disabled = true;
    if (indicator) indicator.textContent = 'Saving...';

    const data = {};
    document.querySelectorAll('#attendance-grid tr[data-student-id]').forEach(function (row) {
        const sid = row.getAttribute('data-student-id');
        const checked = row.querySelector('input[type="radio"]:checked');
        if (checked) data[sid] = checked.value;
    });

    const sessionId = document.getElementById('attendance-session-id')?.value;

    fetch('/teacher/sessions/' + sessionId + '/attendance/save/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCsrfToken(),
        },
        body: new URLSearchParams({
            'attendance_data': JSON.stringify(data),
            'session_id': sessionId,
        }),
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (indicator) {
            if (res.success) {
                indicator.textContent = 'Saved!';
                indicator.className = 'text-success fw-bold';
            } else {
                indicator.textContent = 'Error: ' + res.message;
                indicator.className = 'text-danger fw-bold';
            }
        }
    })
    .catch(function () {
        if (indicator) {
            indicator.textContent = 'Save failed';
            indicator.className = 'text-danger fw-bold';
        }
    })
    .finally(function () {
        btn.disabled = false;
        setTimeout(function () {
            if (indicator) indicator.textContent = '';
        }, 3000);
    });
}

function initDeliveryToggle() {
    const sel = document.getElementById('id_delivery_type');
    if (!sel) return;

    function toggle() {
        const show = sel.value === 'ONLINE';
        document.querySelectorAll('.online-field').forEach(function (el) {
            el.closest('.mb-3')?.style.setProperty('display', show ? '' : 'none');
        });
    }

    sel.addEventListener('change', toggle);
    toggle();
}

function initSessionPolling() {
    const statusBadge = document.getElementById('session-status-badge');
    if (!statusBadge) return;

    const sessionId = statusBadge.getAttribute('data-session-id');
    if (!sessionId) return;

    setInterval(function () {
        fetch('/teacher/sessions/' + sessionId + '/control/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(function (r) { return r.text(); })
        .then(function (html) {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newBadge = doc.getElementById('session-status-badge');
            if (newBadge) {
                statusBadge.outerHTML = newBadge.outerHTML;
            }
        })
        .catch(function () {});
    }, 30000);
}

function getCsrfToken() {
    const name = 'csrftoken';
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : '';
}

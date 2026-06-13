function startTimer(seconds, displayEl) {
    if (!displayEl) return;
    function tick() {
        if (seconds <= 0) {
            displayEl.textContent = 'Time\'s up!';
            displayEl.className = 'fs-4 fw-bold text-danger';
            document.getElementById('assessment-form')?.submit();
            return;
        }
        var m = Math.floor(seconds / 60);
        var s = seconds % 60;
        displayEl.textContent = m + ':' + (s < 10 ? '0' : '') + s;
        if (seconds < 300) displayEl.className = 'fs-4 fw-bold text-danger pulse';
        seconds--;
        setTimeout(tick, 1000);
    }
    tick();
}

function initAutoSave(formId) {
    var form = document.getElementById(formId);
    if (!form) return;
    setInterval(function () {
        var data = {};
        var inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(function (el) {
            if (el.name && el.type !== 'submit' && el.type !== 'hidden') {
                data[el.name] = el.value;
            }
        });
        try {
            localStorage.setItem('autosave_' + formId, JSON.stringify(data));
        } catch (e) {}
    }, 30000);
}

function updateProgress() {
    var cards = document.querySelectorAll('.question-card');
    var bar = document.getElementById('progress-bar');
    if (!cards.length || !bar) return;
    var answered = 0;
    cards.forEach(function (card) {
        var checked = card.querySelector('input[type="radio"]:checked, input[type="checkbox"]:checked');
        var textInput = card.querySelector('input[type="text"], textarea');
        if (checked || (textInput && textInput.value.trim())) answered++;
    });
    var pct = Math.round((answered / cards.length) * 100);
    bar.style.width = pct + '%';
    bar.textContent = pct + '%';
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.question-card input, .question-card textarea').forEach(function (el) {
        el.addEventListener('change', updateProgress);
        el.addEventListener('keyup', updateProgress);
    });
    updateProgress();

    var form = document.getElementById('assessment-form');
    if (form) {
        form.addEventListener('submit', function (e) {
            try { localStorage.removeItem('autosave_' + form.id); } catch (ex) {}
        });
    }
});

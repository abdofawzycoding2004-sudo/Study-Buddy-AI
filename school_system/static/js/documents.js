(function() {
  'use strict';

  if (window.toggleVisibilityFields) return;

  function toggleVisibilityFields() {
    var cb = document.getElementById('id_is_public');
    var fields = document.getElementById('visibility-fields');
    if (cb && fields) {
      fields.style.display = cb.checked ? '' : 'none';
    }
  }
  window.toggleVisibilityFields = toggleVisibilityFields;

  document.addEventListener('DOMContentLoaded', function() {
    toggleVisibilityFields();
    var cb = document.getElementById('id_is_public');
    if (cb) cb.addEventListener('change', toggleVisibilityFields);

    var uploadArea = document.getElementById('upload-area');
    var fileInput = document.getElementById('id_file_upload');
    var fileInfo = document.getElementById('file-info');
    var fileName = document.getElementById('file-name');
    var fileSize = document.getElementById('file-size');
    var fileSizeWarning = document.getElementById('file-size-warning');
    var progressWrap = document.getElementById('upload-progress');
    var progressBar = document.getElementById('upload-progress-bar');
    var form = document.getElementById('document-form');

    if (!uploadArea || !fileInput) return;

    uploadArea.addEventListener('dragover', function(e) {
      e.preventDefault();
      uploadArea.classList.add('upload-area-dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
      e.preventDefault();
      uploadArea.classList.remove('upload-area-dragover');
    });

    uploadArea.addEventListener('drop', function(e) {
      e.preventDefault();
      uploadArea.classList.remove('upload-area-dragover');
      if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        updateFileInfo(e.dataTransfer.files[0]);
      }
    });

    uploadArea.addEventListener('click', function() {
      fileInput.click();
    });

    fileInput.addEventListener('change', function() {
      if (fileInput.files.length) {
        updateFileInfo(fileInput.files[0]);
      }
    });

    function updateFileInfo(file) {
      fileInfo.style.display = '';
      fileName.textContent = file.name;
      var sizeMB = (file.size / (1024 * 1024)).toFixed(1);
      fileSize.textContent = sizeMB + ' MB';
      fileSizeWarning.style.display = file.size > 100 * 1024 * 1024 ? 'inline' : 'none';
    }

    if (form && fileInput) {
      form.addEventListener('submit', function(e) {
        var file = fileInput.files[0];
        if (!file) return;
        if (file.size > 100 * 1024 * 1024) {
          e.preventDefault();
          alert('حجم الملف كبير جداً! الحد الأقصى 100 MB.');
          return;
        }
        var isNew = !form.dataset.hasInstance;
        if (!isNew) return;
        e.preventDefault();
        var fd = new FormData(form);
        var xhr = new XMLHttpRequest();
        progressWrap.style.display = '';
        xhr.upload.addEventListener('progress', function(evt) {
          if (evt.lengthComputable) {
            var pct = Math.round((evt.loaded / evt.total) * 100);
            progressBar.style.width = pct + '%';
            progressBar.textContent = pct + '%';
          }
        });
        xhr.addEventListener('load', function() {
          if (xhr.status >= 200 && xhr.status < 400) {
            window.location.href = xhr.responseURL || form.action;
          } else {
            try {
              var html = xhr.responseText;
              var parser = new DOMParser();
              var doc = parser.parseFromString(html, 'text/html');
              var errors = doc.querySelector('.alert-danger');
              if (errors) {
                var existing = form.querySelector('.alert-danger');
                if (existing) existing.remove();
                form.insertBefore(errors.cloneNode(true), form.firstChild);
              }
            } catch(e) {}
            progressBar.style.width = '0%';
            progressBar.textContent = '';
            progressWrap.style.display = 'none';
          }
        });
        xhr.addEventListener('error', function() {
          alert('فشل رفع الملف. حاول مرة أخرى.');
          progressBar.style.width = '0%';
          progressWrap.style.display = 'none';
        });
        xhr.open('POST', form.action, true);
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        var csrf = form.querySelector('[name=csrfmiddlewaretoken]');
        if (csrf) xhr.setRequestHeader('X-CSRFToken', csrf.value);
        xhr.send(fd);
      });
    }

    var submitBtn = form ? form.querySelector('[type="submit"]') : null;
    if (submitBtn && form && form.dataset.hasInstance) {
      submitBtn.addEventListener('click', function() {
        progressWrap.style.display = '';
        progressBar.style.width = '100%';
        progressBar.textContent = 'جاري الحفظ...';
      });
    }
  });

  document.addEventListener('click', function(e) {
    var link = e.target.closest('[data-track-download]');
    if (link) {
      e.preventDefault();
      var url = link.href;
      var xhr = new XMLHttpRequest();
      xhr.open('HEAD', url, true);
      xhr.setRequestHeader('X-Track-Download', '1');
      xhr.onload = function() { window.location.href = url; };
      xhr.onerror = function() { window.location.href = url; };
      xhr.send();
    }
  });

  if (typeof jQuery !== 'undefined' && jQuery.fn.select2) {
    document.querySelectorAll('select[multiple]').forEach(function(el) {
      if (!el.closest('.select2-hidden-accessible')) {
        $(el).select2({ width: '100%', placeholder: 'اختر...', allowClear: true });
      }
    });
  }
})();

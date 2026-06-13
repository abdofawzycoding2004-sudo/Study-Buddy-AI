(function() {
  'use strict';

  function toggleVisibilityFields() {
    var cb = document.getElementById('id_is_public');
    var fields = document.getElementById('visibility-fields');
    if (cb && fields) {
      fields.style.display = cb.checked ? '' : 'none';
    }
  }

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
    var progressBar = document.getElementById('upload-progress');
    var progressBarInner = document.getElementById('upload-progress-bar');

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
      if (file.size > 100 * 1024 * 1024) {
        fileSizeWarning.style.display = 'inline';
      } else {
        fileSizeWarning.style.display = 'none';
      }
    }

    var form = document.getElementById('document-form');
    if (form) {
      form.addEventListener('submit', function(e) {
        if (fileInput.files.length && fileInput.files[0].size > 100 * 1024 * 1024) {
          e.preventDefault();
          alert('حجم الملف كبير جداً! الحد الأقصى 100 MB.');
        }
      });
    }
  });

  window.toggleVisibilityFields = toggleVisibilityFields;
})();

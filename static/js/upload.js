// Doc Translator - Upload JS

let selectedFile = null;

// Drag and drop handlers
const uploadArea = document.getElementById('upload-area');
if (uploadArea) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event => {
        uploadArea.addEventListener(event, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(event => {
        uploadArea.addEventListener(event, () => uploadArea.classList.add('drag-over'), false);
    });

    ['dragleave', 'drop'].forEach(event => {
        uploadArea.addEventListener(event, () => uploadArea.classList.remove('drag-over'), false);
    });

    uploadArea.addEventListener('drop', handleDrop, false);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDrop(e) {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(input) {
    if (input.files.length > 0) {
        handleFile(input.files[0]);
    }
}

function handleFile(file) {
    const allowedTypes = ['.txt', '.docx', '.pdf', '.xlsx', '.pptx', '.html', '.csv', '.md', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(ext)) {
        alert('Unsupported file format. Please upload: ' + allowedTypes.join(', '));
        return;
    }

    if (file.size > 50 * 1024 * 1024) {
        alert('File too large. Maximum size is 50MB.');
        return;
    }

    selectedFile = file;

    // Update UI
    document.getElementById('upload-placeholder').classList.add('hidden');
    document.getElementById('file-preview').classList.remove('hidden');
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-size').textContent = formatFileSize(file.size);
    document.getElementById('translation-options').classList.remove('hidden');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function clearFile() {
    selectedFile = null;
    document.getElementById('file-input').value = '';
    document.getElementById('upload-placeholder').classList.remove('hidden');
    document.getElementById('file-preview').classList.add('hidden');
    document.getElementById('translation-options').classList.add('hidden');
}

function startTranslation() {
    if (!selectedFile) {
        alert('Please select a file first.');
        return;
    }

    const sourceLang = document.getElementById('source-lang').value;
    const targetLang = document.getElementById('target-lang').value;
    const outputFormat = document.getElementById('output-format').value;
    const styleMode = document.getElementById('style-mode').value;
    const bilingual = document.getElementById('bilingual').checked;

    if (sourceLang === targetLang && sourceLang !== 'auto') {
        alert('Source and target languages must be different.');
        return;
    }

    // Show progress
    document.getElementById('translation-options').classList.add('hidden');
    document.getElementById('upload-area').classList.add('hidden');
    document.getElementById('progress-area').classList.remove('hidden');
    document.getElementById('progress-title').textContent = 'Uploading document...';
    document.getElementById('progress-bar').style.width = '10%';
    document.getElementById('progress-text').textContent = 'Uploading ' + selectedFile.name;

    // Create FormData
    const formData = new FormData();
    formData.append('source_file', selectedFile);
    formData.append('source_language', sourceLang);
    formData.append('target_language', targetLang);
    formData.append('target_format', outputFormat);
    formData.append('style_mode', styleMode);
    formData.append('bilingual', bilingual);

    // Upload
    fetch('/api/jobs/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken(),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.id) {
            document.getElementById('progress-bar').style.width = '30%';
            document.getElementById('progress-title').textContent = 'Translating...';
            document.getElementById('progress-text').textContent = 'This may take a few moments';
            pollJobStatus(data.id);
        } else {
            throw new Error('Failed to create job');
        }
    })
    .catch(error => {
        showError('Failed to upload file: ' + error.message);
    });
}

function pollJobStatus(jobId) {
    const pollInterval = setInterval(() => {
        fetch(`/api/jobs/${jobId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed') {
                    clearInterval(pollInterval);
                    showResult(jobId, data.output_file);
                } else if (data.status === 'failed') {
                    clearInterval(pollInterval);
                    showError(data.error_message || 'Translation failed');
                } else {
                    // Update progress
                    const progress = data.status === 'processing' ? '60%' : '40%';
                    document.getElementById('progress-bar').style.width = progress;
                }
            })
            .catch(error => {
                clearInterval(pollInterval);
                showError('Failed to check status');
            });
    }, 2000);
}

function showResult(jobId, outputUrl) {
    document.getElementById('progress-area').classList.add('hidden');
    document.getElementById('result-area').classList.remove('hidden');
    document.getElementById('download-btn').href = `/api/jobs/${jobId}/download/`;
}

function showError(message) {
    document.getElementById('progress-area').classList.add('hidden');
    document.getElementById('upload-area').classList.remove('hidden');
    document.getElementById('upload-placeholder').classList.remove('hidden');
    document.getElementById('file-preview').classList.add('hidden');
    document.getElementById('translation-options').classList.add('hidden');
    alert('Error: ' + message);
}

function resetForm() {
    selectedFile = null;
    document.getElementById('file-input').value = '';
    document.getElementById('result-area').classList.add('hidden');
    document.getElementById('progress-area').classList.add('hidden');
    document.getElementById('upload-area').classList.remove('hidden');
    document.getElementById('upload-placeholder').classList.remove('hidden');
    document.getElementById('file-preview').classList.add('hidden');
    document.getElementById('translation-options').classList.add('hidden');
}

function getCSRFToken() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

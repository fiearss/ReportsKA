function showUploadPasswordModal() {
    document.getElementById('uploadModal').style.display = "block";
    document.getElementById('uploadModalPassword').focus();
}

function closeUploadModal() {
    document.getElementById('uploadModal').style.display = "none";
}

function checkUploadPassword() {
    const password = document.getElementById('uploadModalPassword').value;
    if (password.length === 4) {
        document.getElementById('uploadPasswordInput').value = password;
        document.getElementById('uploadForm').submit();
        closeUploadModal();
    }
}

function showDeleteModal(filename) {
    document.getElementById('deleteModal').style.display = "block";
    document.getElementById('deleteModalPassword').focus();
    document.getElementById('deleteFilename').value = filename;
}

function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = "none";
}

function checkDeletePassword() {
    const password = document.getElementById('deleteModalPassword').value;
    const filename = document.getElementById('deleteFilename').value;
    if (password.length === 4) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/delete/${filename}`;
        
        const passwordInput = document.createElement('input');
        passwordInput.type = 'hidden';
        passwordInput.name = 'password';
        passwordInput.value = password;
        form.appendChild(passwordInput);

        document.body.appendChild(form);
        form.submit();
        closeDeleteModal();
    }
}

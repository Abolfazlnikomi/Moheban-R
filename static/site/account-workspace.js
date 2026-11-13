const workspace = document.getElementById('account-workspace');

if (workspace) {
    workspace.hidden = true;
    document.querySelectorAll('[data-workspace-link]').forEach((link) => {
        link.addEventListener('click', (event) => {
            if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
            workspace.hidden = false;
            workspace.querySelector('h2').focus();
        });
    });
}


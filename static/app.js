function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
}

function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    section.classList.toggle('collapsed');
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.querySelectorAll('.theme-option').forEach(opt => {
        opt.classList.toggle('active', opt.dataset.theme === theme);
    });
    localStorage.setItem('theme', theme);
}

function setFontSize(size) {
    document.documentElement.style.setProperty('--font-size', size + 'px');
    document.querySelector('.font-size-value').textContent = size + 'px';
    localStorage.setItem('fontSize', size);
}

function openFilePreview(filename) {
    document.getElementById('filePreviewPanel').classList.add('open');
}

function closeFilePreview() {
    document.getElementById('filePreviewPanel').classList.remove('open');
}

function openSubscriptionModal() {
    document.getElementById('subscriptionModal').classList.add('open');
}

function closeSubscriptionModal() {
    document.getElementById('subscriptionModal').classList.remove('open');
}

const sidebar = document.getElementById('sidebar');
const resizer = document.getElementById('sidebarResizer');
let isResizing = false;

resizer.addEventListener('mousedown', (e) => {
    isResizing = true;
    document.body.style.cursor = 'ew-resize';
});

document.addEventListener('mousemove', (e) => {
    if (!isResizing) return;
    const newWidth = e.clientX;
    if (newWidth >= 280 && newWidth <= 480) {
        sidebar.style.width = newWidth + 'px';
    }
});

document.addEventListener('mouseup', () => {
    isResizing = false;
    document.body.style.cursor = 'default';
});

const textarea = document.getElementById('messageInput');
textarea.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

const savedTheme = localStorage.getItem('theme');
if (savedTheme) setTheme(savedTheme);

const savedFontSize = localStorage.getItem('fontSize');
if (savedFontSize) {
    setFontSize(savedFontSize);
    document.querySelector('.font-size-slider').value = savedFontSize;
}

document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        toggleSidebar();
    }
    if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        textarea.focus();
    }
});

const portal = document.querySelector('.portal');
const drawer = document.getElementById('account-menu');
const drawerToggle = document.querySelector('[data-portal-open]');

if (portal && drawer && drawerToggle && typeof drawer.showModal === 'function') {
    const mobile = window.matchMedia('(max-width: 52rem)');
    portal.setAttribute('data-menu-ready', '');

    drawerToggle.addEventListener('click', () => {
        if (!mobile.matches || drawer.open) return;
        drawer.showModal();
        drawerToggle.setAttribute('aria-expanded', 'true');
    });
    drawer.addEventListener('close', () => drawerToggle.setAttribute('aria-expanded', 'false'));
    drawer.addEventListener('click', (event) => {
        if (event.target === drawer || event.target.closest('[data-portal-close]')) {
            drawer.close();
        } else if (event.target.closest('.portal-nav a[href^="#"]')) {
            drawer.close();
        }
    });
    mobile.addEventListener('change', () => {
        if (!mobile.matches && drawer.open) drawer.close();
    });
}

if (portal) {
    const links = portal.querySelectorAll('.portal-nav a[href^="#"]');
    const updateCurrentLink = () => {
        const current = window.location.hash || '#account-overview';
        links.forEach((link) => {
            if (link.hash === current) {
                link.setAttribute('aria-current', 'location');
            } else {
                link.removeAttribute('aria-current');
            }
        });
    };
    window.addEventListener('hashchange', updateCurrentLink);
    updateCurrentLink();
}

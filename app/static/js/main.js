/* IFRI_MentorLink — main.js */

/* ── Sidebar mobile avec overlay ── */
const sidebar       = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebar-toggle');

// Créer l'overlay dynamiquement
let overlay = document.querySelector('.sidebar-overlay');
if (!overlay && sidebar) {
  overlay = document.createElement('div');
  overlay.className = 'sidebar-overlay';
  document.body.appendChild(overlay);
  overlay.addEventListener('click', closeSidebar);
}

function openSidebar() {
  if (!sidebar) return;
  sidebar.classList.add('open');
  overlay && overlay.classList.add('show');
}
function closeSidebar() {
  if (!sidebar) return;
  sidebar.classList.remove('open');
  overlay && overlay.classList.remove('show');
}

if (sidebarToggle) {
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
  });
}

// Fermer la sidebar au clic sur un lien (mobile)
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', () => {
    if (window.innerWidth <= 768) closeSidebar();
  });
});


/* ── Notifications ── */
const notifBtn      = document.getElementById('notif-btn');
const notifDropdown = document.getElementById('notif-dropdown');
const notifCount    = document.getElementById('notif-count');
const notifList     = document.getElementById('notif-list');
const unreadBadge   = document.getElementById('unread-badge');

async function fetchNotifications() {
  try {
    const res  = await fetch('/messaging/api/notifications');
    const data = await res.json();

    if (notifCount) {
      notifCount.textContent = data.length;
      notifCount.style.display = data.length > 0 ? 'inline-flex' : 'none';
    }
    if (notifList) {
      notifList.innerHTML = data.length
        ? data.map(n => `
            <div style="padding:12px 16px;border-bottom:1px solid var(--border);font-size:.82rem;">
              <div>${n.content}</div>
              <div style="font-size:.7rem;color:var(--text-muted);margin-top:2px;">${n.time}</div>
            </div>`).join('')
        : '<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:.85rem;">Aucune notification</div>';
    }
    const msgN = data.filter(n => n.type === 'message').length;
    if (unreadBadge) {
      unreadBadge.textContent = msgN;
      unreadBadge.style.display = msgN > 0 ? 'inline-flex' : 'none';
    }
  } catch (e) {}
}

async function markNotifRead() {
  await fetch('/messaging/api/notifications/mark-read', { method: 'POST' });
  if (notifCount)  notifCount.style.display  = 'none';
  if (unreadBadge) unreadBadge.style.display = 'none';
  if (notifList)   notifList.innerHTML =
    '<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:.85rem;">Aucune notification</div>';
}

if (notifBtn) {
  notifBtn.addEventListener('click', e => {
    e.stopPropagation();
    const open = notifDropdown.style.display === 'block';
    notifDropdown.style.display = open ? 'none' : 'block';
    if (!open) fetchNotifications();
  });
  document.addEventListener('click', () => {
    if (notifDropdown) notifDropdown.style.display = 'none';
  });
  fetchNotifications();
  setInterval(fetchNotifications, 30000);
}


/* ── Auto-dismiss alerts ── */
setTimeout(() => {
  document.querySelectorAll('.alert').forEach(el => {
    el.style.transition = 'opacity .5s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 500);
  });
}, 5000);

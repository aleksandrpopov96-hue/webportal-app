(function() {
  const STORAGE_KEY = 'webportal_sites';
  const DEFAULT_SITES = [
    { name: 'Proxmox', url: 'https://www.proxmox.com', icon: 'P', category: 'Infrastructure' },
    { name: 'Portainer', url: 'http://localhost:9000', icon: 'D', category: 'Infrastructure' },
    { name: 'Grafana', url: 'http://localhost:3000', icon: 'G', category: 'Monitoring' },
    { name: 'YouTube', url: 'https://www.youtube.com', icon: '\u25B6', category: 'Media' },
    { name: 'Reddit', url: 'https://www.reddit.com', icon: 'R', category: 'Social' },
    { name: 'Wikipedia', url: 'https://www.wikipedia.org', icon: 'W', category: 'Reference' }
  ];

  let sites = loadSites();
  let activeIndex = -1;

  const siteList = document.getElementById('siteList');
  const siteFrame = document.getElementById('siteFrame');
  const welcome = document.getElementById('welcome');
  const toolbar = document.getElementById('toolbar');
  const toolbarTitle = document.getElementById('toolbarTitle');
  const openNewTab = document.getElementById('openNewTab');
  const searchInput = document.getElementById('searchInput');
  const manageBtn = document.getElementById('manageBtn');
  const manageModal = document.getElementById('manageModal');
  const closeModal = document.getElementById('closeModal');
  const addSiteForm = document.getElementById('addSiteForm');
  const savedList = document.getElementById('savedList');
  const toggleSidebar = document.getElementById('toggleSidebar');
  const sidebar = document.getElementById('sidebar');

  function proxyUrl(url) {
    return '/proxy/?url=' + encodeURIComponent(url);
  }

  function loadSites() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) return JSON.parse(stored);
    } catch(e) {}
    return [...DEFAULT_SITES];
  }

  function saveSites() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sites));
    } catch(e) {}
  }

  function renderSites(filter) {
    siteList.innerHTML = '';
    const f = (filter || '').toLowerCase();
    const filtered = sites.filter(s =>
      !f || s.name.toLowerCase().includes(f) || s.url.toLowerCase().includes(f) || (s.category || '').toLowerCase().includes(f)
    );

    const categories = {};
    filtered.forEach((site) => {
      const cat = site.category || 'Uncategorized';
      if (!categories[cat]) categories[cat] = [];
      categories[cat].push({ site, originalIndex: sites.indexOf(site) });
    });

    Object.keys(categories).sort().forEach(cat => {
      const header = document.createElement('li');
      header.className = 'category-header';
      header.textContent = cat;
      siteList.appendChild(header);

      categories[cat].forEach(({ site, originalIndex }) => {
        const li = document.createElement('li');
        li.className = 'site-item' + (originalIndex === activeIndex ? ' active' : '');
        li.innerHTML = `
          <div class="site-icon">${site.icon || site.name.charAt(0).toUpperCase()}</div>
          <div class="site-info">
            <div class="site-name">${escapeHtml(site.name)}</div>
            <div class="site-url">${escapeHtml(site.url)}</div>
          </div>
        `;
        li.addEventListener('click', () => loadSite(originalIndex));
        siteList.appendChild(li);
      });
    });
  }

  function renderSavedList() {
    savedList.innerHTML = '';
    sites.forEach((site, i) => {
      const li = document.createElement('li');
      li.className = 'saved-item';
      li.innerHTML = `
        <span>${escapeHtml(site.icon || '')} ${escapeHtml(site.name)} - ${escapeHtml(site.url)}</span>
        <div class="saved-actions">
          <button class="edit-btn" data-index="${i}">Edit</button>
          <button class="delete-btn" data-index="${i}">Delete</button>
        </div>
      `;
      savedList.appendChild(li);
    });

    savedList.querySelectorAll('.edit-btn').forEach(btn => {
      btn.addEventListener('click', () => editSite(parseInt(btn.dataset.index)));
    });

    savedList.querySelectorAll('.delete-btn').forEach(btn => {
      btn.addEventListener('click', () => deleteSite(parseInt(btn.dataset.index)));
    });
  }

  function loadSite(index) {
    const site = sites[index];
    if (!site) return;
    activeIndex = index;

    welcome.style.display = 'none';
    toolbar.style.display = 'flex';
    toolbarTitle.textContent = site.name;
    openNewTab.href = site.url;

    siteFrame.style.display = 'block';
    siteFrame.src = proxyUrl(site.url);

    renderSites(searchInput.value);
  }

  function editSite(index) {
    const site = sites[index];
    document.getElementById('editIndex').value = index;
    document.getElementById('siteName').value = site.name;
    document.getElementById('siteUrl').value = site.url;
    document.getElementById('siteIcon').value = site.icon || '';
    document.getElementById('siteCategory').value = site.category || '';
    document.getElementById('saveBtn').textContent = 'Update Site';
  }

  function deleteSite(index) {
    if (!confirm('Delete "' + sites[index].name + '"?')) return;
    sites.splice(index, 1);
    saveSites();
    if (activeIndex === index) {
      activeIndex = -1;
      siteFrame.style.display = 'none';
      toolbar.style.display = 'none';
      welcome.style.display = 'block';
    } else if (activeIndex > index) {
      activeIndex--;
    }
    renderSites(searchInput.value);
    renderSavedList();
  }

  function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }

  searchInput.addEventListener('input', () => renderSites(searchInput.value));

  toggleSidebar.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
  });

  manageBtn.addEventListener('click', () => {
    renderSavedList();
    manageModal.style.display = 'flex';
  });

  closeModal.addEventListener('click', () => {
    manageModal.style.display = 'none';
    addSiteForm.reset();
    document.getElementById('editIndex').value = -1;
    document.getElementById('saveBtn').textContent = 'Add Site';
  });

  manageModal.addEventListener('click', (e) => {
    if (e.target === manageModal) {
      manageModal.style.display = 'none';
    }
  });

  addSiteForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const editIdx = parseInt(document.getElementById('editIndex').value);
    const newSite = {
      name: document.getElementById('siteName').value.trim(),
      url: document.getElementById('siteUrl').value.trim(),
      icon: document.getElementById('siteIcon').value.trim() || document.getElementById('siteName').value.trim().charAt(0).toUpperCase(),
      category: document.getElementById('siteCategory').value.trim() || 'Uncategorized'
    };

    if (!newSite.url.startsWith('http://') && !newSite.url.startsWith('https://')) {
      newSite.url = 'https://' + newSite.url;
    }

    if (editIdx >= 0) {
      sites[editIdx] = newSite;
    } else {
      sites.push(newSite);
    }

    saveSites();
    renderSites(searchInput.value);
    renderSavedList();
    addSiteForm.reset();
    document.getElementById('editIndex').value = -1;
    document.getElementById('saveBtn').textContent = 'Add Site';
  });

  fetch('/config/sites.json')
    .then(r => r.json())
    .then(configSites => {
      if (configSites && configSites.length > 0) {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (!stored) {
          sites = configSites;
          saveSites();
        }
      }
    })
    .catch(() => {});

  renderSites();
})();

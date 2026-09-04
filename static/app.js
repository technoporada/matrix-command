let map = null;
let mapMarker = null;

function showTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

    document.getElementById(`tab-${tabName}`).classList.add('active');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    if (tabName === 'dashboard') loadDashboard();
    if (tabName === 'games') loadGames();
}

async function api(url) {
    try {
        const resp = await fetch(url);
        return await resp.json();
    } catch (e) {
        return { error: e.message };
    }
}

function formatJSON(data, indent = 0) {
    if (typeof data === 'string') return data;
    return JSON.stringify(data, null, 2);
}

function showResult(elementId, data) {
    document.getElementById(elementId).innerHTML = `<pre>${formatJSON(data)}</pre>`;
}

function showLoading(elementId) {
    document.getElementById(elementId).innerHTML = '<div class="loading">Loading...</div>';
}

async function loadDashboard() {
    const stats = await api('/api/stats');
    const snapshot = await api('/api/system/snapshot');

    let statsHTML = `
        <div class="stat-card">
            <div class="value">${stats.total_scans || 0}</div>
            <div class="label">Total Scans</div>
        </div>
        <div class="stat-card">
            <div class="value">${stats.active_games || 0}</div>
            <div class="label">Free Games</div>
        </div>
        <div class="stat-card">
            <div class="value">${stats.privacy_events || 0}</div>
            <div class="label">Privacy Events</div>
        </div>
        <div class="stat-card">
            <div class="value">${snapshot.system?.hostname || 'Unknown'}</div>
            <div class="label">Hostname</div>
        </div>
    `;
    document.getElementById('stats-grid').innerHTML = statsHTML;

    let sysHTML = `
        <div class="section-title">System</div>
        <div>CPU: ${snapshot.cpu?.percent}% (${snapshot.cpu?.cores} cores)</div>
        <div class="progress-bar"><div class="fill ${getBarClass(snapshot.cpu?.percent)}" style="width: ${snapshot.cpu?.percent}%"></div></div>
        <div>Memory: ${snapshot.memory?.used_gb}GB / ${snapshot.memory?.total_gb}GB (${snapshot.memory?.percent}%)</div>
        <div class="progress-bar"><div class="fill ${getBarClass(snapshot.memory?.percent)}" style="width: ${snapshot.memory?.percent}%"></div></div>
        <div>Disk: ${snapshot.disk?.used_gb}GB / ${snapshot.disk?.total_gb}GB (${snapshot.disk?.percent}%)</div>
        <div class="progress-bar"><div class="fill ${getBarClass(snapshot.disk?.percent)}" style="width: ${snapshot.disk?.percent}%"></div></div>
        <div class="section-title">Network</div>
        <div>Sent: ${snapshot.network?.sent_mb}MB | Received: ${snapshot.network?.recv_mb}MB</div>
        <div>Active connections: ${snapshot.connections?.length || 0}</div>
        <div class="section-title">Top Processes</div>
        <table style="width:100%;border-collapse:collapse;">
            <tr style="border-bottom:1px solid var(--border);text-align:left;">
                <th style="padding:5px;">PID</th><th>Name</th><th>CPU%</th><th>MEM%</th>
            </tr>
            ${(snapshot.top_processes || []).map(p => `
                <tr style="border-bottom:1px solid var(--border);">
                    <td style="padding:5px;">${p.pid}</td><td>${p.name}</td><td>${p.cpu}</td><td>${p.mem}</td>
                </tr>
            `).join('')}
        </table>
    `;
    document.getElementById('system-panel').innerHTML = sysHTML;
}

function getBarClass(percent) {
    if (percent > 80) return 'danger';
    if (percent > 60) return 'warning';
    return '';
}

async function runFullRecon() {
    const target = document.getElementById('network-target').value.trim();
    if (!target) return alert('Enter a target');
    showLoading('network-results');
    const data = await api(`/api/network/full-recon?target=${encodeURIComponent(target)}`);
    renderFullRecon(data);
}

function renderFullRecon(data) {
    if (data.error) {
        document.getElementById('network-results').innerHTML = `<div class="error">${data.error}</div>`;
        return;
    }

    let html = `<div class="section-title">Full Recon: ${data.target} (${data.duration_ms}ms)</div>`;

    if (data.scans?.port_scan) {
        const ps = data.scans.port_scan;
        html += `<div class="section-title">Port Scan (${ps.stats?.open} open)</div>`;
        html += `<div>Open: ${(ps.open || []).map(p => `<span class="port-open">${p}</span>`).join(', ') || 'None'}</div>`;
        html += `<div>Filtered: ${(ps.filtered || []).map(p => `<span class="port-filtered">${p}</span>`).join(', ') || 'None'}</div>`;
    }

    if (data.scans?.dns) {
        const dns = data.scans.dns;
        html += `<div class="section-title">DNS</div>`;
        for (const [rtype, records] of Object.entries(dns.records || {})) {
            if (records.length > 0) {
                html += `<div>${rtype}: ${records.join(', ')}</div>`;
            }
        }
    }

    if (data.scans?.ssl) {
        const ssl = data.scans.ssl;
        html += `<div class="section-title">SSL</div>`;
        html += `<div>Valid: ${ssl.valid ? 'Yes' : 'No'}</div>`;
    }

    if (data.scans?.geoip) {
        const geo = data.scans.geoip;
        html += `<div class="section-title">GeoIP</div>`;
        html += `<div>${geo.city || ''}, ${geo.region || ''}, ${geo.country || ''}</div>`;
        html += `<div>ISP: ${geo.isp || 'Unknown'}</div>`;
        html += `<div>Org: ${geo.org || 'Unknown'}</div>`;

        if (geo.lat && geo.lon) {
            showMap(geo.lat, geo.lon, geo.city || data.target);
        }
    }

    if (data.scans?.web) {
        const web = data.scans.web;
        html += `<div class="section-title">Web</div>`;
        html += `<div>Title: ${web.title || 'N/A'}</div>`;
        html += `<div>Technologies: ${(web.technologies || []).map(t => `<span class="tech-badge">${t.name} <span class="category">${t.category}</span></span>`).join(' ')}</div>`;
        html += `<div>Emails: ${(web.emails || []).join(', ') || 'None'}</div>`;
    }

    document.getElementById('network-results').innerHTML = html;
}

async function runPortScan() {
    const target = document.getElementById('network-target').value.trim();
    if (!target) return alert('Enter a target');
    showLoading('network-results');
    const data = await api(`/api/network/port-scan?target=${encodeURIComponent(target)}`);
    let html = `<div class="section-title">Port Scan: ${target}</div>`;
    html += `<div>Open: ${(data.open || []).map(p => `<span class="port-open">${p}</span>`).join(', ') || 'None'}</div>`;
    html += `<div>Closed: ${(data.closed || []).map(p => `<span class="port-closed">${p}</span>`).join(', ') || 'None'}</div>`;
    html += `<div>Filtered: ${(data.filtered || []).map(p => `<span class="port-filtered">${p}</span>`).join(', ') || 'None'}</div>`;
    document.getElementById('network-results').innerHTML = html;
}

async function runWhois() {
    const target = document.getElementById('network-target').value.trim();
    if (!target) return alert('Enter a domain');
    showLoading('network-results');
    const data = await api(`/api/network/whois?target=${encodeURIComponent(target)}`);
    document.getElementById('network-results').innerHTML = `<pre>${formatJSON(data)}</pre>`;
}

async function runGeoIP() {
    const target = document.getElementById('network-target').value.trim();
    if (!target) return alert('Enter an IP');
    showLoading('network-results');
    const data = await api(`/api/network/geoip?ip=${encodeURIComponent(target)}`);
    document.getElementById('network-results').innerHTML = `<pre>${formatJSON(data)}</pre>`;
    if (data.lat && data.lon) showMap(data.lat, data.lon, data.city || target);
}

async function runDNS() {
    const target = document.getElementById('network-target').value.trim();
    if (!target) return alert('Enter a domain');
    showLoading('network-results');
    const data = await api(`/api/network/dns?domain=${encodeURIComponent(target)}`);
    document.getElementById('network-results').innerHTML = `<pre>${formatJSON(data)}</pre>`;
}

function showMap(lat, lon, label) {
    const mapEl = document.getElementById('map');
    mapEl.classList.add('visible');

    if (!map) {
        map = L.map('map').setView([lat, lon], 10);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        }).addTo(map);
    } else {
        map.setView([lat, lon], 10);
    }

    if (mapMarker) map.removeLayer(mapMarker);
    mapMarker = L.marker([lat, lon]).addTo(map).bindPopup(label).openPopup();
}

async function runPrivacyScan() {
    const url = document.getElementById('privacy-url').value.trim();
    if (!url) return alert('Enter a URL');
    showLoading('privacy-results');
    const data = await api(`/api/privacy/scan?url=${encodeURIComponent(url)}`);
    renderPrivacy(data);
}

function renderPrivacy(data) {
    if (data.error) {
        document.getElementById('privacy-results').innerHTML = `<div class="error">${data.error}</div>`;
        return;
    }

    let scoreClass = 'score-excellent';
    if (data.privacy_score < 50) scoreClass = 'score-bad';
    else if (data.privacy_score < 70) scoreClass = 'score-poor';
    else if (data.privacy_score < 90) scoreClass = 'score-good';

    let html = `
        <div class="section-title">Privacy Scan: ${data.url}</div>
        <div>Privacy Score: <span class="${scoreClass}" style="font-size:1.5em;">${data.privacy_score}/100</span></div>
    `;

    if (data.trackers?.length > 0) {
        html += `<div class="section-title">Trackers (${data.trackers.length})</div>`;
        data.trackers.forEach(t => {
            html += `<div class="tracker-item">
                <span>${t.domain} (${t.category})</span>
                <span class="tracker-risk-${t.risk}">${t.risk}</span>
            </div>`;
        });
    }

    if (data.security_headers) {
        html += `<div class="section-title">Security Headers</div>`;
        for (const [name, info] of Object.entries(data.security_headers)) {
            const cls = info.present ? 'header-present' : 'header-missing';
            const status = info.present ? 'Present' : `Missing (severity: ${info.severity})`;
            html += `<div class="${cls}">${name}: ${status}</div>`;
        }
    }

    if (data.recommendations?.length > 0) {
        html += `<div class="section-title">Recommendations</div>`;
        data.recommendations.forEach(r => {
            html += `<div>- ${r}</div>`;
        });
    }

    document.getElementById('privacy-results').innerHTML = html;
}

async function loadGames() {
    showLoading('games-list');
    const data = await api('/api/games/free');
    renderGames(data);
}

async function refreshGames() {
    showLoading('games-list');
    const data = await api('/api/games/free?refresh=true');
    renderGames(data);
}

function renderGames(games) {
    if (games.error) {
        document.getElementById('games-list').innerHTML = `<div class="error">${games.error}</div>`;
        return;
    }

    if (!Array.isArray(games) || games.length === 0) {
        document.getElementById('games-list').innerHTML = '<div class="loading">No free games found</div>';
        return;
    }

    let html = '';
    games.forEach(g => {
        html += `
            <div class="game-card">
                <div class="title"><a href="${g.url}" target="_blank">${g.title}</a></div>
                <div class="meta">
                    <span class="source">${g.source}</span>
                    <span>${g.platform || 'Unknown'}</span>
                </div>
            </div>
        `;
    });
    document.getElementById('games-list').innerHTML = html;
}

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});

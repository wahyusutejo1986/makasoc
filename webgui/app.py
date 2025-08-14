# Minimal Flask app for web GUI and deployment

# --- Flask Docker Management GUI ---
from flask import Flask, render_template_string, jsonify, request
import subprocess
import os

app = Flask(__name__)


HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MakaraSOC Docker GUI</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', Arial, sans-serif;
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            color: #E2E8F0;
            margin: 0;
            min-height: 100vh;
        }
        .sidebar {
            width: 220px;
            background: rgba(15, 23, 42, 0.98);
            color: #CBD5E1;
            height: 100vh;
            position: fixed;
            top: 0;
            left: 0;
            padding-top: 32px;
            border-right: 1px solid #334155;
            box-shadow: 2px 0 16px 0 rgba(16,24,40,0.08);
            z-index: 10;
        }
        .sidebar h2 {
            color: #3B82F6;
            text-align: center;
            font-size: 1.6rem;
            font-weight: 700;
            margin-bottom: 2rem;
            letter-spacing: 0.02em;
        }
        .sidebar ul {
            list-style: none;
            padding: 0;
        }
        .sidebar li {
            padding: 1rem 2rem;
            margin: 0.5rem 0;
            border-radius: 8px 0 0 8px;
            color: #CBD5E1;
            font-weight: 500;
            font-size: 1.05rem;
            cursor: pointer;
            transition: background 0.2s, color 0.2s;
        }
        .sidebar li:hover, .sidebar .active {
            background: linear-gradient(90deg, #3B82F6 0%, #1E293B 100%);
            color: #fff;
        }
        .main {
            margin-left: 220px;
            padding: 48px 40px 40px 40px;
            max-width: 1400px;
        }
        .card {
            background: rgba(30, 41, 59, 0.85);
            border: 1px solid #334155;
            border-radius: 16px;
            box-shadow: 0 4px 24px 0 rgba(59,130,246,0.08);
            padding: 2rem;
            margin-bottom: 2.5rem;
            transition: box-shadow 0.2s, border 0.2s;
        }
        .card:hover {
            border-color: #3B82F6;
            box-shadow: 0 8px 32px 0 rgba(59,130,246,0.12);
        }
        h3 {
            color: #F1F5F9;
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 1.2rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: rgba(30, 41, 59, 0.8);
            border-radius: 8px;
            overflow: hidden;
        }
        th {
            background: rgba(51, 65, 85, 0.8);
            color: #F1F5F9;
            font-weight: 600;
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid #475569;
        }
        td {
            padding: 1rem;
            color: #CBD5E1;
            border-bottom: 1px solid #334155;
        }
        tr:hover {
            background: rgba(59, 130, 246, 0.05);
        }
        button {
            padding: 0.5rem 1.2rem;
            font-size: 1rem;
            border-radius: 8px;
            border: none;
            background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
            color: #fff;
            font-weight: 500;
            cursor: pointer;
            margin-right: 0.5rem;
            transition: background 0.2s, box-shadow 0.2s;
            box-shadow: 0 2px 8px rgba(59,130,246,0.08);
        }
        button:disabled {
            background: #475569;
            color: #94A3B8;
            cursor: not-allowed;
        }
        .status-running {
            color: #10B981;
            font-weight: bold;
        }
        .status-exited {
            color: #EF4444;
            font-weight: bold;
        }
        pre {
            background: #0F172A;
            color: #10B981;
            padding: 1rem;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 1rem;
            margin-top: 1rem;
            overflow-x: auto;
        }
        ul#platformsList {
            list-style: none;
            padding: 0;
        }
        ul#platformsList li {
            background: rgba(51, 65, 85, 0.5);
            border: 1px solid #475569;
            border-radius: 8px;
            padding: 1rem 1.5rem;
            margin-bottom: 0.7rem;
            color: #F1F5F9;
            font-weight: 500;
            font-size: 1.1rem;
            transition: border 0.2s, background 0.2s;
        }
        ul#platformsList li:hover {
            border-color: #3B82F6;
            background: rgba(59, 130, 246, 0.08);
        }
        @media (max-width: 900px) {
            .main { padding: 24px 8px 8px 8px; }
            .sidebar { width: 100px; }
            .main { margin-left: 100px; }
        }
        @media (max-width: 600px) {
            .sidebar { display: none; }
            .main { margin-left: 0; padding: 8px; }
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>MakaraSOC</h2>
        <ul>
            <li class="active" onclick="showTab('dashboard')">Dashboard</li>
            <li onclick="showTab('containers')">Containers</li>
            <li onclick="showTab('images')">Images</li>
            <li onclick="showTab('platforms')">Platforms</li>
            <li onclick="showTab('deploy')">Deploy</li>
        </ul>
    </div>
    <div class="main">
        <div id="dashboard" class="tab card">
            <h3>System Info</h3>
            <pre id="sysinfo"></pre>
        </div>
        <div id="containers" class="tab card" style="display:none">
            <h3>Docker Containers</h3>
            <table id="containersTable">
                <thead><tr><th>Name</th><th>Image</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody></tbody>
            </table>
        </div>
        <div id="images" class="tab card" style="display:none">
            <h3>Docker Images</h3>
            <table id="imagesTable">
                <thead><tr><th>Repository</th><th>Tag</th><th>Image ID</th><th>Size</th></tr></thead>
                <tbody></tbody>
            </table>
        </div>
        <div id="platforms" class="tab card" style="display:none">
            <h3>Platforms (Modules)</h3>
            <div id="platformsGrid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.5rem;"></div>
            <div id="platformDetailModal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(15,23,42,0.85); z-index:100; align-items:center; justify-content:center;">
                <div style="background:rgba(30,41,59,0.98); border-radius:16px; max-width:500px; width:90vw; padding:2rem; box-shadow:0 8px 32px #000; position:relative;">
                    <button onclick="closePlatformDetail()" style="position:absolute; top:1rem; right:1rem; background:#EF4444; color:#fff; border:none; border-radius:6px; padding:0.3rem 0.8rem; font-size:1.1rem;">&times;</button>
                    <div id="platformDetailContent"></div>
                </div>
            </div>
        </div>
        <div id="deploy" class="tab card" style="display:none">
            <h3>Deploy MakaraSOC</h3>
            <button id="deployBtn">Run Deployment</button>
            <pre id="output"></pre>
        </div>
    </div>
    <script>
        function showTab(tab) {
            document.querySelectorAll('.tab').forEach(e => e.style.display = 'none');
            document.getElementById(tab).style.display = '';
            document.querySelectorAll('.sidebar li').forEach(e => e.classList.remove('active'));
            let idx = {dashboard:0, containers:1, images:2, platforms:3, deploy:4}[tab];
            document.querySelectorAll('.sidebar li')[idx].classList.add('active');
            if(tab==='dashboard') loadSysInfo();
            if(tab==='containers') loadContainers();
            if(tab==='images') loadImages();
            if(tab==='platforms') loadPlatforms();
        }
        // --- Dashboard ---
        function loadSysInfo() {
            fetch('/api/sysinfo').then(r=>r.json()).then(d=>{
                document.getElementById('sysinfo').textContent = d.info;
            });
        }
        // --- Containers ---
        function loadContainers() {
            fetch('/api/containers').then(r=>r.json()).then(d=>{
                let tbody = document.querySelector('#containersTable tbody');
                tbody.innerHTML = '';
                d.containers.forEach(c => {
                    let statusClass = c.status.includes('Up') ? 'status-running' : 'status-exited';
                    tbody.innerHTML += `<tr><td>${c.names}</td><td>${c.image}</td><td class="${statusClass}">${c.status}</td><td>
                        <button onclick="containerAction('${c.id}','start')" ${c.status.includes('Up')?'disabled':''}>Start</button>
                        <button onclick="containerAction('${c.id}','stop')" ${!c.status.includes('Up')?'disabled':''}>Stop</button>
                        <button onclick="containerAction('${c.id}','restart')">Restart</button>
                        <button onclick="containerAction('${c.id}','remove')">Remove</button>
                        <button onclick="viewLogs('${c.id}')">Logs</button>
                    </td></tr>`;
                });
            });
        }
        function containerAction(id, action) {
            fetch(`/api/container/${id}/${action}`, {method:'POST'}).then(()=>loadContainers());
        }
        function viewLogs(id) {
            fetch(`/api/container/${id}/logs`).then(r=>r.json()).then(d=>{
                alert(d.logs);
            });
        }
        // --- Images ---
        function loadImages() {
            fetch('/api/images').then(r=>r.json()).then(d=>{
                let tbody = document.querySelector('#imagesTable tbody');
                tbody.innerHTML = '';
                d.images.forEach(i => {
                    tbody.innerHTML += `<tr><td>${i.repository}</td><td>${i.tag}</td><td>${i.id}</td><td>${i.size}</td></tr>`;
                });
            });
        }
        // --- Platforms ---
        // Utility: safe ID for element
        function safeId(text) {
            return text.replace(/[^a-zA-Z0-9_-]/g, '_');
        }
        function loadPlatforms() {
            fetch('/api/platforms').then(r=>r.json()).then(d=>{
                let grid = document.getElementById('platformsGrid');
                grid.innerHTML = '';
                d.platforms.forEach(p => {
                    const id = safeId(p);
                    const encodedP = encodeURIComponent(p);
                    const isSOC = p.toLowerCase().includes('grafana') || p.toLowerCase().includes('web') || p.toLowerCase().includes('misp') || p.toLowerCase().includes('opencti') || p.toLowerCase().includes('shuffle') || p.toLowerCase().includes('wazuh') || p.toLowerCase().includes('yara');
                    
                    const cardDiv = document.createElement('div');
                    cardDiv.className = 'platform-card';
                    cardDiv.style.cssText = 'background:rgba(51,65,85,0.5); border:1px solid #475569; border-radius:12px; padding:1.5rem; color:#F1F5F9; font-weight:500; font-size:1.1rem; cursor:pointer; transition:box-shadow 0.2s, border 0.2s; box-shadow:0 2px 8px rgba(59,130,246,0.08);';
                    cardDiv.onclick = function() { showPlatformDetail(encodedP); };
                    
                    cardDiv.innerHTML = `
                        <div class="platform-title" style="font-size:1.3rem; font-weight:600; color:#3B82F6; margin-bottom:0.5rem;"></div>
                        <div id="desc-${id}" style="color:#94A3B8; font-size:0.95rem; min-height:2.5em;"></div>
                        <div style="margin-top:0.7rem;">
                            <span style="background:#10B981; color:#fff; border-radius:6px; padding:0.2rem 0.7rem; font-size:0.85rem; display:${isSOC?'inline-block':'none'};">SOC</span>
                        </div>`;
                    
                    // Safely set the platform name using textContent
                    cardDiv.querySelector('.platform-title').textContent = p;
                    
                    grid.appendChild(cardDiv);
                });
                // Fetch short descriptions for each card
                d.platforms.forEach(p => {
                    const id = safeId(p);
                    fetch('/api/platforms/' + encodeURIComponent(p)).then(r=>r.json()).then(info=>{
                        let desc = info.description ? info.description.split('\n')[0] : '';
                        const descEl = document.getElementById('desc-'+id);
                        if(descEl) descEl.textContent = desc;
                    });
                });
            });
        }

        function showPlatformDetail(platform) {
            const decoded = decodeURIComponent(platform);
            fetch(`/api/platforms/${decoded}`).then(r=>r.json()).then(info=>{
                let html = `<h2 style='color:#3B82F6; font-size:1.4rem; font-weight:700; margin-bottom:0.7rem;'>${info.platform}</h2>`;
                if(info.description) html += `<div style='color:#94A3B8; margin-bottom:1rem; white-space:pre-line;'>${info.description}</div>`;
                html += `<div style='margin-bottom:1rem;'><b>Files:</b><ul style='margin:0.5rem 0 0 1.2rem; color:#CBD5E1;'>`;
                info.files.forEach(f=>{
                    html += `<li>${f}</li>`;
                });
                html += `</ul></div>`;
                html += `<div style='margin-bottom:1rem;'><b>Docker Compose:</b> <span style='color:${info.docker_compose?'#10B981':'#EF4444'}; font-weight:600;'>${info.docker_compose?'Yes':'No'}</span></div>`;
                document.getElementById('platformDetailContent').innerHTML = html;
                document.getElementById('platformDetailModal').style.display = 'flex';
            });
        }
        function closePlatformDetail() {
            document.getElementById('platformDetailModal').style.display = 'none';
        }
        // --- Deploy ---
        document.getElementById('deployBtn').onclick = function() {
            this.disabled = true;
            document.getElementById('output').textContent = 'Running...';
            fetch('/deploy', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    document.getElementById('output').textContent = data.output;
                    document.getElementById('deployBtn').disabled = false;
                })
                .catch(e => {
                    document.getElementById('output').textContent = 'Error: ' + e;
                    document.getElementById('deployBtn').disabled = false;
                });
        };
        // Initial load - detect current path
        const path = window.location.pathname.replace('/', '') || 'dashboard';
        showTab(path);
    </script>
</body>
</html>
'''

# --- API Endpoints ---
def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.stdout
    except Exception as e:
        return f'Error: {e}'


# --- Platforms API ---

# Enhanced: List platforms and provide details for each
@app.route('/api/platforms')
def platforms():
    modules_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules'))
    try:
        platforms = [name for name in os.listdir(modules_dir)
                    if os.path.isdir(os.path.join(modules_dir, name))]
    except Exception as e:
        platforms = [f'Error: {e}']
    return jsonify({'platforms': platforms})

@app.route('/api/platforms/<platform>')
def platform_details(platform):
    import glob
    import json
    modules_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules'))
    platform_dir = os.path.join(modules_dir, platform)
    if not os.path.isdir(platform_dir):
        return jsonify({'error': 'Not found'}), 404
    files = os.listdir(platform_dir)
    docker_compose = any(f.startswith('docker-compose') and f.endswith(('.yml', '.yaml')) for f in files)
    description = ''
    # Try to read a README or AUTHORS or description file
    for desc_file in ['README.md', 'AUTHORS.txt', 'description.txt']:
        desc_path = os.path.join(platform_dir, desc_file)
        if os.path.isfile(desc_path):
            with open(desc_path, encoding='utf-8', errors='ignore') as f:
                description = f.read(500)
            break
    return jsonify({
        'platform': platform,
        'files': files,
        'docker_compose': docker_compose,
        'description': description
    })

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/dashboard')
def dashboard():
    return render_template_string(HTML)

@app.route('/containers')
def containers_page():
    return render_template_string(HTML)

@app.route('/images')
def images_page():
    return render_template_string(HTML)

@app.route('/platforms')
def platforms_page():
    return render_template_string(HTML)

@app.route('/deploy')
def deploy_page():
    return render_template_string(HTML)

@app.route('/api/sysinfo')
def sysinfo():
    info = run_cmd(['docker', 'info'])
    return jsonify({'info': info})

@app.route('/api/containers')
def containers():
    out = run_cmd(['docker', 'ps', '-a', '--format', '{{json .}}'])
    containers = []
    for line in out.strip().split('\n'):
        if line:
            import json
            d = json.loads(line)
            containers.append({
                'id': d.get('ID'),
                'names': d.get('Names'),
                'image': d.get('Image'),
                'status': d.get('Status')
            })
    return jsonify({'containers': containers})

@app.route('/api/container/<cid>/<action>', methods=['POST'])
def container_action(cid, action):
    if action not in ['start','stop','restart','remove']:
        return '', 400
    cmd = ['docker', action, cid]
    run_cmd(cmd)
    return '', 204

@app.route('/api/container/<cid>/logs')
def container_logs(cid):
    logs = run_cmd(['docker', 'logs', '--tail', '100', cid])
    return jsonify({'logs': logs})

@app.route('/api/images')
def images():
    out = run_cmd(['docker', 'images', '--format', '{{json .}}'])
    images = []
    for line in out.strip().split('\n'):
        if line:
            import json
            d = json.loads(line)
            images.append({
                'repository': d.get('Repository'),
                'tag': d.get('Tag'),
                'id': d.get('ID'),
                'size': d.get('Size')
            })
    return jsonify({'images': images})

@app.route('/deploy', methods=['POST'])
def deploy():
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'main.sh'))
    try:
        result = subprocess.run(['bash', script_path], capture_output=True, text=True, timeout=600)
        output = result.stdout + '\n' + result.stderr
    except Exception as e:
        output = f'Error: {e}'
    return jsonify({'output': output})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

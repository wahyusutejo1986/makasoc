import http.server
import socketserver
import json
import subprocess
import os
import urllib.parse
import shutil
from pathlib import Path

PORT = 5000
WEB_DIR = Path(__file__).parent

class MakaraSOCHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
            return super().do_GET()
        elif self.path.startswith('/api/'):
            self.handle_api_get()
        else:
            return super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/') or self.path == '/deploy':
            self.handle_api_post()
        else:
            self.send_error(404)

    def handle_api_get(self):
        try:
            if self.path == '/api/sysinfo':
                result = subprocess.run(['docker', 'system', 'info'], capture_output=True, text=True)
                self.send_json_response({'info': result.stdout})
            
            elif self.path == '/api/containers':
                result = subprocess.run(['docker', 'ps', '-a', '--format', 'table {{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}'], 
                                      capture_output=True, text=True)
                containers = []
                for line in result.stdout.split('\n')[1:]:  # Skip header
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 4:
                            containers.append({
                                'id': parts[0],
                                'image': parts[1],
                                'names': parts[2],
                                'status': parts[3]
                            })
                self.send_json_response({'containers': containers})
            
            elif self.path == '/api/images':
                result = subprocess.run(['docker', 'images', '--format', 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}'], 
                                      capture_output=True, text=True)
                images = []
                for line in result.stdout.split('\n')[1:]:  # Skip header
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 4:
                            images.append({
                                'repository': parts[0],
                                'tag': parts[1],
                                'id': parts[2],
                                'size': parts[3]
                            })
                self.send_json_response({'images': images})
            
            elif self.path == '/api/platforms':
                modules_dir = WEB_DIR.parent / 'modules'
                platforms = []
                if modules_dir.exists():
                    for item in modules_dir.iterdir():
                        if item.is_dir():
                            platforms.append(item.name)
                self.send_json_response({'platforms': platforms})
            
            elif self.path.startswith('/api/platforms/'):
                platform_name = urllib.parse.unquote(self.path.split('/')[-1])
                platform_dir = WEB_DIR.parent / 'modules' / platform_name
                
                info = {
                    'platform': platform_name,
                    'description': '',
                    'files': [],
                    'docker_compose': False
                }
                
                if platform_dir.exists():
                    # Get files
                    info['files'] = [f.name for f in platform_dir.iterdir()]
                    
                    # Check for docker-compose
                    info['docker_compose'] = any(f.name.startswith('docker-compose') for f in platform_dir.iterdir())
                    
                    # Try to get description from README or script files
                    readme_files = [f for f in platform_dir.iterdir() if 'readme' in f.name.lower()]
                    if readme_files:
                        try:
                            with open(readme_files[0], 'r', encoding='utf-8') as f:
                                info['description'] = f.read()[:500] + '...' if len(f.read()) > 500 else f.read()
                        except:
                            pass
                    
                    if not info['description']:
                        # Generate basic description
                        if 'grafana' in platform_name.lower():
                            info['description'] = 'Grafana monitoring and visualization platform for SOC operations'
                        elif 'iris' in platform_name.lower():
                            info['description'] = 'IRIS incident response platform module'
                        elif 'misp' in platform_name.lower():
                            info['description'] = 'MISP threat intelligence platform'
                        elif 'opencti' in platform_name.lower():
                            info['description'] = 'OpenCTI cyber threat intelligence platform'
                        elif 'shuffle' in platform_name.lower():
                            info['description'] = 'Shuffle SOAR automation platform'
                        elif 'velociraptor' in platform_name.lower():
                            info['description'] = 'Velociraptor endpoint monitoring and response'
                        elif 'wazuh' in platform_name.lower():
                            info['description'] = 'Wazuh security monitoring platform'
                        elif 'yara' in platform_name.lower():
                            info['description'] = 'YARA malware identification and classification'
                        else:
                            info['description'] = f'SOC platform module: {platform_name}'
                
                self.send_json_response(info)
            
            elif self.path.startswith('/api/container/') and self.path.endswith('/logs'):
                container_id = self.path.split('/')[-2]
                result = subprocess.run(['docker', 'logs', '--tail', '50', container_id], 
                                      capture_output=True, text=True)
                self.send_json_response({'logs': result.stdout + result.stderr})
            
            elif self.path.startswith('/api/files'):
                self.handle_file_api()
            
            else:
                self.send_error(404)
                
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

    def handle_api_post(self):
        try:
            if self.path.startswith('/api/container/'):
                parts = self.path.split('/')
                if len(parts) >= 5:
                    container_id = parts[3]
                    action = parts[4]
                    
                    if action in ['start', 'stop', 'restart', 'remove']:
                        result = subprocess.run(['docker', action, container_id], 
                                              capture_output=True, text=True)
                        self.send_json_response({'success': result.returncode == 0, 'output': result.stdout})
                    else:
                        self.send_error(400)
                else:
                    self.send_error(400)
            
            elif self.path == '/deploy':
                # Run the main deployment script
                script_path = WEB_DIR.parent / 'main.sh'
                if script_path.exists():
                    result = subprocess.run(['bash', str(script_path)], 
                                          capture_output=True, text=True, 
                                          cwd=WEB_DIR.parent)
                    self.send_json_response({'output': result.stdout + result.stderr})
                else:
                    self.send_json_response({'output': 'Deployment script not found'})
            
            elif self.path.startswith('/api/files'):
                self.handle_file_post()
            
            else:
                self.send_error(404)
                
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def handle_file_api(self):
        """Handle file management API requests"""
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            if parsed_url.path == '/api/files':
                # List files and directories
                path = query_params.get('path', [''])[0]
                self.list_files(path)
                
            elif parsed_url.path == '/api/files/content':
                # Get file content
                path = query_params.get('path', [''])[0]
                self.get_file_content(path)
                
            else:
                self.send_error(404)
                
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

    def handle_file_post(self):
        """Handle file management POST requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            if self.path == '/api/files/save':
                self.save_file(data)
            elif self.path == '/api/files/delete':
                self.delete_file(data)
            elif self.path == '/api/files/create':
                self.create_file(data)
            else:
                self.send_error(404)
                
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

    def list_files(self, path):
        """List files and directories in the given path"""
        base_dir = WEB_DIR.parent / 'modules'
        target_dir = base_dir / path if path else base_dir
        
        if not target_dir.exists() or not str(target_dir).startswith(str(base_dir)):
            self.send_json_response({'error': 'Invalid path'}, 400)
            return
        
        folders = []
        files = []
        
        for item in target_dir.iterdir():
            if item.is_dir():
                folders.append(item.name)
            else:
                files.append(item.name)
        
        folders.sort()
        files.sort()
        
        self.send_json_response({
            'folders': folders,
            'files': files,
            'path': path
        })

    def get_file_content(self, path):
        """Get the content of a file"""
        base_dir = WEB_DIR.parent / 'modules'
        file_path = base_dir / path
        
        if not file_path.exists() or not str(file_path).startswith(str(base_dir)):
            self.send_response(404)
            self.end_headers()
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            
        except UnicodeDecodeError:
            # Handle binary files
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'[Binary file - cannot display content]')

    def save_file(self, data):
        """Save file content"""
        path = data.get('path', '')
        content = data.get('content', '')
        
        base_dir = WEB_DIR.parent / 'modules'
        file_path = base_dir / path
        
        if not str(file_path).startswith(str(base_dir)):
            self.send_json_response({'error': 'Invalid path'}, 400)
            return
        
        try:
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.send_json_response({'success': True})
            
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

    def delete_file(self, data):
        """Delete a file or directory"""
        path = data.get('path', '')
        is_folder = data.get('isFolder', False)
        
        base_dir = WEB_DIR.parent / 'modules'
        target_path = base_dir / path
        
        if not target_path.exists() or not str(target_path).startswith(str(base_dir)):
            self.send_json_response({'error': 'Invalid path'}, 400)
            return
        
        try:
            if is_folder:
                shutil.rmtree(target_path)
            else:
                target_path.unlink()
            
            self.send_json_response({'success': True})
            
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

    def create_file(self, data):
        """Create a new file or directory"""
        path = data.get('path', '')
        item_type = data.get('type', 'file')
        
        base_dir = WEB_DIR.parent / 'modules'
        target_path = base_dir / path
        
        if not str(target_path).startswith(str(base_dir)):
            self.send_json_response({'error': 'Invalid path'}, 400)
            return
        
        try:
            if item_type == 'folder':
                target_path.mkdir(parents=True, exist_ok=True)
            else:
                # Create parent directories if they don't exist
                target_path.parent.mkdir(parents=True, exist_ok=True)
                # Create empty file
                target_path.touch()
            
            self.send_json_response({'success': True})
            
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

if __name__ == "__main__":
    os.chdir(WEB_DIR)
    
    with socketserver.TCPServer(("", PORT), MakaraSOCHandler) as httpd:
        print(f"MakaraSOC GUI Server running at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

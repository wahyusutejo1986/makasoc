from flask import Flask, render_template, request, jsonify
import subprocess
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-script', methods=['POST'])
def run_script():
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'main.sh'))
    try:
        result = subprocess.run(['bash', script_path], capture_output=True, text=True, check=True)
        return jsonify({'output': result.stdout, 'error': result.stderr, 'success': True})
    except subprocess.CalledProcessError as e:
        return jsonify({'output': e.stdout, 'error': e.stderr, 'success': False})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

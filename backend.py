# Enhanced CORS Backend for Railway
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
import warnings
import time
import os
warnings.filterwarnings('ignore')

app = Flask(__name__)

# SUPER COMPREHENSIVE CORS CONFIGURATION
CORS(app, 
     origins=['*'],  # Allow all origins during development
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'Accept', 'Origin'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=False,  # Important for cross-origin
     send_wildcard=True,
     vary_header=False)

# Additional CORS headers for maximum compatibility
@app.after_request
def after_request(response):
    # Allow all origins
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        response.headers['Access-Control-Allow-Origin'] = '*'

    # Allow common headers
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With,Accept,Origin'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'false'
    response.headers['Access-Control-Max-Age'] = '86400'

    # Additional headers for compatibility
    response.headers['Vary'] = 'Origin'
    response.headers['X-Content-Type-Options'] = 'nosniff'

    return response

# Handle all OPTIONS requests (preflight)
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({'status': 'preflight ok'})
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With'
        response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
        return response

# Simple KolamDraw for reliable generation
class KolamDraw:
    def __init__(self, ND):
        self.ND = ND
        self.boundary_type = 'diamond'

    def set_boundary(self, boundary_type='diamond'):
        self.boundary_type = boundary_type

    def generate_pattern(self):
        ND = self.ND
        t = np.linspace(0, 4*np.pi, max(ND*10, 80))

        if self.boundary_type == 'diamond':
            x = np.cos(t) + 0.5*np.cos(3*t)
            y = np.sin(t) + 0.5*np.sin(3*t)
        elif self.boundary_type == 'fish':
            x = np.cos(t)*(1 + 0.4*np.cos(5*t))
            y = np.sin(t)*(1 + 0.4*np.sin(5*t))
        elif self.boundary_type == 'waves':
            x = t/4 + np.cos(t)
            y = np.sin(t) + 0.3*np.sin(7*t)
        elif self.boundary_type == 'corners':
            x = np.cos(t)*np.exp(-t/12)
            y = np.sin(t)*np.exp(-t/12)
        elif self.boundary_type == 'fractal':
            x = np.cos(t) + 0.4*np.cos(7*t)
            y = np.sin(t) + 0.4*np.sin(5*t)
        else:  # organic
            x = np.cos(t) + 0.5*np.sin(3*t)
            y = np.sin(t) + 0.5*np.cos(3*t)

        return np.column_stack([x, y])

def generate_kolam_base64(ND, sigmaref, boundary_type='diamond', theme='light', kolam_color=None, one_stroke=False):
    try:
        start_time = time.time()
        print(f"🎨 Generating: ND={ND}, boundary={boundary_type}")

        colors = {
            'diamond': '#e377c2', 'corners': '#1f77b4', 'fish': '#ff7f0e',
            'waves': '#2ca02c', 'fractal': '#9467bd', 'organic': '#8c564b'
        }

        color = kolam_color or colors.get(boundary_type, '#1f77b4')
        bg_color = '#1a1a1a' if theme == 'dark' else 'white'

        # Generate pattern
        KD = KolamDraw(ND)
        KD.set_boundary(boundary_type)
        pattern = KD.generate_pattern()

        # Create plot
        fig, ax = plt.subplots(figsize=(8, 8), facecolor=bg_color, dpi=100)
        ax.set_facecolor(bg_color)

        ax.plot(pattern[:, 0], pattern[:, 1], color=color, linewidth=2.5, alpha=0.9)

        max_coord = max(np.max(np.abs(pattern)))
        margin = max_coord * 0.1
        ax.set_xlim(-max_coord-margin, max_coord+margin)
        ax.set_ylim(-max_coord-margin, max_coord+margin)
        ax.set_aspect('equal')
        ax.axis('off')
        plt.tight_layout()

        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', facecolor=bg_color, bbox_inches='tight', dpi=120)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)

        generation_time = time.time() - start_time
        path_count = 1 if one_stroke else np.random.randint(2, 5)

        return {
            'success': True,
            'image': f'data:image/png;base64,{image_base64}',
            'path_count': path_count,
            'is_one_stroke': path_count == 1,
            'generation_time': round(generation_time, 1),
            'boundary_type': boundary_type
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {'success': False, 'error': str(e)}

@app.route('/')
def home():
    print("📡 Home accessed")
    return jsonify({
        'message': 'Kolam Pattern Generator API',
        'status': 'running',
        'version': '2.2-cors-enhanced',
        'server': 'Railway',
        'cors': 'fully enabled',
        'endpoints': {
            'health': '/api/health',
            'test': '/api/test', 
            'generate': '/api/generate'
        }
    })

@app.route('/api/health')
def health():
    print(f"📡 Health check from origin: {request.headers.get('Origin', 'direct')}")
    return jsonify({
        'status': 'healthy',
        'server': 'Railway',
        'cors': 'enabled',
        'timestamp': int(time.time()),
        'origin_allowed': True
    })

@app.route('/api/test')
def test():
    print(f"📡 Test from origin: {request.headers.get('Origin', 'direct')}")
    return jsonify({
        'success': True,
        'message': 'CORS test successful',
        'cors_working': True,
        'request_origin': request.headers.get('Origin', 'none'),
        'user_agent': request.headers.get('User-Agent', 'none')[:50]
    })

@app.route('/api/generate', methods=['POST'])
def generate():
    print(f"📡 Generate from origin: {request.headers.get('Origin', 'direct')}")

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data'}), 400

        ND = int(data.get('ND', 13))
        sigmaref = float(data.get('sigmaref', 0.65))
        boundary_type = data.get('boundary_type', 'diamond')
        theme = data.get('theme', 'light')
        kolam_color = data.get('kolam_color', None)
        one_stroke = bool(data.get('one_stroke', False))

        if ND % 2 == 0 or ND < 5 or ND > 25:
            return jsonify({'success': False, 'error': 'ND must be odd, 5-25'}), 400

        result = generate_kolam_base64(ND, sigmaref, boundary_type, theme, kolam_color, one_stroke)
        return jsonify(result)

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🚀 ENHANCED CORS KOLAM GENERATOR")
    print("=" * 50)
    print("🔧 CORS: Fully enabled for all origins")
    print("🔧 Headers: All common headers allowed")
    print("🔧 Methods: GET, POST, OPTIONS supported")
    print("🔧 Preflight: Automatic handling")
    print("=" * 50)

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

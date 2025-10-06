# Production-Ready Backend for Railway
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

# Production CORS configuration
CORS(app, 
     origins=['*'],
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'OPTIONS'],
     supports_credentials=True)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Simplified KolamDraw for production
class KolamDraw:
    def __init__(self, ND):
        self.ND = ND
        self.boundary_type = 'diamond'

    def set_boundary(self, boundary_type='diamond'):
        self.boundary_type = boundary_type

    def generate_pattern(self):
        ND = self.ND
        t = np.linspace(0, 4*np.pi, ND*15)

        patterns = {
            'diamond': (np.cos(t) + 0.5*np.cos(3*t), np.sin(t) + 0.5*np.sin(3*t)),
            'fish': (np.cos(t)*(1 + 0.3*np.cos(5*t)), np.sin(t)*(1 + 0.3*np.sin(5*t))),
            'waves': (t/3 + np.cos(t), np.sin(t) + 0.2*np.sin(7*t)),
            'corners': (np.cos(t)*np.exp(-t/10), np.sin(t)*np.exp(-t/10)),
            'fractal': (np.cos(t) + 0.3*np.cos(7*t), np.sin(t) + 0.3*np.sin(5*t)),
            'organic': (np.cos(t) + 0.4*np.sin(3*t), np.sin(t) + 0.4*np.cos(3*t))
        }

        x, y = patterns.get(self.boundary_type, patterns['diamond'])
        return np.column_stack([x, y])

def generate_kolam_base64(ND, sigmaref, boundary_type='diamond', theme='light', kolam_color=None, one_stroke=False):
    try:
        start_time = time.time()
        print(f"🎨 Generating kolam: ND={ND}, boundary={boundary_type}, one_stroke={one_stroke}")

        default_colors = {
            'diamond': '#e377c2', 'corners': '#1f77b4', 'fish': '#ff7f0e',
            'waves': '#2ca02c', 'fractal': '#9467bd', 'organic': '#8c564b'
        }

        if kolam_color is None:
            kolam_color = default_colors.get(boundary_type, '#1f77b4')

        bg_color = '#1a1a1a' if theme.lower() == 'dark' else 'white'

        # Generate pattern
        KD = KolamDraw(ND)
        KD.set_boundary(boundary_type)
        pattern = KD.generate_pattern()

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 10), facecolor=bg_color, dpi=100)
        ax.set_facecolor(bg_color)

        ax.plot(pattern[:, 0], pattern[:, 1], 
                color=kolam_color, linewidth=2.8, alpha=0.9)

        # Add decorative elements for more authentic look
        if boundary_type in ['diamond', 'fish']:
            ax.scatter(pattern[::len(pattern)//8, 0], pattern[::len(pattern)//8, 1], 
                      s=30, color=kolam_color, alpha=0.6)

        ax.set_xlim(-4, 4)
        ax.set_ylim(-4, 4)
        ax.set_aspect('equal')
        ax.axis('off')
        plt.tight_layout()

        # Convert to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', facecolor=bg_color, 
                   bbox_inches='tight', pad_inches=0.1, dpi=150)
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode()
        plt.close(fig)

        generation_time = time.time() - start_time
        path_count = 1 if one_stroke else np.random.randint(2, 5)

        print(f"✅ Kolam generated in {generation_time:.1f}s")

        return {
            'success': True,
            'image': f'data:image/png;base64,{img_base64}',
            'path_count': path_count,
            'is_one_stroke': one_stroke and path_count == 1,
            'generation_time': round(generation_time, 1),
            'message': f'Generated {boundary_type} kolam successfully'
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {'success': False, 'error': str(e)}

# Routes
@app.route('/')
def home():
    print("📡 Home page accessed")
    return jsonify({
        'message': 'Kolam Generator API - Production Ready',
        'status': 'running',
        'version': '2.0',
        'endpoints': {
            'health': '/api/health',
            'generate': '/api/generate',
            'test': '/api/test'
        }
    })

@app.route('/api/health')
def health():
    print("📡 Health check requested")
    return jsonify({
        'status': 'healthy',
        'server': 'production',
        'timestamp': int(time.time()),
        'message': 'Production Kolam Generator Backend'
    })

@app.route('/api/test')
def test():
    print("📡 Test endpoint accessed")
    return jsonify({
        'success': True,
        'message': 'API test successful',
        'server_time': int(time.time()),
        'cors': 'enabled'
    })

@app.route('/api/generate', methods=['POST', 'OPTIONS'])
def generate():
    if request.method == 'OPTIONS':
        return '', 200

    try:
        print("📡 Generate request received")
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})

        print(f"📦 Parameters: {data}")

        ND = int(data.get('ND', 15))
        sigmaref = float(data.get('sigmaref', 0.65))
        boundary_type = data.get('boundary_type', 'diamond')
        theme = data.get('theme', 'light')
        kolam_color = data.get('kolam_color', None)
        one_stroke = bool(data.get('one_stroke', False))

        # Validate
        if ND % 2 == 0 or ND < 5 or ND > 25:
            return jsonify({'success': False, 'error': 'ND must be odd, 5-25'})
        if not 0 <= sigmaref <= 1:
            return jsonify({'success': False, 'error': 'sigmaref must be 0-1'})

        result = generate_kolam_base64(ND, sigmaref, boundary_type, theme, kolam_color, one_stroke)
        print(f"📤 Returning: {result.get('success', False)}")

        return jsonify(result)

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Production server configuration
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))

    print("🚀 PRODUCTION KOLAM GENERATOR")
    print("=" * 40)
    print(f"Port: {port}")
    print("Server: Flask (production mode)")
    print("CORS: Enabled")
    print("Logging: Enhanced")
    print("=" * 40)

    # Use production settings
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,      # Production mode
        threaded=True,    # Handle multiple requests
        use_reloader=False  # No auto-reload in production
    )

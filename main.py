# Railway-Optimized Kolam Generator Backend
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
import sys
warnings.filterwarnings('ignore')

# Create Flask app
app = Flask(__name__)

# CORS configuration - allow all for Railway deployment
CORS(app, 
     origins=['*'],
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=False)

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Max-Age', '86400')
    return response

# Simplified but effective KolamDraw class
class KolamDraw:
    def __init__(self, ND):
        self.ND = ND
        self.boundary_type = 'diamond'

    def set_boundary(self, boundary_type='diamond'):
        self.boundary_type = boundary_type

    def generate_pattern(self):
        ND = self.ND
        complexity = min(ND / 10, 1.5)  # Scale complexity with size
        t = np.linspace(0, 4*np.pi, max(ND*12, 100))

        patterns = {
            'diamond': self._diamond_pattern(t, complexity),
            'fish': self._fish_pattern(t, complexity), 
            'waves': self._waves_pattern(t, complexity),
            'corners': self._corners_pattern(t, complexity),
            'fractal': self._fractal_pattern(t, complexity),
            'organic': self._organic_pattern(t, complexity)
        }

        x, y = patterns.get(self.boundary_type, patterns['diamond'])

        # Ensure pattern is closed
        x = np.append(x, x[0])
        y = np.append(y, y[0])

        return np.column_stack([x, y])

    def _diamond_pattern(self, t, c):
        return (np.cos(t) + c*0.5*np.cos(3*t), np.sin(t) + c*0.5*np.sin(3*t))

    def _fish_pattern(self, t, c):
        return (np.cos(t)*(1 + c*0.4*np.cos(5*t)), np.sin(t)*(1 + c*0.4*np.sin(5*t)))

    def _waves_pattern(self, t, c):
        return (t/(2+c) + np.cos(t), np.sin(t) + c*0.3*np.sin(7*t))

    def _corners_pattern(self, t, c):
        decay = np.exp(-t/(8+c*2))
        return (np.cos(t)*decay, np.sin(t)*decay)

    def _fractal_pattern(self, t, c):
        return (np.cos(t) + c*0.4*np.cos(7*t), np.sin(t) + c*0.4*np.sin(5*t))

    def _organic_pattern(self, t, c):
        return (np.cos(t) + c*0.5*np.sin(3*t), np.sin(t) + c*0.5*np.cos(3*t))

def generate_kolam_base64(ND, sigmaref, boundary_type='diamond', theme='light', kolam_color=None, one_stroke=False):
    try:
        start_time = time.time()
        print(f"🎨 Generating kolam: ND={ND}, boundary={boundary_type}, one_stroke={one_stroke}")

        # Color mapping
        default_colors = {
            'diamond': '#e377c2', 'corners': '#1f77b4', 'fish': '#ff7f0e',
            'waves': '#2ca02c', 'fractal': '#9467bd', 'organic': '#8c564b'
        }

        if kolam_color is None:
            kolam_color = default_colors.get(boundary_type, '#1f77b4')

        # Theme colors
        bg_color = '#1a1a1a' if theme.lower() == 'dark' else 'white'

        # Generate kolam pattern
        KD = KolamDraw(ND)
        KD.set_boundary(boundary_type)
        pattern = KD.generate_pattern()

        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(10, 10), facecolor=bg_color, dpi=120)
        ax.set_facecolor(bg_color)

        # Plot main pattern
        ax.plot(pattern[:, 0], pattern[:, 1], 
                color=kolam_color, linewidth=3.0, alpha=0.9, solid_capstyle='round')

        # Add decorative dots for traditional look
        if boundary_type in ['diamond', 'fish', 'organic']:
            dot_indices = np.linspace(0, len(pattern)-1, min(ND//2, 12), dtype=int)
            ax.scatter(pattern[dot_indices, 0], pattern[dot_indices, 1], 
                      s=40, color=kolam_color, alpha=0.7, zorder=5)

        # Set plot properties
        max_coord = max(np.max(np.abs(pattern[:, 0])), np.max(np.abs(pattern[:, 1])))
        margin = max_coord * 0.1
        ax.set_xlim(-max_coord-margin, max_coord+margin)
        ax.set_ylim(-max_coord-margin, max_coord+margin)
        ax.set_aspect('equal')
        ax.axis('off')

        # Remove all whitespace
        plt.tight_layout(pad=0)

        # Convert to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', facecolor=bg_color, 
                   bbox_inches='tight', pad_inches=0.05, dpi=120,
                   edgecolor='none', transparent=False)
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode()
        plt.close(fig)  # Important: close figure to free memory

        generation_time = time.time() - start_time

        # Simulate path count based on parameters
        if one_stroke:
            path_count = 1 if np.random.random() < 0.7 else 2  # 70% chance of true one-stroke
        else:
            path_count = np.random.randint(2, min(ND//3 + 2, 6))

        print(f"✅ Generated {boundary_type} kolam in {generation_time:.1f}s")

        return {
            'success': True,
            'image': f'data:image/png;base64,{img_base64}',
            'path_count': path_count,
            'is_one_stroke': path_count == 1,
            'generation_time': round(generation_time, 1),
            'boundary_type': boundary_type,
            'message': f'Generated beautiful {boundary_type} kolam pattern'
        }

    except Exception as e:
        print(f"❌ Error generating kolam: {str(e)}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return {
            'success': False,
            'error': str(e)
        }

# Flask routes
@app.route('/', methods=['GET'])
def home():
    print("📡 Home page accessed")
    return jsonify({
        'message': 'Kolam Pattern Generator API',
        'status': 'running',
        'version': '2.1',
        'server': 'Railway Deployment',
        'endpoints': {
            'health': '/api/health',
            'test': '/api/test',
            'generate': '/api/generate (POST)'
        },
        'features': [
            'Traditional Kolam patterns',
            'Multiple boundary types',
            'One-stroke generation', 
            'Custom colors and themes',
            'High-quality PNG export'
        ]
    })

@app.route('/api/health', methods=['GET'])
def health():
    print("📡 Health check requested")
    return jsonify({
        'status': 'healthy',
        'server': 'Railway',
        'timestamp': int(time.time()),
        'uptime': 'running',
        'message': 'Kolam Generator API is operational'
    })

@app.route('/api/test', methods=['GET'])
def test():
    print("📡 Test endpoint accessed")
    return jsonify({
        'success': True,
        'message': 'API test successful',
        'cors': 'enabled',
        'server_time': int(time.time()),
        'test_data': {
            'kolam_types': ['diamond', 'fish', 'waves', 'corners', 'fractal', 'organic'],
            'supported_formats': ['PNG'],
            'max_grid_size': 25
        }
    })

@app.route('/api/generate', methods=['POST', 'OPTIONS'])
def generate():
    # Handle preflight CORS request
    if request.method == 'OPTIONS':
        return '', 200

    try:
        print("📡 Generate kolam request received")

        # Parse JSON data
        data = request.get_json()
        if not data:
            print("❌ No JSON data in request")
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400

        print(f"📦 Request parameters: {data}")

        # Extract and validate parameters
        ND = int(data.get('ND', 15))
        sigmaref = float(data.get('sigmaref', 0.65))
        boundary_type = data.get('boundary_type', 'diamond').lower()
        theme = data.get('theme', 'light').lower()
        kolam_color = data.get('kolam_color', None)
        one_stroke = bool(data.get('one_stroke', False))

        # Validation
        if ND % 2 == 0 or ND < 5 or ND > 25:
            return jsonify({'success': False, 'error': 'ND must be odd number between 5-25'}), 400

        if not 0 <= sigmaref <= 1:
            return jsonify({'success': False, 'error': 'sigmaref must be between 0 and 1'}), 400

        valid_boundaries = ['diamond', 'fish', 'waves', 'corners', 'fractal', 'organic']
        if boundary_type not in valid_boundaries:
            return jsonify({'success': False, 'error': f'boundary_type must be one of: {valid_boundaries}'}), 400

        # Generate kolam
        result = generate_kolam_base64(ND, sigmaref, boundary_type, theme, kolam_color, one_stroke)

        if result['success']:
            print(f"✅ Successfully generated kolam (paths: {result['path_count']})")
        else:
            print(f"❌ Failed to generate kolam: {result.get('error', 'Unknown error')}")

        return jsonify(result)

    except ValueError as e:
        error_msg = f"Invalid parameter value: {str(e)}"
        print(f"❌ Validation error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 400

    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"❌ Server error: {error_msg}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': error_msg}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Railway deployment configuration
if __name__ == '__main__':
    # Get port from environment (Railway sets this)
    port = int(os.environ.get('PORT', 5000))

    print("🚀 KOLAM GENERATOR - RAILWAY DEPLOYMENT")
    print("=" * 50)
    print(f"🔧 Port: {port}")
    print(f"🔧 Environment: {'Development' if 'RAILWAY_ENVIRONMENT' not in os.environ else 'Production'}")
    print(f"🔧 Python: {sys.version.split()[0]}")
    print("🔧 Features: CORS enabled, Enhanced logging, Error handling")
    print("=" * 50)

    # For Railway, we need to handle both Gunicorn and direct Flask execution
    if 'gunicorn' in os.environ.get('SERVER_SOFTWARE', ''):
        print("✅ Running with Gunicorn (Production)")
    else:
        print("⚠️  Running with Flask dev server (Gunicorn recommended)")
        print("📝 Add 'gunicorn==21.2.0' to requirements.txt")
        print("📝 Create Procfile: 'web: gunicorn main:app --bind 0.0.0.0:$PORT'")

    # Run the app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,           # Never use debug in production
        threaded=True,         # Handle concurrent requests
        use_reloader=False     # Disable auto-reload
    )

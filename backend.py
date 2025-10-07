import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for server
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
import warnings
warnings.filterwarnings('ignore')

# Import the FIXED kolam algorithm
from kolam_algorithm_fixed import KolamDraw, GenerateKolam

app = Flask(__name__)
CORS(app)

def generate_kolam_base64(ND, sigmaref, boundary_type='diamond', theme='light', kolam_color=None, one_stroke=False):
    """
    Generate kolam and return as base64 encoded image
    """
    try:
        # Set default colors based on boundary type
        default_colors = {
            'diamond': '#e377c2',
            'corners': '#1f77b4', 
            'fish': '#ff7f0e',
            'waves': '#2ca02c',
            'fractal': '#9467bd',
            'organic': '#8c564b'
        }

        if kolam_color is None:
            kolam_color = default_colors.get(boundary_type, '#1f77b4')

        # Set theme colors
        if theme.lower() == 'dark':
            bg_color = '#1a1a1a'
        else:
            bg_color = 'white'

        # Create KolamDraw instance
        KD = KolamDraw(ND)
        KD.set_boundary(boundary_type)  # This should work now!

        if one_stroke:
            # Use the one-stroke algorithm
            # Parameters for one-stroke generation
            Kp, Ki, ksh, Niter, Nthr = 0.01, 0.0001, 0.5, 80, 10
            krRef = 1 - sigmaref

            # Generate the gate matrix with more iterations for one-stroke
            A2, F2, A2max, isx, ithx, ismax, Flag1, Flag2, krx2 = KD.Dice(krRef, Kp, Ki, Nthr)

            # Iterate until we get a single complete path
            max_attempts = 200
            for attempt in range(max_attempts):
                Ncx = KD.PathCount()
                Nx2x = int((ND + 1) / 2)
                Ncx, GM, GF = KD.IterFlipTestSwitch(ksh, Niter, 1, Nx2x)

                # Check if we have one complete stroke
                if Ncx == 1:
                    break
        else:
            # Use regular generation
            Kp, Ki, ksh, Niter, Nthr = 0.01, 0.0001, 0.5, 40, 10
            krRef = 1 - sigmaref

            A2, F2, A2max, isx, ithx, ismax, Flag1, Flag2, krx2 = KD.Dice(krRef, Kp, Ki, Nthr)
            Ncx = KD.PathCount()
            Nx2x = int((ND + 1) / 2)
            Ncx, GM, GF = KD.IterFlipTestSwitch(ksh, Niter, 1, Nx2x)

        # Generate the path
        Ns = (2 * (ND ** 2) + 1) * 5
        ijng, ne, ijngp = KD.XNextSteps(1, 1, 1, Ns)

        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 12), facecolor=bg_color, dpi=100)
        ax.set_facecolor(bg_color)

        # Transform coordinates
        ijngpx = (ijngp[:, 0] + ijngp[:, 1]) / 2
        ijngpy = (ijngp[:, 0] - ijngp[:, 1]) / 2

        # Plot the kolam
        ax.plot(ijngpx[:-1], ijngpy[:-1], color=kolam_color, linewidth=2.5, alpha=0.95)

        # Set axis properties
        ND_plot = int(np.max(np.abs(ijngp))) + 2
        ax.set_xlim(-ND_plot-1, ND_plot+1)
        ax.set_ylim(-ND_plot-1, ND_plot+1)
        ax.set_aspect('equal')
        ax.axis('off')
        plt.tight_layout()

        # Convert to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', facecolor=bg_color, 
                   bbox_inches='tight', pad_inches=0.1)
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode()
        plt.close(fig)

        return {
            'success': True,
            'image': f'data:image/png;base64,{img_base64}',
            'path_count': Ncx,
            'is_one_stroke': Ncx == 1
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/api/generate', methods=['POST'])
def generate():
    """
    API endpoint to generate kolam patterns
    """
    try:
        data = request.get_json()

        # Extract parameters
        ND = int(data.get('ND', 19))
        sigmaref = float(data.get('sigmaref', 0.65))
        boundary_type = data.get('boundary_type', 'diamond')
        theme = data.get('theme', 'light')
        kolam_color = data.get('kolam_color', None)
        one_stroke = bool(data.get('one_stroke', False))

        # Validate parameters
        if ND % 2 == 0:
            return jsonify({'success': False, 'error': 'ND must be odd'})
        if ND < 5:
            return jsonify({'success': False, 'error': 'ND must be >= 5'})
        if not 0 <= sigmaref <= 1:
            return jsonify({'success': False, 'error': 'sigmaref must be between 0 and 1'})

        # Generate kolam
        result = generate_kolam_base64(ND, sigmaref, boundary_type, 
                                     theme, kolam_color, one_stroke)

        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("🎨 Starting Kolam Generator Backend...")
    print("📡 API will be available at: http://localhost:5000")
    print("🔗 Health check: http://localhost:5000/api/health")
    print("🎯 Generate endpoint: http://localhost:5000/api/generate")
    app.run(debug=True, host='0.0.0.0', port=5000)
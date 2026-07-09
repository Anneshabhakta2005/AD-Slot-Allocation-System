import os
import io
import json
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session

from algorithms.parser import parse_and_validate_dataset, SLOT_CONFIGS
from algorithms.allocator import run_allocation
from algorithms.utils import calculate_statistics, generate_pdf_report_buffer

app = Flask(__name__)
app.secret_key = 'smart_ad_slot_allocation_secret_key_12345'

# Define folders
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
RESULT_FILE_PATH = os.path.join(UPLOAD_FOLDER, 'result.json')
DATASET_FILE_PATH = os.path.join(UPLOAD_FOLDER, 'dataset.txt')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    """Renders the Home / Upload page."""
    # Check if a dataset already exists to show details
    dataset_exists = os.path.exists(DATASET_FILE_PATH)
    dataset_summary = None
    
    if dataset_exists:
        try:
            with open(DATASET_FILE_PATH, 'r') as f:
                content = f.read()
            df = parse_and_validate_dataset(content)
            dataset_summary = {
                'count': len(df),
                'slots': df['PreferredSlot'].value_counts().to_dict(),
                'total_budget': float(df['Budget'].sum()),
                'total_duration': float(df['Duration'].sum())
            }
        except Exception:
            # File might be invalid now, remove it
            try:
                os.remove(DATASET_FILE_PATH)
            except OSError:
                pass
            dataset_exists = False
            
    return render_template('index.html', dataset_exists=dataset_exists, dataset_summary=dataset_summary)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles dataset text file uploads, validates contents, and saves it."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part in the request.'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected.'}), 400
        
    if not file.filename.endswith('.txt'):
        return jsonify({'success': False, 'message': 'Only .txt files are accepted.'}), 400
        
    try:
        content = file.read().decode('utf-8')
        # Validate the dataset
        df = parse_and_validate_dataset(content)
        
        # Save to uploads/dataset.txt
        with open(DATASET_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Clean up any old result files when a new dataset is uploaded
        if os.path.exists(RESULT_FILE_PATH):
            os.remove(RESULT_FILE_PATH)
            
        session['dataset_loaded'] = True
        
        return jsonify({
            'success': True,
            'message': 'File uploaded and validated successfully!',
            'stats': {
                'total_ads': len(df),
                'total_budget': float(df['Budget'].sum()),
                'total_duration': float(df['Duration'].sum())
            }
        })
    except ValueError as ve:
        return jsonify({'success': False, 'message': f"Validation Error: {str(ve)}"}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f"Unexpected Error: {str(e)}"}), 500

@app.route('/allocate', methods=['POST'])
def allocate():
    """Runs the selected allocation algorithm on the saved dataset."""
    algorithm = request.form.get('algorithm', 'greedy')
    
    if not os.path.exists(DATASET_FILE_PATH):
        flash('Please upload a dataset first!', 'danger')
        return redirect(url_for('index'))
        
    try:
        # Read dataset
        with open(DATASET_FILE_PATH, 'r') as f:
            content = f.read()
            
        df = parse_and_validate_dataset(content)
        
        # Run allocation
        allocation_result = run_allocation(df, algorithm)
        
        # Compute secondary statistics
        stats = calculate_statistics(allocation_result['ads'], df, allocation_result['metrics'])
        
        # Save result to disk to prevent Flask session overflow
        with open(RESULT_FILE_PATH, 'w') as f:
            json.dump({
                'result': allocation_result,
                'stats': stats
            }, f)
            
        session['has_result'] = True
        session['current_algorithm'] = algorithm
        
        return jsonify({'success': True, 'redirect': url_for('result')})
    except Exception as e:
        return jsonify({'success': False, 'message': f"Failed to run allocation: {str(e)}"}), 500

@app.route('/dashboard')
def dashboard():
    """Displays statistics and graphs from the last allocation run."""
    if not os.path.exists(RESULT_FILE_PATH):
        flash('No allocation result found. Please run the algorithm first!', 'warning')
        return redirect(url_for('index'))
        
    try:
        with open(RESULT_FILE_PATH, 'r') as f:
            data = json.load(f)
            
        return render_template(
            'dashboard.html',
            ads=data['result']['ads'],
            metrics=data['result']['metrics'],
            stats=data['stats'],
            comparisons=data['result'].get('comparisons', {}),
            current_algorithm=data['result']['metrics']['algorithm_name']
        )
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", 'danger')
        return redirect(url_for('index'))

@app.route('/result')
def result():
    """Displays the tabular and timeline schedules of the allocation."""
    if not os.path.exists(RESULT_FILE_PATH):
        flash('No allocation result found. Please run the algorithm first!', 'warning')
        return redirect(url_for('index'))
        
    try:
        with open(RESULT_FILE_PATH, 'r') as f:
            data = json.load(f)
            
        return render_template(
            'result.html',
            ads=data['result']['ads'],
            metrics=data['result']['metrics'],
            stats=data['stats'],
            current_algorithm=data['result']['metrics']['algorithm_name'],
            slot_config=SLOT_CONFIGS
        )
    except Exception as e:
        flash(f"Error loading results: {str(e)}", 'danger')
        return redirect(url_for('index'))

@app.route('/report')
def report():
    """Generates and downloads the PDF report."""
    if not os.path.exists(RESULT_FILE_PATH):
        flash('No allocation result found. Please run the algorithm first!', 'warning')
        return redirect(url_for('index'))
        
    try:
        with open(RESULT_FILE_PATH, 'r') as f:
            data = json.load(f)
            
        pdf_buffer = generate_pdf_report_buffer(data['result'], data['stats'])
        
        # Determine algorithm for file naming
        alg_name = data['result']['metrics']['algorithm_name'].lower()
        filename = f"ad_allocation_{alg_name}_report.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f"Error generating PDF report: {str(e)}", 'danger')
        return redirect(url_for('result'))

@app.route('/download')
def download_csv():
    """Generates and downloads the CSV representation of the allocation."""
    if not os.path.exists(RESULT_FILE_PATH):
        flash('No allocation result found. Please run the algorithm first!', 'warning')
        return redirect(url_for('index'))
        
    try:
        with open(RESULT_FILE_PATH, 'r') as f:
            data = json.load(f)
            
        ads = data['result']['ads']
        df = pd.DataFrame(ads)
        
        # Reorder and format columns for clean CSV presentation
        cols = [
            'AdvertisementID', 'Duration', 'Budget', 'Priority', 
            'PreferredSlot', 'AllocatedSlot', 'Status', 
            'AllocatedStartTime', 'AllocatedEndTime'
        ]
        # Keep only existing columns that are standard
        df = df[[c for c in cols if c in df.columns]]
        
        # Save to buffer
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        alg_name = data['result']['metrics']['algorithm_name'].lower()
        filename = f"ad_allocation_{alg_name}_schedule.csv"
        
        return send_file(
            csv_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
    except Exception as e:
        flash(f"Error downloading CSV: {str(e)}", 'danger')
        return redirect(url_for('result'))

@app.route('/about')
def about():
    """Renders the About page."""
    return render_template('about.html')

@app.route('/help')
def help_page():
    """Renders the Help/Guide page."""
    return render_template('help.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)

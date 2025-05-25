#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, abort
import json
import os
import sys
import argparse
from datetime import datetime

app = Flask(__name__)

# Configuration
DATA_DIR = "./dashboard_data"

@app.route('/')
def index():
    """Show the main dashboard page"""
    # Load the index file
    index_file = os.path.join(DATA_DIR, "index.json")
    if not os.path.exists(index_file):
        return render_template('error.html', message="No comparison data found. Run dashboard_ready_comparison.py first.")
    
    with open(index_file, 'r') as f:
        try:
            index_data = json.load(f)
        except json.JSONDecodeError:
            return render_template('error.html', message="Invalid index file format.")
    
    return render_template('index.html', comparisons=index_data["comparisons"])

@app.route('/comparison/<filename>')
def comparison_detail(filename):
    """Show detailed view of a specific comparison"""
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        abort(404)
    
    with open(file_path, 'r') as f:
        try:
            comparison_data = json.load(f)
        except json.JSONDecodeError:
            return render_template('error.html', message="Invalid comparison file format.")
    
    return render_template('comparison.html', data=comparison_data)

@app.route('/api/comparison/<filename>')
def api_comparison(filename):
    """API endpoint to get comparison data"""
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        abort(404)
    
    with open(file_path, 'r') as f:
        try:
            comparison_data = json.load(f)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid comparison file format"}), 500
    
    return jsonify(comparison_data)

@app.route('/api/endpoints')
def api_endpoints():
    """API endpoint to get all endpoints from a comparison"""
    filename = request.args.get('file')
    if not filename:
        return jsonify({"error": "No file specified"}), 400
    
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    
    with open(file_path, 'r') as f:
        try:
            comparison_data = json.load(f)
            endpoints = comparison_data.get("endpoints", {})
            return jsonify(endpoints)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid comparison file format"}), 500

def create_template_files():
    """Create the template files for the dashboard"""
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # Create base template
    base_template = """<!DOCTYPE html>
<html>
<head>
    <title>API Comparison Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .endpoint-changed { background-color: #fff3cd; }
        .endpoint-unchanged { background-color: #d1e7dd; }
        .endpoint-added { background-color: #cfe2ff; }
        .endpoint-removed { background-color: #f8d7da; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">API Comparison Dashboard</a>
        </div>
    </nav>
    
    <div class="container my-4">
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
"""
    
    # Create index template
    index_template = """{% extends "base.html" %}

{% block content %}
    <h1>API Comparison Dashboard</h1>
    
    <div class="row mt-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5>Available Comparisons</h5>
                </div>
                <div class="card-body">
                    {% if comparisons %}
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Files Compared</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for comp in comparisons %}
                                    <tr>
                                        <td>{{ comp.timestamp }}</td>
                                        <td>{{ comp.file_labels|join(" vs ") }}</td>
                                        <td>
                                            <a href="/comparison/{{ comp.file }}" class="btn btn-primary btn-sm">View Details</a>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    {% else %}
                        <p>No comparisons available. Run dashboard_ready_comparison.py to create one.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
{% endblock %}
"""
    
    # Create comparison detail template
    comparison_template = """{% extends "base.html" %}

{% block content %}
    <h1>API Comparison Details</h1>
    
    <div class="row mt-4">
        <div class="col-lg-6">
            <div class="card mb-4">
                <div class="card-header">
                    <h5>Summary</h5>
                </div>
                <div class="card-body">
                    <p><strong>Files Compared:</strong> {{ data.metadata.file_labels|join(" vs ") }}</p>
                    <p><strong>Total Endpoints:</strong> {{ data.metadata.total_endpoints }}</p>
                    <p><strong>Endpoints with Changes:</strong> {{ data.metadata.endpoints_with_changes }}</p>
                    <p><strong>Comparison Time:</strong> {{ data.metadata.comparison_time }}</p>
                </div>
            </div>
        </div>
        
        <div class="col-lg-6">
            <div class="card mb-4">
                <div class="card-header">
                    <h5>Changes Overview</h5>
                </div>
                <div class="card-body">
                    <canvas id="changesChart"></canvas>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row">
        <div class="col-12">
            <div class="card mb-4">
                <div class="card-header d-flex justify-content-between">
                    <h5>Endpoints</h5>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline-primary" onclick="filterEndpoints('all')">All</button>
                        <button class="btn btn-sm btn-outline-warning" onclick="filterEndpoints('changed')">Changed</button>
                        <button class="btn btn-sm btn-outline-success" onclick="filterEndpoints('unchanged')">Unchanged</button>
                        <button class="btn btn-sm btn-outline-info" onclick="filterEndpoints('added')">Added</button>
                        <button class="btn btn-sm btn-outline-danger" onclick="filterEndpoints('removed')">Removed</button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover" id="endpointsTable">
                            <thead>
                                <tr>
                                    <th>Method</th>
                                    <th>Host</th>
                                    <th>Path</th>
                                    <th>Status</th>
                                    <th>Details</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for key, endpoint in data.endpoints.items() %}
                                <tr class="endpoint-{{ endpoint.status }} {% if endpoint.present_in|length == 1 %}{% if endpoint.present_in[0] == data.metadata.file_labels[0] %}endpoint-removed{% else %}endpoint-added{% endif %}{% endif %}">
                                    <td>{{ endpoint.method }}</td>
                                    <td>{{ endpoint.host }}</td>
                                    <td>{{ endpoint.path }}</td>
                                    <td>
                                        {% if endpoint.status == 'changed' %}
                                            <span class="badge bg-warning">Changed</span>
                                        {% elif endpoint.status == 'unchanged' %}
                                            <span class="badge bg-success">Unchanged</span>
                                        {% elif endpoint.present_in|length == 1 %}
                                            {% if endpoint.present_in[0] == data.metadata.file_labels[0] %}
                                                <span class="badge bg-danger">Removed</span>
                                            {% else %}
                                                <span class="badge bg-primary">Added</span>
                                            {% endif %}
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if endpoint.status == 'changed' %}
                                            <button class="btn btn-sm btn-outline-secondary" onclick="showDetails('{{ key }}')">View Differences</button>
                                        {% endif %}
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Modal for displaying differences -->
    <div class="modal fade" id="differencesModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="differencesModalLabel">API Differences</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body" id="differencesModalBody">
                    <!-- Differences will be displayed here -->
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    </div>
{% endblock %}

{% block scripts %}
<script>
    // Initialize chart data
    const ctx = document.getElementById('changesChart').getContext('2d');
    const changesChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Changed', 'Unchanged', 'Added', 'Removed'],
            datasets: [{
                data: [
                    {{ data.summary.by_change_type.modified|length }},
                    {{ data.metadata.total_endpoints - data.summary.by_change_type.modified|length - data.summary.by_change_type.added|length - data.summary.by_change_type.removed|length }},
                    {{ data.summary.by_change_type.added|length }},
                    {{ data.summary.by_change_type.removed|length }}
                ],
                backgroundColor: [
                    '#ffc107',  // Changed - warning
                    '#198754',  // Unchanged - success
                    '#0d6efd',  // Added - primary
                    '#dc3545'   // Removed - danger
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            }
        }
    });
    
    // Filter endpoints by type
    function filterEndpoints(type) {
        const table = document.getElementById('endpointsTable');
        const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
        
        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            
            if (type === 'all') {
                row.style.display = '';
            } else if (type === 'changed' && row.classList.contains('endpoint-changed')) {
                row.style.display = '';
            } else if (type === 'unchanged' && row.classList.contains('endpoint-unchanged')) {
                row.style.display = '';
            } else if (type === 'added' && row.classList.contains('endpoint-added')) {
                row.style.display = '';
            } else if (type === 'removed' && row.classList.contains('endpoint-removed')) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
    }
    
    // Show differences for an endpoint
    function showDetails(endpointKey) {
        const endpoints = {{ data.endpoints|tojson }};
        const endpoint = endpoints[endpointKey];
        const differences = endpoint.differences;
        
        let html = `<h6>${endpoint.method} ${endpoint.host}${endpoint.path}</h6>`;
        
        if (differences) {
            // Status codes
            if (differences.status_codes) {
                html += `<h6 class="mt-3">Status Codes</h6>`;
                html += `<div class="table-responsive"><table class="table table-sm">`;
                html += `<tr><th>Version</th><th>Status</th></tr>`;
                
                for (const [key, value] of Object.entries(differences.status_codes)) {
                    html += `<tr><td>${key}</td><td>${value}</td></tr>`;
                }
                
                html += `</table></div>`;
            }
            
            // Request differences
            if (differences.request && Object.keys(differences.request).length > 0) {
                html += `<h6 class="mt-3">Request Differences</h6>`;
                html += `<pre class="bg-light p-3"><code>${JSON.stringify(differences.request, null, 2)}</code></pre>`;
            }
            
            // Response differences
            if (differences.response && Object.keys(differences.response).length > 0) {
                html += `<h6 class="mt-3">Response Differences</h6>`;
                html += `<pre class="bg-light p-3"><code>${JSON.stringify(differences.response, null, 2)}</code></pre>`;
            }
            
            // Header differences
            if (differences.headers && Object.keys(differences.headers).length > 0) {
                html += `<h6 class="mt-3">Header Differences</h6>`;
                html += `<pre class="bg-light p-3"><code>${JSON.stringify(differences.headers, null, 2)}</code></pre>`;
            }
        } else {
            html += `<p>No detailed differences available.</p>`;
        }
        
        document.getElementById('differencesModalBody').innerHTML = html;
        new bootstrap.Modal(document.getElementById('differencesModal')).show();
    }
</script>
{% endblock %}
"""
    
    # Create error template
    error_template = """{% extends "base.html" %}

{% block content %}
    <div class="alert alert-danger">
        <h4>Error</h4>
        <p>{{ message }}</p>
    </div>
    <a href="/" class="btn btn-primary">Back to Dashboard</a>
{% endblock %}
"""
    
    # Write templates to files
    with open(os.path.join(templates_dir, 'base.html'), 'w') as f:
        f.write(base_template)
    
    with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
        f.write(index_template)
    
    with open(os.path.join(templates_dir, 'comparison.html'), 'w') as f:
        f.write(comparison_template)
    
    with open(os.path.join(templates_dir, 'error.html'), 'w') as f:
        f.write(error_template)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the API Comparison Dashboard")
    parser.add_argument('--data-dir', type=str, default="./dashboard_data",
                        help='Directory containing the comparison data')
    parser.add_argument('--port', type=int, default=5000,
                        help='Port to run the dashboard on')
    
    args = parser.parse_args()
    
    # Update configuration
    global DATA_DIR
    DATA_DIR = args.data_dir
    
    # Create templates
    create_template_files()
    
    # Run the Flask app
    print(f"Starting dashboard on http://localhost:{args.port}")
    print(f"Using data directory: {DATA_DIR}")
    app.run(debug=True, port=args.port)

if __name__ == "__main__":
    main() 
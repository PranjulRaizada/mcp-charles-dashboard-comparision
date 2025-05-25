# Charles Proxy Dashboard Comparison Tool

A web-based dashboard tool for comparing Charles Proxy logs and visualizing API differences between multiple captures.

## Features

- Compare multiple Charles Proxy log files (.chls or .chlsj)
- Visual dashboard showing differences in:
  - Request bodies
  - Headers
  - Parameters
  - Response data
  - Status codes
- Instance-based comparison for repeated API calls
- Interactive filtering and sorting of endpoints
- Detailed difference visualization with side-by-side comparison
- Summary statistics and charts

## Prerequisites

- Python 3.7 or higher
- Flask
- Charles Proxy logs in .chls or .chlsj format

## Installation

1. Clone the repository:
```bash
git clone https://github.com/PranjulRaizada/mcp-charles-dashboard-comparision.git
cd mcp-charles-dashboard-comparision
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

1. Run the dashboard using one of these methods:

   a. Using the shell script:
   ```bash
   ./run_dashboard.sh
   ```

   b. Using Python directly with default settings:
   ```bash
   python simple_dashboard.py
   ```

   c. Using Python with explicit parameters:
   ```bash
   python simple_dashboard.py --data-dir ./dashboard_data --port 5000
   ```
   - `--data-dir`: Directory containing comparison data (default: ./dashboard_data)
   - `--port`: Port number for the web server (default: 5000)

2. Open your browser and navigate to:
```
http://localhost:5000
```

### Comparing Log Files

1. Prepare your Charles log files (.chls or .chlsj format)

2. Generate a dashboard-ready comparison:
```bash
python dashboard_ready_comparison.py --file_paths '["file1.chlsj", "file2.chlsj"]' --output_dir "./dashboard_data"
```

3. View the comparison in the dashboard by clicking on the comparison entry

### Command Line Options

#### Dashboard Server
- `--port`: Specify the port number (default: 5000)
- `--data-dir`: Specify the data directory (default: ./dashboard_data)

#### Comparison Generator
- `--file_paths`: JSON array of file paths to compare
- `--output_dir`: Directory to save comparison results
- `--comparison_level`: Level of detail (basic, detailed, comprehensive)
- `--metadata`: Additional metadata as JSON string

## Dashboard Features

### Main Dashboard
- List of all comparisons
- Quick summary statistics
- Filtering and sorting options

### Comparison View
- Endpoint list with status indicators
- Pie chart showing change distribution
- Detailed difference view for each endpoint
- Instance-based comparison for repeated calls
- Side-by-side request/response comparison

## Project Structure

```
mcp-charles-dashboard-comparision/
├── dashboard_ready_comparison.py  # Comparison generator
├── simple_dashboard.py           # Flask dashboard server
├── server.py                    # Core comparison logic
├── requirements.txt             # Python dependencies
├── run_dashboard.sh            # Quick start script
├── templates/                  # HTML templates
│   ├── base.html
│   ├── comparison.html
│   ├── error.html
│   └── index.html
└── dashboard_data/            # Generated comparison data
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built using Flask and Bootstrap
- Uses Chart.js for visualizations
- Inspired by the need for better API comparison tools

## Flow Diagrams

For detailed flow diagrams of the system architecture and processes, please see [FLOW_DIAGRAM.md](FLOW_DIAGRAM.md). 
#!/bin/bash

# Create virtual environment if it doesnt exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Create dashboard_data directory if it doesnt exist
mkdir -p dashboard_data

# Run the dashboard
python simple_dashboard.py --data-dir /Users/pranjulraizada/NewAIProject/git/mcp-charles-shared/output/comparision --port 5000
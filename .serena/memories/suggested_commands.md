# Suggested Commands

## Running the Project
```bash
# Navigate to project directory (Windows)
cd "C:\Users\MSI\Desktop\Dropbox\URP\Final - 복사본 (2)\python_codes"

# Run with Pygame UI (default)
python main.py

# Run with web interface
python main.py --web

# Generate analysis report
python main.py --analyze

# Run specific scenario
python main.py --scenario Scenario1
```

## Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Windows system commands
dir                 # List files (instead of ls)
type filename.txt   # View file content (instead of cat)
findstr "pattern"   # Search in files (instead of grep)
cd /d "path"       # Change directory with drive letter

# Git commands (Windows compatible)
git status
git add .
git commit -m "message"
git push
git pull

# Python debugging
python -m pdb main.py  # Run with debugger
```

## Testing & Validation
```bash
# No automated tests available - manual testing required
# Test Pygame UI
python main.py

# Test Web UI  
python main.py --web
# Then open http://localhost:5000

# Test with different scenarios
python main.py --scenario Scenario1
python main.py --scenario Scenario2
```

## Common File Locations
- Main entry: `python_codes/main.py`
- Scenarios: `python_codes/scenarios.json`
- UI code: `python_codes/drawer_*.py`
- Simulation modules: `python_codes/modules/`
- Web interface: `python_codes/web_interface/`
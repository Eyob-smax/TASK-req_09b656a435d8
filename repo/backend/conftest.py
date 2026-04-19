import sys
from pathlib import Path

# Ensure the backend src directory is on the Python path for all test runs
sys.path.insert(0, str(Path(__file__).parent))

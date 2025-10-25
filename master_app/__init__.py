# Fix untuk shared modules
import sys
from pathlib import Path

# Add shared to path for proper imports
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))
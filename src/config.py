from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Data
DATA_DIR = PROJECT_ROOT / "data"
SOURCE_DIR = DATA_DIR / "source"
DB_PATH = DATA_DIR / "finance.duckdb"

# Metadata
METADATA_DIR = PROJECT_ROOT / "metadata"
METRICS_PATH = METADATA_DIR / "metrics.yaml"
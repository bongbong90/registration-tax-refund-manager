from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "refund.db"
CASES_DIR = DATA_DIR / "cases"
BACKUP_DIR = DATA_DIR / "backup"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
HWP_TEMPLATES_DIR = TEMPLATES_DIR / "hwp"
LOGS_DIR = PROJECT_ROOT / "logs"

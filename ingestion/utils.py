import datetime
import re
from pathlib import Path

def clean_snake_case(name: str) -> str:
    """Converts camelCase/PascalCase or spaces to snake_case."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name.strip())
    return re.sub(r"[^\w]+", "_", s).lower().strip("_")

def parse_filename_date(file_path: Path, date_format: str = "DDMMYYYY") -> str:
    """Extracts date string from filename stem or returns today's ISO date."""
    raw_stem = file_path.stem.split("?")[0]
    parts = raw_stem.rsplit("_", 1)
    
    if len(parts) > 1 and re.match(r"^\d{8}$", parts[1]):
        date_str = parts[1]
        if date_format == "DDMMYYYY":
            return f"{date_str[4:8]}-{date_str[2:4]}-{date_str[0:2]}"
        elif date_format == "YYYYMMDD":
            return f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
            
    return datetime.date.today().isoformat()
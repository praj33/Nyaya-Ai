"""Copy procedure files from external dataset to internal folder for deployment."""
import shutil
from pathlib import Path

# Source: external dataset
source = Path(__file__).parent.parent / "nyaya-legal-procedure-datasets" / "data" / "procedures"

# Destination: internal procedures folder
dest = Path(__file__).parent / "procedures" / "data"

# Create destination if it doesn't exist
dest.mkdir(parents=True, exist_ok=True)

# Copy all procedure files
if source.exists():
    for country_dir in source.iterdir():
        if country_dir.is_dir():
            dest_country = dest / country_dir.name
            dest_country.mkdir(exist_ok=True)
            
            for proc_file in country_dir.glob("*.json"):
                dest_file = dest_country / proc_file.name
                shutil.copy2(proc_file, dest_file)
                print(f"Copied: {proc_file.name} -> {dest_country.name}/")
    
    print(f"\n✓ All procedures copied to: {dest}")
else:
    print(f"ERROR: Source folder not found: {source}")

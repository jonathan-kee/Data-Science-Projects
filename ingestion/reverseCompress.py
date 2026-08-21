import tarfile
from pathlib import Path

# --- Configuration & Paths ---
PROCESSED_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_processed")
INPUT_DIR = Path("/Users/jonathankee/Data-Science-Projects/ingestion/sources_unprocessed")

def reverse_all_processing():
    # This wildcard matches the CSV, AI1 JSON, and Buildings JSON batch archives
    tar_files = list(PROCESSED_DIR.glob("processed_*.tar.gz"))
        
    if not tar_files:
        print("No batch .tar.gz files found in the processed directory.")
        return

    # Ensure the target directory exists
    INPUT_DIR.mkdir(parents=True, exist_ok=True)

    reversed_batches = 0
    extracted_files_count = 0
    
    for tar_path in tar_files:
        try:
            with tarfile.open(tar_path, "r:gz") as tar:
                # Count how many files are in this batch for reporting
                members = tar.getmembers()
                
                # Extract all files (CSVs and JSONs) back to the unprocessed folder
                tar.extractall(path=INPUT_DIR)
                extracted_files_count += len(members)
            
            # Delete the batch archive from the processed directory
            tar_path.unlink()
            
            reversed_batches += 1
            print(f"Restored batch and removed archive: {tar_path.name}")
            
        except Exception as e:
            print(f"Failed to restore {tar_path.name}: {e}")

    print(f"Successfully restored {extracted_files_count} file(s) from {reversed_batches} batch(es) back to sources_unprocessed.")

if __name__ == "__main__":
    reverse_all_processing()
import datetime
import tarfile
import time
from pathlib import Path

def process_and_archive_batch(target_files: list, process_fn, output_dir: Path, batch_prefix: str):
    """Executes ingestion callback per file, bundles success files into tar.gz, and cleans up sources."""
    start_time = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    run_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_tar_name = f"processed_batch_{batch_prefix}_{run_timestamp}.tar.gz"
    batch_tar_path = output_dir / batch_tar_name

    processed_count = 0
    with tarfile.open(batch_tar_path, "w:gz") as tar:
        for file_path in target_files:
            print(f"Processing {file_path.name}...")
            try:
                process_fn(file_path)
                tar.add(file_path, arcname=file_path.name)
                file_path.unlink()
                processed_count += 1
                print(f"-> Successfully processed & archived: {file_path.name}")
            except Exception as e:
                print(f"-> Failed processing {file_path.name}: {e}")

    if processed_count == 0:
        batch_tar_path.unlink(missing_ok=True)
        print("No files were processed successfully.")
    else:
        print(f"\nSUCCESS: Bundled {processed_count} file(s) into {batch_tar_name}.")

    print(f"Pipeline finished in {time.perf_counter() - start_time:.4f} seconds.")
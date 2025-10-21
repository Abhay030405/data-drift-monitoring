"""
Initialize Baseline Dataset Script
Phase 1: Data Ingestion & Quality Setup
Usage: python scripts/init_baseline.py --file path/to/data.csv --description "Training dataset Q1 2025"
"""
import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from backend.app.utils.file_handler import FileHandler
from backend.app.utils.versioning import VersioningManager
from backend.app.utils.logger import NeuralWatchLogger

logger = NeuralWatchLogger.get_logger("init_baseline")


def init_baseline(file_path: str, description: str = None):
    """
    Initialize a baseline dataset from a file
    
    Args:
        file_path: Path to the dataset file
        description: Optional description for the baseline
    """
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False
        
        logger.info(f"Initializing baseline from: {file_path}")
        
        # Initialize handlers
        file_handler = FileHandler()
        versioning_manager = VersioningManager()
        
        # Step 1: Validate file format
        is_valid_format, format_message = file_handler.validate_file_format(file_path.name)
        if not is_valid_format:
            logger.error(format_message)
            return False
        
        logger.info(f"✓ File format valid: {format_message}")
        
        # Step 2: Validate file size
        is_valid_size, size_message = file_handler.validate_file_size(file_path)
        if not is_valid_size:
            logger.error(size_message)
            return False
        
        logger.info(f"✓ File size valid: {size_message}")
        
        # Step 3: Read file
        df, read_error = file_handler.read_file(file_path)
        if df is None:
            logger.error(f"Error reading file: {read_error}")
            return False
        
        logger.info(f"✓ File loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Step 4: Validate DataFrame
        is_valid, validation_message, validation_report = file_handler.validate_dataframe(
            df, file_path.name
        )
        
        if not is_valid:
            logger.error(f"Validation failed: {validation_message}")
            return False
        
        logger.info(f"✓ Validation passed: {validation_message}")
        
        if validation_report.get('warnings'):
            logger.warning("Validation warnings:")
            for warning in validation_report['warnings']:
                logger.warning(f"  - {warning}")
        
        # Step 5: Compute metadata
        metadata = file_handler.compute_metadata(df, file_path.name, file_path)
        logger.info(f"✓ Metadata computed")
        
        # Step 6: Create baseline
        success, message, baseline_info = versioning_manager.create_baseline_version(
            file_path, metadata, description
        )
        
        if not success:
            logger.error(f"Failed to create baseline: {message}")
            return False
        
        logger.info("="*60)
        logger.info(f"✓ Baseline created successfully!")
        logger.info(f"  Version ID: {baseline_info['version_id']}")
        logger.info(f"  Description: {baseline_info['description']}")
        logger.info(f"  Rows: {metadata['rows']:,}")
        logger.info(f"  Columns: {metadata['columns']}")
        logger.info(f"  File Size: {metadata['file_size_mb']:.2f} MB")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False


def main():
    """Main script entry point"""
    parser = argparse.ArgumentParser(
        description="Initialize baseline dataset for Neural Watch"
    )
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to the dataset file (CSV, JSON, or Parquet)"
    )
    parser.add_argument(
        "--description",
        type=str,
        default=None,
        help="Optional description for the baseline"
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("Neural Watch - Baseline Initialization Script")
    logger.info("="*60)
    
    success = init_baseline(args.file, args.description)
    
    if success:
        logger.info("✓ Baseline initialization completed successfully")
        sys.exit(0)
    else:
        logger.error("✗ Baseline initialization failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
"""
Unit Tests for FileHandler
Phase 1: Data Ingestion & Quality Setup
Run with: pytest backend/tests/test_file_handler.py -v
"""
import pytest
import pandas as pd
from pathlib import Path
import sys
import tempfile
import shutil

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from backend.app.utils.file_handler import FileHandler


@pytest.fixture
def file_handler():
    """Fixture to create FileHandler instance"""
    return FileHandler()


@pytest.fixture
def temp_dir():
    """Fixture to create temporary directory"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_dataframe():
    """Fixture to create sample DataFrame"""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', None, 'Eve'],
        'age': [25, 30, 35, 40, 45],
        'salary': [50000, 60000, None, 80000, 90000]
    })


class TestFileFormatValidation:
    """Tests for file format validation"""
    
    def test_valid_csv_format(self, file_handler):
        """Test valid CSV file format"""
        is_valid, message = file_handler.validate_file_format("data.csv")
        assert is_valid is True
        assert "csv" in message.lower()
    
    def test_valid_json_format(self, file_handler):
        """Test valid JSON file format"""
        is_valid, message = file_handler.validate_file_format("data.json")
        assert is_valid is True
        assert "json" in message.lower()
    
    def test_valid_parquet_format(self, file_handler):
        """Test valid Parquet file format"""
        is_valid, message = file_handler.validate_file_format("data.parquet")
        assert is_valid is True
        assert "parquet" in message.lower()
    
    def test_invalid_format(self, file_handler):
        """Test invalid file format"""
        is_valid, message = file_handler.validate_file_format("data.xlsx")
        assert is_valid is False
        assert "unsupported" in message.lower()
    
    def test_case_insensitive(self, file_handler):
        """Test case insensitive format checking"""
        is_valid, _ = file_handler.validate_file_format("data.CSV")
        assert is_valid is True


class TestFileReading:
    """Tests for file reading operations"""
    
    def test_read_csv(self, file_handler, temp_dir, sample_dataframe):
        """Test reading CSV file"""
        csv_path = temp_dir / "test.csv"
        sample_dataframe.to_csv(csv_path, index=False)
        
        df, error = file_handler.read_file(csv_path)
        
        assert df is not None
        assert error == ""
        assert len(df) == 5
        assert list(df.columns) == ['id', 'name', 'age', 'salary']
    
    def test_read_json(self, file_handler, temp_dir, sample_dataframe):
        """Test reading JSON file"""
        json_path = temp_dir / "test.json"
        sample_dataframe.to_json(json_path, orient='records')
        
        df, error = file_handler.read_file(json_path)
        
        assert df is not None
        assert error == ""
        assert len(df) == 5
    
    def test_read_parquet(self, file_handler, temp_dir, sample_dataframe):
        """Test reading Parquet file"""
        parquet_path = temp_dir / "test.parquet"
        sample_dataframe.to_parquet(parquet_path, index=False)
        
        df, error = file_handler.read_file(parquet_path)
        
        assert df is not None
        assert error == ""
        assert len(df) == 5
    
    def test_read_nonexistent_file(self, file_handler, temp_dir):
        """Test reading non-existent file"""
        df, error = file_handler.read_file(temp_dir / "nonexistent.csv")
        
        assert df is None
        assert error != ""


class TestDataFrameValidation:
    """Tests for DataFrame validation"""
    
    def test_valid_dataframe(self, file_handler, sample_dataframe):
        """Test validation of valid DataFrame"""
        is_valid, message, report = file_handler.validate_dataframe(
            sample_dataframe, "test.csv"
        )
        
        assert is_valid is True
        assert report['is_valid'] is True
        assert len(report['errors']) == 0
    
    def test_empty_dataframe(self, file_handler):
        """Test validation of empty DataFrame"""
        empty_df = pd.DataFrame()
        is_valid, message, report = file_handler.validate_dataframe(
            empty_df, "empty.csv"
        )
        
        assert is_valid is False
        assert "empty" in message.lower()
    
    def test_insufficient_rows(self, file_handler):
        """Test validation with insufficient rows"""
        small_df = pd.DataFrame({'col1': [1, 2]})
        is_valid, message, report = file_handler.validate_dataframe(
            small_df, "small.csv"
        )
        
        assert is_valid is False
        assert "insufficient" in message.lower() or "rows" in message.lower()
    
    def test_missing_values_warning(self, file_handler, sample_dataframe):
        """Test warning for high missing values"""
        is_valid, message, report = file_handler.validate_dataframe(
            sample_dataframe, "test.csv"
        )
        
        # sample_dataframe has missing values
        assert len(report['warnings']) > 0
    
    def test_column_schema_match(self, file_handler, sample_dataframe):
        """Test column schema validation against expected columns"""
        expected_columns = ['id', 'name', 'age', 'salary']
        
        is_valid, message, report = file_handler.validate_dataframe(
            sample_dataframe, "test.csv", expected_columns=expected_columns
        )
        
        assert is_valid is True
        assert any("schema matches" in check.lower() for check in report['checks_passed'])
    
    def test_column_schema_mismatch(self, file_handler, sample_dataframe):
        """Test column schema validation with missing columns"""
        expected_columns = ['id', 'name', 'age', 'salary', 'extra_column']
        
        is_valid, message, report = file_handler.validate_dataframe(
            sample_dataframe, "test.csv", expected_columns=expected_columns
        )
        
        assert len(report['warnings']) > 0
        assert any("missing expected columns" in w.lower() for w in report['warnings'])


class TestMetadataComputation:
    """Tests for metadata computation"""
    
    def test_basic_metadata(self, file_handler, temp_dir, sample_dataframe):
        """Test basic metadata extraction"""
        csv_path = temp_dir / "test.csv"
        sample_dataframe.to_csv(csv_path, index=False)
        
        metadata = file_handler.compute_metadata(sample_dataframe, "test.csv", csv_path)
        
        assert metadata['rows'] == 5
        assert metadata['columns'] == 4
        assert metadata['filename'] == "test.csv"
        assert 'column_names' in metadata
        assert 'dtypes' in metadata
        assert 'missing_values' in metadata
    
    def test_missing_values_metadata(self, file_handler, temp_dir, sample_dataframe):
        """Test missing values in metadata"""
        csv_path = temp_dir / "test.csv"
        sample_dataframe.to_csv(csv_path, index=False)
        
        metadata = file_handler.compute_metadata(sample_dataframe, "test.csv", csv_path)
        
        missing = metadata['missing_values']
        assert 'name' in missing['columns_with_missing']
        assert 'salary' in missing['columns_with_missing']
        assert missing['counts']['name'] == 1
        assert missing['counts']['salary'] == 1
    
    def test_duplicate_metadata(self, file_handler, temp_dir):
        """Test duplicate detection in metadata"""
        df_with_duplicates = pd.DataFrame({
            'col1': [1, 2, 2, 3],
            'col2': ['a', 'b', 'b', 'c']
        })
        
        csv_path = temp_dir / "duplicates.csv"
        df_with_duplicates.to_csv(csv_path, index=False)
        
        metadata = file_handler.compute_metadata(df_with_duplicates, "duplicates.csv", csv_path)
        
        assert metadata['duplicates']['count'] == 1
        assert metadata['duplicates']['percentage'] == 25.0


class TestFileSaving:
    """Tests for file saving operations"""
    
    def test_save_csv(self, file_handler, temp_dir, sample_dataframe):
        """Test saving DataFrame as CSV"""
        success, message, saved_path = file_handler.save_file(
            sample_dataframe, temp_dir, "output.csv"
        )
        
        assert success is True
        assert saved_path.exists()
        assert saved_path.suffix == ".csv"
    
    def test_save_json(self, file_handler, temp_dir, sample_dataframe):
        """Test saving DataFrame as JSON"""
        success, message, saved_path = file_handler.save_file(
            sample_dataframe, temp_dir, "output.json"
        )
        
        assert success is True
        assert saved_path.exists()
        assert saved_path.suffix == ".json"
    
    def test_save_parquet(self, file_handler, temp_dir, sample_dataframe):
        """Test saving DataFrame as Parquet"""
        success, message, saved_path = file_handler.save_file(
            sample_dataframe, temp_dir, "output.parquet"
        )
        
        assert success is True
        assert saved_path.exists()
        assert saved_path.suffix == ".parquet"
    
    def test_timestamped_filename(self, file_handler, temp_dir, sample_dataframe):
        """Test that saved files have timestamps"""
        success, message, saved_path = file_handler.save_file(
            sample_dataframe, temp_dir, "data.csv"
        )
        
        assert success is True
        # Filename should contain timestamp
        assert "data_" in saved_path.name
        assert saved_path.name != "data.csv"


class TestDuplicateDetection:
    """Tests for duplicate file detection"""
    
    def test_no_duplicate(self, file_handler, temp_dir, sample_dataframe):
        """Test when no duplicate exists"""
        csv_path = temp_dir / "test.csv"
        sample_dataframe.to_csv(csv_path, index=False)
        
        file_hash = file_handler.compute_file_hash(csv_path)
        is_duplicate, existing = file_handler.check_duplicate_file(file_hash)
        
        # Should not find duplicate (file not in raw path)
        assert is_duplicate is False
    
    def test_compute_file_hash(self, file_handler, temp_dir, sample_dataframe):
        """Test file hash computation"""
        csv_path = temp_dir / "test.csv"
        sample_dataframe.to_csv(csv_path, index=False)
        
        hash1 = file_handler.compute_file_hash(csv_path)
        hash2 = file_handler.compute_file_hash(csv_path)
        
        # Same file should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 16  # Truncated to 16 chars


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
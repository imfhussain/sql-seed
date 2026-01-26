import pytest
from click.testing import CliRunner
from pathlib import Path
from sql_seed.cli import main
import tempfile


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_csv(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("id,name,age\n1,John,25\n2,Jane,30")
    return csv_file


class TestCLI:
    def test_basic_csv_to_stdout(self, runner, sample_csv):
        result = runner.invoke(main, [str(sample_csv)])
        assert result.exit_code == 0
        assert "INSERT INTO" in result.output
        assert "test" in result.output
    
    def test_custom_table_name(self, runner, sample_csv):
        result = runner.invoke(main, [str(sample_csv), "--table", "users"])
        assert result.exit_code == 0
        assert "INSERT INTO users" in result.output
    
    def test_output_to_file(self, runner, sample_csv, tmp_path):
        output_file = tmp_path / "output.sql"
        result = runner.invoke(main, [str(sample_csv), "--output", str(output_file)])
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "INSERT INTO" in content
    
    def test_dialect_option(self, runner, sample_csv):
        result = runner.invoke(main, [str(sample_csv), "--dialect", "mysql"])
        assert result.exit_code == 0
        assert "INSERT INTO" in result.output
    
    def test_batch_size_option(self, runner, sample_csv):
        result = runner.invoke(main, [str(sample_csv), "--batch-size", "1"])
        assert result.exit_code == 0
        assert result.output.count("INSERT INTO") == 2
    
    def test_dry_run_flag(self, runner, sample_csv):
        result = runner.invoke(main, [str(sample_csv), "--dry-run"])
        assert result.exit_code == 0
        assert "-- Showing first 5 INSERT statements" in result.output
    
    def test_create_table_flag(self, runner, sample_csv):
        result = runner.invoke(main, [str(sample_csv), "--create-table"])
        assert result.exit_code == 0
        assert "CREATE TABLE" in result.output
    
    def test_column_mapping(self, runner, sample_csv):
        result = runner.invoke(main, [str(sample_csv), "--columns", "id:user_id,name:full_name"])
        assert result.exit_code == 0
        assert "user_id" in result.output
        assert "full_name" in result.output
    
    def test_nonexistent_file_error(self, runner):
        result = runner.invoke(main, ["nonexistent.csv"])
        assert result.exit_code == 2
    
    def test_invalid_csv_error(self, runner, tmp_path):
        bad_csv = tmp_path / "bad.csv"
        bad_csv.write_text("")
        result = runner.invoke(main, [str(bad_csv)])
        assert result.exit_code == 1
        assert "Error" in result.output

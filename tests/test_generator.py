import pytest
import pandas as pd
from pathlib import Path
from sql_seed.generator import SQLGenerator
import tempfile
import os


@pytest.fixture
def sample_csv(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("id,name,age,price,active,created\n1,John,25,19.99,true,2024-01-15\n2,Jane,30,29.50,false,2024-01-16\n3,Bob,,15.00,1,2024-01-17")
    return csv_file


@pytest.fixture
def empty_csv(tmp_path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("id,name\n")
    return csv_file


class TestSQLGenerator:
    def test_load_csv_success(self, sample_csv):
        generator = SQLGenerator(sample_csv, "users")
        assert len(generator.df) == 3
        assert list(generator.df.columns) == ["id", "name", "age", "price", "active", "created"]
    
    def test_load_csv_with_column_mapping(self, sample_csv):
        mapping = {"id": "user_id", "name": "full_name"}
        generator = SQLGenerator(sample_csv, "users", column_mapping=mapping)
        assert "user_id" in generator.df.columns
        assert "full_name" in generator.df.columns
        assert "id" not in generator.df.columns
    
    def test_load_csv_empty_raises_error(self, empty_csv):
        with pytest.raises(ValueError, match="CSV file is empty"):
            SQLGenerator(empty_csv, "users")
    
    def test_load_csv_nonexistent_raises_error(self):
        with pytest.raises(ValueError, match="Failed to load CSV"):
            SQLGenerator(Path("nonexistent.csv"), "users")
    
    def test_infer_integer_type(self, sample_csv):
        generator = SQLGenerator(sample_csv, "users")
        assert generator.column_types["id"] == "INTEGER"
        assert generator.column_types["age"] == "INTEGER"
    
    def test_infer_decimal_type(self, sample_csv):
        generator = SQLGenerator(sample_csv, "users")
        assert generator.column_types["price"] == "DECIMAL(10,2)"
    
    def test_infer_boolean_type(self, sample_csv):
        generator = SQLGenerator(sample_csv, "users")
        assert generator.column_types["active"] == "BOOLEAN"
    
    def test_infer_date_type(self, sample_csv):
        generator = SQLGenerator(sample_csv, "users")
        assert generator.column_types["created"] == "DATE"
    
    def test_infer_varchar_type(self, sample_csv):
        generator = SQLGenerator(sample_csv, "users")
        assert "VARCHAR" in generator.column_types["name"]
    
    def test_escape_null_values(self, sample_csv):
        generator = SQLGenerator(sample_csv, "users")
        assert generator._escape_value("", "VARCHAR(255)") == "NULL"
        assert generator._escape_value(pd.NA, "INTEGER") == "NULL"
    
    def test_escape_string_with_quotes(self, sample_csv):
        generator = SQLGenerator(sample_csv, "users")
        result = generator._escape_value("O'Brien", "VARCHAR(255)")
        assert result == "'O''Brien'"
    
    def test_escape_string_with_backslash(self, sample_csv):
        generator = SQLGenerator(sample_csv, "users")
        result = generator._escape_value("C:\\path", "VARCHAR(255)")
        assert result == "'C:\\\\path'"
    
    def test_escape_integer_no_quotes(self, sample_csv):
        generator = SQLGenerator(sample_csv, "users")
        assert generator._escape_value(42, "INTEGER") == "42"
    
    def test_escape_boolean_postgresql(self, sample_csv):
        generator = SQLGenerator(sample_csv, "users", dialect="postgresql")
        assert generator._escape_value("true", "BOOLEAN") == "TRUE"
        assert generator._escape_value("false", "BOOLEAN") == "FALSE"
    
    def test_escape_boolean_mysql(self, sample_csv):
        generator = SQLGenerator(sample_csv, "users", dialect="mysql")
        assert generator._escape_value("true", "BOOLEAN") == "1"
        assert generator._escape_value("false", "BOOLEAN") == "0"
    
    def test_generate_insert_statements(self, sample_csv):
        generator = SQLGenerator(sample_csv, "users", batch_size=2)
        output = generator.generate()
        assert "INSERT INTO users" in output
        assert "VALUES" in output
        assert "John" in output
    
    def test_generate_with_create_table(self, sample_csv):
        generator = SQLGenerator(sample_csv, "users")
        output = generator.generate(include_create_table=True)
        assert "CREATE TABLE" in output
        assert "users" in output
    
    def test_generate_dry_run(self, sample_csv):
        generator = SQLGenerator(sample_csv, "users")
        output = generator.generate(dry_run=True)
        assert "-- Showing first 5 INSERT statements" in output
    
    def test_batch_size_splits_correctly(self, tmp_path):
        csv_file = tmp_path / "large.csv"
        rows = "\n".join([f"{i},Name{i}" for i in range(250)])
        csv_file.write_text(f"id,name\n{rows}")
        generator = SQLGenerator(csv_file, "users", batch_size=100)
        output = generator.generate()
        assert output.count("INSERT INTO") == 3
    
    def test_different_dialects(self, sample_csv):
        for dialect in ["postgresql", "mysql", "sqlite"]:
            generator = SQLGenerator(sample_csv, "users", dialect=dialect)
            output = generator.generate()
            assert "INSERT INTO" in output

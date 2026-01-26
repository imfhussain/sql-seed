# sql-seed

Generate realistic SQL INSERT statements from CSV files with automatic type inference and batch sizing

## Features

- Parse CSV files and automatically infer column data types (INTEGER, VARCHAR, DECIMAL, DATE, BOOLEAN, NULL)
- Generate batched INSERT statements with configurable batch size (default 100 rows per statement)
- Support multiple SQL dialects: PostgreSQL, MySQL, SQLite with appropriate syntax differences
- Handle NULL values correctly with SQL NULL keyword instead of empty strings
- Escape special characters in string values (quotes, backslashes) according to SQL standards
- Detect and preserve numeric types (integers vs decimals) without unnecessary quotes
- Generate table name from CSV filename or accept custom table name via CLI flag
- Output to stdout or write directly to file with --output flag
- Show preview mode with --dry-run flag that displays first 5 INSERT statements
- Support custom column name mapping via --columns flag for renaming CSV headers
- Validate CSV structure and provide helpful error messages for malformed input
- Option to include CREATE TABLE statement based on inferred types with --create-table flag

## How to Use

Use this project when you need to:

- Quickly solve problems related to sql-seed
- Integrate python functionality into your workflow
- Learn how python handles common patterns with click

## Installation

```bash
# Clone the repository
git clone https://github.com/KurtWeston/sql-seed.git
cd sql-seed

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Built With

- python using click

## Dependencies

- `click`
- `pandas`

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

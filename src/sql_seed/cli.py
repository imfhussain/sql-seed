import click
import sys
from pathlib import Path
from .generator import SQLGenerator


@click.command()
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--table', '-t', help='Table name (defaults to CSV filename)')
@click.option('--dialect', '-d', type=click.Choice(['postgresql', 'mysql', 'sqlite']), default='postgresql', help='SQL dialect')
@click.option('--batch-size', '-b', type=int, default=100, help='Rows per INSERT statement')
@click.option('--output', '-o', type=click.Path(), help='Output file (defaults to stdout)')
@click.option('--dry-run', is_flag=True, help='Show first 5 INSERT statements only')
@click.option('--create-table', is_flag=True, help='Include CREATE TABLE statement')
@click.option('--columns', help='Column mapping (e.g., "id:user_id,name:full_name")')
def main(csv_file, table, dialect, batch_size, output, dry_run, create_table, columns):
    """Generate SQL INSERT statements from CSV files."""
    try:
        csv_path = Path(csv_file)
        if not table:
            table = csv_path.stem
        
        column_mapping = None
        if columns:
            column_mapping = dict(pair.split(':') for pair in columns.split(','))
        
        generator = SQLGenerator(
            csv_path=csv_path,
            table_name=table,
            dialect=dialect,
            batch_size=batch_size,
            column_mapping=column_mapping
        )
        
        sql_output = generator.generate(include_create_table=create_table, dry_run=dry_run)
        
        if output:
            Path(output).write_text(sql_output)
            click.echo(f"SQL written to {output}", err=True)
        else:
            click.echo(sql_output)
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

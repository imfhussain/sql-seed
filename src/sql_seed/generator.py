import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional, Any


class SQLGenerator:
    def __init__(self, csv_path: Path, table_name: str, dialect: str = 'postgresql',
                 batch_size: int = 100, column_mapping: Optional[Dict[str, str]] = None):
        self.csv_path = csv_path
        self.table_name = table_name
        self.dialect = dialect
        self.batch_size = batch_size
        self.column_mapping = column_mapping or {}
        self.df = self._load_csv()
        self.column_types = self._infer_types()
    
    def _load_csv(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.csv_path, keep_default_na=False)
            if df.empty:
                raise ValueError("CSV file is empty")
            if self.column_mapping:
                df = df.rename(columns=self.column_mapping)
            return df
        except Exception as e:
            raise ValueError(f"Failed to load CSV: {str(e)}")
    
    def _infer_types(self) -> Dict[str, str]:
        types = {}
        for col in self.df.columns:
            types[col] = self._infer_column_type(self.df[col])
        return types
    
    def _infer_column_type(self, series: pd.Series) -> str:
        non_empty = series[series != '']
        if len(non_empty) == 0:
            return 'VARCHAR(255)'
        
        if non_empty.apply(lambda x: str(x).lower() in ['true', 'false', '1', '0']).all():
            return 'BOOLEAN'
        
        if non_empty.apply(self._is_integer).all():
            return 'INTEGER'
        
        if non_empty.apply(self._is_decimal).all():
            return 'DECIMAL(10,2)'
        
        if non_empty.apply(self._is_date).all():
            return 'DATE'
        
        max_len = non_empty.astype(str).str.len().max()
        return f'VARCHAR({max(max_len + 50, 255)})'
    
    def _is_integer(self, val: Any) -> bool:
        try:
            return str(val).strip() and float(val) == int(float(val))
        except (ValueError, TypeError):
            return False
    
    def _is_decimal(self, val: Any) -> bool:
        try:
            float(val)
            return True
        except (ValueError, TypeError):
            return False
    
    def _is_date(self, val: Any) -> bool:
        date_patterns = [r'^\d{4}-\d{2}-\d{2}$', r'^\d{2}/\d{2}/\d{4}$']
        return any(re.match(pattern, str(val)) for pattern in date_patterns)
    
    def _escape_value(self, val: Any, col_type: str) -> str:
        if val == '' or pd.isna(val):
            return 'NULL'
        
        if col_type in ['INTEGER', 'DECIMAL(10,2)']:
            return str(val)
        
        if col_type == 'BOOLEAN':
            bool_val = str(val).lower() in ['true', '1']
            if self.dialect == 'mysql':
                return '1' if bool_val else '0'
            return 'TRUE' if bool_val else 'FALSE'
        
        escaped = str(val).replace('\\', '\\\\').replace("'", "''")
        return f"'{escaped}'"
    
    def _generate_create_table(self) -> str:
        lines = [f"CREATE TABLE {self.table_name} ("]
        for i, (col, col_type) in enumerate(self.column_types.items()):
            comma = ',' if i < len(self.column_types) - 1 else ''
            lines.append(f"  {col} {col_type}{comma}")
        lines.append(");\n")
        return '\n'.join(lines)
    
    def _generate_insert_batch(self, rows: List[Dict]) -> str:
        if not rows:
            return ''
        
        columns = ', '.join(self.df.columns)
        values_list = []
        
        for row in rows:
            values = [self._escape_value(row[col], self.column_types[col]) for col in self.df.columns]
            values_list.append(f"({', '.join(values)})")
        
        if self.dialect == 'mysql':
            values_str = ',\n  '.join(values_list)
            return f"INSERT INTO {self.table_name} ({columns})\nVALUES\n  {values_str};\n"
        else:
            values_str = ',\n  '.join(values_list)
            return f"INSERT INTO {self.table_name} ({columns})\nVALUES\n  {values_str};\n"
    
    def generate(self, include_create_table: bool = False, dry_run: bool = False) -> str:
        output = []
        
        if include_create_table:
            output.append(self._generate_create_table())
        
        rows = self.df.to_dict('records')
        limit = 5 if dry_run else len(rows)
        
        for i in range(0, min(limit, len(rows)), self.batch_size):
            batch = rows[i:i + self.batch_size]
            if dry_run and i >= 5:
                break
            output.append(self._generate_insert_batch(batch[:min(self.batch_size, 5 - i if dry_run else self.batch_size)]))
        
        return '\n'.join(output)

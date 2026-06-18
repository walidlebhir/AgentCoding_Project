#!/usr/bin/env python
"""
Database Diagnostic and Migration Tool
Analyzes the PostgreSQL database schema and identifies missing columns
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from sqlalchemy import inspect, text, MetaData, Table
from src.Config.database import engine, SessionLocal
from src.models.project import Project
from src.models.user import User

def get_db_columns():
    """Get actual columns in PostgreSQL projects table."""
    inspector = inspect(engine)
    if not inspector.has_table("projects"):
        return None
    
    columns = inspector.get_columns("projects")
    return {col["name"]: col for col in columns}

def get_model_columns():
    """Get columns defined in SQLAlchemy Project model."""
    mapper = inspect(Project)
    return {col.key: col for col in mapper.columns}

def compare_schemas():
    """Compare SQLAlchemy model with PostgreSQL schema."""
    print("\n" + "="*70)
    print("DATABASE SCHEMA ANALYSIS")
    print("="*70)
    
    db_cols = get_db_columns()
    model_cols = get_model_columns()
    
    if db_cols is None:
        print("❌ ERROR: 'projects' table does not exist in PostgreSQL!")
        print("\nYou need to:")
        print("  1. Create the table using: python fix_database.py --init")
        print("  2. Or manually run create_tables in the application startup")
        return False
    
    print(f"\n📊 SUMMARY:")
    print(f"  SQLAlchemy Model: {len(model_cols)} columns")
    print(f"  PostgreSQL Table: {len(db_cols)} columns")
    
    # Find missing columns
    missing = set(model_cols.keys()) - set(db_cols.keys())
    extra = set(db_cols.keys()) - set(model_cols.keys())
    
    if not missing and not extra:
        print("\n✅ SCHEMAS ARE IN SYNC - No mismatches found!")
        return True
    
    if missing:
        print(f"\n⚠️  MISSING IN DATABASE ({len(missing)} columns):")
        for col_name in sorted(missing):
            col = model_cols[col_name]
            col_type = str(col.type)
            nullable = "NULL" if col.nullable else "NOT NULL"
            print(f"  - {col_name:<25} {col_type:<30} {nullable}")
    
    if extra:
        print(f"\n⚠️  EXTRA IN DATABASE ({len(extra)} columns):")
        for col_name in sorted(extra):
            col = db_cols[col_name]
            print(f"  - {col_name:<25} {col['type']}")
    
    print("\n" + "-"*70)
    print("DETAILED COMPARISON:")
    print("-"*70)
    print(f"{'Column Name':<30} {'Model':<25} {'Database':<25} {'Status'}")
    print("-"*70)
    
    all_cols = set(model_cols.keys()) | set(db_cols.keys())
    for col_name in sorted(all_cols):
        in_model = col_name in model_cols
        in_db = col_name in db_cols
        
        model_type = str(model_cols[col_name].type) if in_model else "N/A"
        db_type = str(db_cols[col_name]["type"]) if in_db else "N/A"
        
        if in_model and in_db:
            status = "✓ OK"
        elif in_model and not in_db:
            status = "❌ MISSING"
        else:
            status = "⚠️  EXTRA"
        
        print(f"{col_name:<30} {model_type:<25} {db_type:<25} {status}")
    
    return not (missing or extra)

def generate_migration_sql():
    """Generate SQL migration script."""
    db_cols = get_db_columns()
    model_cols = get_model_columns()
    
    if db_cols is None:
        return None
    
    missing = set(model_cols.keys()) - set(db_cols.keys())
    
    if not missing:
        return None
    
    sql_statements = []
    
    for col_name in sorted(missing):
        col = model_cols[col_name]
        col_type = str(col.type)
        nullable = "NULL" if col.nullable else "NOT NULL"
        default = ""
        
        # Map SQLAlchemy types to PostgreSQL types
        if "VARCHAR" in col_type:
            pg_type = col_type
        elif "TEXT" in col_type:
            pg_type = "TEXT"
        elif "FLOAT" in col_type or "DOUBLE" in col_type:
            pg_type = "DOUBLE PRECISION"
        elif "INTEGER" in col_type:
            pg_type = "INTEGER"
        elif "DATETIME" in col_type or "TIMESTAMP" in col_type:
            pg_type = "TIMESTAMP WITH TIME ZONE"
        else:
            pg_type = col_type
        
        sql = f"ALTER TABLE projects ADD COLUMN IF NOT EXISTS {col_name} {pg_type} {nullable}{default};"
        sql_statements.append(sql)
    
    return sql_statements

def main():
    """Main diagnostic function."""
    print("\n🔍 PostgreSQL Database Diagnostic Tool")
    print("="*70)
    
    # Connect to database
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("\n✅ Database connection: OK")
    except Exception as e:
        print(f"\n❌ Database connection FAILED: {e}")
        return False
    
    # Compare schemas
    schemas_match = compare_schemas()
    
    # Generate migration if needed
    if not schemas_match:
        migration_sql = generate_migration_sql()
        
        if migration_sql:
            print("\n" + "="*70)
            print("SQL MIGRATION SCRIPT")
            print("="*70)
            print("\nRun these SQL statements:\n")
            for stmt in migration_sql:
                print(stmt)
            
            print("\n" + "="*70)
            print("Or run: python fix_database.py --migrate")
            print("="*70)
            return False
    
    print("\n" + "="*70)
    print("✅ Database schema is up to date!")
    print("="*70)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

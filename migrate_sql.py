#!/usr/bin/env python
"""
Alternative: Direct SQL migration script for PostgreSQL
Use if you prefer manual SQL or Python scripts aren't working
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def get_migration_sql():
    """Get all required SQL migration statements."""
    return [
        # Add missing columns to projects table
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS language VARCHAR(50);",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS prompt TEXT;",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS steps TEXT;",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS folder_name VARCHAR(100);",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS download_url VARCHAR(500);",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS provider VARCHAR(50);",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS model VARCHAR(100);",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS generation_time DOUBLE PRECISION;",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();",
        
        # Create indexes for better query performance
        "CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects(user_id);",
        "CREATE INDEX IF NOT EXISTS ix_projects_created_at ON projects(created_at);",
        "CREATE INDEX IF NOT EXISTS ix_projects_updated_at ON projects(updated_at);",
        "CREATE INDEX IF NOT EXISTS ix_projects_folder_name ON projects(folder_name);",
    ]

def run_migrations():
    """Run the migrations."""
    from sqlalchemy import text
    from src.Config.database import engine
    
    print("\n" + "="*70)
    print("Direct PostgreSQL Migration")
    print("="*70)
    
    statements = get_migration_sql()
    
    print(f"\nExecuting {len(statements)} SQL statements...\n")
    
    try:
        with engine.connect() as connection:
            for idx, stmt in enumerate(statements, 1):
                print(f"[{idx:2d}/{len(statements)}] {stmt[:60]}...")
                try:
                    connection.execute(text(stmt))
                except Exception as e:
                    # Column might already exist, continue
                    if "already exists" in str(e) or "duplicate" in str(e).lower():
                        print(f"        ↳ Column already exists (skipped)")
                    else:
                        print(f"        ↳ Warning: {e}")
            
            connection.commit()
        
        print("\n✅ Migration completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False

def get_migration_sql_for_export():
    """Get SQL statements formatted for copy-paste."""
    return """
-- PostgreSQL Migration: Add missing columns to projects table
-- Run this SQL in your PostgreSQL database if the migration scripts don't work

BEGIN TRANSACTION;

-- Add language column
ALTER TABLE projects ADD COLUMN IF NOT EXISTS language VARCHAR(50) NULL;

-- Add prompt column
ALTER TABLE projects ADD COLUMN IF NOT EXISTS prompt TEXT NULL;

-- Add steps column
ALTER TABLE projects ADD COLUMN IF NOT EXISTS steps TEXT NULL;

-- Add folder_name column
ALTER TABLE projects ADD COLUMN IF NOT EXISTS folder_name VARCHAR(100) NULL;

-- Add download_url column
ALTER TABLE projects ADD COLUMN IF NOT EXISTS download_url VARCHAR(500) NULL;

-- Add provider column
ALTER TABLE projects ADD COLUMN IF NOT EXISTS provider VARCHAR(50) NULL;

-- Add model column
ALTER TABLE projects ADD COLUMN IF NOT EXISTS model VARCHAR(100) NULL;

-- Add generation_time column
ALTER TABLE projects ADD COLUMN IF NOT EXISTS generation_time DOUBLE PRECISION NULL;

-- Add created_at column if missing (should exist, but just in case)
ALTER TABLE projects ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();

-- Add updated_at column if missing (should exist, but just in case)
ALTER TABLE projects ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS ix_projects_created_at ON projects(created_at);
CREATE INDEX IF NOT EXISTS ix_projects_updated_at ON projects(updated_at);
CREATE INDEX IF NOT EXISTS ix_projects_folder_name ON projects(folder_name);

COMMIT;

-- Verify the migration
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'projects' 
ORDER BY ordinal_position;
"""

if __name__ == "__main__":
    # Option 1: Run migrations directly via SQLAlchemy
    if "--run" in sys.argv:
        success = run_migrations()
        sys.exit(0 if success else 1)
    
    # Option 2: Print SQL for manual execution
    if "--print-sql" in sys.argv:
        print(get_migration_sql_for_export())
        sys.exit(0)
    
    # Default: Show help
    print("\nDirect SQL Migration Tool")
    print("-" * 70)
    print("\nUsage:")
    print("  python migrate_sql.py --run       # Run migrations via SQLAlchemy")
    print("  python migrate_sql.py --print-sql # Print SQL for copy-paste")
    print("\nExample copy-paste SQL:")
    print("-" * 70)
    print(get_migration_sql_for_export())

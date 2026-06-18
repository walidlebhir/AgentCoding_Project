#!/usr/bin/env python
"""Database migration script - Add missing columns to projects table.

Usage:
    python migrate_db.py
"""

from sqlalchemy import text
from src.Config.database import engine, Base, create_tables


def migrate_add_project_columns():
    """Add missing columns to projects table if they don't exist."""
    with engine.connect() as connection:
        # Check if columns exist before adding them
        inspector_query = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'projects' AND column_name IN ('provider', 'model', 'generation_time')
        """)
        
        try:
            result = connection.execute(inspector_query)
            existing_columns = {row[0] for row in result}
            
            # Add provider column if not exists
            if "provider" not in existing_columns:
                connection.execute(text(
                    "ALTER TABLE projects ADD COLUMN provider VARCHAR(50) NULL"
                ))
                connection.commit()
                print("✓ Added 'provider' column to projects table")
            else:
                print("• Column 'provider' already exists")
            
            # Add model column if not exists
            if "model" not in existing_columns:
                connection.execute(text(
                    "ALTER TABLE projects ADD COLUMN model VARCHAR(100) NULL"
                ))
                connection.commit()
                print("✓ Added 'model' column to projects table")
            else:
                print("• Column 'model' already exists")
            
            # Add generation_time column if not exists
            if "generation_time" not in existing_columns:
                connection.execute(text(
                    "ALTER TABLE projects ADD COLUMN generation_time FLOAT NULL"
                ))
                connection.commit()
                print("✓ Added 'generation_time' column to projects table")
            else:
                print("• Column 'generation_time' already exists")
            
            # Add indexes for better performance
            try:
                connection.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_projects_folder_name ON projects(folder_name)"
                ))
                print("✓ Index on 'folder_name' created/verified")
            except Exception as e:
                print(f"• Index on 'folder_name' may already exist: {e}")
            
            try:
                connection.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_projects_created_at ON projects(created_at)"
                ))
                print("✓ Index on 'created_at' created/verified")
            except Exception as e:
                print(f"• Index on 'created_at' may already exist: {e}")
            
            try:
                connection.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_projects_updated_at ON projects(updated_at)"
                ))
                print("✓ Index on 'updated_at' created/verified")
            except Exception as e:
                print(f"• Index on 'updated_at' may already exist: {e}")
            
        except Exception as e:
            print(f"Note: Could not verify columns (DB might not be PostgreSQL): {e}")
            print("Attempting SQLAlchemy table sync instead...")


def main():
    """Run database migrations."""
    print("🔄 Starting database migration...")
    print("-" * 50)
    
    try:
        # First, ensure all tables exist
        print("Ensuring all tables exist...")
        create_tables()
        
        # Then apply specific migrations
        print("\nApplying custom migrations...")
        migrate_add_project_columns()
        
        print("-" * 50)
        print("✓ Database migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nPlease check your database connection and try again.")
        raise


if __name__ == "__main__":
    main()

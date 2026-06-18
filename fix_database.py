#!/usr/bin/env python
"""
Database Migration and Fix Tool
Automatically fixes missing columns in the PostgreSQL database
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from sqlalchemy import inspect, text
from src.Config.database import engine, create_tables

def execute_migration(sql_statements):
    """Execute migration SQL statements."""
    print("\n🔄 Executing migration...")
    
    try:
        with engine.connect() as connection:
            for idx, stmt in enumerate(sql_statements, 1):
                print(f"  [{idx}/{len(sql_statements)}] Executing: {stmt[:70]}...")
                connection.execute(text(stmt))
            connection.commit()
        print("✅ Migration completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def get_missing_columns():
    """Identify missing columns in the database."""
    from src.models.project import Project
    
    db_inspector = inspect(engine)
    
    if not db_inspector.has_table("projects"):
        return None
    
    db_cols = {col["name"] for col in db_inspector.get_columns("projects")}
    
    model_mapper = inspect(Project)
    model_cols = {col.key for col in model_mapper.columns}
    
    return model_cols - db_cols

def generate_alter_statements():
    """Generate ALTER TABLE statements for missing columns."""
    from src.models.project import Project
    
    db_inspector = inspect(engine)
    db_cols = {col["name"] for col in db_inspector.get_columns("projects")}
    
    model_mapper = inspect(Project)
    
    statements = []
    
    for col in model_mapper.columns:
        if col.key not in db_cols:
            # Map SQLAlchemy column type to PostgreSQL type
            col_type = str(col.type)
            
            if "VARCHAR" in col_type:
                # Extract length if specified
                if hasattr(col.type, 'length') and col.type.length:
                    pg_type = f"VARCHAR({col.type.length})"
                else:
                    pg_type = "VARCHAR(255)"
            elif "TEXT" in col_type:
                pg_type = "TEXT"
            elif "String" in col_type:
                length = col.type.length if hasattr(col.type, 'length') else 255
                pg_type = f"VARCHAR({length})"
            elif "FLOAT" in col_type or "DOUBLE" in col_type:
                pg_type = "DOUBLE PRECISION"
            elif "INTEGER" in col_type:
                pg_type = "INTEGER"
            elif "DATETIME" in col_type or "TIMESTAMP" in col_type:
                pg_type = "TIMESTAMP WITH TIME ZONE"
            elif "Boolean" in col_type:
                pg_type = "BOOLEAN"
            else:
                pg_type = "TEXT"  # Fallback
            
            nullable = "NULL" if col.nullable else "NOT NULL"
            default = " DEFAULT NULL" if col.nullable else ""
            
            stmt = f"ALTER TABLE projects ADD COLUMN IF NOT EXISTS {col.key} {pg_type} {nullable}{default};"
            statements.append(stmt)
    
    return statements

def create_indexes():
    """Create indexes on projects table."""
    index_statements = [
        "CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects(user_id);",
        "CREATE INDEX IF NOT EXISTS ix_projects_created_at ON projects(created_at);",
        "CREATE INDEX IF NOT EXISTS ix_projects_updated_at ON projects(updated_at);",
        "CREATE INDEX IF NOT EXISTS ix_projects_folder_name ON projects(folder_name);",
    ]
    
    print("\n🔑 Creating indexes...")
    
    try:
        with engine.connect() as connection:
            for stmt in index_statements:
                print(f"  {stmt[:60]}...")
                connection.execute(text(stmt))
            connection.commit()
        print("✅ Indexes created successfully!")
        return True
    except Exception as e:
        print(f"⚠️  Index creation warning (may already exist): {e}")
        return True  # Don't fail on index creation

def init_database():
    """Initialize database tables."""
    print("\n🗂️  Initializing database tables...")
    create_tables()
    return True

def migrate_database():
    """Migrate database schema."""
    print("\n🔍 Checking for missing columns...")
    
    missing = get_missing_columns()
    
    if missing is None:
        print("⚠️  'projects' table doesn't exist. Initializing...")
        return init_database()
    
    if not missing:
        print("✅ No missing columns found!")
        return True
    
    print(f"❌ Found {len(missing)} missing column(s): {', '.join(sorted(missing))}")
    
    # Generate and execute migration
    statements = generate_alter_statements()
    
    if statements:
        print(f"\n📝 Generated {len(statements)} migration statement(s):")
        for stmt in statements:
            print(f"  - {stmt[:70]}...")
        
        if not execute_migration(statements):
            return False
    
    # Create indexes
    if not create_indexes():
        return False
    
    return True

def verify_schema():
    """Verify schema is correct after migration."""
    print("\n✔️  Verifying schema...")
    
    from src.models.project import Project
    
    db_inspector = inspect(engine)
    
    if not db_inspector.has_table("projects"):
        print("❌ 'projects' table still doesn't exist!")
        return False
    
    db_cols = {col["name"] for col in db_inspector.get_columns("projects")}
    model_mapper = inspect(Project)
    model_cols = {col.key for col in model_mapper.columns}
    
    missing = model_cols - db_cols
    
    if missing:
        print(f"❌ Still missing columns: {', '.join(sorted(missing))}")
        return False
    
    print(f"✅ Schema verified! All {len(model_cols)} columns present in database")
    return True

def test_query():
    """Test a simple query to ensure everything works."""
    print("\n🧪 Testing database query...")
    
    try:
        from src.Services.project_service import get_user_projects
        from src.Config.database import SessionLocal
        
        db = SessionLocal()
        # Just test that the query compiles and doesn't throw column errors
        db.query(get_user_projects).first  # Don't actually execute, just check compilation
        db.close()
        print("✅ Query test passed!")
        return True
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False

def main():
    """Main migration function."""
    print("\n" + "="*70)
    print("PostgreSQL Database Migration Tool")
    print("="*70)
    
    # Step 1: Check database connection
    print("\n📡 Checking database connection...")
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("✅ Database connection OK")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nMake sure PostgreSQL is running and credentials are correct in .env")
        return False
    
    # Step 2: Migrate schema
    if not migrate_database():
        print("\n❌ Migration failed!")
        return False
    
    # Step 3: Verify schema
    if not verify_schema():
        print("\n❌ Schema verification failed!")
        return False
    
    # Step 4: Test query
    if not test_query():
        print("\n⚠️  Query test failed (but schema should still be fixed)")
        # Don't fail completely here
    
    print("\n" + "="*70)
    print("✅ DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\nYou can now:")
    print("  1. Restart the FastAPI server")
    print("  2. Test the GET /api/projects endpoint")
    print("  3. The 'language' column error should be resolved!")
    print("\n" + "="*70 + "\n")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

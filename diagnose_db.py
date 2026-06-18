#!/usr/bin/env python
"""Diagnostic script for SQLAlchemy F405 error resolution.

Usage:
    python diagnose_db.py
"""

from sqlalchemy import text, inspect
from src.Config.database import engine, SessionLocal
from src.models.project import Project
from src.models.user import User


def check_database_connection():
    """Verify database connection."""
    print("\n🔌 Checking database connection...")
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        print("✓ Database connection OK")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def check_table_structure():
    """Verify Project table structure."""
    print("\n📋 Checking Project table structure...")
    try:
        inspector = inspect(engine)
        
        # Get table info
        if not inspector.has_table("projects"):
            print("❌ Table 'projects' does not exist")
            return False
        
        columns = inspector.get_columns("projects")
        column_names = {col["name"] for col in columns}
        
        required_columns = {
            "id", "user_id", "name", "description", "language",
            "prompt", "steps", "folder_name", "download_url",
            "provider", "model", "generation_time",
            "created_at", "updated_at"
        }
        
        missing = required_columns - column_names
        extra = column_names - required_columns
        
        print(f"✓ Table 'projects' exists")
        print(f"  Total columns: {len(column_names)}")
        print(f"  Required columns: {len(required_columns)}")
        
        if missing:
            print(f"\n  ⚠️  Missing columns ({len(missing)}):")
            for col in sorted(missing):
                print(f"     - {col}")
        
        if extra:
            print(f"\n  ℹ️  Extra columns ({len(extra)}):")
            for col in sorted(extra):
                print(f"     - {col}")
        
        if not missing:
            print("✓ All required columns present")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Table structure check failed: {e}")
        return False


def check_indexes():
    """Verify indexes on Project table."""
    print("\n🔑 Checking indexes on 'projects' table...")
    try:
        inspector = inspect(engine)
        indexes = inspector.get_indexes("projects")
        index_names = {idx["name"] for idx in indexes}
        
        expected_indexes = {
            "ix_projects_user_id",
            "ix_projects_folder_name",
            "ix_projects_created_at",
            "ix_projects_updated_at",
        }
        
        print(f"  Total indexes: {len(index_names)}")
        print(f"  Indexes found:")
        for idx in indexes:
            status = "✓" if idx["name"] in expected_indexes else "ℹ️"
            columns = ", ".join(idx["column_names"])
            print(f"    {status} {idx['name']} ({columns})")
        
        missing_indexes = expected_indexes - index_names
        if missing_indexes:
            print(f"\n  ⚠️  Missing indexes ({len(missing_indexes)}):")
            for idx in sorted(missing_indexes):
                print(f"     - {idx}")
            return False
        else:
            print("✓ All expected indexes present")
            return True
            
    except Exception as e:
        print(f"⚠️  Could not verify indexes: {e}")
        return False


def check_models():
    """Verify SQLAlchemy models."""
    print("\n🗂️  Checking SQLAlchemy models...")
    try:
        # Check Project model columns
        proj_mapper = inspect(Project)
        proj_columns = {col.key for col in proj_mapper.columns}
        
        required_attrs = {
            "id", "user_id", "name", "description", "language",
            "prompt", "steps", "folder_name", "download_url",
            "provider", "model", "generation_time",
            "created_at", "updated_at"
        }
        
        missing = required_attrs - proj_columns
        
        print(f"✓ Project model has {len(proj_columns)} columns")
        
        if missing:
            print(f"  ❌ Missing attributes ({len(missing)}):")
            for attr in sorted(missing):
                print(f"     - {attr}")
            return False
        else:
            print("✓ All required attributes present")
            
        # Check relationships
        proj_relations = {rel.key for rel in proj_mapper.relationships}
        print(f"\n✓ Project relationships: {', '.join(proj_relations)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model check failed: {e}")
        return False


def check_query_execution():
    """Test actual query execution."""
    print("\n⚙️  Testing query execution...")
    try:
        db = SessionLocal()
        
        # Test simple query
        try:
            # This will test the get_user_projects-like query
            query = db.query(Project).order_by(Project.created_at.desc())
            result = query.first()
            print("✓ Query with order_by(created_at) executed successfully")
        except Exception as e:
            print(f"❌ Query execution failed: {e}")
            return False
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False


def check_user_table():
    """Verify User table (dependency)."""
    print("\n👤 Checking User table...")
    try:
        inspector = inspect(engine)
        
        if not inspector.has_table("users"):
            print("❌ Table 'users' does not exist")
            return False
        
        columns = inspector.get_columns("users")
        column_names = {col["name"] for col in columns}
        
        print(f"✓ Table 'users' exists")
        print(f"  Columns: {', '.join(sorted(column_names))}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  User table check failed: {e}")
        return False


def main():
    """Run all diagnostic checks."""
    print("=" * 60)
    print("SQLAlchemy F405 Error - Diagnostic Tool")
    print("=" * 60)
    
    checks = [
        ("Database Connection", check_database_connection),
        ("User Table", check_user_table),
        ("Project Table Structure", check_table_structure),
        ("Project Indexes", check_indexes),
        ("SQLAlchemy Models", check_models),
        ("Query Execution", check_query_execution),
    ]
    
    results = {}
    for name, check_func in checks:
        results[name] = check_func()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("-" * 60)
    print(f"Result: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✅ All checks passed! SQLAlchemy F405 error should be resolved.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} check(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

#!/usr/bin/env python
"""
QUICK FIX - Résoudre "Column language n'existe pas" en 5 minutes
Exécutez ce script et c'est fini!
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def main():
    print("\n" + "="*70)
    print("🚀 QUICK FIX - PostgreSQL Column Migration")
    print("="*70)
    
    # Step 1: Diagnostic
    print("\n[STEP 1/3] Running diagnostic...\n")
    os.system(f"{sys.executable} diagnose_schema.py")
    
    input("\n⏸️  Press ENTER to continue with migration...")
    
    # Step 2: Migration
    print("\n[STEP 2/3] Running migration...\n")
    success = os.system(f"{sys.executable} fix_database.py") == 0
    
    if not success:
        print("\n❌ Migration failed!")
        return False
    
    # Step 3: Summary
    print("\n[STEP 3/3] Summary\n")
    print("-" * 70)
    print("✅ Migration completed successfully!")
    print("\nNow do this:")
    print("  1. Stop the FastAPI server (Ctrl+C)")
    print("  2. Restart it: uvicorn src.Server:app --reload")
    print("  3. Test: curl http://localhost:8000/api/projects")
    print("-" * 70)
    print("\nThe error 'Column language n'existe pas' is now fixed! 🎉\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

"""
Cloud Storage System - Universal Setup Script
Works on Windows, Linux, and Mac
Run: python setup_cloud_storage.py
"""
import subprocess
import sys
import os


def print_header(text):
    """Print colored header"""
    print("\n" + "=" * 60)
    print(f"   {text}")
    print("=" * 60 + "\n")


def print_step(step_num, total, text):
    """Print step information"""
    print(f"[{step_num}/{total}] {text}")
    print()


def run_command(command, error_message):
    """Run command and handle errors"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=False,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ ERROR: {error_message}")
        print(f"Command failed: {command}")
        return False


def main():
    """Main setup function"""
    print_header("CLOUD STORAGE SYSTEM - QUICK SETUP")
    
    # Step 1: Install packages
    print_step(1, 2, "Installing required packages...")
    
    packages = [
        "sqlalchemy",
        "asyncpg",
        "pandas",
        "python-docx",
        "aiosqlite",
        "alembic",
        "beautifulsoup4",
        "lxml"
    ]
    
    install_cmd = f"{sys.executable} -m pip install {' '.join(packages)}"
    
    if not run_command(install_cmd, "Failed to install packages"):
        print("\nPlease check your Python installation")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print("✓ Packages installed successfully\n")
    
    # Step 2: Fix all database issues
    print_step(2, 2, "Fixing all database issues...")
    
    fix_database_cmd = f"{sys.executable} fix_all_database.py"
    
    if not run_command(fix_database_cmd, "Failed to fix database"):
        print("\nPlease check your database connection")
        print("Make sure DATABASE_URL is set correctly in database.py")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print("✓ Database fixed successfully\n")
    
    # Success
    print_header("SETUP COMPLETE!")
    
    print("✓ Cloud storage system is ready to use!\n")
    print("Next steps:")
    print("  1. Start backend: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    print("  2. Open http://localhost:8000/docs")
    print("  3. Look for 'Cloud Storage' section")
    print("  4. Test the endpoints\n")
    
    input("Press Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

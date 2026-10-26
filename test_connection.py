import sys
from config.database import test_connection, ensure_database_exists

def main():
    print("=" * 60)
    print("PostgreSQL Database Connection Diagnostic")
    print("=" * 60)
    
    # Try testing database
    if not test_connection():
        print("\nAttempting to create database automatically if PostgreSQL service is reachable...")
        if ensure_database_exists():
            test_connection()
        else:
            print("\nPlease check your PostgreSQL service or edit your .env file with valid credentials.")
            sys.exit(1)

if __name__ == "__main__":
    main()

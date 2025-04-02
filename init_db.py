# init_db.py
import sys
from sqlalchemy.exc import SQLAlchemyError
from app import app, db, create_initial_data # Import necessary components from your app.py/models.py

print("Running Database Initializer...")

try:
    # Establish an application context
    with app.app_context():
        print("Creating database tables...")
        # Create tables based on models defined in models.py
        # This is generally idempotent (doesn't harm existing tables)
        db.create_all()
        print("Tables created (or already exist).")

        print("Seeding initial data...")
        # Call your function to add the initial warehouse data.
        # Ensure this function is safe to run multiple times or checks
        # if data already exists, though create_all handles table structure.
        create_initial_data()
        print("Initial data seeding function executed.")

    print("Database initialization complete.")
    sys.exit(0) # Exit successfully

except SQLAlchemyError as e:
    print(f"Database Error during initialization: {e}", file=sys.stderr)
    sys.exit(1) # Exit with failure code if DB error occurs
except Exception as e:
    print(f"Unexpected Error during database initialization: {e}", file=sys.stderr)
    sys.exit(1) # Exit with failure code for any other error
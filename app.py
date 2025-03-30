# app.py
import os
from flask import Flask, request, jsonify
from models import db, Warehouse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

app = Flask(__name__)

# --- Database Configuration ---
# Use DATABASE_URL from environment variables (set by Heroku Postgres)
# Provide a default fallback for local development (e.g., SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///local_warehouse.db'
).replace("postgres://", "postgresql://", 1) # Adjust protocol for SQLAlchemy if needed
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- Helper Function for Initial Data ---
def create_initial_data():
    """Creates initial warehouse data if the table is empty."""
    with app.app_context():
        if Warehouse.query.count() == 0:
            print("Populating initial warehouse data...")
            initial_warehouses = [
                Warehouse(warehouseId='0001', warehouseName='New York', quantityAvailable=50, quantityIncoming=0),
                Warehouse(warehouseId='0002', warehouseName='Boston', quantityAvailable=3, quantityIncoming=0),
                Warehouse(warehouseId='0003', warehouseName='Texas', quantityAvailable=5, quantityIncoming=20),
            ]
            try:
                db.session.add_all(initial_warehouses)
                db.session.commit()
                print("Initial data added successfully.")
            except (IntegrityError, SQLAlchemyError) as e:
                db.session.rollback()
                print(f"Error adding initial data: {e}")
        else:
            print("Database already contains data. Skipping initial data population.")


# --- API Endpoints ---

@app.route('/')
def home():
    """Simple home route to confirm the app is running."""
    return "Warehouse API is running!"

@app.route('/quantity', methods=['POST'])
def get_quantity():
    """Endpoint to query quantity for a specific warehouse."""
    data = request.get_json()

    if not data or 'warehouseName' not in data:
        return jsonify({"error": "BadRequest", "message": "Missing 'warehouseName' in request body."}), 400

    warehouse_name = data['warehouseName']

    try:
        warehouse = Warehouse.query.filter_by(warehouseName=warehouse_name).first()

        if warehouse:
            return jsonify(warehouse.to_dict()), 200
        else:
            # Use the error formatting method from the model
            error_response = Warehouse().to_error_dict(warehouse_name)
            return jsonify(error_response), 404

    except SQLAlchemyError as e:
        # Log the error internally
        app.logger.error(f"Database error on /quantity: {e}")
        return jsonify({"error": "ServerError", "message": "An internal database error occurred."}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error on /quantity: {e}")
        return jsonify({"error": "ServerError", "message": "An unexpected error occurred."}), 500


@app.route('/transfer', methods=['POST'])
def transfer_quantity():
    """Endpoint to transfer quantity between warehouses."""
    data = request.get_json()

    # Validate input
    required_fields = ['originWarehouseName', 'destinationWarehouseName', 'quantityTransfer']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "BadRequest", "message": f"Missing one or more required fields: {required_fields}"}), 400

    origin_name = data['originWarehouseName']
    dest_name = data['destinationWarehouseName']
    quantity_str = data.get('quantityTransfer') # Use .get for safer access

    # Check for self-transfer
    if origin_name == dest_name:
        return jsonify({"error": "Transfer Failed", "message": "Origin and destination warehouses cannot be the same."}), 400

    # Validate quantity is a positive integer
    try:
        quantity = int(quantity_str)
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
    except (ValueError, TypeError):
         return jsonify({"error": "Transfer Failed", "message": "quantityTransfer must be a positive integer."}), 400

    try:
        # Fetch both warehouses within a single session context
        origin_warehouse = Warehouse.query.filter_by(warehouseName=origin_name).first()
        dest_warehouse = Warehouse.query.filter_by(warehouseName=dest_name).first()

        # Check if warehouses exist
        if not origin_warehouse:
            return jsonify({"error": "Transfer Failed", "message": f"Origin warehouse '{origin_name}' not found."}), 404
        if not dest_warehouse:
            return jsonify({"error": "Transfer Failed", "message": f"Destination warehouse '{dest_name}' not found."}), 404

        # Check available quantity
        if origin_warehouse.quantityAvailable < quantity:
            return jsonify({
                "error": "Transfer Failed",
                "message": f"Insufficient quantity available in '{origin_name}'. Available: {origin_warehouse.quantityAvailable}, Requested: {quantity}"
            }), 400

        # Perform the transfer - use a transaction
        origin_warehouse.quantityAvailable -= quantity
        dest_warehouse.quantityIncoming += quantity

        db.session.commit()

        return jsonify({
            "message": "Success - Transfer Initiated",
            "originWarehouseName": origin_name,
            "destinationWarehouseName": dest_name,
            "quantityTransfer": quantity
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback() # Rollback transaction on error
        app.logger.error(f"Database error on /transfer: {e}")
        return jsonify({"error": "ServerError", "message": "An internal database error occurred during transfer."}), 500
    except Exception as e:
        db.session.rollback() # Ensure rollback on any unexpected error
        app.logger.error(f"Unexpected error on /transfer: {e}")
        return jsonify({"error": "ServerError", "message": "An unexpected error occurred during transfer."}), 500


@app.route('/delivery', methods=['POST'])
def process_delivery():
    """Endpoint to process incoming deliveries for all warehouses."""
    try:
        warehouses = Warehouse.query.filter(Warehouse.quantityIncoming > 0).all() # Optimization: only process warehouses with incoming stock

        if not warehouses:
             return jsonify({"message": "Success - No pending deliveries to process."}), 200

        updated_count = 0
        for warehouse in warehouses:
            warehouse.quantityAvailable += warehouse.quantityIncoming
            warehouse.quantityIncoming = 0
            updated_count += 1

        db.session.commit()

        return jsonify({"message": f"Success - Deliveries processed for {updated_count} warehouses."}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error on /delivery: {e}")
        return jsonify({"error": "ServerError", "message": "An internal database error occurred during delivery processing."}), 500
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Unexpected error on /delivery: {e}")
        return jsonify({"error": "ServerError", "message": "An unexpected error occurred during delivery processing."}), 500


# --- Application Context for DB Operations ---
# # Create tables and initial data if run directly or via `flask run` for local dev
# # Note: For Heroku, you'll typically run migrations/setup separately
# with app.app_context():
#     print("Attempting DB initialization (should only happen locally or via manual command)...") # Add print for clarity if keeping locally
#     db.create_all() # Create tables if they don't exist
#     create_initial_data() # Add initial data if needed

# --- Main Execution --- (For local development)
if __name__ == '__main__':
    with app.app_context():
         print("Running local DB initialization...")
         db.create_all()
         create_initial_data()
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
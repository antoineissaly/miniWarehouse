# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Warehouse(db.Model):
    __tablename__ = 'warehouseTable'

    # Define columns
    # Note: Unsing warehouseName as primary key for app simplicity (not best practice):
    warehouseId = db.Column(db.String(10), unique=True, nullable=False) # Added unique constraint
    warehouseName = db.Column(db.String(80), primary_key=True, unique=True, nullable=False)
    quantityAvailable = db.Column(db.Integer, nullable=False, default=0)
    quantityIncoming = db.Column(db.Integer, nullable=False, default=0)

    # quantityForecast is calculated dynamically in the API, not stored in DB

    def __repr__(self):
        return f'<Warehouse {self.warehouseName}>'

    def to_dict(self):
        """Serializes the object to a dictionary, calculating forecast."""
        return {
            "warehouseName": self.warehouseName,
            "quantityAvailable": self.quantityAvailable,
            "quantityIncoming": self.quantityIncoming,
            "quantityForecast": self.quantityAvailable + self.quantityIncoming
            # "warehouseId": self.warehouseId # Optional: include if needed elsewhere
        }

    def to_error_dict(self, requested_name):
      """Formats a standard 'Not Found' error."""
      return {
          "error": "NotFound",
          "message": "The requested item was not found in the specified warehouse.",
          "requestedWarehouseName": requested_name
      }
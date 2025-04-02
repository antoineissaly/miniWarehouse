# miniWarehouse API (Agentforce Demo Backend)

A simple Flask-based REST API simulating a Warehouse Management System (WMS) backend. This project was created as a demonstration backend for integration with platforms like Salesforce Agentforce, allowing users to query and manage basic warehouse inventory via API calls.

The application is designed for deployment on Heroku using a Heroku Postgres database and includes automated database initialization during deployment via the Heroku Release Phase.

## Features

* **REST API:** Provides endpoints to manage warehouse inventory.
    * Query item quantity (available, incoming, forecast).
    * Initiate stock transfers between warehouses.
    * Process incoming deliveries for all warehouses.
* **Database:** Uses PostgreSQL to store warehouse data.
* **Automated DB Setup:** Leverages Heroku Release Phase to automatically create database tables and seed initial data on deployment.
* **Heroku Ready:** Includes `Procfile` and `requirements.txt` for easy Heroku deployment.

## Technology Stack

* **Backend:** Python 3
* **Framework:** Flask
* **ORM:** SQLAlchemy (with Flask-SQLAlchemy)
* **Database:** PostgreSQL (specifically Heroku Postgres for deployment)
* **WSGI Server:** Gunicorn
* **Deployment:** Heroku

## Project Structure


.
├── app.py             # Main Flask application, API routes, core logic
├── models.py          # SQLAlchemy database model (Warehouse table)
├── init_db.py         # Python script for DB initialization (called by release phase)
├── release-tasks.sh   # Shell script executed by Heroku Release Phase
├── requirements.txt   # Python dependencies
├── Procfile           # Heroku process definitions (web, release)
├── .gitignore         # Standard Python gitignore
└── README.md          # This file


## Local Development Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd miniWarehouse # Or your repo name
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Database Setup:**
    * **Option A (SQLite - Default Fallback):** The app defaults to using a local `local_warehouse.db` SQLite file if `DATABASE_URL` is not set. No extra setup needed.
    * **Option B (Local PostgreSQL):**
        * Install PostgreSQL locally.
        * Create a database and user.
        * Set the `DATABASE_URL` environment variable. You can use a `.env` file (add `.env` to `.gitignore`!) and `python-dotenv` (already in requirements):
            ```.env
            DATABASE_URL=postgresql://user:password@host:port/database_name
            ```
5.  **Initialize the Database (Local):** Run the initialization script manually:
    ```bash
    python init_db.py
    ```
6.  **Run the application:**
    ```bash
    python app.py
    ```
    The app should be running on `http://127.0.0.1:5001` (or the port specified in `app.py`).

## Heroku Deployment

1.  **Install Heroku CLI:** [https://devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)
2.  **Login to Heroku:**
    ```bash
    heroku login
    ```
3.  **Create Heroku App:**
    ```bash
    heroku create your-unique-app-name
    ```
4.  **Provision Heroku Postgres:**
    ```bash
    heroku addons:create heroku-postgresql:essential-0 -a your-unique-app-name
    # This automatically sets the DATABASE_URL config var on Heroku
    ```
5.  **Deploy:**
    ```bash
    git push heroku main # Or your deployment branch name
    ```
    * The deployment process will automatically run the `release` task defined in the `Procfile`, which executes `release-tasks.sh` and `init_db.py` to set up the database tables and initial data.

6.  **Install `psql` locally (Optional but Recommended):** To interact directly with the Heroku database using `heroku pg:psql`, you need the `psql` command-line tool installed locally (see [Heroku Dev Center](https://devcenter.heroku.com/articles/heroku-postgresql#local-setup) for instructions).

## API Endpoints

The base URL will be your Heroku app URL (e.g., `https://your-unique-app-name.herokuapp.com`) or `http://127.0.0.1:5001` for local development.

**1. Get Quantity**

* **Endpoint:** `/quantity`
* **Method:** `POST`
* **Description:** Retrieves available, incoming, and forecast quantities for a specific warehouse.
* **Request Body:**
    ```json
    {
        "warehouseName": "West"
    }
    ```
* **Success Response (200 OK):**
    ```json
    {
        "warehouseName": "West",
        "quantityAvailable": 50000,
        "quantityIncoming": 10000,
        "quantityForecast": 60000
    }
    ```
* **Error Response (404 Not Found):**
    ```json
    {
        "error": "NotFound",
        "message": "The requested item was not found in the specified warehouse.",
        "requestedWarehouseName": "NonExistentWarehouse"
    }
    ```
* **Error Response (400 Bad Request):**
    ```json
    {
        "error": "BadRequest",
        "message": "Missing 'warehouseName' in request body."
    }
    ```

**2. Transfer Quantity**

* **Endpoint:** `/transfer`
* **Method:** `POST`
* **Description:** Initiates a stock transfer. Decrements `quantityAvailable` from the origin and increments `quantityIncoming` at the destination.
* **Request Body:**
    ```json
    {
        "originWarehouseName": "West",
        "destinationWarehouseName": "East",
        "quantityTransfer": 5000
    }
    ```
* **Success Response (200 OK):**
    ```json
    {
        "message": "Success - Transfer Initiated",
        "originWarehouseName": "West",
        "destinationWarehouseName": "East",
        "quantityTransfer": 5000
    }
    ```
* **Error Response (4xx):**
    ```json
    {
        "error": "Transfer Failed",
        "message": "<Explanation: e.g., Insufficient quantity available..., Origin warehouse ... not found., Destination warehouse ... not found., quantityTransfer must be a positive integer.>"
    }
    ```

**3. Process Delivery**

* **Endpoint:** `/delivery`
* **Method:** `POST`
* **Description:** Processes incoming deliveries for *all* warehouses. For each warehouse, adds `quantityIncoming` to `quantityAvailable` and resets `quantityIncoming` to 0.
* **Request Body:** None
* **Success Response (200 OK):**
    ```json
    {
        "message": "Success - Deliveries processed for X warehouses."
        // Or: "Success - No pending deliveries to process."
    }
    ```
* **Error Response (500 Internal Server Error):**
    ```json
    {
        "error": "ServerError",
        "message": "An internal database error occurred during delivery processing."
    }
    ```

## Database Schema

* **Table:** `warehouseTable`
* **Columns:**
    * `warehouseId` (String, Unique): A unique identifier for the warehouse (e.g., 'W001').
    * `warehouseName` (String, Primary Key, Unique): The name of the warehouse (e.g., 'West').
    * `quantityAvailable` (Integer): Current stock level available for use/transfer.
    * `quantityIncoming` (Integer): Stock level currently in transit to this warehouse.
    * `quantityForecast` (Calculated): Not stored in the database; calculated dynamically in the API response as `quantityAvailable + quantityIncoming`.

## Testing

A Postman collection (`WarehouseAPI_v2.postman_collection.json`) and environment (`WarehouseAPI_Heroku.postman_environment.json`) are available in the repository (or were provided separately).

1.  Import both files into Postman.
2.  Select the "Warehouse API (Heroku)" environment.
3.  Update the `baseURL` variable in the environment if your Heroku app URL or local port differs.
4.  Run the requests to test the API endpoints. Remember that `/transfer` and `/delivery` modify the database state.

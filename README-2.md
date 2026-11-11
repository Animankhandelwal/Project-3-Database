# E-Commerce Customer and Order Intelligence Portal

**Columbia University — COMS W4111, Project 1**

A Flask-based web application for exploring e-commerce customers, orders, products, transactions, shipments, suppliers, warehouses, and customer locations.

The backend uses PostgreSQL hosted on a Google Compute Engine VM and provides REST GET endpoints for retrieving data, filtering records, exploring relationships, and performing business analytics.

## 1. Technology Stack

| Component | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database | PostgreSQL |
| Database access | SQLAlchemy Core (raw SQL) |
| Cloud infrastructure | Google Compute Engine |
| Local database connectivity | SSH tunneling |
| API response format | JSON |

The project uses parameterized SQL queries without an ORM.

## 2. Project Structure

```text
ecommerce-project/
├── server.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

The `server.py` file contains the Flask application and GET endpoints.

## 3. Prerequisites

Before running the application, ensure you have:

- Python 3 installed on your Mac.
- Google Cloud CLI (`gcloud`) installed.
- Access to the Google Cloud project and Compute Engine VM.
- PostgreSQL installed and running on the VM.
- The project database and its 12 tables created.
- A PostgreSQL username, password, and database name.
- Appropriate permissions to SSH into the VM.

You can check your Python installation with:

```bash
python3 --version
```

To install Google Cloud CLI on macOS using Homebrew:

```bash
brew install --cask google-cloud-sdk
```

Then authenticate:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

Replace `YOUR_PROJECT_ID` with the actual Google Cloud project ID.

## 4. Set Up the Python Environment

Open a terminal on your Mac and navigate to the project directory:

```bash
cd ecommerce-project
```

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

The `requirements.txt` file should contain:

```text
Flask
SQLAlchemy
psycopg2-binary
python-dotenv
```

If you are using the Columbia-provided starter project, retain its required dependencies and database configuration.

## 5. Start the Google Compute Engine VM

Open the Google Cloud Console:

https://console.cloud.google.com/compute/instances

Locate the VM containing PostgreSQL and start it if it is stopped.

Connect to the VM using SSH.

Check PostgreSQL status:

```bash
sudo systemctl status postgresql
```

If PostgreSQL is stopped:

```bash
sudo systemctl start postgresql
```

### Verify the database

Open PostgreSQL:

```bash
sudo -u postgres psql
```

List available databases:

```sql
\l
```

Connect to your project database:

```sql
\c YOUR_DATABASE_NAME
```

List tables:

```sql
\dt
```

The project schema contains the following tables:

**Entity tables:**
- Customers
- Locations
- Suppliers
- Warehouses
- Products
- Orders
- Transactions
- Shipments

**Relationship tables:**
- lives_in
- sells
- supplies
- ships

PostgreSQL normally stores unquoted table names in lowercase.

Verify that data exists:

```sql
SELECT COUNT(*) FROM Customers;
SELECT COUNT(*) FROM Orders;
SELECT COUNT(*) FROM Products;
```

Exit PostgreSQL:

```sql
\q
```

## 6. Connect Your Mac to PostgreSQL on the VM

The PostgreSQL database runs remotely on Google Compute Engine. It is not necessary to download the database to your Mac.

Instead, establish an SSH tunnel.

### Open Terminal 1 — SSH tunnel

Run:

```bash
gcloud compute ssh YOUR_VM_NAME \
  --zone YOUR_VM_ZONE \
  -- -N -L 5433:127.0.0.1:5432
```

Replace:

- `YOUR_VM_NAME` with the Compute Engine VM name.
- `YOUR_VM_ZONE` with the VM's zone.

This command forwards:

```text
Mac localhost:5433
        |
        | SSH Tunnel
        |
Google Compute Engine VM
        |
PostgreSQL localhost:5432
```

Keep Terminal 1 open while using the application.

**Important:** If the VM has no external IP address, IAP tunneling and additional permissions may be required.

### Verify the SSH tunnel

Open a second terminal on your Mac.

If the PostgreSQL client (`psql`) is installed, run:

```bash
psql -h 127.0.0.1 \
     -p 5433 \
     -U YOUR_DB_USER \
     -d YOUR_DB_NAME
```

Enter your PostgreSQL password when prompted.

Test the connection:

```sql
SELECT COUNT(*) FROM Customers;
```

If the query succeeds, your Mac can access the remote PostgreSQL database.

If authentication fails, verify the PostgreSQL user's password and TCP connection permissions.

## 7. Configure Environment Variables

Create a `.env` file in the project directory.

```env
DB_HOST=127.0.0.1
DB_PORT=5433
DB_NAME=YOUR_DATABASE_NAME
DB_USER=YOUR_DATABASE_USER
DB_PASSWORD=YOUR_DATABASE_PASSWORD
```

Replace the placeholders with the actual PostgreSQL credentials.

The Flask application uses these values to connect to PostgreSQL.

Never commit `.env` to GitHub.

Add the following to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc
```

## 8. Run the Flask Application

Make sure:

1. The Google Compute Engine VM is running.
2. PostgreSQL is running on the VM.
3. The SSH tunnel is active.
4. The `.env` file contains valid database credentials.
5. The Python virtual environment is activated.

Open another terminal in the project directory.

Start the application:

```bash
python server.py
```

The application should start on:

```text
http://127.0.0.1:8111
```

Open an implemented endpoint in your browser:

```text
http://127.0.0.1:8111/customers
```

If everything is configured correctly, the endpoint will retrieve customer records from PostgreSQL and return them as JSON.

## 9. Available GET Endpoints

The implementation provides 20 read-only endpoints.

### Entity endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/customers` | List and filter customers |
| GET | `/customers/<customer_id>` | Retrieve a customer by ID |
| GET | `/locations` | Retrieve customer locations |
| GET | `/suppliers` | Retrieve suppliers |
| GET | `/warehouses` | Retrieve warehouses |
| GET | `/products` | Retrieve and filter products |
| GET | `/orders` | Retrieve orders with customer information |
| GET | `/orders/<order_id>/details` | Retrieve order, payment, and shipment details |
| GET | `/transactions` | Retrieve payment transactions |
| GET | `/shipments` | Retrieve shipment records |

### Relationship endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/customers/<customer_id>/locations` | Customer-location relationships |
| GET | `/customers/<customer_id>/orders` | Customer purchase history |
| GET | `/orders/<order_id>/products` | Products associated with an order |
| GET | `/products/<product_id>/suppliers` | Suppliers associated with a product |
| GET | `/shipments/<shipment_id>/warehouses` | Warehouses associated with a shipment |

### Analytics endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/demographics` | Customer distribution by gender |
| GET | `/analytics/order-segments` | Orders grouped by customer segment |
| GET | `/analytics/payments` | Payment-status distribution and percentages |
| GET | `/analytics/warehouses` | Warehouses ranked by shipment count |
| GET | `/analytics/suppliers` | Suppliers ranked by distinct associated orders |

The supplier analytics endpoint measures orders containing products associated with each supplier; it does not independently verify physical order fulfillment.

## 10. Testing API Endpoints

Endpoints can be tested through a browser, Postman, or `curl`.

### Retrieve all customers

```bash
curl http://127.0.0.1:8111/customers
```

### Search customers by name

```bash
curl "http://127.0.0.1:8111/customers?name=Alice"
```

### Retrieve orders

```bash
curl http://127.0.0.1:8111/orders
```

### Filter orders by status

```bash
curl "http://127.0.0.1:8111/orders?status=Delivered"
```

### Filter products by category

```bash
curl "http://127.0.0.1:8111/products?category=Electronics"
```

### Retrieve a customer's order history

```bash
curl http://127.0.0.1:8111/customers/C001/orders
```

Replace `C001` with an existing customer ID.

### Retrieve payment analytics

```bash
curl http://127.0.0.1:8111/analytics/payments
```

### Retrieve warehouse analytics

```bash
curl http://127.0.0.1:8111/analytics/warehouses
```

### Limit returned records

For supported listing endpoints:

```bash
curl "http://127.0.0.1:8111/customers?limit=20"
```

The implemented limit must be between 1 and 500. The default is 100.

## 11. SQL Operations Used

The endpoints demonstrate several SQL concepts covered in COMS W4111.

| SQL concept | Example endpoint |
|---|---|
| SELECT | `/customers` |
| WHERE | `/products?category=Electronics` |
| ORDER BY | `/orders` |
| JOIN | `/orders` |
| LEFT JOIN | `/orders/<order_id>/details` |
| GROUP BY | `/analytics/demographics` |
| COUNT | `/analytics/warehouses` |
| DISTINCT | `/analytics/suppliers` |
| Aggregate/window functions | `/analytics/payments` |
| LIMIT | `/customers?limit=20` |

All filtering parameters are passed through SQLAlchemy's parameterized query execution.

## 12. Troubleshooting

### Error: Connection refused

Possible causes:

- The Compute Engine VM is stopped.
- PostgreSQL is not running.
- The SSH tunnel is closed.
- The wrong port is configured.

Check PostgreSQL on the VM:

```bash
sudo systemctl status postgresql
```

Verify the SSH tunnel is still running.

Ensure your `.env` contains:

```env
DB_HOST=127.0.0.1
DB_PORT=5433
```

### Error: Password authentication failed

Verify:

- PostgreSQL username.
- PostgreSQL password.
- Database name.
- PostgreSQL authentication settings.

The Google Cloud SSH credentials and PostgreSQL database credentials are separate.

### Error: Database does not exist

List databases on the VM:

```bash
sudo -u postgres psql -l
```

Update `DB_NAME` with the correct database name.

### Error: Relation does not exist

Check the available tables:

```sql
\dt
```

Ensure you connected to the correct database and schema.

### Error: Port already in use

If local port 5433 is occupied, use another port such as 5434:

```bash
gcloud compute ssh YOUR_VM_NAME \
  --zone YOUR_VM_ZONE \
  -- -N -L 5434:127.0.0.1:5432
```

Update the `.env` file:

```env
DB_PORT=5434
```

### Error: ModuleNotFoundError

Activate the virtual environment:

```bash
source venv/bin/activate
```

Reinstall dependencies:

```bash
pip install -r requirements.txt
```

### Endpoint returns an empty list

An empty JSON array (`[]`) usually means the SQL query returned no matching rows.

Check the table directly:

```sql
SELECT COUNT(*) FROM Customers;
```

Also verify that the requested filters match actual database values.

## 13. Development Workflow

For each development session:

**Terminal 1 — SSH tunnel**

```bash
gcloud compute ssh YOUR_VM_NAME \
  --zone YOUR_VM_ZONE \
  -- -N -L 5433:127.0.0.1:5432
```

**Terminal 2 — Flask application**

```bash
cd ecommerce-project
source venv/bin/activate
python server.py
```

**Browser or Postman**

```text
http://127.0.0.1:8111/customers
```

Both the VM and SSH tunnel must remain active for database queries to succeed.

To stop development:

1. Stop Flask with `Ctrl+C`.
2. Stop the SSH tunnel with `Ctrl+C`.
3. Stop the Compute Engine VM when it is no longer needed.

Stopping the VM does not normally delete its persistent disk data, but the VM will need to be restarted for future database access.

## 14. Cloud Deployment Notes

Local development uses an SSH tunnel between the Mac and the Compute Engine VM.

This tunnel is not available to a Flask application deployed on Google Cloud Run.

Cloud Run deployment requires a separate secure network configuration that allows the service to communicate with PostgreSQL on the VM, typically through private VPC connectivity and appropriate firewall rules.

The deployed application must also:

- Use securely configured database credentials.
- Listen on the port supplied by the Cloud Run environment.
- Avoid exposing PostgreSQL directly to the public internet.
- Disable Flask debug mode.

Deployment configuration is separate from the local setup described in this README.

## 15. Current Scope

This backend implements read-only database operations through GET endpoints.

It supports:

- Retrieving records from entity tables.
- Filtering and searching data.
- Exploring foreign-key and relationship-table associations.
- Aggregating business metrics.
- Returning structured JSON responses.

The GET endpoints do not modify database records.

A complete user-facing submission may additionally require HTML templates, navigation, forms, and other interactions according to the Part 3 assignment requirements.

---

**Project:** COMS W4111 — E-Commerce Customer and Order Intelligence Portal

**Database:** PostgreSQL on Google Compute Engine

**Backend:** Python Flask

**Local API:** `http://127.0.0.1:8111`

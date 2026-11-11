
import os
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv
from decimal import Decimal
from datetime import date, datetime

load_dotenv()

app = Flask(__name__)

# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "5433")),
    database=os.environ["DB_NAME"]
)

engine = create_engine(db_url, pool_pre_ping=True)


def serialize(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def run_query(sql, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        return [
            {key: serialize(value)
             for key, value in row.items()}
            for row in result.mappings()
        ]


def get_limit():
    value = request.args.get("limit", "100")
    try:
        limit = int(value)
    except ValueError:
        return None
    return limit if 1 <= limit <= 500 else None


@app.errorhandler(500)
def internal_error(error):
    app.logger.error("Internal server error: %s", error)
    return jsonify({"error": "Internal server error"}), 500


# --------------------------------------------------
# 1. CUSTOMERS
# GET /customers?name=Alice&segment=Premium
# --------------------------------------------------

@app.get("/customers")
def get_customers():
    limit = get_limit()
    if limit is None:
        return jsonify({"error": "Invalid limit"}), 400

    sql = """
        SELECT customer_id, customer_name,
               customer_age, customer_gender,
               customer_segment
        FROM Customers
        WHERE customer_name ILIKE :name
          AND customer_segment ILIKE :segment
        ORDER BY customer_name
        LIMIT :limit
    """

    return jsonify(run_query(sql, {
        "name": f"%{request.args.get('name', '')}%",
        "segment": f"%{request.args.get('segment', '')}%",
        "limit": limit
    }))


# --------------------------------------------------
# 2. SINGLE CUSTOMER
# GET /customers/C001
# --------------------------------------------------

@app.get("/customers/<customer_id>")
def get_customer(customer_id):
    sql = """
        SELECT *
        FROM Customers
        WHERE customer_id = :customer_id
    """

    rows = run_query(sql, {"customer_id": customer_id})

    if not rows:
        return jsonify({"error": "Customer not found"}), 404

    return jsonify(rows[0])


# --------------------------------------------------
# 3. LOCATIONS
# GET /locations?country=India
# --------------------------------------------------

@app.get("/locations")
def get_locations():
    limit = get_limit()
    if limit is None:
        return jsonify({"error": "Invalid limit"}), 400

    sql = """
        SELECT customer_city, customer_state,
               customer_country, region,
               customer_postal_code
        FROM Locations
        WHERE customer_country ILIKE :country
        ORDER BY customer_country, customer_city
        LIMIT :limit
    """

    return jsonify(run_query(sql, {
        "country": f"%{request.args.get('country', '')}%",
        "limit": limit
    }))


# --------------------------------------------------
# 4. SUPPLIERS
# GET /suppliers
# --------------------------------------------------

@app.get("/suppliers")
def get_suppliers():
    limit = get_limit()
    if limit is None:
        return jsonify({"error": "Invalid limit"}), 400

    sql = """
        SELECT supplier_name
        FROM Suppliers
        ORDER BY supplier_name
        LIMIT :limit
    """

    return jsonify(run_query(sql, {"limit": limit}))


# --------------------------------------------------
# 5. WAREHOUSES
# GET /warehouses
# --------------------------------------------------

@app.get("/warehouses")
def get_warehouses():
    limit = get_limit()
    if limit is None:
        return jsonify({"error": "Invalid limit"}), 400

    sql = """
        SELECT warehouse_id
        FROM Warehouses
        ORDER BY warehouse_id
        LIMIT :limit
    """

    return jsonify(run_query(sql, {"limit": limit}))


# --------------------------------------------------
# 6. PRODUCTS
# GET /products?category=Electronics&brand=Apple
# --------------------------------------------------

@app.get("/products")
def get_products():
    limit = get_limit()
    if limit is None:
        return jsonify({"error": "Invalid limit"}), 400

    max_price = request.args.get("max_price", type=float)

    sql = """
        SELECT product_id, product_category,
               product_subcategory, brand,
               unit_price
        FROM Products
        WHERE product_category ILIKE :category
          AND brand ILIKE :brand
          AND (:max_price IS NULL
               OR unit_price <= :max_price)
        ORDER BY unit_price
        LIMIT :limit
    """

    return jsonify(run_query(sql, {
        "category": f"%{request.args.get('category', '')}%",
        "brand": f"%{request.args.get('brand', '')}%",
        "max_price": max_price,
        "limit": limit
    }))


# --------------------------------------------------
# 7. ORDERS
# GET /orders?status=Delivered
# --------------------------------------------------

@app.get("/orders")
def get_orders():
    limit = get_limit()
    if limit is None:
        return jsonify({"error": "Invalid limit"}), 400

    sql = """
        SELECT o.order_id, o.order_datetime,
               o.order_status, o.customer_id,
               c.customer_name
        FROM Orders o
        JOIN Customers c
          ON o.customer_id = c.customer_id
        WHERE o.order_status ILIKE :status
        ORDER BY o.order_datetime DESC
        LIMIT :limit
    """

    return jsonify(run_query(sql, {
        "status": f"%{request.args.get('status', '')}%",
        "limit": limit
    }))


# --------------------------------------------------
# 8. ORDER DETAILS
# GET /orders/O001/details
# --------------------------------------------------

@app.get("/orders/<order_id>/details")
def get_order_details(order_id):
    sql = """
        SELECT o.order_id, o.order_datetime,
               o.order_status, c.customer_name,
               t.transaction_id, t.gross_sales,
               t.payment_method, t.payment_status,
               s.shipment_id, s.shipping_method,
               s.delivery_status
        FROM Orders o
        JOIN Customers c
          ON o.customer_id = c.customer_id
        LEFT JOIN Transactions t
          ON o.order_id = t.order_id
        LEFT JOIN Shipments s
          ON o.order_id = s.order_id
        WHERE o.order_id = :order_id
    """

    rows = run_query(sql, {"order_id": order_id})

    if not rows:
        return jsonify({"error": "Order not found"}), 404

    return jsonify(rows)


# --------------------------------------------------
# 9. TRANSACTIONS
# GET /transactions?status=Success
# --------------------------------------------------

@app.get("/transactions")
def get_transactions():
    limit = get_limit()
    if limit is None:
        return jsonify({"error": "Invalid limit"}), 400

    sql = """
        SELECT transaction_id, gross_sales,
               currency, payment_method,
               payment_status, order_id
        FROM Transactions
        WHERE payment_status ILIKE :status
        LIMIT :limit
    """

    return jsonify(run_query(sql, {
        "status": f"%{request.args.get('status', '')}%",
        "limit": limit
    }))


# --------------------------------------------------
# 10. SHIPMENTS
# GET /shipments?status=Delivered
# --------------------------------------------------

@app.get("/shipments")
def get_shipments():
    limit = get_limit()
    if limit is None:
        return jsonify({"error": "Invalid limit"}), 400

    sql = """
        SELECT shipment_id, delivery_days,
               estimated_delivery_days,
               shipping_method, delivery_status,
               order_id
        FROM Shipments
        WHERE delivery_status ILIKE :status
        LIMIT :limit
    """

    return jsonify(run_query(sql, {
        "status": f"%{request.args.get('status', '')}%",
        "limit": limit
    }))


# --------------------------------------------------
# 11. CUSTOMER LOCATIONS (lives_in)
# GET /customers/C001/locations
# --------------------------------------------------

@app.get("/customers/<customer_id>/locations")
def get_customer_locations(customer_id):
    sql = """
        SELECT l.customer_city, l.customer_state,
               l.customer_country, l.region,
               l.customer_postal_code
        FROM lives_in li
        JOIN Locations l
          ON li.customer_country = l.customer_country
         AND li.customer_postal_code =
             l.customer_postal_code
        WHERE li.customer_id = :customer_id
    """

    return jsonify(run_query(sql, {
        "customer_id": customer_id
    }))


# --------------------------------------------------
# 12. CUSTOMER ORDER HISTORY
# GET /customers/C001/orders
# --------------------------------------------------

@app.get("/customers/<customer_id>/orders")
def get_customer_orders(customer_id):
    sql = """
        SELECT o.order_id, o.order_datetime,
               o.order_status, t.gross_sales,
               t.currency, t.payment_status
        FROM Orders o
        LEFT JOIN Transactions t
          ON o.order_id = t.order_id
        WHERE o.customer_id = :customer_id
        ORDER BY o.order_datetime DESC
    """

    return jsonify(run_query(sql, {
        "customer_id": customer_id
    }))


# --------------------------------------------------
# 13. ORDER PRODUCTS (sells)
# GET /orders/O001/products
# --------------------------------------------------

@app.get("/orders/<order_id>/products")
def get_order_products(order_id):
    sql = """
        SELECT p.product_id, p.product_category,
               p.product_subcategory, p.brand,
               p.unit_price
        FROM sells se
        JOIN Products p
          ON se.product_id = p.product_id
        WHERE se.order_id = :order_id
    """

    return jsonify(run_query(sql, {
        "order_id": order_id
    }))


# --------------------------------------------------
# 14. PRODUCT SUPPLIERS (supplies)
# GET /products/P001/suppliers
# --------------------------------------------------

@app.get("/products/<product_id>/suppliers")
def get_product_suppliers(product_id):
    sql = """
        SELECT s.supplier_name
        FROM supplies sp
        JOIN Suppliers s
          ON sp.supplier_name = s.supplier_name
        WHERE sp.product_id = :product_id
    """

    return jsonify(run_query(sql, {
        "product_id": product_id
    }))


# --------------------------------------------------
# 15. SHIPMENT WAREHOUSES (ships)
# GET /shipments/S001/warehouses
# --------------------------------------------------

@app.get("/shipments/<shipment_id>/warehouses")
def get_shipment_warehouses(shipment_id):
    sql = """
        SELECT w.warehouse_id
        FROM ships sh
        JOIN Warehouses w
          ON sh.warehouse_id = w.warehouse_id
        WHERE sh.shipment_id = :shipment_id
    """

    return jsonify(run_query(sql, {
        "shipment_id": shipment_id
    }))


# --------------------------------------------------
# 16. CUSTOMER DEMOGRAPHICS
# GET /analytics/demographics
# --------------------------------------------------

@app.get("/analytics/demographics")
def get_demographics():
    sql = """
        SELECT customer_gender,
               COUNT(*) AS total_customers
        FROM Customers
        GROUP BY customer_gender
        ORDER BY total_customers DESC
    """

    return jsonify(run_query(sql))


# --------------------------------------------------
# 17. ORDER DISTRIBUTION BY SEGMENT
# GET /analytics/order-segments
# --------------------------------------------------

@app.get("/analytics/order-segments")
def get_order_segments():
    sql = """
        SELECT c.customer_segment,
               COUNT(o.order_id) AS total_orders,
               ROUND(
                   100.0 * COUNT(o.order_id)
                   / NULLIF(
                       SUM(COUNT(o.order_id)) OVER (),
                       0
                   ), 2
               ) AS percentage
        FROM Customers c
        LEFT JOIN Orders o
          ON c.customer_id = o.customer_id
        GROUP BY c.customer_segment
        ORDER BY total_orders DESC
    """

    return jsonify(run_query(sql))


# --------------------------------------------------
# 18. PAYMENT SUCCESS ANALYTICS
# GET /analytics/payments
# --------------------------------------------------

@app.get("/analytics/payments")
def get_payment_analytics():
    sql = """
        SELECT payment_status,
               COUNT(*) AS transaction_count,
               ROUND(
                   100.0 * COUNT(*) /
                   NULLIF(SUM(COUNT(*)) OVER (), 0),
                   2
               ) AS percentage
        FROM Transactions
        GROUP BY payment_status
        ORDER BY transaction_count DESC
    """

    return jsonify(run_query(sql))


# --------------------------------------------------
# 19. WAREHOUSE ANALYTICS
# GET /analytics/warehouses
# --------------------------------------------------

@app.get("/analytics/warehouses")
def get_warehouse_analytics():
    sql = """
        SELECT w.warehouse_id,
               COUNT(DISTINCT sh.shipment_id)
                   AS total_shipments
        FROM Warehouses w
        LEFT JOIN ships sh
          ON w.warehouse_id = sh.warehouse_id
        GROUP BY w.warehouse_id
        ORDER BY total_shipments DESC
    """

    return jsonify(run_query(sql))


# --------------------------------------------------
# 20. SUPPLIER ANALYTICS
# GET /analytics/suppliers
# --------------------------------------------------

@app.get("/analytics/suppliers")
def get_supplier_analytics():
    sql = """
        SELECT sp.supplier_name,
               COUNT(DISTINCT se.order_id)
                   AS total_orders
        FROM supplies sp
        LEFT JOIN sells se
          ON sp.product_id = se.product_id
        GROUP BY sp.supplier_name
        ORDER BY total_orders DESC
    """

    return jsonify(run_query(sql))


# --------------------------------------------------
# START SERVER
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8111,
        debug=True
    )

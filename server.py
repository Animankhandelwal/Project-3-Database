
from flask import request, jsonify
from sqlalchemy import text

# 1. List available tables
@app.get("/api/tables")
def list_tables():
    sql = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()

    return jsonify({
        "tables": [r["table_name"] for r in rows]
    })


# Helper: validate table against database metadata
def valid_table(conn, table_name):
    return conn.execute(text("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
              AND table_name = :table_name
        )
    """), {"table_name": table_name}).scalar()


# 2. List columns for a table
@app.get("/api/tables/<table_name>/columns")
def list_columns(table_name):
    with engine.connect() as conn:
        if not valid_table(conn, table_name):
            return jsonify({"error": "Unknown table"}), 404

        rows = conn.execute(text("""
            SELECT column_name, data_type,
                   is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table_name
            ORDER BY ordinal_position
        """), {"table_name": table_name}).mappings().all()

    return jsonify({
        "table": table_name,
        "columns": [dict(r) for r in rows]
    })


# 3. List known foreign-key relationships
@app.get("/api/schema/relationships")
def list_relationships():
    sql = text("""
        SELECT
            tc.table_name AS source_table,
            kcu.column_name AS source_column,
            ccu.table_name AS target_table,
            ccu.column_name AS target_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.constraint_schema = kcu.constraint_schema
        JOIN information_schema.constraint_column_usage ccu
          ON tc.constraint_name = ccu.constraint_name
         AND tc.constraint_schema = ccu.constraint_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'public'
        ORDER BY tc.table_name
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()

    return jsonify({
        "relationships": [dict(r) for r in rows]
    })

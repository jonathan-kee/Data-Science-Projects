import duckdb
from sqlalchemy import create_engine, text

def init_connections(db_url: str, schema: str = "raw"):
    """Initializes PostgreSQL engine with schema and attaches DuckDB to Postgres."""
    engine = create_engine(db_url)
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema};"))

    duck_con = duckdb.connect()
    duck_con.execute("INSTALL postgres; LOAD postgres;")
    duck_con.execute(f"ATTACH '{db_url}' AS pg (TYPE postgres);")
    
    return engine, duck_con

def perform_upsert(engine, target_table: str, staging_table: str, pks: list, columns: list, schema: str = "raw"):
    """Merges staging table into target table using native Postgres UPSERT with dynamic DDL."""
    col_names = ", ".join([f'"{col}"' for col in columns])
    
    with engine.begin() as conn:
        # 1. Create target table from staging if missing
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {schema}.{target_table} 
            AS SELECT * FROM {schema}.{staging_table} WHERE 1=0;
        """))
        
        # 2. Schema Evolution: Add missing columns
        staging_cols = conn.execute(text(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = '{schema}' AND table_name = '{staging_table}';
        """)).fetchall()
        
        target_cols = {row[0] for row in conn.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{schema}' AND table_name = '{target_table}';
        """)).fetchall()}
        
        for col_name, data_type in staging_cols:
            if col_name not in target_cols:
                conn.execute(text(f'ALTER TABLE {schema}.{target_table} ADD COLUMN "{col_name}" {data_type};'))

        # 3. Ensure Primary Key constraint
        if pks:
            pk_str = ", ".join([f'"{pk}"' for pk in pks])
            has_pk = conn.execute(text("""
                SELECT 1
                FROM pg_constraint
                JOIN pg_class ON pg_constraint.conrelid = pg_class.oid
                JOIN pg_namespace ON pg_class.relnamespace = pg_namespace.oid
                WHERE pg_namespace.nspname = :schema
                  AND pg_class.relname = :table
                  AND pg_constraint.contype = 'p';
            """), {"schema": schema, "table": target_table}).scalar()
            
            if not has_pk:
                try:
                    conn.execute(text(f'ALTER TABLE {schema}.{target_table} ADD PRIMARY KEY ({pk_str});'))
                except Exception as e:
                    print(f"Warning: Could not add PRIMARY KEY to {schema}.{target_table}: {e}")
        
        # 4. Upsert or Append
        updates = ", ".join([f'"{col}" = EXCLUDED."{col}"' for col in columns if col not in pks])
        do_update = f"DO UPDATE SET {updates}" if updates else "DO NOTHING"
        
        if pks:
            pk_str = ", ".join([f'"{pk}"' for pk in pks])
            upsert_query = f"""
                INSERT INTO {schema}.{target_table} ({col_names})
                SELECT {col_names} FROM {schema}.{staging_table}
                ON CONFLICT ({pk_str}) {do_update};
            """
            conn.execute(text(upsert_query))
        else:
            append_query = f"""
                INSERT INTO {schema}.{target_table} ({col_names})
                SELECT {col_names} FROM {schema}.{staging_table};
            """
            conn.execute(text(append_query))
            
        # 5. Drop staging table
        conn.execute(text(f"DROP TABLE {schema}.{staging_table};"))
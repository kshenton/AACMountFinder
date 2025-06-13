import sqlite3

def update_database():
    conn = sqlite3.connect('mounting_solutions.db')
    cursor = conn.cursor()
    
    # First, create a new mounts table without the type column
    cursor.execute("""
        CREATE TABLE mounts (
            id INTEGER PRIMARY KEY,
            name TEXT,
            manufacturer TEXT,
            weight_capacity REAL,
            description TEXT,
            url TEXT
        )
    """)
    
    # Copy data from products table to new mounts table
    cursor.execute("""
        INSERT INTO mounts (id, name, manufacturer, weight_capacity, description, url)
        SELECT id, name, manufacturer, weight_capacity, description, url
        FROM products
    """)
    
    # Drop the old products table
    cursor.execute("DROP TABLE products")
    
    # Reset IDs for each table
    # Mounts
    cursor.execute("""
        CREATE TABLE temp_mounts AS
        SELECT ROW_NUMBER() OVER (ORDER BY id) as id,
               name, manufacturer, weight_capacity, description, url
        FROM mounts
    """)
    cursor.execute("DROP TABLE mounts")
    cursor.execute("ALTER TABLE temp_mounts RENAME TO mounts")
    
    # Clamps
    cursor.execute("""
        CREATE TABLE temp_clamps AS
        SELECT ROW_NUMBER() OVER (ORDER BY id) as id,
               name, manufacturer, description, url
        FROM clamps
    """)
    cursor.execute("DROP TABLE clamps")
    cursor.execute("ALTER TABLE temp_clamps RENAME TO clamps")
    
    # Adaptors
    cursor.execute("""
        CREATE TABLE temp_adaptors AS
        SELECT ROW_NUMBER() OVER (ORDER BY id) as id,
               name, manufacturer, description, url
        FROM adaptors
    """)
    cursor.execute("DROP TABLE adaptors")
    cursor.execute("ALTER TABLE temp_adaptors RENAME TO adaptors")
    
    # Floorstands
    cursor.execute("""
        CREATE TABLE temp_floorstands AS
        SELECT ROW_NUMBER() OVER (ORDER BY id) as id,
               name, manufacturer, description, url
        FROM floorstands
    """)
    cursor.execute("DROP TABLE floorstands")
    cursor.execute("ALTER TABLE temp_floorstands RENAME TO floorstands")
    
    # Commit the changes
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_database()
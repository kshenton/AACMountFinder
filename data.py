# data.py

import sqlite3
import os
import logging

# -------------------------------
# Logging setup
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# -------------------------------
# Database path
# -------------------------------
DB_PATH = os.path.join(os.path.dirname(__file__), "mounting_solutions.db")


# -------------------------------
# DB Helpers
# -------------------------------
def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        logging.info("Connected to database.")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection failed: {e}")
        return None


def get_all_wheelchairs():
    conn = get_db_connection()
    if conn is None:
        return {}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, model FROM wheelchairs ORDER BY model")
        results = cursor.fetchall()
        return {row[1]: row[0] for row in results}
    except sqlite3.Error as e:
        logging.error(f"Failed to fetch wheelchairs: {e}")
        return {}
    finally:
        conn.close()


def get_aac_devices():
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT make, model FROM aac_devices ORDER BY make, model")
        return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Failed to fetch AAC devices: {e}")
        return []
    finally:
        conn.close()


def get_aac_device_by_make_model(make, model):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM aac_devices WHERE make = ? AND model = ?", (make, model))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        logging.error(f"Failed to fetch AAC device by make/model: {e}")
        return None
    finally:
        conn.close()


def get_device_eyegaze_status(device_id):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT eyegaze FROM aac_devices WHERE id = ?", (device_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        logging.error(f"Failed to fetch eyegaze status: {e}")
        return None
    finally:
        conn.close()


def get_recommendations(wheelchair_id, aac_device_id, uses_eyegaze=False):
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed."

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT model, frame_clamps, mount_location FROM wheelchairs WHERE id = ?", (wheelchair_id,))
        wheelchair = cursor.fetchone()

        cursor.execute("SELECT weight FROM aac_devices WHERE id = ?", (aac_device_id,))
        aac_device = cursor.fetchone()

        if not wheelchair or not aac_device:
            return "Invalid wheelchair or AAC device selection."

        frame_clamp_ids = [int(id.strip()) for id in wheelchair[1].split(',')]
        mount_location = wheelchair[2]
        device_weight = aac_device[0]

        cursor.execute(
            f"SELECT * FROM clamps WHERE id IN ({','.join('?' * len(frame_clamp_ids))})",
            frame_clamp_ids
        )
        frame_clamps = cursor.fetchall()

        cursor.execute(
            "SELECT * FROM mounts WHERE weight_capacity >= ? ORDER BY weight_capacity ASC",
            (device_weight,)
        )
        all_mounts = cursor.fetchall()

        rehadapt_mount_id, daessy_mount_id = None, None

        if device_weight > 2.6:
            rehadapt_mount_id = 3
            daessy_mount_id = 7
        elif 1.5 <= device_weight <= 2.5:
            rehadapt_mount_id = 1
            daessy_mount_id = 10
        else:
            rehadapt_mount_id = 4

        # ✅ NEW: order preference based on eye gaze flag
        if uses_eyegaze:
            primary_mount_ids = [id for id in [daessy_mount_id, rehadapt_mount_id] if id]
        else:
            primary_mount_ids = [id for id in [rehadapt_mount_id, daessy_mount_id] if id]

        cursor.execute(
            f"SELECT * FROM mounts WHERE id IN ({','.join('?' * len(primary_mount_ids))})",
            primary_mount_ids
        )
        primary_mounts = cursor.fetchall()

        other_mounts = [m for m in all_mounts if m not in primary_mounts]
        mounts = primary_mounts + other_mounts

        cursor.execute("SELECT * FROM adaptors WHERE id = 1")
        adapter_ring = cursor.fetchone()

        return {
            "frame_clamps": frame_clamps,
            "mounts": mounts,
            "adapter_ring": adapter_ring,
            "mount_location": mount_location
        }

    except sqlite3.Error as e:
        logging.error(f"Failed to get recommendations: {e}")
        return "Failed to retrieve recommendations due to a database error."

    finally:
        conn.close()

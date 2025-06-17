# data.py

import sqlite3
import os
import logging
from typing import Dict, List, Tuple, Optional, Union
from contextlib import contextmanager

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
# Constants for mount logic
# -------------------------------
class MountLogic:
    """Centralized mount selection logic to avoid duplication"""
    
    @staticmethod
    def get_rehadapt_mount_id(device_weight: float, left_hand_side: bool = False) -> int:
        """Get Rehadapt mount ID based on device weight and mounting side"""
        if left_hand_side:
            # Use sturdy mounts with rotation lock for left-hand side
            if device_weight >= 2.8:
                return 3  # M3D Plus HD
            elif 1.7 <= device_weight <= 2.79:
                return 2 #M3D Quickshift Sturdy
            else:
                return 13  # H3D Short UDS Sturdy
        else:
            # Standard right-hand side mounts
            if device_weight >= 2.6:
                return 3
            elif 1.6 <= device_weight <= 2.59:
                return 1
            elif 1.1 <= device_weight <= 1.59:
                return 4
            else:
                return 6
    
    @staticmethod
    def get_daessy_mount_id(device_weight: float, left_hand_side: bool = False) -> int:
        """Get Daessy mount ID based on device weight and mounting side"""
        # Daessy mounts are typically stable regardless of side due to their locking mechanism
        if device_weight >= 2.6:
            return 7
        else:
            return 10
    
    @staticmethod
    def get_mount_recommendation_note(left_hand_side: bool) -> str:
        """Get explanatory note about mount selection"""
        if left_hand_side:
            return "Left-hand side mounting detected - recommending sturdy mounts with rotation lock to prevent unwanted movement."
        else:
            return "Standard right-hand side mounting - flexible positioning options available."

# -------------------------------
# DB Helpers
# -------------------------------
@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        logging.info("Connected to database.")
        yield conn
    except sqlite3.Error as e:
        logging.error(f"Database connection failed: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def safe_sql_in_clause(ids: List[int]) -> Tuple[str, List[int]]:
    """Safely create IN clause for SQL queries"""
    if not ids:
        return "id IN ()", []
    placeholders = ','.join('?' * len(ids))
    return f"id IN ({placeholders})", ids

def get_all_wheelchairs() -> Dict[str, int]:
    """Get all wheelchairs as a dict mapping model to ID"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, model FROM wheelchairs ORDER BY model")
            results = cursor.fetchall()
            return {row[1]: row[0] for row in results}
    except sqlite3.Error as e:
        logging.error(f"Failed to fetch wheelchairs: {e}")
        return {}

def get_aac_devices() -> List[Tuple[str, str]]:
    """Get all AAC devices as list of (make, model) tuples"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT make, model FROM aac_devices ORDER BY make, model")
            return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Failed to fetch AAC devices: {e}")
        return []

def get_aac_device_by_make_model(make: str, model: str) -> Optional[int]:
    """Get AAC device ID by make and model"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM aac_devices WHERE make = ? AND model = ?", (make, model))
            result = cursor.fetchone()
            return result[0] if result else None
    except sqlite3.Error as e:
        logging.error(f"Failed to fetch AAC device by make/model: {e}")
        return None

def get_floorstands_for_device(aac_device_id: int) -> Union[List[Tuple], str]:
    """Get suitable floorstands for an AAC device based on weight capacity"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # First get the device weight
            cursor.execute("SELECT weight FROM aac_devices WHERE id = ?", (aac_device_id,))
            device_result = cursor.fetchone()
            
            if not device_result:
                return "Invalid AAC device selection."
            
            device_weight = device_result[0]
            
            # Get all floorstands that can support the device weight
            # Structure: (id, name, manufacturer, description, url, weight_capacity, max_height)
            cursor.execute("""
                SELECT id, name, manufacturer, description, url, weight_capacity, max_height 
                FROM floorstands 
                WHERE weight_capacity >= ? 
                ORDER BY manufacturer, name
            """, (device_weight,))
            
            floorstands = cursor.fetchall()
            return floorstands
            
    except sqlite3.Error as e:
        logging.error(f"Failed to get floorstands for device: {e}")
        return "Failed to retrieve floorstands due to a database error."
    except Exception as e:
        logging.error(f"Unexpected error in get_floorstands_for_device: {e}")
        return "An unexpected error occurred while getting floorstands."

def get_tablemounts_for_device(aac_device_id: int) -> Union[List[Tuple], str]:
    """Get suitable table mounts for an AAC device based on weight capacity"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # First get the device weight
            cursor.execute("SELECT weight FROM aac_devices WHERE id = ?", (aac_device_id,))
            device_result = cursor.fetchone()
            
            if not device_result:
                return "Invalid AAC device selection."
            
            device_weight = device_result[0]
            
            # Get all table mounts that can support the device weight
            # Structure: (id, name, manufacturer, description, url, max_weight, style)
            cursor.execute("""
                SELECT id, name, manufacturer, description, url, max_weight, style 
                FROM tablemounts 
                WHERE max_weight >= ? 
                ORDER BY manufacturer, style, name
            """, (device_weight,))
            
            tablemounts = cursor.fetchall()
            return tablemounts
            
    except sqlite3.Error as e:
        logging.error(f"Failed to get table mounts for device: {e}")
        return "Failed to retrieve table mounts due to a database error."
    except Exception as e:
        logging.error(f"Unexpected error in get_tablemounts_for_device: {e}")
        return "An unexpected error occurred while getting table mounts."

def get_recommendations(wheelchair_id: int, aac_device_id: int, uses_eyegaze: bool = False, left_hand_side: bool = False) -> Union[Dict, str]:
    """Get mounting recommendations for wheelchair and AAC device combination"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get wheelchair details
            cursor.execute("SELECT model, frame_clamps, mount_location FROM wheelchairs WHERE id = ?", (wheelchair_id,))
            wheelchair = cursor.fetchone()

            # Get AAC device details
            cursor.execute("SELECT weight FROM aac_devices WHERE id = ?", (aac_device_id,))
            aac_device = cursor.fetchone()

            if not wheelchair or not aac_device:
                return "Invalid wheelchair or AAC device selection."

            frame_clamp_ids = [int(id.strip()) for id in wheelchair[1].split(',')]
            mount_location = wheelchair[2]
            device_weight = aac_device[0]

            # Get frame clamps
            clamp_where, clamp_params = safe_sql_in_clause(frame_clamp_ids)
            cursor.execute(f"SELECT * FROM clamps WHERE {clamp_where}", clamp_params)
            frame_clamps = cursor.fetchall()

            # Get all suitable mounts by weight
            cursor.execute(
                "SELECT * FROM mounts WHERE weight_capacity >= ? ORDER BY weight_capacity ASC",
                (device_weight,)
            )
            all_mounts = cursor.fetchall()

            # Get primary mount IDs using centralized logic
            rehadapt_mount_id = MountLogic.get_rehadapt_mount_id(device_weight, left_hand_side)
            daessy_mount_id = MountLogic.get_daessy_mount_id(device_weight, left_hand_side)
            primary_mount_ids = [rehadapt_mount_id, daessy_mount_id]

            # Get primary mounts
            primary_where, primary_params = safe_sql_in_clause(primary_mount_ids)
            cursor.execute(f"SELECT * FROM mounts WHERE {primary_where}", primary_params)
            primary_mounts = cursor.fetchall()

            # Separate primary and other mounts
            primary_mount_dict = {mount[0]: mount for mount in primary_mounts}
            other_mounts = [m for m in all_mounts if m[0] not in primary_mount_dict]
            mounts = list(primary_mount_dict.values()) + other_mounts

            # Get adapter ring
            cursor.execute("SELECT * FROM adaptors WHERE id = 1")
            adapter_ring = cursor.fetchone()

            return {
                "frame_clamps": frame_clamps,
                "mounts": mounts,
                "adapter_ring": adapter_ring,
                "mount_location": mount_location,
                "device_weight": device_weight,
                "primary_mount_ids": primary_mount_ids,
                "left_hand_side": left_hand_side,
                "mount_note": MountLogic.get_mount_recommendation_note(left_hand_side)
            }

    except sqlite3.Error as e:
        logging.error(f"Failed to get recommendations: {e}")
        return "Failed to retrieve recommendations due to a database error."
    except Exception as e:
        logging.error(f"Unexpected error in get_recommendations: {e}")
        return "An unexpected error occurred while getting recommendations."
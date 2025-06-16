import streamlit as st
import sqlite3
from typing import Dict, List, Tuple, Optional

DB_PATH = "./mounting_solutions.db"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def get_all_wheelchairs() -> Dict[str, int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, model FROM wheelchairs ORDER BY model")
    results = cursor.fetchall()
    conn.close()
    return {row[1]: row[0] for row in results}

def get_aac_devices() -> List[Tuple[str, str]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT make, model FROM aac_devices ORDER BY make, model")
    results = cursor.fetchall()
    conn.close()
    return results

def get_aac_device_by_make_model(make: str, model: str) -> Optional[int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM aac_devices WHERE make = ? AND model = ?", (make, model))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_recommendations(wheelchair_id: int, aac_device_id: int) -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT model, frame_clamps, mount_location FROM wheelchairs WHERE id = ?", (wheelchair_id,))
    wheelchair = cursor.fetchone()

    cursor.execute("SELECT weight FROM aac_devices WHERE id = ?", (aac_device_id,))
    aac_device = cursor.fetchone()

    if not wheelchair or not aac_device:
        conn.close()
        return "Invalid wheelchair or AAC device selection"

    frame_clamp_ids = [int(id.strip()) for id in wheelchair[1].split(',')]
    mount_location = wheelchair[2]
    device_weight = aac_device[0]

    cursor.execute(f"SELECT * FROM clamps WHERE id IN ({','.join('?' * len(frame_clamp_ids))})", frame_clamp_ids)
    frame_clamps = cursor.fetchall()

    cursor.execute("SELECT * FROM mounts WHERE weight_capacity >= ? ORDER BY weight_capacity ASC", (device_weight,))
    all_mounts = cursor.fetchall()

    # Split brand-specific logic
    rehadapt_mount_id, daessy_mount_id = None, None

    # Rehadapt weight bands
    if device_weight >= 2.6:
        rehadapt_mount_id = 3
    elif 1.6 <= device_weight <= 2.59:
        rehadapt_mount_id = 1
    elif 1.1 <= device_weight <= 1.59:
        rehadapt_mount_id = 4
    else:
        rehadapt_mount_id = 6

    # Daessy weight bands
    if device_weight >= 2.6:
        daessy_mount_id = 7
    else:
        daessy_mount_id = 10

    primary_mount_ids = [id for id in [rehadapt_mount_id, daessy_mount_id] if id]

    cursor.execute(f"SELECT * FROM mounts WHERE id IN ({','.join('?' * len(primary_mount_ids))})", primary_mount_ids)
    primary_mounts = cursor.fetchall()

    other_mounts = [m for m in all_mounts if m not in primary_mounts]
    mounts = primary_mounts + other_mounts

    cursor.execute("SELECT * FROM adaptors WHERE id = 1")
    adapter_ring = cursor.fetchone()

    conn.close()

    return {
        "frame_clamps": frame_clamps,
        "mounts": mounts,
        "adapter_ring": adapter_ring,
        "mount_location": mount_location
    }

st.markdown("<h1 style='text-align: center;'>AAC Mount Finder</h1>", unsafe_allow_html=True)

st.write("""
Welcome to the AAC Mount Finder! This tool will help you find compatible mounting solutions 
for your wheelchair and AAC device combination.
""")

st.warning("""
⚠️ Please note: The suggestions provided are based on general compatibility. The final solution may 
vary depending on factors such as:
- Wheelchair customizations or modifications
- Specific positioning requirements
- User needs and preferences
- Additional accessories on the wheelchair

Always consult with a qualified professional to confirm the most appropriate mounting solution for your specific needs.
""")

wheelchair_options = get_all_wheelchairs()
aac_devices = get_aac_devices()

selected_wheelchair = st.selectbox("Select Wheelchair", ["--Select Wheelchair--"] + list(wheelchair_options.keys()))
makes = ["--Select make--"] + sorted(list(set(device[0] for device in aac_devices)))
selected_make = st.selectbox("Select AAC Device Make", makes)

if selected_make != "--Select make--":
    models = ["--Select model--"] + sorted(list(set(device[1] for device in aac_devices if device[0] == selected_make)))
    selected_model = st.selectbox("Select AAC Device Model", models)
else:
    selected_model = "--Select model--"

if st.button("Find Solution"):
    if (selected_wheelchair == "--Select Wheelchair--" or selected_make == "--Select make--" or selected_model == "--Select model--"):
        st.warning("Please make selections for all dropdowns.")
    else:
        wheelchair_id = wheelchair_options[selected_wheelchair]
        aac_device_id = get_aac_device_by_make_model(selected_make, selected_model)

        recommendations = get_recommendations(wheelchair_id, aac_device_id)

        if isinstance(recommendations, str):
            st.error(recommendations)
        else:
            st.write(recommendations)  # Replace with your detailed display logic

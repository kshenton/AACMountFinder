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

# Streamlit app setup

st.markdown("<h1 style='text-align: center;'>AAC Mount Finder</h1>", unsafe_allow_html=True)

st.write("""
Welcome to the AAC Mount Finder! This tool will help you find compatible mounting solutions 
for your wheelchair and AAC device combination.
""")

st.warning("""
⚠️ Please note: The suggestions provided are based on general compatibility. The final solution may 
vary depending on factors such as:
- Wheelchair customisations or modifications
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
            # Get the manufacturer-specific components
            rehadapt_clamps = [c for c in recommendations["frame_clamps"] if c[2].lower() == 'rehadapt']
            rehadapt_mounts = [m for m in recommendations["mounts"] if m[2].lower() == 'rehadapt']
            daessy_clamps = [c for c in recommendations["frame_clamps"] if c[2].lower() == 'daessy']
            daessy_mounts = [m for m in recommendations["mounts"] if m[2].lower() == 'daessy']

            # Display mount location if available
            if recommendations.get("mount_location"):
                st.info(f"💡 **Suggested Mounting Location:** {recommendations['mount_location']}")

            # Rehadapt Solution (full width)
            if rehadapt_clamps and rehadapt_mounts:
                st.markdown("<h2 style='font-size: 24px;'>Suggested Rehadapt Solution</h2>", unsafe_allow_html=True)
                st.markdown("<p style='color: #28a745; font-size: 16px;'>+ Flexible positioning with quick-release system for easy adjustment</p>", unsafe_allow_html=True)
                with st.expander("Show/Hide Solution"):
                    st.write("Complete Rehadapt mounting solution:")
                    clamp = rehadapt_clamps[0]
                    mount = rehadapt_mounts[0]
                    st.write(f"**Inner Clamp:** {clamp[1]}")
                    st.write(clamp[3])
                    st.markdown(f"[More Info]({clamp[4]})")
                    st.write(f"**Mount:** {mount[1]}")
                    st.write(mount[4])
                    st.markdown(f"[More Info]({mount[5]})")

            # Daessy Solution (full width)
            if daessy_clamps and daessy_mounts:
                st.markdown("<h2 style='font-size: 24px;'>Suggested Daessy Solution</h2>", unsafe_allow_html=True)
                st.markdown("<p style='color: #28a745; font-size: 16px;'>+ Maximum stability with locked positioning for precise access methods such as Eyegaze</p>", unsafe_allow_html=True)
                with st.expander("Show/Hide Solution"):
                    st.write("Complete Daessy mounting solution:")
                    clamp = daessy_clamps[0]
                    mount = daessy_mounts[0]
                    st.write(f"**Inner Clamp:** {clamp[1]}")
                    st.write(clamp[3])
                    st.markdown(f"[More Info]({clamp[4]})")
                    st.write(f"**Mount:** {mount[1]}")
                    st.write(mount[4])
                    st.markdown(f"[More Info]({mount[5]})")

            # Cross-manufacturer combinations
            if any(c[2].lower() == 'daessy' for c in recommendations["frame_clamps"]) and any(m[2].lower() == 'rehadapt' for m in recommendations["mounts"]):
                st.markdown("<h2 style='font-size: 24px;'>Cross-Manufacturer Combinations</h2>", unsafe_allow_html=True)
                st.markdown("<p style='color: #28a745; font-size: 16px;'>+ Allows for using a Daessy Clamp with Rehadapt Mount using M3D Adapter Ring</p>", unsafe_allow_html=True)
                with st.expander("Show/Hide Combinations"):
                    st.write("**Note:** The following combinations require an adapter ring:")
                        
                    # Get device weight
                    cursor = get_db_connection().cursor()
                    cursor.execute("SELECT weight FROM aac_devices WHERE id = ?", (aac_device_id,))
                    device_weight = cursor.fetchone()[0]
                        
                    # Get compatible Daessy clamps from the recommendations
                    suitable_daessy_clamps = [c for c in recommendations["frame_clamps"] 
                                            if c[2].lower() == 'daessy']
                        
                    suitable_rehadapt_mounts = [m for m in rehadapt_mounts if 
                                                (device_weight >= 2.6 and m[0] == 3) or  # Heavy devices: ID 3
                                                (1.6 <= device_weight <= 2.59 and m[0] == 1) or  # Standard devices: ID 1
                                                (1.1 <= device_weight <= 1.59 and m[0] == 4) or  # Medium devices: ID 4
                                                (device_weight < 1.09 and m[0] == 6)]  # Light devices: ID 6
                        
                    for clamp in suitable_daessy_clamps:
                        for mount in suitable_rehadapt_mounts:
                            if recommendations["adapter_ring"]:
                                adapter = recommendations["adapter_ring"]
                                st.write(f"**Daessy Clamp:** {clamp[1]} + **Rehadapt Mount:** {mount[1]}")
                                st.write("**Required Adapter Ring:**")
                                st.write(f"- {adapter[1]}")
                                st.write(adapter[3])
                                st.markdown(f"[More Info]({adapter[4]})")
                                st.write("")
            
            # Other Suitable Mounts (full width)
            if len(rehadapt_mounts) > 1 or len(daessy_mounts) > 1:
                st.markdown("<h2 style='font-size: 24px;'>Other Compatible Mounts (By weight)</h2>", unsafe_allow_html=True)
                st.markdown("<p style='color: #28a745; font-size: 16px;'>+ Other suitable mounts by supplier depending on device weight</p>", unsafe_allow_html=True)
                with st.expander("Show/Hide Solutions"):
                    if len(rehadapt_mounts) > 1:
                        st.subheader("Rehadapt")
                        for mount in rehadapt_mounts[1:]:
                            st.write(f"**{mount[1]}**")
                            st.write(mount[4])
                            st.markdown(f"[More Info]({mount[5]})")
                            st.write("")
                        
                    if len(daessy_mounts) > 1:
                        st.subheader("Daessy")
                        for mount in daessy_mounts[1:]:
                            st.write(f"**{mount[1]}**")
                            st.write(mount[4])
                            st.markdown(f"[More Info]({mount[5]})")
                            st.write("")

            

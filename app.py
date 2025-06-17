import streamlit as st
from data import (
    get_all_wheelchairs, 
    get_aac_devices, 
    get_aac_device_by_make_model, 
    get_recommendations,
    get_floorstands_for_device,
    get_tablemounts_for_device,
    MountLogic,
    get_db_connection
)
import logging

# Configure logging for the Streamlit app
logging.basicConfig(level=logging.INFO)

def get_device_weight(aac_device_id: int) -> float:
    """Helper function to get device weight by ID"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT weight FROM aac_devices WHERE id = ?", (aac_device_id,))
            result = cursor.fetchone()
            return result[0] if result else 0.0
    except Exception as e:
        logging.error(f"Failed to get device weight: {e}")
        return 0.0

def display_component_info(component, component_type="Component"):
    """Helper function to display component information consistently"""
    st.write(f"**{component_type}:** {component[1]}")
    
    # Handle different component structures
    if component_type == "Mount":
        # Mounts have structure: (id, name, manufacturer, weight_capacity, description, url)
        if len(component) > 4:
            st.write(component[4])  # description
        if len(component) > 5 and component[5]:
            st.markdown(f"[More Info]({component[5]})")  # url
    else:
        # Clamps and Adaptors have structure: (id, name, manufacturer, description, url)
        if len(component) > 3:
            st.write(component[3])  # description
        if len(component) > 4 and component[4]:
            st.markdown(f"[More Info]({component[4]})")  # url

def display_floorstand_info(floorstand):
    """Helper function to display floorstand information"""
    # Floorstand structure: (id, name, manufacturer, description, url, weight_capacity, max_height)
    st.write(f"**Name:** {floorstand[1]}")
    if len(floorstand) > 3 and floorstand[3]:
        st.write(f"**Description:** {floorstand[3]}")
    if len(floorstand) > 5 and floorstand[5]:
        st.write(f"**Max Weight:** {floorstand[5]} kg")
    if len(floorstand) > 6 and floorstand[6]:
        st.write(f"**Max Height:** {floorstand[6]} mm")
    if len(floorstand) > 4 and floorstand[4]:
        st.markdown(f"[More Info]({floorstand[4]})")

def display_floorstands_by_manufacturer(floorstands):
    """Display floorstands organized by manufacturer"""
    # Group floorstands by manufacturer
    manufacturers = {}
    for floorstand in floorstands:
        manufacturer = floorstand[2]  # manufacturer is at index 2
        if manufacturer not in manufacturers:
            manufacturers[manufacturer] = []
        manufacturers[manufacturer].append(floorstand)
    
    # Display each manufacturer's floorstands
    for manufacturer, stands in manufacturers.items():
        st.markdown(f"<h2 style='font-size: 24px;'>{manufacturer} Solutions</h2>", unsafe_allow_html=True)
        
        with st.expander(f"Show/Hide {manufacturer} Floorstands"):
            for floorstand in stands:
                display_floorstand_info(floorstand)
                st.write("---")  # Separator between floorstands

def display_tablemount_info(tablemount):
    """Display information for a single table mount"""
    # Tablemount structure: (id, name, manufacturer, description, url, max_weight, style)
    st.write(f"**Name:** {tablemount[1]}")
    if len(tablemount) > 3 and tablemount[3]:
        st.write(f"**Description:** {tablemount[3]}")
    if len(tablemount) > 5 and tablemount[5]:
        st.write(f"**Max Weight:** {tablemount[5]} kg")
    if len(tablemount) > 6 and tablemount[6]:
        st.write(f"**Style:** {tablemount[6]}")
    if len(tablemount) > 4 and tablemount[4]:
        st.markdown(f"[More Info]({tablemount[4]})")

def display_tablemounts_by_manufacturer_and_style(tablemounts):
    """Display table mounts organized by manufacturer and style"""
    manufacturers = {}
    for tablemount in tablemounts:
        manufacturer = tablemount[2]
        style = tablemount[6] if len(tablemount) > 6 else "Unknown Style"
        key = (manufacturer, style)
        if key not in manufacturers:
            manufacturers[key] = []
        manufacturers[key].append(tablemount)
    
    for (manufacturer, style), mounts in manufacturers.items():
        st.markdown(f"<h2 style='font-size: 24px;'>{manufacturer} - {style}</h2>", unsafe_allow_html=True)
        with st.expander(f"Show/Hide {manufacturer} {style} Table Mounts"):
            for mount in mounts:
                display_tablemount_info(mount)
                st.write("---")


def display_mount_solutions(recommendations, aac_device_id):
    """Display the mount solutions in organized sections"""
    
    # Get manufacturer-specific components
    rehadapt_clamps = [c for c in recommendations["frame_clamps"] if c[2].lower() == 'rehadapt']
    rehadapt_mounts = [m for m in recommendations["mounts"] if m[2].lower() == 'rehadapt']
    daessy_clamps = [c for c in recommendations["frame_clamps"] if c[2].lower() == 'daessy']
    daessy_mounts = [m for m in recommendations["mounts"] if m[2].lower() == 'daessy']
    
    device_weight = recommendations.get("device_weight", 0.0)
    
    # Display mount location if available
    if recommendations.get("mount_location"):
        st.info(f"💡 **Suggested Mounting Location:** {recommendations['mount_location']}")
    
    # Display mounting side recommendation note
    if recommendations.get("mount_note"):
        side_color = "#17a2b8" if recommendations.get("left_hand_side") else "#28a745"
        st.markdown(f"<p style='color: {side_color}; font-size: 14px; font-style: italic;'>ℹ️ {recommendations['mount_note']}</p>", unsafe_allow_html=True)

    # Rehadapt Solution
    if rehadapt_clamps and rehadapt_mounts:
        st.markdown("<h2 style='font-size: 24px;'>Suggested Rehadapt Solution</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #28a745; font-size: 16px;'>+ Flexible positioning with quick-release system for easy adjustment</p>", unsafe_allow_html=True)
        
        # Get the primary Rehadapt mount based on weight and side
        primary_rehadapt_id = MountLogic.get_rehadapt_mount_id(device_weight, recommendations.get("left_hand_side", False))
        primary_rehadapt_mount = next((m for m in rehadapt_mounts if m[0] == primary_rehadapt_id), rehadapt_mounts[0] if rehadapt_mounts else None)
        
        with st.expander("Show/Hide Solution"):
            st.write("Complete Rehadapt mounting solution:")
            if recommendations.get("left_hand_side"):
                st.markdown("*🔒 Sturdy mount with rotation lock recommended for left-hand side mounting*")
            clamp = rehadapt_clamps[0]
            display_component_info(clamp, "Inner Clamp")
            if primary_rehadapt_mount:
                display_component_info(primary_rehadapt_mount, "Mount")
            else:
                st.warning("No suitable Rehadapt mount found for the selected criteria.")

    # Daessy Solution
    if daessy_clamps and daessy_mounts:
        st.markdown("<h2 style='font-size: 24px;'>Suggested Daessy Solution</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #28a745; font-size: 16px;'>+ Maximum stability with locked positioning for precise access methods such as Eyegaze</p>", unsafe_allow_html=True)
        
        # Get the primary Daessy mount based on weight and side
        primary_daessy_id = MountLogic.get_daessy_mount_id(device_weight, recommendations.get("left_hand_side", False))
        primary_daessy_mount = next((m for m in daessy_mounts if m[0] == primary_daessy_id), daessy_mounts[0] if daessy_mounts else None)
        
        with st.expander("Show/Hide Solution"):
            st.write("Complete Daessy mounting solution:")
            clamp = daessy_clamps[0]
            display_component_info(clamp, "Inner Clamp")
            if primary_daessy_mount:
                display_component_info(primary_daessy_mount, "Mount")
            else:
                st.warning("No suitable Daessy mount found for the selected criteria.")

    # Cross-manufacturer combinations
    if daessy_clamps and rehadapt_mounts and recommendations.get("adapter_ring"):
        st.markdown("<h2 style='font-size: 24px;'>Cross-Manufacturer Combinations</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #28a745; font-size: 16px;'>+ Allows for using a Daessy Clamp with Rehadapt Mount using M3D Adapter Ring</p>", unsafe_allow_html=True)
        
        with st.expander("Show/Hide Combinations"):
            st.write("**Note:** The following combinations require an adapter ring:")
            
            # Get the primary Rehadapt mount for cross-compatibility
            primary_rehadapt_id = MountLogic.get_rehadapt_mount_id(device_weight, recommendations.get("left_hand_side", False))
            suitable_rehadapt_mount = next((m for m in rehadapt_mounts if m[0] == primary_rehadapt_id), None)
            
            if suitable_rehadapt_mount:
                for clamp in daessy_clamps:
                    st.write(f"**Daessy Clamp:** {clamp[1]} + **Rehadapt Mount:** {suitable_rehadapt_mount[1]}")
                    st.write("**Required Adapter Ring:**")
                    adapter = recommendations["adapter_ring"]
                    st.write(f"- {adapter[1]}")
                    st.write(adapter[3])
                    if len(adapter) > 4 and adapter[4]:
                        st.markdown(f"[More Info]({adapter[4]})")
                    st.write("")

    # Other Suitable Mounts
    other_rehadapt_mounts = [m for m in rehadapt_mounts if m[0] != MountLogic.get_rehadapt_mount_id(device_weight, recommendations.get("left_hand_side", False))]
    other_daessy_mounts = [m for m in daessy_mounts if m[0] != MountLogic.get_daessy_mount_id(device_weight, recommendations.get("left_hand_side", False))]
    
    if other_rehadapt_mounts or other_daessy_mounts:
        st.markdown("<h2 style='font-size: 24px;'>Other Compatible Mounts (By weight)</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #28a745; font-size: 16px;'>+ Other suitable mounts by supplier depending on device weight</p>", unsafe_allow_html=True)
        
        with st.expander("Show/Hide Solutions"):
            if other_rehadapt_mounts:
                st.subheader("Rehadapt")
                for mount in other_rehadapt_mounts:
                    display_component_info(mount, "Mount")
                    st.write("")
                
            if other_daessy_mounts:
                st.subheader("Daessy")
                for mount in other_daessy_mounts:
                    display_component_info(mount, "Mount")
                    st.write("")

def show_landing_page():
    """Display the landing page with three options"""
    st.markdown("<h1 style='text-align: center;'>AAC Mount Finder</h1>", unsafe_allow_html=True)
    
    st.write("""
    Welcome to the AAC Mount Finder! This tool will help you find compatible mounting solutions 
    for your AAC device. Please choose the type of mounting solution you need:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🦽 Wheelchair Mounts", use_container_width=True):
            st.session_state.page = "wheelchair_mounts"
            st.rerun()
    
    with col2:
        if st.button("🏢 Floor Stands", use_container_width=True):
            st.session_state.page = "floorstands"
            st.rerun()
    
    with col3:
        if st.button("📋 Table Mounts", use_container_width=True):
            st.session_state.page = "tablemounts"
            st.rerun()

def show_wheelchair_mounts():
    """Display the wheelchair mounts page (existing functionality)"""
    st.markdown("<h1 style='text-align: center;'>Wheelchair Mount Finder</h1>", unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to Main Menu"):
        st.session_state.page = "landing"
        st.rerun()

    st.write("""
    This tool will help you find compatible mounting solutions 
    for your wheelchair and AAC device combination.
    """)

    # Warning message
    st.warning("""
    ⚠️ Please note: This app is intended to be used as a guide, and the suggestions provided are based on general compatibility. The final solution may 
    vary depending on factors such as:
    - Wheelchair customisations or modifications
    - Specific positioning requirements
    - User needs and preferences
    - Additional accessories on the wheelchair

    Always consult with a qualified professional to confirm the most appropriate mounting solution for your specific needs.
    """)

    # Load data with error handling
    try:
        wheelchair_options = get_all_wheelchairs()
        aac_devices = get_aac_devices()
    except Exception as e:
        st.error(f"Failed to load data from database: {e}")
        logging.error(f"Data loading failed: {e}")
        return

    if not wheelchair_options:
        st.error("No wheelchairs found in database.")
        return
    
    if not aac_devices:
        st.error("No AAC devices found in database.")
        return

    # Selection interface
    selected_wheelchair = st.selectbox(
        "Select Wheelchair", 
        ["--Select Wheelchair--"] + list(wheelchair_options.keys())
    )
    
    makes = ["--Select make--"] + sorted(list(set(device[0] for device in aac_devices)))
    selected_make = st.selectbox("Select AAC Device Make", makes)

    selected_model = "--Select model--"
    if selected_make != "--Select make--":
        models = ["--Select model--"] + sorted(list(set(
            device[1] for device in aac_devices if device[0] == selected_make
        )))
        selected_model = st.selectbox("Select AAC Device Model", models)
    
    # Add left-hand side checkbox
    left_hand_side = st.checkbox(
        "Mounted left-hand side?", 
        help="Check this if the device will be mounted on the left side of the wheelchair. This will recommend sturdy mounts with rotation lock to prevent unwanted movement."
    )

    # Process selection
    if st.button("Find Solution"):
        if (selected_wheelchair == "--Select Wheelchair--" or 
            selected_make == "--Select make--" or 
            selected_model == "--Select model--"):
            st.warning("Please make selections for all dropdowns.")
            return

        try:
            wheelchair_id = wheelchair_options[selected_wheelchair]
            aac_device_id = get_aac_device_by_make_model(selected_make, selected_model)
            
            if not aac_device_id:
                st.error("Selected AAC device not found.")
                return

            # Get recommendations
            recommendations = get_recommendations(wheelchair_id, aac_device_id, left_hand_side=left_hand_side)

            if isinstance(recommendations, str):
                st.error(recommendations)
                return

            # Display solutions
            display_mount_solutions(recommendations, aac_device_id)
            
        except Exception as e:
            st.error(f"An error occurred while finding solutions: {e}")
            logging.error(f"Solution finding failed: {e}")

def show_floorstands():
    """Display the floorstands page"""
    st.markdown("<h1 style='text-align: center;'>Floor Stand Finder</h1>", unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to Main Menu"):
        st.session_state.page = "landing"
        st.rerun()

    st.write("""
    This tool will help you find suitable floor stand solutions for your AAC device.
    """)

    # Warning message
    st.warning("""
    ⚠️ Please note: This app is intended to be used as a guide, and the suggestions provided are based on general compatibility. The final solution may 
    vary depending on factors such as:
    - Specific positioning requirements
    - User needs and preferences
    - Environmental considerations
    - Height and weight requirements

    Always consult with a qualified professional to confirm the most appropriate floor stand solution for your specific needs.
    """)

    # Load AAC devices
    try:
        aac_devices = get_aac_devices()
    except Exception as e:
        st.error(f"Failed to load data from database: {e}")
        logging.error(f"Data loading failed: {e}")
        return

    if not aac_devices:
        st.error("No AAC devices found in database.")
        return

    # Device selection interface
    makes = ["--Select make--"] + sorted(list(set(device[0] for device in aac_devices)))
    selected_make = st.selectbox("Select AAC Device Make", makes)

    selected_model = "--Select model--"
    if selected_make != "--Select make--":
        models = ["--Select model--"] + sorted(list(set(
            device[1] for device in aac_devices if device[0] == selected_make
        )))
        selected_model = st.selectbox("Select AAC Device Model", models)

    # Process selection
    if st.button("Find Floor Stands"):
        if selected_make == "--Select make--" or selected_model == "--Select model--":
            st.warning("Please select both make and model.")
            return

        try:
            aac_device_id = get_aac_device_by_make_model(selected_make, selected_model)
            
            if not aac_device_id:
                st.error("Selected AAC device not found.")
                return

            # Get suitable floorstands
            floorstands = get_floorstands_for_device(aac_device_id)

            if isinstance(floorstands, str):
                st.error(floorstands)
                return

            if not floorstands:
                st.warning("No suitable floor stands found for the selected device.")
                return

            # Display floorstands
            st.success(f"Found {len(floorstands)} suitable floor stand(s) for your device:")
            display_floorstands_by_manufacturer(floorstands)
        except Exception as e:
            st.error(f"An error occurred while finding floor stands: {e}")
            logging.error(f"Floor stand finding failed: {e}")
            
def show_tablemounts():
    """Display the table mounts page"""
    st.markdown("<h1 style='text-align: center;'>Table Mount Finder</h1>", unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to Main Menu"):
        st.session_state.page = "landing"
        st.rerun()

    st.write("""
    This tool will help you find suitable table mounting solutions for your AAC device.
    """)

    # Warning message
    st.warning("""
    ⚠️ Please note: This app is intended to be used as a guide, and the suggestions provided are based on general compatibility. The final solution may 
    vary depending on factors such as:
    - Table thickness and material
    - Specific positioning requirements
    - User needs and preferences
    - Environmental considerations
    - Desk/table stability requirements

    Always consult with a qualified professional to confirm the most appropriate table mount solution for your specific needs.
    """)

    # Load AAC devices
    try:
        aac_devices = get_aac_devices()
    except Exception as e:
        st.error(f"Failed to load data from database: {e}")
        logging.error(f"Data loading failed: {e}")
        return

    if not aac_devices:
        st.error("No AAC devices found in database.")
        return

    # Device selection interface
    makes = ["--Select make--"] + sorted(list(set(device[0] for device in aac_devices)))
    selected_make = st.selectbox("Select AAC Device Make", makes)

    selected_model = "--Select model--"
    if selected_make != "--Select make--":
        models = ["--Select model--"] + sorted(list(set(
            device[1] for device in aac_devices if device[0] == selected_make
        )))
        selected_model = st.selectbox("Select AAC Device Model", models)

    # Process selection
    if st.button("Find Table Mounts"):
        if selected_make == "--Select make--" or selected_model == "--Select model--":
            st.warning("Please select both make and model.")
            return

        try:
            aac_device_id = get_aac_device_by_make_model(selected_make, selected_model)
            
            if not aac_device_id:
                st.error("Selected AAC device not found.")
                return

            # Get suitable table mounts
            tablemounts = get_tablemounts_for_device(aac_device_id)

            if isinstance(tablemounts, str):
                st.error(tablemounts)
                return

            if not tablemounts:
                st.warning("No suitable table mounts found for the selected device.")
                return

            # Display table mounts
            st.success(f"Found {len(tablemounts)} suitable table mount(s) for your device:")
            display_tablemounts_by_manufacturer_and_style(tablemounts)
            
        except Exception as e:
            st.error(f"An error occurred while finding table mounts: {e}")
            logging.error(f"Table mount finding failed: {e}")

def main():
    """Main Streamlit application function"""
    
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = "landing"
    
    # Display appropriate page based on session state
    if st.session_state.page == "landing":
        show_landing_page()
    elif st.session_state.page == "wheelchair_mounts":
        show_wheelchair_mounts()
    elif st.session_state.page == "floorstands":
        show_floorstands()
    elif st.session_state.page == "tablemounts":
        show_tablemounts()

if __name__ == "__main__":
    main()
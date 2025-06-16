import streamlit as st
from data import (
    get_all_wheelchairs, 
    get_aac_devices, 
    get_aac_device_by_make_model, 
    get_recommendations,
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
    if len(component) > 3:
        st.write(component[3])
    if len(component) > 4 and component[4]:
        st.markdown(f"[More Info]({component[4]})")

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

    # Rehadapt Solution
    if rehadapt_clamps and rehadapt_mounts:
        st.markdown("<h2 style='font-size: 24px;'>Suggested Rehadapt Solution</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #28a745; font-size: 16px;'>+ Flexible positioning with quick-release system for easy adjustment</p>", unsafe_allow_html=True)
        
        # Get the primary Rehadapt mount based on weight
        primary_rehadapt_id = MountLogic.get_rehadapt_mount_id(device_weight)
        primary_rehadapt_mount = next((m for m in rehadapt_mounts if m[0] == primary_rehadapt_id), rehadapt_mounts[0])
        
        with st.expander("Show/Hide Solution"):
            st.write("Complete Rehadapt mounting solution:")
            clamp = rehadapt_clamps[0]
            display_component_info(clamp, "Inner Clamp")
            display_component_info(primary_rehadapt_mount, "Mount")

    # Daessy Solution
    if daessy_clamps and daessy_mounts:
        st.markdown("<h2 style='font-size: 24px;'>Suggested Daessy Solution</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #28a745; font-size: 16px;'>+ Maximum stability with locked positioning for precise access methods such as Eyegaze</p>", unsafe_allow_html=True)
        
        # Get the primary Daessy mount based on weight
        primary_daessy_id = MountLogic.get_daessy_mount_id(device_weight)
        primary_daessy_mount = next((m for m in daessy_mounts if m[0] == primary_daessy_id), daessy_mounts[0])
        
        with st.expander("Show/Hide Solution"):
            st.write("Complete Daessy mounting solution:")
            clamp = daessy_clamps[0]
            display_component_info(clamp, "Inner Clamp")
            display_component_info(primary_daessy_mount, "Mount")

    # Cross-manufacturer combinations
    if daessy_clamps and rehadapt_mounts and recommendations.get("adapter_ring"):
        st.markdown("<h2 style='font-size: 24px;'>Cross-Manufacturer Combinations</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #28a745; font-size: 16px;'>+ Allows for using a Daessy Clamp with Rehadapt Mount using M3D Adapter Ring</p>", unsafe_allow_html=True)
        
        with st.expander("Show/Hide Combinations"):
            st.write("**Note:** The following combinations require an adapter ring:")
            
            # Get the primary Rehadapt mount for cross-compatibility
            primary_rehadapt_id = MountLogic.get_rehadapt_mount_id(device_weight)
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
    other_rehadapt_mounts = [m for m in rehadapt_mounts if m[0] != MountLogic.get_rehadapt_mount_id(device_weight)]
    other_daessy_mounts = [m for m in daessy_mounts if m[0] != MountLogic.get_daessy_mount_id(device_weight)]
    
    if other_rehadapt_mounts or other_daessy_mounts:
        st.markdown("<h2 style='font-size: 24px;'>Other Compatible Mounts (By weight)</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #28a745; font-size: 16px;'>+ Other suitable mounts by supplier depending on device weight</p>", unsafe_allow_html=True)
        
        with st.expander("Show/Hide Solutions"):
            if other_rehadapt_mounts:
                st.subheader("Rehadapt")
                for mount in other_rehadapt_mounts:
                    display_component_info(mount, mount[1])
                    st.write("")
                
            if other_daessy_mounts:
                st.subheader("Daessy")
                for mount in other_daessy_mounts:
                    display_component_info(mount, mount[1])
                    st.write("")

def main():
    """Main Streamlit application function"""
    
    # App header
    st.markdown("<h1 style='text-align: center;'>AAC Mount Finder</h1>", unsafe_allow_html=True)

    st.write("""
    Welcome to the AAC Mount Finder! This tool will help you find compatible mounting solutions 
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
            recommendations = get_recommendations(wheelchair_id, aac_device_id)

            if isinstance(recommendations, str):
                st.error(recommendations)
                return

            # Display solutions
            display_mount_solutions(recommendations, aac_device_id)
            
        except Exception as e:
            st.error(f"An error occurred while finding solutions: {e}")
            logging.error(f"Solution finding failed: {e}")

if __name__ == "__main__":
    main()
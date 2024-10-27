import streamlit as st

def init_target_settings():
    """Initialize target settings in session state if not present."""
    if 'targets' not in st.session_state:
        st.session_state.targets = {
            'heart_rate': {'min': 120, 'max': 150, 'enabled': False},
            'power': {'min': 150, 'max': 200, 'enabled': False},
            'cadence': {'min': 70, 'max': 90, 'enabled': False},
            'speed': {'min': 20, 'max': 30, 'enabled': False},
            'resistance': {'min': 5, 'max': 10, 'enabled': False}
        }

def render_target_settings():
    """Render target settings in the sidebar."""
    init_target_settings()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Target Settings")
    
    metrics = {
        'heart_rate': ('Heart Rate (bpm)', (60, 200)),
        'power': ('Power (W)', (0, 400)),
        'cadence': ('Cadence (rpm)', (0, 120)),
        'speed': ('Speed (km/h)', (0, 50)),
        'resistance': ('Resistance Level', (1, 20))
    }
    
    for metric, (label, (min_limit, max_limit)) in metrics.items():
        st.sidebar.markdown(f"### {label}")
        enabled = st.sidebar.checkbox(f"Enable {label} Target", 
                                    value=st.session_state.targets[metric]['enabled'],
                                    key=f"enable_{metric}")
        
        if enabled:
            col1, col2 = st.sidebar.columns(2)
            with col1:
                min_val = st.number_input(
                    f"Min {label}",
                    min_value=min_limit,
                    max_value=max_limit,
                    value=st.session_state.targets[metric]['min'],
                    key=f"min_{metric}"
                )
            with col2:
                max_val = st.number_input(
                    f"Max {label}",
                    min_value=min_limit,
                    max_value=max_limit,
                    value=st.session_state.targets[metric]['max'],
                    key=f"max_{metric}"
                )
            
            # Update target values in session state
            st.session_state.targets[metric].update({
                'enabled': enabled,
                'min': min_val,
                'max': max_val
            })
        else:
            st.session_state.targets[metric]['enabled'] = False

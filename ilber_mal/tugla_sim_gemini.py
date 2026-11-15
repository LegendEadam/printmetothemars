import streamlit as st
import math
import time

# --- PAGE SETTINGS ---
st.set_page_config(page_title="ISRU Physics-Based Simulator", layout="centered", page_icon="🧱")

# --- CONSTANT PLANET DATABASE ---
planet_constants = {
    "Mars": {
        "T_min": -125.0,
        "T_max": 20.0,
        "pressure_Pa": 600.0,
        "oxygen_ratio": "0.13% (Main gas: 95% CO2)",
        "water_status": "No liquid surface water (Ice and hydrated minerals)",
        "g": 3.72,
        "solar_W_m2": 590.0,
        "iron_oxide_pct": 17.5,
        "perchlorate_ratio": 0.005,
        "water_energy_J_L": 2.88e7
    },
    "Earth": {
        "T_min": 10.0,
        "T_max": 25.0,
        "pressure_Pa": 101325.0,
        "oxygen_ratio": "21.0% (Main gas: 78% N2)",
        "water_status": "High (71% of surface is liquid water)",
        "g": 9.81,
        "solar_W_m2": 1361.0,
        "iron_oxide_pct": 12.0,
        "perchlorate_ratio": 0.0,
        "water_energy_J_L": 1.8e6
    }
}

# --- BASE REGOLITH PHYSICAL CONSTANTS ---
base_regolith = {
    "c": 800.0,
    "L_f": 400000.0,
    "rho": 3000.0,
    "alpha": 7.5,
    "K": 50.0,
    "T_m_silica": 1710.0
}

# --- CONSTANT RAW MATERIAL DATABASE ---
method_constants = {
    "Sulfur Concrete (Sulfur Binder)": {
        "code": "sulfur",
        "resource": {
            "Mars": "High (Widespread Ca/Mg sulfate deposits on surface)",
            "Earth": "Medium-High (Volcanic sulfur and industrial byproduct)"
        },
        "binder_pct": 30,
        "press_pressure_MPa": 20.0,
        "furnace_power_kW": 50.0,
        "c_binder": 710.0,
        "L_f_binder": 54000.0,
        "rho_binder": 2070.0,
        "alpha_binder": 64.0,
        "K_binder": 7.7,
        "T_m_binder": 115.2,
        "water_ratio": 0.0,
        "extra_facility": "Sulfate reduction and 120-140 °C melting kettle"
    },
    "Sintered Regolith (Direct Firing)": {
        "code": "sinter",
        "resource": {
            "Mars": "Very High (45% SiO2, 17-18% iron oxide basaltic soil)",
            "Earth": "High (Basaltic rock and volcanic ash deposits)"
        },
        "binder_pct": 20,
        "press_pressure_MPa": 45.0,
        "furnace_power_kW": 50.0,
        "c_binder": 800.0,
        "L_f_binder": 120000.0,
        "rho_binder": 3000.0,
        "alpha_binder": 8.5,
        "K_binder": 50.0,
        "T_m_binder": 1250.0,
        "water_ratio": 0.0,
        "extra_facility": "Perchlorate treatment furnace (400-600 °C) + Microwave/Resistance Sintering"
    },
    "Geopolymer / Conventional Water-Based Concrete": {
        "code": "geopolymer",
        "resource": {
            "Mars": "Low (No liquid water, difficult water extraction from hydrated minerals)",
            "Earth": "Very High (Abundant surface water and aluminosilicate clay)"
        },
        "binder_pct": 25,
        "press_pressure_MPa": 15.0,
        "furnace_power_kW": 50.0,
        "c_binder": 4184.0,
        "L_f_binder": 334000.0,
        "rho_binder": 2400.0,
        "alpha_binder": 12.0,
        "K_binder": 22.0,
        "T_m_binder": 1100.0,
        "water_ratio": 0.15,
        "extra_facility": "Alkaline activator (NaOH) synthesizer and pressurized curing chamber"
    }
}

# --- SIDEBAR: SELECTIONS ---
st.sidebar.header("1. Planet Selection")
planet_options = ["Mars", "Earth", "Custom (Custom Planet)"]
selected_planet = st.sidebar.radio("Environment:", planet_options)

if selected_planet != "Custom (Custom Planet)":
    p_data = planet_constants[selected_planet].copy()
else:
    st.sidebar.subheader("🌍 Custom Planet Parameters")
    c_T_min = st.sidebar.slider("Night Temperature (°C)", -273.0, 1000.0, -100.0, 1.0)
    c_T_max = st.sidebar.slider("Day Temperature (°C)", -273.0, 1000.0, 20.0, 1.0)
    c_pressure = st.sidebar.number_input("Surface Pressure (Pa)", min_value=0.0, max_value=10000000.0, value=600.0, step=100.0)
    c_g = st.sidebar.slider("Gravitational Acceleration (m/s²)", 0.01, 50.0, 3.72, 0.01)
    c_iron = st.sidebar.slider("Regolith Iron Oxide Ratio (%)", 0.0, 100.0, 15.0, 0.5)
    c_perchlorate = st.sidebar.slider("Soil Perchlorate Ratio (%)", 0.0, 100.0, 0.5, 0.1)
    c_oxygen = st.sidebar.slider("Atmospheric Oxygen Ratio (%)", 0.0, 100.0, 0.5, 0.1)
    c_solar = st.sidebar.slider("Solar Irradiance (W/m²)", 0.0, 10000

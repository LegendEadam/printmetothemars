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
    c_solar = st.sidebar.slider("Solar Irradiance (W/m²)", 0.0, 10000.0, 600.0, 10.0)
    c_water_status = st.sidebar.selectbox(
        "Water Availability:",
        [
            "None / In Ice Form (High Energy)",
            "Limited Groundwater (Medium Energy)",
            "Abundant Liquid Surface Water (Low Energy)"
        ]
    )

    water_energy_map = {
        "None / In Ice Form (High Energy)": 2.88e7,
        "Limited Groundwater (Medium Energy)": 1.2e7,
        "Abundant Liquid Surface Water (Low Energy)": 1.8e6
    }

    p_data = {
        "T_min": c_T_min,
        "T_max": c_T_max,
        "pressure_Pa": c_pressure,
        "oxygen_ratio": f"{c_oxygen:.2f}%",
        "water_status": c_water_status,
        "g": c_g,
        "solar_W_m2": c_solar,
        "iron_oxide_pct": c_iron,
        "perchlorate_ratio": c_perchlorate / 100.0,
        "water_energy_J_L": water_energy_map[c_water_status]
    }

st.sidebar.markdown("---")
st.sidebar.header("2. Raw Material Selection")
method_options = list(method_constants.keys()) + ["Custom (Custom Material)"]
selected_method = st.sidebar.selectbox("Raw Material / Method:", method_options)

if selected_method != "Custom (Custom Material)":
    m_data = method_constants[selected_method].copy()
    resource_text = m_data["resource"][selected_planet] if selected_planet != "Custom (Custom Planet)" else "User-Defined Planetary Resource"
else:
    st.sidebar.subheader("🧱 Custom Material Parameters")
    c_binder_pct = st.sidebar.slider("Binder / Active Phase Ratio (%)", 0, 100, 30, 1)
    c_Tm_binder = st.sidebar.slider("Binder Pure Melting Point (°C)", -273.0, 4000.0, 150.0, 5.0)
    c_alpha_binder = st.sidebar.slider("Binder Thermal Expansion (×10⁻⁶ /°C)", 0.0, 1000.0, 35.0, 1.0)
    c_c_binder = st.sidebar.slider("Binder Specific Heat (J/kg·K)", 1.0, 20000.0, 900.0, 50.0)
    c_Lf_binder = st.sidebar.slider("Phase Change Latent Heat (kJ/kg)", 0.0, 10000.0, 100.0, 10.0) * 1000.0
    c_rho_binder = st.sidebar.slider("Binder Density (kg/m³)", 10.0, 30000.0, 2200.0, 50.0)
    c_water_pct = st.sidebar.slider("Water Requirement by Mass (%)", 0, 100, 0, 1)
    c_press_MPa = st.sidebar.slider("Forming Press Pressure (MPa)", 0.0, 1000.0, 30.0, 1.0)
    c_furnace_kW = st.sidebar.slider("Furnace / Reactor Power (kW)", 1.0, 100000.0, 50.0, 1.0)

    m_data = {
        "code": "custom",
        "binder_pct": c_binder_pct,
        "press_pressure_MPa": c_press_MPa,
        "furnace_power_kW": c_furnace_kW,
        "c_binder": c_c_binder,
        "L_f_binder": c_Lf_binder,
        "rho_binder": c_rho_binder,
        "alpha_binder": c_alpha_binder,
        "K_binder": 15.0,
        "T_m_binder": c_Tm_binder,
        "water_ratio": c_water_pct / 100.0,
        "extra_facility": "User-Defined Production Unit"
    }
    resource_text = "Custom Mixture"

# --- PLANETARY PHYSICAL CALCULATIONS ---
Delta_T_daily = abs(p_data["T_max"] - p_data["T_min"])
T_avg = (p_data["T_max"] + p_data["T_min"]) / 2.0

# Clausius-Clapeyron: clamped at 1e-5 Pa internally when pressure is 0.0 Pa to prevent log(0) error
safe_pressure_Pa = max(1e-5, p_data["pressure_Pa"])
T_boiling_K = 1.0 / ((1.0 / 373.15) - (8.314 / 40660.0) * math.log(safe_pressure_Pa / 101325.0))
T_boiling_C = round(T_boiling_K - 273.15, 1)

st.title("🧱 Physics-Based ISRU Production Simulator")
st.markdown("Environmental and material-based physical simulation for producing 1 Ton (1000 kg) of structural blocks.")

st.subheader(f"🌍 Selected Environment Parameters: {selected_planet}")
p_col1, p_col2 = st.columns(2)

with p_col1:
    st.write(f"**Day-Night Temperature Range:** {p_data['T_min']} °C to {p_data['T_max']} °C")
    st.write(f"**Daily Temperature Difference (ΔT):** {Delta_T_daily:.1f} °C")
    st.write(f"**Average Surface Temperature:** {T_avg:.1f} °C")
    st.write(f"**Surface Pressure:** {p_data['pressure_Pa']:.1f} Pa")
    st.write(f"**Oxygen Ratio:** {p_data['oxygen_ratio']}")

with p_col2:
    st.write(f"**Water Availability:** {p_data['water_status']}")
    st.write(f"**Pressure-Dependent Water Boiling Point:** {T_boiling_C} °C")
    st.write(f"**Gravitational Acceleration (g):** {p_data['g']:.2f} m/s²")
    st.write(f"**Solar Irradiance:** {p_data['solar_W_m2']} W/m²")
    st.write(f"**Regolith Iron Oxide Ratio:** {p_data['iron_oxide_pct']}%")

st.markdown("---")

# --- PRODUCTION BUTTON AND CALCULATIONS ---
if st.button(f"🚀 Start Production with {selected_method} (1 Ton)", use_container_width=True):
    with st.spinner('Solving physical equations...'):
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.003)
            progress_bar.progress(i + 1)

    w_b = m_data["binder_pct"] / 100.0
    w_r = 1.0 - w_b
    press_MPa = m_data["press_pressure_MPa"]

    T_m_regolith = base_regolith["T_m_silica"] - (p_data["iron_oxide_pct"] * 26.5)

    if m_data["code"] == "sulfur":
        T_melting_C = m_data["T_m_binder"] + (p_data["pressure_Pa"] - 101325.0) * 1e-7
        T_process_C = T_melting_C + 21.5 - (press_MPa * 0.08)
    elif m_data["code"] == "sinter":
        T_melting_C = T_m_regolith
        T_process_C = ((T_melting_C + 273.15) * (0.85 - (press_MPa * 0.0005))) - 273.15
    elif m_data["code"] == "geopolymer":
        T_melting_C = T_m_regolith
        T_process_C = max(25.0, T_avg + 15.0)
    else:  # Custom
        T_melting_C = m_data["T_m_binder"]
        T_process_C = T_melting_C + 20.0 - (press_MPa * 0.05)

    # Turner Thermal Expansion Model
    numerator = (w_r * base_regolith["alpha"] * base_regolith["K"]) + (w_b * m_data["alpha_binder"] * m_data["K_binder"])
    denominator = (w_r * base_regolith["K"]) + (w_b * m_data["K_binder"])
    alpha_eff = numerator / denominator if denominator > 0 else 0
    daily_expansion_mm = alpha_eff * 1e-6 * Delta_T_daily * 1000.0

    # Density and Block Count
    porosity = 0.25 * math.exp(-press_MPa / 50.0)
    rho_theoretical = 1.0 / ((w_r / base_regolith["rho"]) + (w_b / m_data["rho_binder"])) if w_b > 0 or w_r > 0 else 0
    rho_block = rho_theoretical * (1.0 - porosity)
    brick_mass_kg = rho_block * 0.0015
    brick_count = int(1000.0 / brick_mass_kg) if brick_mass_kg > 0 else 0

    # Thermodynamic Energy
    mass_kg = 1000.0
    c_eff = (w_r * base_regolith["c"]) + (w_b * m_data["c_binder"])
    delta_T_heating = max(0.0, T_process_C - T_avg)

    Q_sensible_J = mass_kg * c_eff * delta_T_heating

    # In custom material, if the entire mass does not melt, latent heat is added only for the binder fraction
    if m_data["code"] == "sinter":
        Q_latent_J = mass_kg * m_data["L_f_binder"]
    else:
        Q_latent_J = (mass_kg * w_b) * m_data["L_f_binder"]

    Q_preprocess_J = 0.0
    if p_data["perchlorate_ratio"] > 0 and T_process_C > 400.0:
        Q_preprocess_J = mass_kg * p_data["perchlorate_ratio"] * 2.5e6

    water_needed_L = mass_kg * m_data["water_ratio"]
    water_energy_J = water_needed_L * p_data["water_energy_J_L"]

    furnace_efficiency = max(0.1, min(1.0, 0.85 - (T_process_C / 3500.0)))
    total_energy_J = ((Q_sensible_J + Q_latent_J + Q_preprocess_J) / furnace_efficiency) + water_energy_J
    total_energy_kWh = total_energy_J / 3.6e6

    # Duration (division by zero errors prevented)
    feeding_time_hr = 1.2 / math.sqrt(p_data["g"] / 9.81) if p_data["g"] > 0 else float('inf')
    heating_time_hr = ((Q_sensible_J + Q_latent_J) / 3.6e6) / m_data["furnace_power_kW"] if m_data["furnace_power_kW"] > 0 else float('inf')
    convection_coeff = 1.0 + 0.4 * math.exp(-p_data["pressure_Pa"] / 5000.0)
    cooling_time_hr = (delta_T_heating / 140.0) * convection_coeff

    total_time_hr = feeding_time_hr + heating_time_hr + cooling_time_hr

    st.subheader("📊 Raw Material and Production Data")

    m_col1, m_col2 = st.columns(2)

    with m_col1:
        st.markdown("**Physical Parameters**")
        st.write(f"**Resource:** {resource_text}")
        st.write(f"**Binder Ratio:** {m_data['binder_pct']}%")
        st.write(f"**Process Temperature:** {T_process_C:.1f} °C")
        st.write(f"**Melting Point:** {T_melting_C:.1f} °C")
        st.write(f"**Thermal Expansion (α):** {alpha_eff:.2f} × 10⁻⁶ /°C")
        st.write(f"**Daily Expansion/Contraction:** {daily_expansion_mm:.3f} mm/m")

    with m_col2:
        st.markdown("**Consumption and Output (1 Ton)**")
        st.write(f"**Water Requirement:** {water_needed_L:.0f} Liters")
        st.write(f"**Additional Facility:** {m_data['extra_facility']}")
        st.write(f"**Output:** {brick_count} Bricks ({rho_block:.0f} kg/m³)")
        st.metric(label="Calculated Total Energy", value=f"{total_energy_kWh:.1f} kWh")
        st.metric(label="Completion Time", value=f"{total_time_hr:.1f} Hours")

    with st.expander("📐 Show Underlying Physics Equations"):
        st.latex(r"Q_{\text{total}} = \frac{m \cdot c_{\text{eff}} \cdot (T_{\text{process}} - T_{\text{ambient}}) + m_{\text{active}} \cdot L_f + \Delta H_{\text{perchlorate}}}{\eta_{\text{furnace}}} + E_{\text{water}}")
        st.latex(r"\alpha_{\text{eff}} = \frac{\alpha_r w_r K_r + \alpha_b w_b K_b}{w_r K_r + w_b K_b} \quad , \quad \Delta L = L_0 \cdot \alpha_{\text{eff}} \cdot \Delta T_{\text{daily}}")
        st.latex(r"t_{\text{total}} = \frac{m}{\dot{m}_0 \sqrt{g / g_{\text{Earth}}}} + \frac{Q_{\text{heating}}}{P_{\text{furnace}}} + t_{\text{annealing}}(P_{\text{ambient}}, \Delta T)")

import streamlit as st
import math
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="ISRU Fizik Tabanlı Simülatör", layout="centered", page_icon="🧱")

# --- SABİT GEZEGEN VERİTABANI ---
gezegen_sabitleri = {
    "Mars": {
        "T_min": -125.0,
        "T_max": 20.0,
        "basinc_Pa": 600.0,
        "oksijen_orani": "%0,13 (Ana gaz: %95 CO2)",
        "su_durumu": "Yüzeyde sıvı su yok (Buz ve hidratlı mineraller)",
        "g": 3.72, 
        "gunes_W_m2": 590.0,
        "demir_oksit_yuzde": 17.5,
        "perklorat_orani": 0.005,
        "su_enerji_J_L": 2.88e7
    },
    "Dünya": {
        "T_min": 10.0,
        "T_max": 25.0,
        "basinc_Pa": 101325.0,
        "oksijen_orani": "%21,0 (Ana gaz: %78 N2)",
        "su_durumu": "Yüksek (Yüzeyin %71'i sıvı su)",
        "g": 9.81, 
        "gunes_W_m2": 1361.0,
        "demir_oksit_yuzde": 12.0, 
        "perklorat_orani": 0.0,
        "su_enerji_J_L": 1.8e6
    }
}

# --- BAZ REGOLİT FİZİKSEL SABİTLERİ ---
regolit_baz = {
    "c": 800.0,          
    "L_f": 400000.0,     
    "rho": 3000.0,       
    "alpha": 7.5,        
    "K": 50.0,           
    "T_m_silika": 1710.0 
}

# --- SABİT HAMMADDE VERİTABANI ---
yontem_sabitleri = {
    "Kükürt Betonu (Sülfür Bağlayıcılı)": {
        "kod": "sulfur",
        "kaynak": {
            "Mars": "Yüksek (Yüzeyde yaygın Ca/Mg sülfat yatakları)",
            "Dünya": "Orta-Yüksek (Volkanik sülfür ve endüstriyel yan ürün)"
        },
        "baglayici_yuzde": 30,    
        "pres_basinci_MPa": 20.0,   
        "firin_gucu_kW": 50.0,      
        "c_baglayici": 710.0,
        "L_f_baglayici": 54000.0,
        "rho_baglayici": 2070.0,
        "alpha_baglayici": 64.0,
        "K_baglayici": 7.7,
        "T_m_baglayici": 115.2,
        "su_orani": 0.0,
        "ek_tesis": "Sülfat indirgeme ve 120-140 °C eritme kazanı"
    },
    "Sinterlenmiş Regolit (Doğrudan Pişirme)": {
        "kod": "sinter",
        "kaynak": {
            "Mars": "Çok Yüksek (%45 SiO2, %17-18 demir oksit bazaltik toprak)",
            "Dünya": "Yüksek (Bazaltik kayaç ve volkanik kül yatakları)"
        },
        "baglayici_yuzde": 20,    
        "pres_basinci_MPa": 45.0,   
        "firin_gucu_kW": 50.0,
        "c_baglayici": 800.0,
        "L_f_baglayici": 120000.0,
        "rho_baglayici": 3000.0,
        "alpha_baglayici": 8.5,
        "K_baglayici": 50.0,
        "T_m_baglayici": 1250.0,
        "su_orani": 0.0,
        "ek_tesis": "Perklorat arıtma fırını (400-600 °C) + Mikrodalga/Direnç Sinterleme"
    },
    "Jeopolimer / Geleneksel Su Bazlı Beton": {
        "kod": "geopolymer",
        "kaynak": {
            "Mars": "Düşük (Sıvı su yok, hidratlı minerallerden su eldesi zor)",
            "Dünya": "Çok Yüksek (Yüzey suyu ve alüminosilikat kil yaygın)"
        },
        "baglayici_yuzde": 25,
        "pres_basinci_MPa": 15.0,
        "firin_gucu_kW": 50.0,
        "c_baglayici": 4184.0,
        "L_f_baglayici": 334000.0,
        "rho_baglayici": 2400.0,
        "alpha_baglayici": 12.0,
        "K_baglayici": 22.0,
        "T_m_baglayici": 1100.0,
        "su_orani": 0.15,
        "ek_tesis": "Alkali aktivatör (NaOH) sentezleyici ve basınçlı kürleme odası"
    }
}

# --- YAN MENÜ: SEÇİMLER ---
st.sidebar.header("1. Gezegen Seçimi")
gezegen_secenekleri = ["Mars", "Dünya", "Custom (Özel Gezegen)"]
secilen_gezegen = st.sidebar.radio("Ortam:", gezegen_secenekleri)

if secilen_gezegen != "Custom (Özel Gezegen)":
    g_veri = gezegen_sabitleri[secilen_gezegen].copy()
else:
    st.sidebar.subheader("🌍 Özel Gezegen Parametreleri")
    c_T_min = st.sidebar.slider("Gece Sıcaklığı (°C)", -273.0, 1000.0, -100.0, 1.0)
    c_T_max = st.sidebar.slider("Gündüz Sıcaklığı (°C)", -273.0, 1000.0, 20.0, 1.0)
    c_basinc = st.sidebar.number_input("Yüzey Basıncı (Pa)", min_value=0.1, max_value=10000000.0, value=600.0, step=100.0)
    c_g = st.sidebar.slider("Yerçekimi İvmesi (m/s²)", 0.01, 50.0, 3.72, 0.01)
    c_demir = st.sidebar.slider("Regolit Demir Oksit Oranı (%)", 0.0, 100.0, 15.0, 0.5)
    c_perklorat = st.sidebar.slider("Toprak Perklorat Oranı (%)", 0.0, 100.0, 0.5, 0.1)
    c_oksijen = st.sidebar.slider("Atmosferik Oksijen Oranı (%)", 0.0, 100.0, 0.5, 0.1)
    c_gunes = st.sidebar.slider("Güneş Işınımı (W/m²)", 0.0, 10000.0, 600.0, 10.0)
    c_su_durumu = st.sidebar.selectbox("Su Bulunabilirliği:", ["Yok / Buz Halinde (Yüksek Enerji)", "Kısıtlı Yeraltı Suyu (Orta Enerji)", "Yüzeyde Bol Sıvı Su (Düşük Enerji)"])
    
    su_enerji_haritasi = {
        "Yok / Buz Halinde (Yüksek Enerji)": 2.88e7,
        "Kısıtlı Yeraltı Suyu (Orta Enerji)": 1.2e7,
        "Yüzeyde Bol Sıvı Su (Düşük Enerji)": 1.8e6
    }
    
    g_veri = {
        "T_min": c_T_min,
        "T_max": c_T_max,
        "basinc_Pa": c_basinc,
        "oksijen_orani": f"%{c_oksijen:.2f}",
        "su_durumu": c_su_durumu,
        "g": c_g,
        "gunes_W_m2": c_gunes,
        "demir_oksit_yuzde": c_demir,
        "perklorat_orani": c_perklorat / 100.0,
        "su_enerji_J_L": su_enerji_haritasi[c_su_durumu]
    }

st.sidebar.markdown("---")
st.sidebar.header("2. Hammadde Seçimi")
yontem_secenekleri = list(yontem_sabitleri.keys()) + ["Custom (Özel Hammadde)"]
secilen_yontem = st.sidebar.selectbox("Hammadde / Yöntem:", yontem_secenekleri)

if secilen_yontem != "Custom (Özel Hammadde)":
    m_veri = yontem_sabitleri[secilen_yontem].copy()
    kaynak_metni = m_veri["kaynak"][secilen_gezegen] if secilen_gezegen != "Custom (Özel Gezegen)" else "Kullanıcı Tanımlı Gezegen Kaynağı"
else:
    st.sidebar.subheader("🧱 Özel Hammadde Parametreleri")
    c_baglayici_yuzde = st.sidebar.slider("Bağlayıcı / Aktif Faz Oranı (%)", 0, 100, 30, 1)
    c_Tm_baglayici = st.sidebar.slider("Bağlayıcı Saf Erime Noktası (°C)", -273.0, 4000.0, 150.0, 5.0)
    c_alpha_baglayici = st.sidebar.slider("Bağlayıcı Genleşme (×10⁻⁶ /°C)", 0.0, 1000.0, 35.0, 1.0)
    c_c_baglayici = st.sidebar.slider("Bağlayıcı Özgül Isısı (J/kg·K)", 1.0, 20000.0, 900.0, 50.0)
    c_Lf_baglayici = st.sidebar.slider("Faz Değişim Gizli Isısı (kJ/kg)", 0.0, 10000.0, 100.0, 10.0) * 1000.0
    c_rho_baglayici = st.sidebar.slider("Bağlayıcı Yoğunluğu (kg/m³)", 10.0, 30000.0, 2200.0, 50.0)
    c_su_yuzde = st.sidebar.slider("Kütlece Su İhtiyacı (%)", 0, 100, 0, 1)
    c_pres_MPa = st.sidebar.slider("Şekillendirme Pres Basıncı (MPa)", 0.0, 1000.0, 30.0, 1.0)
    c_firin_kW = st.sidebar.slider("Fırın / Reaktör Gücü (kW)", 1.0, 100000.0, 50.0, 1.0)
    
    m_veri = {
        "kod": "custom",
        "baglayici_yuzde": c_baglayici_yuzde,
        "pres_basinci_MPa": c_pres_MPa,
        "firin_gucu_kW": c_firin_kW,
        "c_baglayici": c_c_baglayici,
        "L_f_baglayici": c_Lf_baglayici,
        "rho_baglayici": c_rho_baglayici,
        "alpha_baglayici": c_alpha_baglayici,
        "K_baglayici": 15.0,
        "T_m_baglayici": c_Tm_baglayici,
        "su_orani": c_su_yuzde / 100.0,
        "ek_tesis": "Kullanıcı Tanımlı Üretim Ünitesi"
    }
    kaynak_metni = "Özel Karışım"

# --- GEZEGEN FİZİKSEL HESAPLAMALARI ---
Delta_T_gunluk = abs(g_veri["T_max"] - g_veri["T_min"])
T_ortalama = (g_veri["T_max"] + g_veri["T_min"]) / 2.0

# Clausius-Clapeyron: log(0) hatasını önlemek için basınç min 0.1 Pa sınırında
T_kaynama_K = 1.0 / ((1.0 / 373.15) - (8.314 / 40660.0) * math.log(g_veri["basinc_Pa"] / 101325.0))
T_kaynama_C = round(T_kaynama_K - 273.15, 1)

st.title("🧱 Fizik Tabanlı ISRU Üretim Simülatörü")
st.markdown("1 Ton (1000 kg) yapı bloğu üretimi için çevresel ve malzeme bazlı fiziksel simülasyon.")

st.subheader(f"🌍 Seçilen Ortam Parametreleri: {secilen_gezegen}")
p_col1, p_col2 = st.columns(2)

with p_col1:
    st.write(f"**Gece-Gündüz Sıcaklık Aralığı:** {g_veri['T_min']} °C ile {g_veri['T_max']} °C")
    st.write(f"**Günlük Sıcaklık Farkı (ΔT):** {Delta_T_gunluk:.1f} °C")
    st.write(f"**Ortalama Yüzey Sıcaklığı:** {T_ortalama:.1f} °C")
    st.write(f"**Yüzey Basıncı:** {g_veri['basinc_Pa']:.1f} Pa")
    st.write(f"**Oksijen Oranı:** {g_veri['oksijen_orani']}")

with p_col2:
    st.write(f"**Su Bulunabilirliği:** {g_veri['su_durumu']}")
    st.write(f"**Basınca Bağlı Su Kaynama Noktası:** {T_kaynama_C} °C")
    st.write(f"**Yerçekimi İvmesi (g):** {g_veri['g']:.2f} m/s²")
    st.write(f"**Güneş Işınımı:** {g_veri['gunes_W_m2']} W/m²")
    st.write(f"**Regolit Demir Oksit Oranı:** %{g_veri['demir_oksit_yuzde']}")

st.markdown("---")

# --- ÜRETİM BUTONU VE HESAPLAMALAR ---
if st.button(f"🚀 {secilen_yontem} ile Üretimi Başlat (1 Ton)", use_container_width=True):
    with st.spinner('Fiziksel denklemler çözülüyor...'):
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.003)
            progress_bar.progress(i + 1)

    w_b = m_veri["baglayici_yuzde"] / 100.0
    w_r = 1.0 - w_b
    pres_MPa = m_veri["pres_basinci_MPa"]

    T_m_regolit = regolit_baz["T_m_silika"] - (g_veri["demir_oksit_yuzde"] * 26.5)

    if m_veri["kod"] == "sulfur":
        T_erime_C = m_veri["T_m_baglayici"] + (g_veri["basinc_Pa"] - 101325.0) * 1e-7
        T_islem_C = T_erime_C + 21.5 - (pres_MPa * 0.08)
    elif m_veri["kod"] == "sinter":
        T_erime_C = T_m_regolit
        T_islem_C = ((T_erime_C + 273.15) * (0.85 - (pres_MPa * 0.0005))) - 273.15
    elif m_veri["kod"] == "geopolymer":
        T_erime_C = T_m_regolit
        T_islem_C = max(25.0, T_ortalama + 15.0)
    else: # Custom
        T_erime_C = m_veri["T_m_baglayici"]
        T_islem_C = T_erime_C + 20.0 - (pres_MPa * 0.05)

    # Turner Genleşme Modeli
    pay = (w_r * regolit_baz["alpha"] * regolit_baz["K"]) + (w_b * m_veri["alpha_baglayici"] * m_veri["K_baglayici"])
    payda = (w_r * regolit_baz["K"]) + (w_b * m_veri["K_baglayici"])
    alpha_eff = pay / payda if payda > 0 else 0
    gunluk_genlesme_mm = alpha_eff * 1e-6 * Delta_T_gunluk * 1000.0

    # Yoğunluk ve Blok Adedi
    gozeneklilik = 0.25 * math.exp(-pres_MPa / 50.0)
    rho_teorik = 1.0 / ((w_r / regolit_baz["rho"]) + (w_b / m_veri["rho_baglayici"])) if w_b > 0 or w_r > 0 else 0
    rho_blok = rho_teorik * (1.0 - gozeneklilik)
    tugla_kutlesi_kg = rho_blok * 0.0015
    tugla_adedi = int(1000.0 / tugla_kutlesi_kg) if tugla_kutlesi_kg > 0 else 0

    # Termodinamik Enerji
    kutle_kg = 1000.0
    c_eff = (w_r * regolit_baz["c"]) + (w_b * m_veri["c_baglayici"])
    delta_T_isitma = max(0.0, T_islem_C - T_ortalama)

    Q_duyulur_J = kutle_kg * c_eff * delta_T_isitma
    
    # Custom malzemede tüm kütle erimiyorsa sadece bağlayıcı oranı kadar gizli ısı eklenir
    if m_veri["kod"] == "sinter":
        Q_gizli_J = kutle_kg * m_veri["L_f_baglayici"]
    else:
        Q_gizli_J = (kutle_kg * w_b) * m_veri["L_f_baglayici"]

    Q_on_islem_J = 0.0
    if g_veri["perklorat_orani"] > 0 and T_islem_C > 400.0:
        Q_on_islem_J = kutle_kg * g_veri["perklorat_orani"] * 2.5e6

    su_ihtiyaci_L = kutle_kg * m_veri["su_orani"]
    su_enerji_J = su_ihtiyaci_L * g_veri["su_enerji_J_L"]

    firin_verimi = max(0.1, min(1.0, 0.85 - (T_islem_C / 3500.0)))
    toplam_enerji_J = ((Q_duyulur_J + Q_gizli_J + Q_on_islem_J) / firin_verimi) + su_enerji_J
    toplam_enerji_kWh = toplam_enerji_J / 3.6e6

    # Süre (0'a bölünme hataları engellendi)
    besleme_suresi_saat = 1.2 / math.sqrt(g_veri["g"] / 9.81) if g_veri["g"] > 0 else float('inf')
    isitma_suresi_saat = ((Q_duyulur_J + Q_gizli_J) / 3.6e6) / m_veri["firin_gucu_kW"] if m_veri["firin_gucu_kW"] > 0 else float('inf')
    konveksiyon_katsayisi = 1.0 + 0.4 * math.exp(-g_veri["basinc_Pa"] / 5000.0)
    soguma_suresi_saat = (delta_T_isitma / 140.0) * konveksiyon_katsayisi
    
    toplam_sure_saat = besleme_suresi_saat + isitma_suresi_saat + soguma_suresi_saat

    st.subheader(f"📊 Hammadde ve Üretim Verileri")
    
    m_col1, m_col2 = st.columns(2)
    
    with m_col1:
        st.markdown("**Fiziksel Parametreler**")
        st.write(f"**Kaynak:** {kaynak_metni}")
        st.write(f"**Bağlayıcı Oranı:** %{m_veri['baglayici_yuzde']}")
        st.write(f"**İşlem Sıcaklığı:** {T_islem_C:.1f} °C")
        st.write(f"**Erime Noktası:** {T_erime_C:.1f} °C")
        st.write(f"**Genleşme (α):** {alpha_eff:.2f} × 10⁻⁶ /°C")
        st.write(f"**Günlük Uzama/Büzülme:** {gunluk_genlesme_mm:.3f} mm/m")
        
    with m_col2:
        st.markdown("**Tüketim ve Çıktı (1 Ton)**")
        st.write(f"**Su İhtiyacı:** {su_ihtiyaci_L:.0f} Litre")
        st.write(f"**Ek Tesis:** {m_veri['ek_tesis']}")
        st.write(f"**Çıktı:** {tugla_adedi} Tuğla ({rho_blok:.0f} kg/m³)")
        st.metric(label="Hesaplanan Toplam Enerji", value=f"{toplam_enerji_kWh:.1f} kWh")
        st.metric(label="Tamamlanma Süresi", value=f"{toplam_sure_saat:.1f} Saat")

    with st.expander("📐 Arka Planda Çalışan Fizik Denklemlerini Göster"):
        st.latex(r"Q_{\text{toplam}} = \frac{m \cdot c_{\text{eff}} \cdot (T_{\text{işlem}} - T_{\text{ortam}}) + m_{\text{aktif}} \cdot L_f + \Delta H_{\text{perklorat}}}{\eta_{\text{fırın}}} + E_{\text{su}}")
        st.latex(r"\alpha_{\text{eff}} = \frac{\alpha_r w_r K_r + \alpha_b w_b K_b}{w_r K_r + w_b K_b} \quad , \quad \Delta L = L_0 \cdot \alpha_{\text{eff}} \cdot \Delta T_{\text{günlük}}")
        st.latex(r"t_{\text{toplam}} = \frac{m}{\dot{m}_0 \sqrt{g / g_{\text{Dünya}}}} + \frac{Q_{\text{ısıtma}}}{P_{\text{fırın}}} + t_{\text{tavlama}}(P_{\text{ortam}}, \Delta T)")
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from datetime import datetime, timedelta
import numpy as np

# Configuration de la page
st.set_page_config(page_title="PDM Tracker", layout="wide", page_icon="📈")

# --- STYLE CSS (Tout ce qui change l'esthétique est ici) ---
st.markdown("""
    <style>
    /* 1. FOND DE TOUTE LA PAGE (Blanc cassé / Crème) */
    .stApp {
        background-color: ##fffff3 !important;
    }

    /* 2. LE TITRE PRINCIPAL EN ROUGE */
    .title-rouge {
        color: #ca0201 !important;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 20px;
    }

    /* 3. BARRE LATÉRALE (SIDEBAR) */
    [data-testid="stSidebar"] {
        background-color: ##fffff3 !important;
    }
    /* Titres et labels de la sidebar en ROUGE */
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] label p,
    [data-testid="stSidebar"] h3 {
        color: #ca0201 !important;
        font-weight: bold !important;
    }
    /* Les petits textes "30 jours", "365 jours" en ROUGE */
    .sidebar-text {
        color: #ca0201 !important;
        font-size: 0.8rem;
    }

    /* 4. BLOC MESSAGE D'AMOUR (Le grand bloc rouge) */
    .message-damour {
        background-color: #ca0201; /* Le même rouge passion */
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0px 4px 15px rgba(202, 2, 1, 0.2);
    }
    /* Force le texte à l'intérieur en BLANC CRÈME pour la lisibilité */
    .message-damour h3, .message-damour p, .message-damour strong {
        color: ##fffff3 !important; /* Un blanc légèrement cassé */
    }

    /* 5. SLIDERS ROUGES */
    .stSlider [data-baseweb="slider"] > div > div > div > div {
        background-color: #ca0201 !important;
    }
    .stSlider [data-baseweb="slider"] > div > div {
        background-color: rgba(151, 151, 151, 0.2) !important;
    }
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background-color: #ca0201 !important;
        border: 2px solid #ca0201 !important;
    }
    .stSlider [data-testid="stThumbValue"] {
        color: #ca0201 !important;
        font-weight: bold;
    }

    /* 6. STATISTIQUES (Metrics) */
    .stMetric { 
        background-color: rgba(245, 209, 208, 0.3) !important; /* Rose très pâle */
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #ca0201; 
    }
    [data-testid="stMetricLabel"] p { color: #2C2C2C !important; } /* Label sombre */
    [data-testid="stMetricValue"] div { color: #ca0201 !important; font-weight: bold; } /* Valeur rouge */

    /* 7. ZONE DE SAISIE */
    .stTextArea textarea {
        background-color: #FAF9F6 !important; /* Fond blanc cassé */
        color: #2C2C2C !important; /* Texte sombre */
        border: 1px solid #cccccc !important;
    }
    /* Titre de la saisie en NOIR */
    .saisie-titre {
        color: #000000 !important;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 0px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- TITRE DE L'APPLICATION EN ROUGE ---
st.markdown('<p class="title-rouge">📈 Suivi et prédiction PDM</p>', unsafe_allow_html=True)

# --- MESSAGE PERSONNEL (Bloc rouge, texte blanc) ---
st.markdown(f"""
    <div class="message-damour">
        <h3>Coucou mon amoureux ❤️</h3>
        <p>Comme promis, je t'ai codé un site qui te permet de voir ta progression. C'est super simple à utiliser et tu n'auras pas de difficultés vu que tu es super intelligent, super beau, super musclé, super drôle.</p>
        <p>Si tu as des questions, envoie-moi un snap, j'essayerai de te répondre sous 3 à 5 jours ouvrés.</p>
        <p><strong>Gros kiss, ton amoureuse</strong></p>
    </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR (PARAMÈTRES EN ROUGE) ---
st.sidebar.header("⚙️ Paramètres")

forecast_days = st.sidebar.slider("Nombre de jours à prédire :", 30, 365, 90)
col_a, col_b = st.sidebar.columns(2)
col_a.markdown("<p class='sidebar-text'>30 jours</p>", unsafe_allow_html=True)
col_b.markdown("<p class='sidebar-text' style='text-align: right;'>365 jours</p>", unsafe_allow_html=True)

st.sidebar.divider()

st.sidebar.subheader("Méthode de calcul")
recent_weight_val = st.sidebar.slider(
    "Pondération", 
    min_value=0, 
    max_value=100, 
    value=44, # Sa valeur actuelle
    label_visibility="collapsed") / 100

c1, c2 = st.sidebar.columns(2)
c1.markdown("<p class='sidebar-text'>Sur tout l'historique</p>", unsafe_allow_html=True)
c2.markdown("<p class='sidebar-text' style='text-align: right;'>Sur les 30 derniers jours</p>", unsafe_allow_html=True)

# --- ZONE DE SAISIE (Texte noir) ---
st.write("")
st.markdown('<p class="saisie-titre">📝 Saisie des données</p>', unsafe_allow_html=True)
st.markdown('<p style="color: #2C2C2C;">Ici tu colles directement ta note avec tes poids et leurs dates :</p>', unsafe_allow_html=True)

raw_text = st.text_area(
    "Zone de saisie", 
    placeholder="Exemple :\n01/01/2026 75.5\n05/01/2026 75.8", 
    height=200, 
    label_visibility="collapsed"
)

if raw_text:
    # Regex pour capturer la date et le poids
    pattern = r"(\d{1,2}/\d{1,2}/\d{2,4}).*?(\d{2,3}[.,]?\d?)"
    matches = re.findall(pattern, raw_text)

    if matches:
        data = []
        for m_date, m_weight in matches:
            try:
                # Nettoyage du poids (remplacement virgule par point)
                val_weight = float(m_weight.replace(',', '.'))
                # Conversion de la date
                clean_date = pd.to_datetime(m_date, dayfirst=True)
                data.append({"Date": clean_date, "Poids": val_weight})
            except:
                continue

        # Création et tri du DataFrame
        df = pd.DataFrame(data).sort_values("Date")

        if not df.empty and 'Poids' in df.columns:
            # Lissage de la courbe (Moyenne Mobile Exponentielle)
            df['Poids_Lisse'] = df['Poids'].ewm(span=7).mean()
            
            # --- CALCULS DES PENTES ---
            first_date = df['Date'].min()
            df['DaysPassed'] = (df['Date'] - first_date).dt.days
            
            # Pente Globale
            m_global, _ = np.polyfit(df['DaysPassed'], df['Poids'], 1)
            
            # Pente Récente (30 derniers jours)
            recent_cutoff = df['Date'].max() - timedelta(days=30)
            recent_df = df[df['Date'] >= recent_cutoff]
            
            if len(recent_df) > 1:
                r_days = (recent_df['Date'] - recent_df['Date'].min()).dt.days
                m_recent, _ = np.polyfit(r_days, recent_df['Poids'], 1)
            else:
                m_recent = m_global 

            # Mélange hybride
            m_hybrid = (m_global * (1 - recent_weight_val)) + (m_recent * recent_weight_val)

            # --- PRÉDICTION ---
            last_date = df['Date'].max()
            last_weight_smooth = df['Poids_Lisse'].iloc[-1]
            last_weight_real = df['Poids'].iloc[-1]
            
            future_dates = [last_date + timedelta(days=x) for x in range(0, forecast_days + 1)]
            prediction_path = [last_weight_smooth + (m_hybrid * x) for x in range(0, forecast_days + 1)]

            # --- GRAPHIQUE ---
            fig = go.Figure()

            # Historique (Ligne rouge fluide)
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['Poids_Lisse'], 
                mode='lines', name='Historique',
                line=dict(color='#ca0201', width=4, shape='spline')
            ))
            
            # Prédiction (Dots espacés tous les 7 jours)
            fig.add_trace(go.Scatter(
                x=future_dates[::7], y=prediction_path[::7],
                mode='markers', name='Prédiction',
                marker=dict(color='#ca0201', size=5, symbol='circle')
            ))

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis=dict(gridcolor='rgba(0,0,0,0.1)', tickfont=dict(color='#2C2C2C')),
                yaxis=dict(gridcolor='rgba(0,0,0,0.1)', tickfont=dict(color='#2C2C2C')),
                hovermode="x unified",
                legend=dict(font=dict(color="#2C2C2C"), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- STATS ---
            st.write("### Statistiques")
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Poids actuel", f"{last_weight_real} kg")
            target_w = prediction_path[-1]
            diff = target_w - last_weight_real
            col_m2.metric(f"Objectif ({forecast_days} j)", f"{target_w:.1f} kg", f"{diff:+.1f} kg")
            weekly_rate = (m_hybrid * 7)
            col_m3.metric("Vitesse actuelle", f"{weekly_rate:+.2f} kg / sem")
    else:
        st.info("💡 J'attends tes données... Copie-les au format 'Date Poids' !")
else:
    st.info("👋 Hello ! Colle tes données de poids ci-dessus pour voir la magie opérer.")        color: #ca0201 !important;
        font-weight: bold !important;
    }

    /* 4. BLOC MESSAGE D'AMOUR (Rose) */
    .message-damour {
        background-color: #ca0201;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #ca0201;
        margin-bottom: 25px;
    }
    .message-damour p, .message-damour h3 {
        color: #fffff3 !important;
    }

    /* 5. SLIDERS (Rouge #ca0201) */
    .stSlider [data-baseweb="slider"] > div > div > div > div {
        background-color: #ca0201 !important;
    }
    .stSlider [data-baseweb="slider"] > div > div {
        background-color: rgba(151, 151, 151, 0.2) !important;
    }
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background-color: #ca0201 !important;
        border: 2px solid #ca0201 !important;
    }
    .stSlider [data-testid="stThumbValue"] {
        color: #ca0201 !important;
        font-weight: bold;
    }

    /* 6. STATISTIQUES (Metrics en bas) */
    .stMetric { 
        background-color: #F5D1D0 !important;
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #ca0201; 
    }
    [data-testid="stMetricLabel"] p { color: #000000 !important; }
    [data-testid="stMetricValue"] div { color: #ca0201 !important; font-weight: bold; }

    /* 7. ZONE DE SAISIE */
    .stTextArea textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
    }
    .saisie-titre {
        color: #000000 !important;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 0px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Suivi et prédiction PDM")

# --- MESSAGE PERSONNEL ---
st.markdown(f"""
    <div class="message-damour">
        <h3>Coucou mon amoureux ❤️</h3>
        <p>Comme promis, je t'ai codé un site qui te permet de voir ta progression. C'est super simple à utiliser et tu n'auras pas de difficultés vu que tu es super intelligent, super beau, super musclé, super drôle.</p>
        <p>Si tu as des questions, envoie-moi un snap, j'essayerai de te répondre sous 3 à 5 jours ouvrés.</p>
        <p><strong>Gros kiss, ton amoureuse</strong></p>
    </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.header("⚙️ Paramètres")

forecast_days = st.sidebar.slider("Nombre de jours à prédire :", 30, 365, 90)
col_a, col_b = st.sidebar.columns(2)
col_a.markdown("<p style='color: #ca0201; font-size: 0.8rem;'>30 jours</p>", unsafe_allow_html=True)
col_b.markdown("<p style='text-align: right; color: #ca0201; font-size: 0.8rem;'>365 jours</p>", unsafe_allow_html=True)

st.sidebar.divider()

st.sidebar.subheader("Méthode de calcul")
recent_weight_val = st.sidebar.slider(
    "Pondération", 
    min_value=0, 
    max_value=100, 
    value=50,
    label_visibility="collapsed") / 100

c1, c2 = st.sidebar.columns(2)
c1.markdown("<p style='color: #ca0201; font-size: 0.8rem;'>Sur tout l'historique</p>", unsafe_allow_html=True)
c2.markdown("<p style='text-align: right; color: #ca0201; font-size: 0.8rem;'>Sur les 30 derniers jours</p>", unsafe_allow_html=True)

# --- ZONE DE SAISIE ---
st.write("")
st.markdown('<p class="saisie-titre">📝 Saisie des données</p>', unsafe_allow_html=True)
st.markdown('<p style="color: #000000;">Ici tu colles directement ta note avec tes poids et leurs dates :</p>', unsafe_allow_html=True)

raw_text = st.text_area(
    "Zone de saisie", 
    placeholder="Exemple :\n01/01/2026 75.5\n05/01/2026 75.8", 
    height=200, 
    label_visibility="collapsed"
)

if raw_text:
    pattern = r"(\d{1,2}/\d{1,2}/\d{2,4}).*?(\d{2,3}[.,]?\d?)"
    matches = re.findall(pattern, raw_text)

    if matches:
        data = []
        for m_date, m_weight in matches:
            try:
                val_weight = float(m_weight.replace(',', '.'))
                clean_date = pd.to_datetime(m_date, dayfirst=True)
                data.append({"Date": clean_date, "Poids": val_weight})
            except:
                continue

        df = pd.DataFrame(data).sort_values("Date")

        if not df.empty and 'Poids' in df.columns:
            # Lissage de la courbe
            df['Poids_Lisse'] = df['Poids'].ewm(span=7).mean()
            
            # Calculs des pentes
            first_date = df['Date'].min()
            df['DaysPassed'] = (df['Date'] - first_date).dt.days
            m_global, _ = np.polyfit(df['DaysPassed'], df['Poids'], 1)
            
            recent_cutoff = df['Date'].max() - timedelta(days=30)
            recent_df = df[df['Date'] >= recent_cutoff]
            
            if len(recent_df) > 1:
                r_days = (recent_df['Date'] - recent_df['Date'].min()).dt.days
                m_recent, _ = np.polyfit(r_days, recent_df['Poids'], 1)
            else:
                m_recent = m_global 

            m_hybrid = (m_global * (1 - recent_weight_val)) + (m_recent * recent_weight_val)

            last_date = df['Date'].max()
            last_weight_smooth = df['Poids_Lisse'].iloc[-1]
            last_weight_real = df['Poids'].iloc[-1]
            
            future_dates = [last_date + timedelta(days=x) for x in range(0, forecast_days + 1)]
            prediction_path = [last_weight_smooth + (m_hybrid * x) for x in range(0, forecast_days + 1)]

            # --- GRAPHIQUE ---
            fig = go.Figure()

            # Historique (Ligne rouge fluide)
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['Poids_Lisse'], 
                mode='lines', name='Historique',
                line=dict(color='#ca0201', width=4, shape='spline')
            ))
            
            # Prédiction (Dots espacés tous les 7 jours)
            fig.add_trace(go.Scatter(
                x=future_dates[::7], y=prediction_path[::7],
                mode='markers', name='Prédiction',
                marker=dict(color='#ca0201', size=5, symbol='circle')
            ))

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis=dict(gridcolor='rgba(0,0,0,0.1)', tickfont=dict(color='black')),
                yaxis=dict(gridcolor='rgba(0,0,0,0.1)', tickfont=dict(color='black')),
                hovermode="x unified",
                legend=dict(font=dict(color="black"), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- STATS ---
            st.markdown("### 📊 Statistiques")
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Poids actuel", f"{last_weight_real} kg")
            target_w = prediction_path[-1]
            diff = target_w - last_weight_real
            col_m2.metric(f"Objectif ({forecast_days} j)", f"{target_w:.1f} kg", f"{diff:+.1f} kg")
            weekly_rate = (m_hybrid * 7)
            col_m3.metric("Vitesse actuelle", f"{weekly_rate:+.2f} kg / sem")
    else:
        st.info("💡 J'attends tes données... Copie-les au format 'Date Poids' !")
else:
    st.info("👋 Hello ! Colle tes données de poids ci-dessus pour voir la magie opérer.")

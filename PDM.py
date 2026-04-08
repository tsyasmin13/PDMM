import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="PDM Tracker", layout="wide")
st.title("Suivi et prédiction PDM")
st.header("d")

with st.container(border=True):
    st.markdown("### 💡 Astuce PDM")
    st.write("Pour une prédiction plus précise, essayez de vous peser à heure fixe, idéalement le matin à jeun.")

# --- SIDEBAR ---
st.sidebar.header("Paramètres")

# 1. Slider de prédiction
forecast_days = st.sidebar.slider("Je veux une prédiction de poids sur X jours :", 30, 365, 90)
# Utilisation de colonnes pour mettre le texte aux extrémités
col1, col2 = st.sidebar.columns(2)
col1.caption("30 jours")
col2.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>365 jours</p>", unsafe_allow_html=True)

st.sidebar.write("") # Petit espace

# 2. Slider de pondération
recent_weight = st.sidebar.slider(
    "Je veux que ma prédiction soit basée sur :", 
    min_value=0, 
    max_value=100, 
    value=50) / 100

# Labels aux extrémités pour la pondération
c1, c2 = st.sidebar.columns(2)
c1.caption("Tout l'historique")
c2.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>30 derniers jours</p>", unsafe_allow_html=True)

raw_text = st.text_area("Je colle mes poids avec leur date ici (ex: 01/01/2025 75.5) :", height=200)

if raw_text:
    # Regex pour capturer la date et le poids (accepte point et virgule)
    pattern = r"(\d{1,2}/\d{1,2}/\d{4}).*?(\d{2,3}[.,]?\d?)"
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

        df = pd.DataFrame(data).sort_values("Date")

        if not df.empty and 'Poids' in df.columns:
            # --- 1. CALCUL DES PENTES ---
            first_date = df['Date'].min()
            df['DaysPassed'] = (df['Date'] - first_date).dt.days
            
            # Pente Globale (Regression linéaire sur tout)
            m_global, _ = np.polyfit(df['DaysPassed'], df['Poids'], 1)
            
            # Pente Récente (Regression sur les 30 derniers jours)
            recent_cutoff = df['Date'].max() - timedelta(days=30)
            recent_df = df[df['Date'] > recent_cutoff]
            
            if len(recent_df) > 1:
                r_days = (recent_df['Date'] - recent_df['Date'].min()).dt.days
                m_recent, _ = np.polyfit(r_days, recent_df['Poids'], 1)
            else:
                m_recent = m_global 

            # Mélange hybride
            m_hybrid = (m_global * (1 - recent_weight)) + (m_recent * recent_weight)

            # --- 2. PRÉDICTION ---
            last_date = df['Date'].max()
            last_weight = df['Poids'].iloc[-1]
            future_dates = [last_date + timedelta(days=x) for x in range(0, forecast_days + 1)]
            prediction_path = [last_weight + (m_hybrid * x) for x in range(0, forecast_days + 1)]

            # --- 3. GRAPHIQUE ---
            fig = go.Figure()

            # Historique en BLEU
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['Poids'], 
                mode='lines+markers', name='Historique',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=3, opacity=0.6)
            ))
            
            # Prédiction en VERT
            fig.add_trace(go.Scatter(
                x=future_dates, y=prediction_path, 
                mode='lines+markers', name='Prédiction',
                line=dict(color='#2ca02c', width=2, dash='dot'),
                marker=dict(size=3, symbol='circle')
            ))

            fig.update_layout(
                template="plotly_dark", 
                title="Évolution du poids",
                xaxis_title="Date",
                yaxis_title="Poids (kg)",
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)

            # --- STATS ---
            st.write("### Statistiques")
            c1, c2 = st.columns(2)
            c1.metric("Poids actuel", f"{last_weight} kg")
            c2.metric(f"Projecté dans ({forecast_days} jours )", 
                      f"{prediction_path[-1]:.1f} kg", 
                      f"{prediction_path[-1]-last_weight:+.1f} kg")
        else:
            st.error("Données invalides. Vérifiez le format (JJ/MM/AAAA Poids).")
    else:
        st.info("Aucune donnée trouvée. Il faut que vos notes au format : JJ/MM/AAAA Poids")
else:
    st.info("Copie tes notes dans la zone de texte pour générer le graphique.")



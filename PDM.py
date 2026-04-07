import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="PDM Tracker", layout="wide")
st.title("Suivi et prédiction PDM")

# --- SIDEBAR ---
st.sidebar.header("Paramètres")
forecast_days = st.sidebar.slider("Prédiction sur X jours", 30, 365, 90)

st.sidebar.write("### Pondération de la prédiction")
recent_weight = st.sidebar.slider(
    "Ajustement de l'influence", 
    min_value=0, 
    max_value=100, 
    value=50) / 100

st.sidebar.caption("⬅️ 0% = Tout l'historique | 100% = 30 derniers jours ➡️")

raw_text = st.text_area("Je colle mes poids avec leur date ici (ex: 01/01/2025 75.5) :", height=200)

if raw_text:
    # Regex améliorée pour accepter points et virgules
    pattern = r"(\d{1,2}/\d{1,2}/\d{4}).*?(\d{2,3}[.,]?\d?)"
    matches = re.findall(pattern, raw_text)

    if matches:
        data = []
        for m_date, m_weight in matches:
            try:
                # Conversion du poids en gérant la virgule française
                val_weight = float(m_weight.replace(',', '.'))
                clean_date = pd.to_datetime(m_date, dayfirst=True)
                data.append({"Date": clean_date, "Poids": val_weight})
            except:
                continue

        df = pd.DataFrame(data).sort_values("Date")

        # Utilisation de 'Poids' partout pour éviter le KeyError
        if not df.empty and 'Poids' in df.columns:
            # --- 1. CALCUL DES PENTES (SLOPES) ---
            first_date = df['Date'].min()
            df['DaysPassed'] = (df['Date'] - first_date).dt.days
            
            # Pente Globale
            m_global, _ = np.polyfit(df['DaysPassed'], df['Poids'], 1)
            
            # Pente Récente (30 derniers jours)
            recent_cutoff = df['Date'].max() - timedelta(days=30)
            recent_df = df[df['Date'] > recent_cutoff]
            
            if len(recent_df) > 1:
                recent_days = (recent_df['Date'] - recent_df['Date'].min()).dt.days
                m_recent, _ = np.polyfit(recent_days, recent_df['Poids'], 1)
            else:
                m_recent = m_global 

            # Calcul Hybride
            m_hybrid = (m_global * (1 - recent_weight)) + (m_recent * recent_weight)

            # --- 2. GÉNÉRATION DE LA PRÉDICTION ---
            last_date = df['Date'].max()
            last_weight = df['Poids'].iloc[-1]
            future_dates = [last_date + timedelta(days=x) for x in range(0, forecast_days + 1)]
            prediction_path = [last_weight + (m_hybrid * x) for x in range(0, forecast_days + 1)]

            # --- 3. GRAPHIQUE ---
            fig = go.Figure()

            # HISTORIQUE : Ligne bleue
            fig.add_trace(go.Scatter(
                x=df['Date'], 
                y=df['Poids'], 
                mode='lines+markers', 
                name='Historique',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=4, opacity=0.6)
            ))
            
            # PRÉDICTION : Points verts
            fig.add_trace(go.Scatter(
                x=future_dates, 
                y=prediction_path, 
                mode='lines+markers', 
                name='Prédiction',
                line=dict(color='#2ca02c', width=3, dash='dot'),
                marker=dict(size=5, symbol='circle')
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
            col1, col2 = st.columns(2)
            col1.metric("Poids actuel", f"{last_weight} kg")
            col2.metric(f"Projecté ({forecast_days} j)", 
                        f"{prediction_path[-1]:.1f} kg", 
                        f"{prediction_path[-1]-last_weight:+.1f} kg")

    else:
        st.info("Aucune donnée détectée. Formats acceptés : JJ/MM/AAAA Poids")
else:
    st.info("Copie tes notes dans la zone de texte pour générer le graphique.")                clean_date = pd.to_datetime(m_date, dayfirst=True)
                data.append({"Date": clean_date, "Poids": float(m_weight)})
            except:
                continue

        df = pd.DataFrame(data).sort_values("Date")

        if not df.empty:
            # --- 1. CALCULATE HYBRID SLOPE ---
            # Global Slope
            first_date = df['Date'].min()
            df['DaysPassed'] = (df['Date'] - first_date).dt.days
            m_global, _ = np.polyfit(df['DaysPassed'], df['Weight'], 1)
            
            # Recent Slope (Last 30 Days)
            recent_df = df[df['Date'] > (df['Date'].max() - timedelta(days=30))]
            if len(recent_df) > 1:
                recent_days = (recent_df['Date'] - recent_df['Date'].min()).dt.days
                m_recent, _ = np.polyfit(recent_days, recent_df['Weight'], 1)
            else:
                m_recent = m_global 

            # Hybrid Calculation
            m_hybrid = (m_global * (1 - recent_weight)) + (m_recent * recent_weight)

            # --- 2. GENERATE FORECAST ---
            last_date = df['Date'].max()
            last_weight = df['Weight'].iloc[-1]
            future_dates = [last_date + timedelta(days=x) for x in range(0, forecast_days + 1)]
            prediction_path = [last_weight + (m_hybrid * x) for x in range(0, forecast_days + 1)]

            # --- 3. PLOTTING ---
            fig = go.Figure()

            # HISTORY: Blue Line Plot
            fig.add_trace(go.Scatter(
                x=df['Date'], 
                y=df['Weight'], 
                mode='lines+markers', 
                name='History',
                line=dict(color='#1f77b4', width=3), # Standard Blue
                marker=dict(size=4, opacity=0.6)
            ))
            
            # PREDICTION: Green Line with Small Dots
            fig.add_trace(go.Scatter(
                x=future_dates, 
                y=prediction_path, 
                mode='lines+markers', 
                name='Prediction',
                line=dict(color='#2ca02c', width=3, dash='dot'), # Green Dotted
                marker=dict(size=5, symbol='circle')
            ))

            fig.update_layout(
                template="plotly_dark", 
                title="Weight Journey",
                xaxis_title="Date",
                yaxis_title="Weight (kg)",
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)

            # --- METRICS ---
            st.write("### Stats")
            col1, col2 = st.columns(2)
            col1.metric("Current weight", f"{last_weight} kg")
            col2.metric(f"Projected ({forecast_days} days)", f"{prediction_path[-1]:.1f} kg", f"{prediction_path[-1]-last_weight:+.1f} kg")

    else:
        st.info("Paste your data to see the graph!")

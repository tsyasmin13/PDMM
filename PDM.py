import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from datetime import datetime, timedelta
import numpy as np

# Configuration de la page
st.set_page_config(page_title="PDM Tracker", layout="wide", page_icon="📈")

# Style CSS pour un look pro et moderne
st.markdown("""
    <style>
    .stMetric { background-color: rgba(28, 131, 225, 0.1); padding: 15px; border-radius: 10px; border: 1px solid rgba(28, 131, 225, 0.2); }
    [data-testid="stMetricValue"] { color: #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Suivi et prédiction PDM")

# --- MESSAGE PERSONNEL ---
with st.container(border=True):
    st.subheader("Coucou mon amoureux ❤️")
    st.write("Comme promis, je t'ai codé un site qui te permet de voir ta progression. C'est super simple à utiliser et tu n'auras pas de difficultés vu que tu es super intelligent, super beau, super musclé, super drôle.")
    st.write("Si tu as des questions, envoie-moi un snap, j'essayerai de te répondre sous 3 à 5 jours ouvrés.")
    st.markdown("*Gros kiss,* \n**Ton amoureuse (aka petit bébé) (aka yasmin)**")

# --- SIDEBAR (PARAMÈTRES) ---
st.sidebar.header("⚙️ Paramètres")

# 1. Slider de prédiction
st.sidebar.subheader("Horizon de prédiction")
forecast_days = st.sidebar.slider("Nombre de jours à prédire :", 30, 365, 90)
col_a, col_b = st.sidebar.columns(2)
col_a.caption("30 jours")
col_b.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>365 jours</p>", unsafe_allow_html=True)

st.sidebar.divider()

# 2. Slider de pondération
st.sidebar.subheader("Méthode de calcul")
st.sidebar.write("Influence sur la prédiction :")
recent_weight = st.sidebar.slider(
    "Pondération", 
    min_value=0, 
    max_value=100, 
    value=50,
    label_visibility="collapsed") / 100

c1, c2 = st.sidebar.columns(2)
c1.caption("Global (Stable)")
c2.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>Récent (Dynamique)</p>", unsafe_allow_html=True)

# --- ZONE DE SAISIE ---
st.write("")
st.markdown("### 📝 Saisie des données")
st.markdown("**Ici tu colles directement ta note avec tes poids et leurs dates :**")

raw_text = st.text_area(
    "Zone de saisie", 
    placeholder="Exemple :\n01/01/2026 75.5\n05/01/2026 75.8\n10/01/2026 76.2", 
    height=200, 
    label_visibility="collapsed"
)

if raw_text:
    # Regex : JJ/MM/AAAA + Poids (accepte point et virgule)
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
            
            # --- OPTIMISATION FLUIDITÉ (Lissage EWMA) ---
            # 'span=7' lisse les variations sur environ une semaine
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
            m_hybrid = (m_global * (1 - recent_weight)) + (m_recent * recent_weight)

            # --- PRÉDICTION ---
            last_date = df['Date'].max()
            # On part du dernier point LISSÉ pour une prédiction plus propre
            last_weight_smooth = df['Poids_Lisse'].iloc[-1]
            last_weight_real = df['Poids'].iloc[-1]
            
            future_dates = [last_date + timedelta(days=x) for x in range(0, forecast_days + 1)]
            prediction_path = [last_weight_smooth + (m_hybrid * x) for x in range(0, forecast_days + 1)]

            # --- GRAPHIQUE ---
            fig = go.Figure()

            # 1. Vrais poids (Points discrets en arrière-plan)
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['Poids'], 
                mode='markers', name='Poids réels',
                marker=dict(size=5, color='rgba(255, 255, 255, 0.3)')
            ))

            # 2. Tendance lissée (Ligne bleue fluide)
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['Poids_Lisse'], 
                mode='lines', name='Tendance fluide',
                line=dict(color='#1f77b4', width=4, shape='spline') # Spline = Courbes
            ))
            
            # 3. Prédiction (Ligne verte pointillée)
            fig.add_trace(go.Scatter(
                x=future_dates, y=prediction_path, 
                mode='lines+markers', name='Projection',
                line=dict(color='#2ca02c', width=2, dash='dot'),
                marker=dict(size=4, symbol='circle-open')
            ))

            fig.update_layout(
                template="plotly_dark", 
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Temps",
                yaxis_title="Poids (kg)",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)

            # --- STATS ---
            st.markdown("### 📊 Statistiques")
            col_m1, col_m2, col_m3 = st.columns(3)
            
            col_m1.metric("Dernier poids réel", f"{last_weight_real} kg")
            
            target_w = prediction_path[-1]
            diff = target_w - last_weight_real
            col_m2.metric(f"Objectif ({forecast_days} j)", f"{target_w:.1f} kg", f"{diff:+.1f} kg")
            
            weekly_rate = (m_hybrid * 7)
            col_m3.metric("Vitesse actuelle", f"{weekly_rate:+.2f} kg / sem")
            
        else:
            st.error("Oups ! Je n'arrive pas à lire les poids. Vérifie bien le format.")
    else:
        st.info("💡 J'attends tes données... Copie-les au format 'Date Poids' !")
else:
    st.info("👋 Hello ! Colle tes données de poids ci-dessus pour voir la magie opérer.")c1, c2 = st.sidebar.columns(2)
c1.caption("Tout l'historique")
c2.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>30 derniers jours</p>", unsafe_allow_html=True)

st.markdown("**Ici tu colles directement ta note avec tes poids avec leur date :**")

# On crée la zone de texte avec un label caché (label_visibility="collapsed")
raw_text = st.text_area(
    "Label invisible", 
    placeholder="ex: 01/01/2025 75.5", 
    height=200, 
    label_visibility="collapsed"
)
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



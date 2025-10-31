"""
Dashboard Streamlit avec Copy Trading pour suivre et copier 25usdc
Lance avec: streamlit run dashboard/app_copy_trading.py
Version API - Se connecte au backend Railway
"""

import streamlit as st
import pandas as pd
import sys
import time
from pathlib import Path
from datetime import datetime

# Import API Client
sys.path.append(str(Path(__file__).parent))
from api_client import get_api_client

# Configuration de la page
st.set_page_config(
    page_title="Polymarket Copy Trading",
    page_icon="📊",
    layout="wide"
)

# CSS personnalisé pour un design moderne avec thème sombre
st.markdown("""
<style>
    .stDataFrame {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    h1 {
        color: #667eea;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #2b2b2b;
        border-radius: 10px 10px 0 0;
        padding-left: 20px;
        padding-right: 20px;
        color: #b0b0b0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #404040;
        color: #e0e0e0;
    }
    /* Compacter les métriques dans la sidebar */
    [data-testid="stMetricValue"] {
        font-size: 20px;
    }
    [data-testid="stMetricLabel"] {
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Initialiser le session state pour l'auto-refresh
if 'last_refresh_time' not in st.session_state:
    st.session_state.last_refresh_time = time.time()

if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 60  # 1 minute par défaut

if 'api_client' not in st.session_state:
    st.session_state.api_client = None

# Pas de titre principal pour gagner de l'espace

# Créer le client API (avec authentification)
if st.session_state.api_client is None:
    with st.spinner("🔐 Connexion à l'API Railway..."):
        st.session_state.api_client = get_api_client()

api_client = st.session_state.api_client

# Chargement des données depuis l'API
with st.spinner("📡 Chargement des données depuis l'API..."):
    df = api_client.get_latest_positions()

if df is None or df.empty:
    st.error("⚠️ Impossible de charger les données depuis l'API Railway")
    st.stop()

st.sidebar.success(f"✅ Connecté à l'API Railway")
st.sidebar.info(f"📊 {len(df)} positions chargées")

# Vérifier que les deux traders sont présents
if '25usdc' not in df['user'].values:
    st.error("⚠️ 25usdc n'est pas dans les données. Vérifie config/traders.json")
    st.stop()

if 'Shunky' not in df['user'].values:
    st.error("⚠️ Shunky n'est pas dans les données. Vérifie config/traders.json")
    st.stop()

# Séparer les données
df_25usdc = df[df['user'] == '25usdc'].copy()
df_shunky = df[df['user'] == 'Shunky'].copy()

# Créer les onglets
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Copy Trading",
    "📊 Portfolio 25usdc",
    "💼 Mon Portfolio (Shunky)",
    "📈 Analyse Globale"
])

# ========== SIDEBAR: Configuration et métriques compactes ==========
with st.sidebar:
    st.markdown("### ⚙️ Config")
    copy_percentage = st.slider(
        "% Copy Trading",
        min_value=1,
        max_value=100,
        value=10,
        step=1,
        help="Pourcentage du portefeuille de 25usdc à copier"
    )

    # Auto-refresh configuration
    st.markdown("---")
    st.markdown("### 🔄 Auto-Refresh")

    refresh_options = {
        "1 minute": 60,
        "2 minutes": 120,
        "5 minutes": 300,
        "10 minutes": 600
    }

    selected_interval = st.selectbox(
        "Intervalle",
        options=list(refresh_options.keys()),
        index=0,
        help="Fréquence de mise à jour des données"
    )

    st.session_state.refresh_interval = refresh_options[selected_interval]

    # Calculer le temps restant
    elapsed = time.time() - st.session_state.last_refresh_time
    time_left = max(0, st.session_state.refresh_interval - elapsed)

    # Afficher le compte à rebours
    if time_left > 0:
        minutes = int(time_left // 60)
        seconds = int(time_left % 60)
        st.info(f"⏱️ Prochain refresh: {minutes}m {seconds}s")
    else:
        st.warning("🔄 Refresh en cours...")

    # Bouton pour forcer le refresh
    if st.button("🔄 Forcer le refresh", use_container_width=True):
        with st.spinner("🔄 Demande de refresh à l'API Railway..."):
            try:
                success = api_client.trigger_refresh()
                if success:
                    st.session_state.last_refresh_time = time.time()
                    st.success("✅ Refresh lancé sur Railway! Les données seront mises à jour dans quelques secondes.")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Échec du refresh API")
            except Exception as e:
                st.error(f"❌ Erreur: {str(e)}")

    # Auto-refresh si le temps est écoulé
    if time_left <= 0:
        st.session_state.last_refresh_time = time.time()
        st.info("🔄 Temps écoulé - Rechargement des données...")
        time.sleep(1)
        st.rerun()

    # Calculer les exposures (montant investi)
    exposure_25usdc = (df_25usdc['size'] * df_25usdc['avg_price']).sum()
    exposure_shunky = (df_shunky['size'] * df_shunky['avg_price']).sum()

    diff_positions = len(df_25usdc) - len(df_shunky)
    diff_exposure = exposure_25usdc - exposure_shunky
    diff_pnl = df_25usdc['pnl'].sum() - df_shunky['pnl'].sum()

    st.markdown("---")

    # Format compact: tout en une seule table
    st.markdown("### 📊 Métriques")

    metrics_data = f"""
| | 25usdc | Shunky | Δ |
|---|---:|---:|---:|
| **Pos** | {len(df_25usdc)} | {len(df_shunky)} | {diff_positions:+} |
| **Exp** | ${exposure_25usdc:,.0f} | ${exposure_shunky:,.0f} | ${diff_exposure:+,.0f} |
| **PnL** | ${df_25usdc['pnl'].sum():,.0f} | ${df_shunky['pnl'].sum():,.0f} | ${diff_pnl:+,.0f} |
"""
    st.markdown(metrics_data)

# ========== ONGLET 1: COPY TRADING ==========
with tab1:
    # Merger les deux dataframes pour comparer
    comparison = df_25usdc[['market', 'side', 'size', 'avg_price', 'current_price', 'pnl']].merge(
        df_shunky[['market', 'side', 'size', 'avg_price', 'current_price', 'pnl']],
        on=['market', 'side'],
        how='outer',
        suffixes=('_25usdc', '_shunky')
    )

    # Remplir les NaN avec 0
    comparison['size_25usdc'] = comparison['size_25usdc'].fillna(0)
    comparison['size_shunky'] = comparison['size_shunky'].fillna(0)
    comparison['avg_price_25usdc'] = comparison['avg_price_25usdc'].fillna(0)
    comparison['avg_price_shunky'] = comparison['avg_price_shunky'].fillna(0)
    comparison['current_price_25usdc'] = comparison['current_price_25usdc'].fillna(0)
    comparison['pnl_25usdc'] = comparison['pnl_25usdc'].fillna(0)
    comparison['pnl_shunky'] = comparison['pnl_shunky'].fillna(0)

    # Appliquer le % de copy trading aux targets
    comparison['target_size'] = comparison['size_25usdc'] * (copy_percentage / 100)
    comparison['target_avg_price'] = comparison['avg_price_25usdc']

    # Calculer les montants investis
    comparison['invested_target'] = comparison['target_size'] * comparison['target_avg_price']
    comparison['invested_shunky'] = comparison['size_shunky'] * comparison['avg_price_shunky']

    # Calculer les différences en shares et en $
    comparison['delta_shares'] = comparison['target_size'] - comparison['size_shunky']
    comparison['delta_invested'] = comparison['invested_target'] - comparison['invested_shunky']

    comparison['action'] = comparison['delta_shares'].apply(
        lambda x: '🟢 ACHETER' if x > 0 else ('🔴 VENDRE' if x < 0 else '✅ OK')
    )

    # Filtrer uniquement les actions nécessaires
    actions_needed = comparison[comparison['delta_shares'].abs() > 0.01].copy()  # Seuil minimal pour éviter les micro-ajustements
    actions_needed = actions_needed.sort_values('delta_shares', key=lambda x: x.abs(), ascending=False)

    st.subheader(f"🎯 Actions à effectuer ({len(actions_needed)} positions)")

    # Statistiques des actions
    col1, col2, col3 = st.columns(3)
    with col1:
        to_buy = len(actions_needed[actions_needed['delta_shares'] > 0])
        st.metric("🟢 À acheter", to_buy)
    with col2:
        to_sell = len(actions_needed[actions_needed['delta_shares'] < 0])
        st.metric("🔴 À vendre", to_sell)
    with col3:
        total_investment = actions_needed['delta_invested'].abs().sum()
        st.metric("💰 Investissement requis", f"${total_investment:,.0f}")

    # Table des actions - DESIGN MODERNE
    if not actions_needed.empty:
        # Préparer le dataframe pour l'affichage
        actions_display = pd.DataFrame({
            'Marché': actions_needed['market'].str[:50],  # Limiter la longueur
            'Côté': actions_needed['side'],
            'Action': actions_needed['action'],
            'Δ Shares': actions_needed['delta_shares'].apply(lambda x: f"{x:+,.0f}"),
            'Montant $': actions_needed['delta_invested'].apply(lambda x: f"${x:+,.2f}"),
            'Prix Moy 25usdc': actions_needed['avg_price_25usdc'].apply(lambda x: f"{x:.3f}"),
            'Prix Moy Shunky': actions_needed['avg_price_shunky'].apply(lambda x: f"{x:.3f}" if x > 0 else "-"),
            'Target Shares': actions_needed['target_size'].apply(lambda x: f"{x:,.0f}"),
            'Actuel Shares': actions_needed['size_shunky'].apply(lambda x: f"{x:,.0f}")
        })

        # Style le dataframe avec des couleurs sombres
        def highlight_action(row):
            if '🟢' in row['Action']:
                return ['background-color: #1a3d2e; color: #b0b0b0'] * len(row)  # Vert sombre + texte gris clair
            elif '🔴' in row['Action']:
                return ['background-color: #3d1a1a; color: #b0b0b0'] * len(row)  # Rouge sombre + texte gris clair
            else:
                return ['color: #b0b0b0'] * len(row)  # Texte gris clair par défaut

        # Afficher le tableau avec style - PLEIN ÉCRAN
        st.dataframe(
            actions_display.style.apply(highlight_action, axis=1),
            use_container_width=True,
            height=800  # Hauteur fixe grande pour voir tout le tableau
        )

        # Export CSV
        csv = actions_needed.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger les actions (CSV)",
            data=csv,
            file_name=f"copy_trading_actions_{copy_percentage}pct.csv",
            mime="text/csv"
        )
    else:
        st.success(f"✅ Ton portefeuille est parfaitement aligné avec {copy_percentage}% de 25usdc !")

# ========== ONGLET 2: PORTFOLIO 25USDC ==========
with tab2:
    st.header("📊 Portfolio de 25usdc")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Positions", len(df_25usdc))
    with col2:
        exposure_25 = (df_25usdc['size'] * df_25usdc['avg_price']).sum()
        st.metric("Exposure (investi)", f"${exposure_25:,.0f}")
    with col3:
        pnl_25 = df_25usdc['pnl'].sum()
        st.metric("PnL", f"${pnl_25:,.0f}", delta=f"{pnl_25:+.0f}")
    with col4:
        st.metric("Markets", df_25usdc['market'].nunique())

    st.markdown("---")

    # Table des positions
    display_25 = df_25usdc[['market', 'side', 'size', 'avg_price', 'current_price', 'pnl']].copy()
    display_25['size'] = display_25['size'].apply(lambda x: f"{x:,.2f}")
    display_25['avg_price'] = display_25['avg_price'].apply(lambda x: f"{x:.3f}")
    display_25['current_price'] = display_25['current_price'].apply(lambda x: f"{x:.3f}")
    display_25['pnl'] = display_25['pnl'].apply(lambda x: f"${x:+,.2f}")
    display_25.columns = ['Market', 'Side', 'Size (shares)', 'Avg Price', 'Current Price', 'PnL']

    st.dataframe(display_25, use_container_width=True, height=600)

    # Top 10 positions
    st.subheader("🏆 Top 10 positions par taille")
    top_10 = df_25usdc.nlargest(10, 'size')
    st.bar_chart(top_10.set_index('market')['size'])

# ========== ONGLET 3: MON PORTFOLIO ==========
with tab3:
    st.header("💼 Mon Portfolio (Shunky)")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Positions", len(df_shunky))
    with col2:
        exposure_shk = (df_shunky['size'] * df_shunky['avg_price']).sum()
        st.metric("Exposure (investi)", f"${exposure_shk:,.0f}")
    with col3:
        pnl_shunky = df_shunky['pnl'].sum()
        st.metric("PnL", f"${pnl_shunky:,.0f}", delta=f"{pnl_shunky:+.0f}")
    with col4:
        st.metric("Markets", df_shunky['market'].nunique())

    st.markdown("---")

    # Table des positions
    display_shunky = df_shunky[['market', 'side', 'size', 'avg_price', 'current_price', 'pnl']].copy()
    display_shunky['size'] = display_shunky['size'].apply(lambda x: f"{x:,.2f}")
    display_shunky['avg_price'] = display_shunky['avg_price'].apply(lambda x: f"{x:.3f}")
    display_shunky['current_price'] = display_shunky['current_price'].apply(lambda x: f"{x:.3f}")
    display_shunky['pnl'] = display_shunky['pnl'].apply(lambda x: f"${x:+,.2f}")
    display_shunky.columns = ['Market', 'Side', 'Size (shares)', 'Avg Price', 'Current Price', 'PnL']

    st.dataframe(display_shunky, use_container_width=True, height=600)

    # Top positions
    st.subheader("🏆 Top positions par taille")
    if len(df_shunky) > 0:
        top_shunky = df_shunky.nlargest(min(10, len(df_shunky)), 'size')
        st.bar_chart(top_shunky.set_index('market')['size'])

# ========== ONGLET 4: ANALYSE GLOBALE ==========
with tab4:
    st.header("📈 Analyse Globale")

    # Vue d'ensemble des deux portefeuilles
    st.subheader("Comparaison des expositions (montant investi)")

    exposure_25_total = (df_25usdc['size'] * df_25usdc['avg_price']).sum()
    exposure_shunky_total = (df_shunky['size'] * df_shunky['avg_price']).sum()

    comparison_data = pd.DataFrame({
        '25usdc': [exposure_25_total],
        'Shunky': [exposure_shunky_total]
    })
    st.bar_chart(comparison_data.T)

    # PnL comparison
    st.subheader("Comparaison des PnL")
    pnl_data = pd.DataFrame({
        '25usdc': [df_25usdc['pnl'].sum()],
        'Shunky': [df_shunky['pnl'].sum()]
    })
    st.bar_chart(pnl_data.T)

    # Marchés communs
    st.subheader("🔥 Marchés communs")

    common_markets = set(df_25usdc['market']) & set(df_shunky['market'])
    st.metric("Marchés en commun", len(common_markets))

    if common_markets:
        st.write("Liste des marchés communs:")
        for market in sorted(common_markets):
            st.write(f"- {market}")

# Footer
st.markdown("---")
st.caption(f"🚀 Polymarket Copy Trading Dashboard | Copy à {copy_percentage}% | Mise à jour automatique")

# Forcer le rerun toutes les 5 secondes pour mettre à jour le timer
time.sleep(5)
st.rerun()

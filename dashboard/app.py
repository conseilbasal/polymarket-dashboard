"""
Dashboard Streamlit pour le suivi des positions des top traders Polymarket
Lance avec: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Ajouter le dossier parent au path pour importer utils
sys.path.append(str(Path(__file__).parent.parent / "scripts"))
from utils import get_latest_snapshot, get_trader_history

# Configuration de la page
st.set_page_config(
    page_title="Polymarket Pro Tracker",
    page_icon="📊",
    layout="wide"
)

# Chemins
BASE_DIR = Path(__file__).parent.parent
SNAPSHOTS_DIR = BASE_DIR / "data" / "snapshots"
ALERTS_PATH = BASE_DIR / "data" / "alerts.csv"

# Titre principal
st.title("📊 Polymarket Smart Tracker – Top Traders")
st.markdown("---")

# Vérifier si des données existent
snapshots = sorted(SNAPSHOTS_DIR.glob("positions_*.csv"))
if not snapshots:
    st.error("⚠️ Aucun snapshot trouvé. Lance `python scripts/fetch_positions.py` pour collecter les données.")
    st.stop()

# Chargement du dernier snapshot
df = pd.read_csv(snapshots[-1])
last_update = snapshots[-1].stem.split('_', 1)[1]
st.sidebar.success(f"✅ Last update: {last_update}")
st.sidebar.info(f"📦 {len(snapshots)} total snapshots")

# Sidebar: Filtres
st.sidebar.markdown("## 🎯 Filtres")
traders_list = ["All"] + sorted(df['user'].unique().tolist())
selected_trader = st.sidebar.selectbox("Trader", traders_list)

# Filtrage des données
if selected_trader != "All":
    df_filtered = df[df['user'] == selected_trader]
else:
    df_filtered = df

# Section 1: Vue d'ensemble
st.header("📈 Vue d'ensemble")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Positions", len(df_filtered))
with col2:
    st.metric("Total Exposure", f"${df_filtered['size'].sum():,.0f}")
with col3:
    total_pnl = df_filtered['pnl'].sum()
    st.metric("Total PnL", f"${total_pnl:,.0f}",
              delta=f"{total_pnl:+.0f}" if total_pnl != 0 else None)
with col4:
    st.metric("Unique Markets", df_filtered['market'].nunique())

st.markdown("---")

# Section 2: Positions détaillées par trader
st.header(f"💼 Positions: {selected_trader}")

if not df_filtered.empty:
    # Préparer les données pour l'affichage
    display_df = df_filtered[[
        "user", "market", "side", "size", "avg_price",
        "current_price", "pnl"
    ]].copy()

    # Formater les colonnes numériques
    display_df["size"] = display_df["size"].apply(lambda x: f"${x:,.2f}")
    display_df["avg_price"] = display_df["avg_price"].apply(lambda x: f"{x:.3f}")
    display_df["current_price"] = display_df["current_price"].apply(lambda x: f"{x:.3f}")
    display_df["pnl"] = display_df["pnl"].apply(lambda x: f"${x:+,.2f}")

    # Renommer les colonnes
    display_df.columns = ["Trader", "Market", "Side", "Size", "Avg Price", "Current Price", "PnL"]

    st.dataframe(display_df, use_container_width=True, height=400)
else:
    st.info("Aucune position pour ce filtre.")

st.markdown("---")

# Section 3: Expositions par trader
st.header("🎯 Expositions totales par trader")

exposure_by_trader = df.groupby('user')['size'].sum().sort_values(ascending=False)
st.bar_chart(exposure_by_trader)

# Section 4: PnL par trader
st.header("💰 PnL par trader")

pnl_by_trader = df.groupby('user')['pnl'].sum().sort_values(ascending=False)
colors = ['green' if x > 0 else 'red' for x in pnl_by_trader.values]

col1, col2 = st.columns([2, 1])
with col1:
    st.bar_chart(pnl_by_trader)
with col2:
    st.dataframe(
        pnl_by_trader.reset_index().rename(columns={'user': 'Trader', 'pnl': 'PnL'}),
        use_container_width=True
    )

st.markdown("---")

# Section 5: Heatmap marchés communs
st.header("🔥 Heatmap: Marchés communs")

heatmap_data = pd.crosstab(df['market'], df['user'], values=df['size'], aggfunc='sum').fillna(0)
st.dataframe(heatmap_data.style.background_gradient(cmap='YlOrRd'), use_container_width=True)

st.markdown("---")

# Section 6: Alertes récentes
st.header("🚨 Alertes récentes")

if ALERTS_PATH.exists():
    alerts_df = pd.read_csv(ALERTS_PATH)

    if not alerts_df.empty:
        # Filtrer par trader si sélectionné
        if selected_trader != "All":
            alerts_df = alerts_df[alerts_df['user'] == selected_trader]

        # Afficher les alertes par catégorie
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            new_entries = alerts_df[alerts_df['action'] == 'new_entry']
            st.metric("🆕 New Entries", len(new_entries))

        with col2:
            closed = alerts_df[alerts_df['action'] == 'closed']
            st.metric("🔒 Closed", len(closed))

        with col3:
            adds = alerts_df[alerts_df['action'] == 'add']
            st.metric("📈 Increased", len(adds))

        with col4:
            reduces = alerts_df[alerts_df['action'] == 'reduce']
            st.metric("📉 Reduced", len(reduces))

        # Tableau des alertes
        st.subheader("Détails des alertes")

        # Trier par delta absolu
        alerts_display = alerts_df.sort_values('abs_delta_size', ascending=False) if 'abs_delta_size' in alerts_df.columns else alerts_df

        # Sélection des colonnes à afficher
        alert_cols = ['user', 'market', 'action', 'delta_size', 'size', 'size_prev', 'pnl', 'delta_pnl']
        available_cols = [col for col in alert_cols if col in alerts_display.columns]

        st.dataframe(
            alerts_display[available_cols],
            use_container_width=True,
            height=300
        )
    else:
        st.info("Aucune alerte détectée dans la dernière analyse.")
else:
    st.info("⚠️ Fichier alerts.csv non trouvé. Lance `python scripts/detect_changes.py` pour générer des alertes.")

st.markdown("---")

# Section 6.5: Evolution des positions 24h
st.header("📈 Évolution des positions sur les dernières 24h")

CHANGES_24H_PATH = BASE_DIR / "data" / "changes_24h.csv"

if CHANGES_24H_PATH.exists():
    changes_df = pd.read_csv(CHANGES_24H_PATH)

    if not changes_df.empty:
        # Filtrer par trader si sélectionné
        if selected_trader != "All":
            changes_filtered = changes_df[changes_df['user'] == selected_trader]
        else:
            changes_filtered = changes_df

        # Métriques globales
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_increases = len(changes_filtered[changes_filtered['change_type'] == 'increase'])
            st.metric("📈 Augmentations", total_increases)

        with col2:
            total_decreases = len(changes_filtered[changes_filtered['change_type'] == 'decrease'])
            st.metric("📉 Réductions", total_decreases)

        with col3:
            total_new = len(changes_filtered[changes_filtered['change_type'] == 'new'])
            st.metric("🆕 Nouvelles", total_new)

        with col4:
            total_closed = len(changes_filtered[changes_filtered['change_type'] == 'closed'])
            st.metric("🔒 Fermées", total_closed)

        # Sélecteur de trader pour le graphique
        st.subheader("Variations par trader")

        available_traders = ["Tous"] + sorted(changes_df['user'].unique().tolist())
        chart_trader = st.selectbox("Trader à afficher :", available_traders, key="chart_trader")

        if chart_trader != "Tous":
            chart_data = changes_df[changes_df['user'] == chart_trader].copy()
        else:
            chart_data = changes_df.copy()

        # Préparer les données pour le graphique
        if not chart_data.empty:
            # Top 10 changements (positifs et négatifs)
            top_changes = chart_data.nlargest(10, 'abs_delta_size')

            # Créer un label combiné pour l'axe
            top_changes['label'] = top_changes['user'] + ': ' + top_changes['market'].str[:30]

            # Graphique en barres
            st.bar_chart(top_changes.set_index('label')['delta_size'])

            # Table détaillée
            st.subheader("Détails des changements")

            # Formatage de la table
            display_cols = ['user', 'market', 'change_type', 'delta_size', 'pct_change', 'size_prev', 'size']
            available_display_cols = [col for col in display_cols if col in chart_data.columns]

            # Formater les valeurs numériques pour l'affichage
            chart_data_display = chart_data[available_display_cols].copy()
            chart_data_display['delta_size'] = chart_data_display['delta_size'].apply(lambda x: f"${x:+,.2f}")
            chart_data_display['pct_change'] = chart_data_display['pct_change'].apply(lambda x: f"{x:+.1f}%")
            chart_data_display['size_prev'] = chart_data_display['size_prev'].apply(lambda x: f"${x:,.2f}")
            chart_data_display['size'] = chart_data_display['size'].apply(lambda x: f"${x:,.2f}")

            # Renommer les colonnes pour l'affichage
            chart_data_display.columns = ['Trader', 'Marché', 'Type', 'Δ Size', '% Change', 'Size (avant)', 'Size (après)']

            st.dataframe(chart_data_display, use_container_width=True, height=400)
        else:
            st.info("Aucune donnée pour ce trader.")
    else:
        st.info("Aucun changement détecté sur les dernières 24h.")
else:
    st.warning("⚠️ Fichier changes_24h.csv non trouvé. Lance `python scripts/analyze_last_24h.py` pour générer l'analyse 24h.")

st.markdown("---")

# Section 7: Top markets
st.header("🏆 Top Markets (par exposition)")

top_markets = df.groupby('market')['size'].sum().sort_values(ascending=False).head(10)
st.bar_chart(top_markets)

# Footer
st.markdown("---")
st.caption("🚀 Polymarket Pro Tracker | Mise à jour automatique via scripts Python")

"""
Dashboard pour visualiser l'activité du BOT COPY TRADING AUTOMATIQUE
Affiche ce que le bot a réellement copié, pas la comparaison théorique
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# Configuration
st.set_page_config(
    page_title="Bot Copy Trading - Activité Automatique",
    page_icon="🤖",
    layout="wide"
)

# Style
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .pending-order {
        background-color: #2b2b2b;
        border-left: 4px solid #f59e0b;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    .executed-trade {
        background-color: #1a3d2e;
        border-left: 4px solid #10b981;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    .accumulation {
        background-color: #3d1a1a;
        border-left: 4px solid #ef4444;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_URL = "https://web-production-62f43.up.railway.app"
PASSWORD = "@@@TestApp@@@"

# Login function
@st.cache_data(ttl=3600)
def get_token():
    response = requests.post(
        f"{API_URL}/api/auth/login",
        json={"password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

# Get copy trading status
def get_copy_trading_status(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_URL}/api/copy-trading/status",
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    return None

# Get copy trading history
def get_copy_trading_history(token, days=7):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_URL}/api/copy-trading/history",
        params={"days": days},
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    return None

# Main app
st.title("🤖 Bot Copy Trading - Activité Automatique")
st.markdown("Visualisation en temps réel de ce que le bot a automatiquement copié depuis 25usdc")

# Login
token = get_token()
if not token:
    st.error("❌ Échec de connexion à l'API")
    st.stop()

st.sidebar.success("✅ Connecté à Railway")

# Refresh button
if st.sidebar.button("🔄 Rafraîchir les données"):
    st.cache_data.clear()
    st.rerun()

# Get data
status = get_copy_trading_status(token)

if not status:
    st.error("❌ Impossible de récupérer le statut du copy trading")
    st.stop()

# Extract data
active_configs = status.get("active_configs", [])
pending_orders = status.get("pending_orders", [])
total_pnl = status.get("total_pnl", 0)

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Vue d'ensemble",
    "⏳ Ordres en attente",
    "✅ Trades exécutés",
    "💰 Accumulations"
])

# TAB 1: VUE D'ENSEMBLE
with tab1:
    st.header("📊 Statut du Bot Copy Trading")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🎯 Configurations actives",
            len(active_configs),
            help="Nombre de traders actuellement copiés"
        )

    with col2:
        st.metric(
            "⏳ Ordres en attente",
            len(pending_orders),
            help="Ordres placés mais pas encore exécutés"
        )

    with col3:
        st.metric(
            "💰 PnL Total",
            f"${total_pnl:.2f}",
            delta=f"{total_pnl:+.2f}",
            help="Profit/Perte cumulé du copy trading"
        )

    with col4:
        # Calculate total exposure from pending orders
        total_exposure = sum([o.get("size", 0) * o.get("price", 0) for o in pending_orders])
        st.metric(
            "💵 Exposition actuelle",
            f"${total_exposure:.2f}",
            help="Montant total investi dans les ordres en attente"
        )

    st.markdown("---")

    # Active configurations
    st.subheader("🎯 Configurations Actives")

    if active_configs:
        for config in active_configs:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    st.markdown(f"**Trader:** {config.get('target_trader_name', 'N/A')}")
                    st.caption(f"Adresse: {config.get('target_trader_address', 'N/A')[:10]}...")

                with col2:
                    st.markdown(f"**Copy %**")
                    st.markdown(f"<span style='font-size: 24px; color: #667eea;'>{config.get('copy_percentage', 0)}%</span>", unsafe_allow_html=True)

                with col3:
                    enabled = config.get('enabled', False)
                    status_text = "✅ Actif" if enabled else "⏸️ Inactif"
                    st.markdown(f"**Statut**")
                    st.markdown(status_text)

                with col4:
                    created = config.get('created_at', '')
                    if created:
                        created_date = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        st.markdown(f"**Depuis**")
                        st.caption(created_date.strftime("%d/%m/%Y"))

                st.markdown("---")
    else:
        st.info("ℹ️ Aucune configuration active. Activez le copy trading dans les paramètres.")

# TAB 2: ORDRES EN ATTENTE
with tab2:
    st.header("⏳ Ordres en Attente d'Exécution")

    if pending_orders:
        st.info(f"📋 {len(pending_orders)} ordre(s) en attente")

        # Convert to DataFrame
        orders_data = []
        for order in pending_orders:
            orders_data.append({
                "ID": order.get("id"),
                "Marché": order.get("market_id", "N/A")[:50],
                "Côté": order.get("outcome", "N/A"),
                "Side": order.get("side", "N/A"),
                "Size": f"{order.get('size', 0):,.2f}",
                "Prix": f"${order.get('price', 0):.3f}",
                "Valeur": f"${order.get('size', 0) * order.get('price', 0):.2f}",
                "Statut": order.get("status", "N/A"),
                "Créé": datetime.fromisoformat(order.get('created_at', '').replace('Z', '+00:00')).strftime("%d/%m %H:%M") if order.get('created_at') else "N/A"
            })

        df_orders = pd.DataFrame(orders_data)

        st.dataframe(
            df_orders,
            use_container_width=True,
            height=400,
            hide_index=True
        )

        # Details for each order
        st.markdown("### 📝 Détails des Ordres")
        for order in pending_orders:
            with st.expander(f"Ordre #{order.get('id')} - {order.get('market_id', 'N/A')[:40]}..."):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Order ID:** {order.get('order_id', 'N/A')}")
                    st.markdown(f"**Marché:** {order.get('market_id', 'N/A')}")
                    st.markdown(f"**Outcome:** {order.get('outcome', 'N/A')}")
                    st.markdown(f"**Side:** {order.get('side', 'N/A')}")

                with col2:
                    st.markdown(f"**Size:** {order.get('size', 0):,.2f} shares")
                    st.markdown(f"**Prix:** ${order.get('price', 0):.3f}")
                    st.markdown(f"**Valeur totale:** ${order.get('size', 0) * order.get('price', 0):.2f}")
                    st.markdown(f"**Statut:** {order.get('status', 'N/A')}")

                if order.get('error_message'):
                    st.error(f"❌ Erreur: {order.get('error_message')}")
    else:
        st.success("✅ Aucun ordre en attente")
        st.info("Le bot placera automatiquement des ordres quand 25usdc prendra de nouvelles positions")

# TAB 3: TRADES EXÉCUTÉS
with tab3:
    st.header("✅ Historique des Trades Exécutés")

    # Date filter
    days = st.slider("Période (jours)", 1, 30, 7)

    history = get_copy_trading_history(token, days=days)

    if history and history.get("trades"):
        trades = history.get("trades", [])

        st.success(f"✅ {len(trades)} trade(s) exécuté(s) dans les {days} derniers jours")

        # Convert to DataFrame
        trades_data = []
        for trade in trades:
            trades_data.append({
                "Date": datetime.fromisoformat(trade.get('executed_at', '').replace('Z', '+00:00')).strftime("%d/%m %H:%M") if trade.get('executed_at') else "N/A",
                "Marché": trade.get("market_title", "N/A")[:50],
                "Outcome": trade.get("outcome", "N/A"),
                "Side": trade.get("side", "N/A"),
                "Size": f"{trade.get('size', 0):,.2f}",
                "Prix": f"${trade.get('price', 0):.3f}",
                "Valeur": f"${trade.get('size', 0) * trade.get('price', 0):.2f}",
                "Copy %": f"{trade.get('copy_percentage', 0):.1f}%",
                "PnL": f"${trade.get('pnl', 0):+,.2f}" if trade.get('pnl') else "N/A"
            })

        df_trades = pd.DataFrame(trades_data)

        # Highlight profitable trades
        def highlight_pnl(row):
            if 'PnL' in row and row['PnL'] != 'N/A':
                if '+' in row['PnL']:
                    return ['background-color: #1a3d2e'] * len(row)
                elif '-' in row['PnL']:
                    return ['background-color: #3d1a1a'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_trades.style.apply(highlight_pnl, axis=1),
            use_container_width=True,
            height=500,
            hide_index=True
        )

        # Statistics
        st.markdown("### 📊 Statistiques")

        col1, col2, col3, col4 = st.columns(4)

        total_trades = len(trades)
        total_value = sum([t.get('size', 0) * t.get('price', 0) for t in trades])
        avg_value = total_value / total_trades if total_trades > 0 else 0
        profitable_trades = len([t for t in trades if t.get('pnl', 0) > 0])

        with col1:
            st.metric("Total Trades", total_trades)

        with col2:
            st.metric("Volume Total", f"${total_value:,.2f}")

        with col3:
            st.metric("Valeur Moyenne", f"${avg_value:,.2f}")

        with col4:
            win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
            st.metric("Win Rate", f"{win_rate:.1f}%")
    else:
        st.info(f"ℹ️ Aucun trade exécuté dans les {days} derniers jours")
        st.markdown("Le bot exécutera automatiquement des trades quand il détectera de nouvelles positions de 25usdc")

# TAB 4: ACCUMULATIONS
with tab4:
    st.header("💰 Positions en Accumulation")

    st.info("🔄 Positions trop petites en cours de cumul (< $0.50)")

    st.markdown("""
    **Comment ça marche ?**

    Quand une position copiée est trop petite pour être placée immédiatement (< $0.50),
    le bot l'accumule ici jusqu'à atteindre le montant minimum.

    Exemple:
    - Position 1: $0.10 → Accumulé
    - Position 2: $0.15 → Accumulé (Total: $0.25)
    - Position 3: $0.30 → **Ordre placé pour $0.55** ✅
    """)

    # TODO: Fetch from pending_accumulation table
    # For now, show placeholder
    st.markdown("### 📊 Accumulations en cours")
    st.caption("Fonctionnalité en cours de développement - Sera disponible prochainement")

    # Placeholder structure
    st.markdown("""
    Cette section affichera:
    - Marché en accumulation
    - Montant accumulé ($)
    - Shares cumulées
    - Timestamp dernière mise à jour
    - Progression vers le minimum ($0.50)
    """)

# Footer
st.markdown("---")
st.caption(f"🤖 Bot Copy Trading Automatique | Mis à jour: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# Auto-refresh every 30 seconds
import time
time.sleep(30)
st.rerun()

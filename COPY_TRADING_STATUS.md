# 🚀 Copy Trading - État d'Avancement

**Dernière mise à jour**: 31 janvier 2025
**Status**: Phase 2 en cours (Core Engine Complété ✅)

---

## ✅ COMPLÉTÉ (Phase 1 & 2)

### Infrastructure Database
- ✅ **migrations/001_copy_trading_schema.sql** - 4 tables PostgreSQL
- ✅ **run_migration.py** - Script automatisé de migration

### Algorithmes & Clients
- ✅ **smart_pricing.py** (374 lignes) - Algorithme adaptatif de pricing
  - 3 stratégies selon liquidité (tight/normal/wide spread)
  - Ajustement progressif sur 36h
  - Market order automatique après 36h

- ✅ **clob_client.py** (295 lignes) - Wrapper Polymarket CLOB API
  - Création ordres limite & market
  - Tracking, annulation, market data
  - Gestion positions & balance

- ✅ **copy_trading_engine.py** (676 lignes) - Moteur principal COMPLET ✅
  - ✅ Position monitoring (détection changements)
  - ✅ Copy trade execution (calcul proportionnel)
  - ✅ Smart order management (prix progressifs)
  - ✅ Pending orders management
  - ✅ Cancellation logic (Option A)
  - ✅ Partial fill handling (Option A: retry)

### Configuration
- ✅ **requirements.txt** mis à jour:
  - py-clob-client>=0.26.0
  - web3>=7.14.0

- ✅ **Railway Secrets** configurés:
  - POLYMARKET_PRIVATE_KEY ✅
  - POLYMARKET_WALLET_ADDRESS ✅
  - POLYMARKET_BUILDER_API_KEY ✅

### Documentation
- ✅ **COPY_TRADING_README.md** (376 lignes) - Documentation complète
- ✅ **COPY_TRADING_STATUS.md** (ce fichier) - Suivi de progression

---

## 🚧 EN COURS / À FAIRE

### Phase 3: Intégration Backend (30 min)

**À Ajouter dans `api_server.py`:**

```python
# Copy Trading Endpoints (à ajouter)

from copy_trading_engine import copy_trading_engine

@app.post("/api/copy-trading/enable")
async def enable_copy_trading(
    target_trader: str,
    trader_name: str,
    copy_percentage: float,
    current_user = Depends(get_current_user)
):
    """
    Activer copy trading pour un trader

    Args:
        target_trader: Adresse Ethereum du trader (0x...)
        trader_name: Nom friendly (ex: "25usdc")
        copy_percentage: Pourcentage à copier (0.1-100)

    Returns:
        {"status": "enabled", "config": {...}}
    """
    # Validation
    if not (0.1 <= copy_percentage <= 100):
        raise HTTPException(400, "Percentage must be between 0.1 and 100")

    # Insérer dans DB
    with engine.connect() as conn:
        query = text("""
            INSERT INTO copy_trading_config
            (user_wallet_address, target_trader_address, target_trader_name, copy_percentage, enabled)
            VALUES (:user_wallet, :target_trader, :trader_name, :percentage, true)
            ON CONFLICT (user_wallet_address, target_trader_address)
            DO UPDATE SET
                copy_percentage = :percentage,
                enabled = true,
                updated_at = NOW()
            RETURNING *
        """)

        result = conn.execute(query, {
            "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS"),
            "target_trader": target_trader,
            "trader_name": trader_name,
            "percentage": copy_percentage
        })

        conn.commit()
        config = dict(result.fetchone()._mapping)

    return {"status": "enabled", "config": config}


@app.post("/api/copy-trading/disable")
async def disable_copy_trading(
    target_trader: str,
    current_user = Depends(get_current_user)
):
    """Désactiver copy trading pour un trader"""

    with engine.connect() as conn:
        # Désactiver dans config
        query = text("""
            UPDATE copy_trading_config
            SET enabled = false, updated_at = NOW()
            WHERE user_wallet_address = :user_wallet
            AND target_trader_address = :target_trader
        """)

        conn.execute(query, {
            "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS"),
            "target_trader": target_trader
        })

        # Annuler tous les ordres en attente
        cancel_query = text("""
            UPDATE pending_copy_orders
            SET status = 'cancelled', last_updated = NOW()
            WHERE user_wallet_address = :user_wallet
            AND target_trader_address = :target_trader
            AND status IN ('pending', 'partial')
        """)

        conn.execute(cancel_query, {
            "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS"),
            "target_trader": target_trader
        })

        conn.commit()

    return {"status": "disabled"}


@app.get("/api/copy-trading/status")
async def get_copy_trading_status(current_user = Depends(get_current_user)):
    """
    Get copy trading status

    Returns:
        {
            "active_configs": [...],
            "pending_orders": [...],
            "total_pnl": float
        }
    """

    with engine.connect() as conn:
        # Active configs
        configs_query = text("""
            SELECT *
            FROM copy_trading_config
            WHERE user_wallet_address = :user_wallet
            AND enabled = true
        """)

        result = conn.execute(configs_query, {
            "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS")
        })

        configs = [dict(row._mapping) for row in result.fetchall()]

        # Pending orders
        orders_query = text("""
            SELECT *
            FROM pending_copy_orders
            WHERE user_wallet_address = :user_wallet
            AND status IN ('pending', 'partial')
            ORDER BY created_at DESC
            LIMIT 100
        """)

        result = conn.execute(orders_query, {
            "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS")
        })

        pending_orders = [dict(row._mapping) for row in result.fetchall()]

        # Total PnL from executed trades
        pnl_query = text("""
            SELECT SUM(profit_loss) as total_pnl
            FROM executed_copy_trades
            WHERE user_wallet_address = :user_wallet
        """)

        result = conn.execute(pnl_query, {
            "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS")
        })

        total_pnl = result.fetchone()[0] or 0.0

    return {
        "active_configs": configs,
        "pending_orders": pending_orders,
        "total_pnl": float(total_pnl)
    }


@app.get("/api/copy-trading/history")
async def get_copy_trading_history(
    days: int = 30,
    current_user = Depends(get_current_user)
):
    """Get copy trading history"""

    with engine.connect() as conn:
        query = text("""
            SELECT *
            FROM executed_copy_trades
            WHERE user_wallet_address = :user_wallet
            AND executed_at >= NOW() - INTERVAL ':days days'
            ORDER BY executed_at DESC
            LIMIT 1000
        """)

        result = conn.execute(query, {
            "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS"),
            "days": days
        })

        trades = [dict(row._mapping) for row in result.fetchall()]

    return {
        "trades": trades,
        "count": len(trades),
        "total_pnl": sum(t.get('profit_loss', 0) or 0 for t in trades)
    }


@app.get("/api/copy-trading/performance")
async def get_copy_trading_performance(current_user = Depends(get_current_user)):
    """Get detailed performance stats"""

    with engine.connect() as conn:
        # Stats par trader
        query = text("""
            SELECT
                target_trader_address,
                target_trader_name,
                COUNT(*) as trade_count,
                SUM(profit_loss) as total_pnl,
                AVG(slippage_percentage) as avg_slippage,
                SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END)::float / COUNT(*)::float as win_rate
            FROM executed_copy_trades
            WHERE user_wallet_address = :user_wallet
            GROUP BY target_trader_address, target_trader_name
        """)

        result = conn.execute(query, {
            "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS")
        })

        stats = [dict(row._mapping) for row in result.fetchall()]

    return {"trader_stats": stats}
```

**À Ajouter dans `scheduler.py`:**

```python
# Ajouter en haut du fichier
from copy_trading_engine import copy_trading_engine

# Dans setup_scheduler(), ajouter ces 2 jobs:

# Job 1: Monitor positions (toutes les 5 min)
scheduler.add_job(
    func=lambda: asyncio.run(copy_trading_engine.monitor_positions()),
    trigger='interval',
    minutes=5,
    id='copy_trading_monitor',
    name='Copy Trading - Position Monitor',
    replace_existing=True
)

# Job 2: Manage pending orders (toutes les 5 min)
scheduler.add_job(
    func=lambda: asyncio.run(copy_trading_engine.manage_pending_orders()),
    trigger='interval',
    minutes=5,
    id='copy_trading_orders',
    name='Copy Trading - Order Manager',
    replace_existing=True
)
```

---

### Phase 4: Frontend React (1h)

**À Créer: `frontend/src/pages/CopyTrading.tsx`**

Structure de la page:

```typescript
import { useState, useEffect } from 'react'
import { apiClient } from '../api/client'

interface CopyConfig {
  id: number
  target_trader_address: string
  target_trader_name: string
  copy_percentage: number
  enabled: boolean
  created_at: string
}

interface PendingOrder {
  id: number
  market_name: string
  order_side: string
  target_size: number
  current_price: number
  target_price: number
  created_at: string
  status: string
}

export default function CopyTradingPage() {
  const [configs, setConfigs] = useState<CopyConfig[]>([])
  const [pendingOrders, setPendingOrders] = useState<PendingOrder[]>([])
  const [totalPnL, setTotalPnL] = useState(0)
  const [loading, setLoading] = useState(true)

  // Sélection nouveau trader
  const [selectedTrader, setSelectedTrader] = useState('')
  const [percentage, setPercentage] = useState(5)

  // Fetch status
  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const fetchStatus = async () => {
    try {
      const response = await apiClient.get('/api/copy-trading/status')
      setConfigs(response.data.active_configs)
      setPendingOrders(response.data.pending_orders)
      setTotalPnL(response.data.total_pnl)
    } catch (error) {
      console.error('Failed to fetch status:', error)
    } finally {
      setLoading(false)
    }
  }

  const enableCopyTrading = async () => {
    if (!selectedTrader || !percentage) {
      alert('Please select a trader and percentage')
      return
    }

    // Map trader names to addresses
    const traders = {
      '25usdc': '0x75e765216a57942d738d880ffcda854d9f869080',
      'Shunky': '0x535585bfE3f231029dBC2218263dC4Be91bFFAE9',
      'Car': '0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b'
    }

    const address = traders[selectedTrader]

    try {
      await apiClient.post('/api/copy-trading/enable', {
        target_trader: address,
        trader_name: selectedTrader,
        copy_percentage: percentage
      })

      alert(`✅ Copy trading activated for ${selectedTrader} at ${percentage}%`)
      fetchStatus()
    } catch (error: any) {
      alert('Failed: ' + (error.response?.data?.detail || error.message))
    }
  }

  const disableCopyTrading = async (traderAddress: string) => {
    if (!confirm('Disable copy trading for this trader?')) return

    try {
      await apiClient.post('/api/copy-trading/disable', {
        target_trader: traderAddress
      })

      alert('✅ Copy trading disabled')
      fetchStatus()
    } catch (error: any) {
      alert('Failed: ' + (error.response?.data?.detail || error.message))
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            🤖 Copy Trading Automatique
          </h1>
          <p className="text-gray-400">
            Copiez automatiquement les positions des meilleurs traders de Polymarket
          </p>
        </div>

        {/* Total PnL */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
          <div className="text-gray-400 text-sm mb-1">Total PnL Copy Trading</div>
          <div className={`text-3xl font-bold ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
          </div>
        </div>

        {/* Configuration Panel */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-white mb-4">
            Activer Copy Trading
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Sélection trader */}
            <div>
              <label className="block text-sm text-gray-300 mb-2">
                Trader à copier
              </label>
              <select
                value={selectedTrader}
                onChange={(e) => setSelectedTrader(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
              >
                <option value="">Choisir un trader...</option>
                <option value="25usdc">25usdc (+$686k PnL)</option>
                <option value="Shunky">Shunky (+$301k PnL)</option>
                <option value="Car">Car (+$296k PnL)</option>
              </select>
            </div>

            {/* Pourcentage */}
            <div>
              <label className="block text-sm text-gray-300 mb-2">
                Pourcentage à copier: {percentage}%
              </label>
              <input
                type="range"
                min="0.1"
                max="20"
                step="0.1"
                value={percentage}
                onChange={(e) => setPercentage(Number(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500 mt-1">
                Si il achète 100 shares, vous achèterez {percentage} shares
              </p>
            </div>

            {/* Bouton activer */}
            <div className="flex items-end">
              <button
                onClick={enableCopyTrading}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition-all"
              >
                Activer
              </button>
            </div>
          </div>
        </div>

        {/* Active Configs */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-white mb-4">
            Traders Suivis ({configs.length})
          </h2>

          {configs.length === 0 ? (
            <p className="text-gray-400 text-center py-8">
              Aucun trader suivi pour le moment
            </p>
          ) : (
            <div className="space-y-4">
              {configs.map(config => (
                <div
                  key={config.id}
                  className="bg-gray-700 rounded-lg p-4 flex justify-between items-center"
                >
                  <div>
                    <div className="text-white font-bold text-lg">
                      {config.target_trader_name}
                    </div>
                    <div className="text-gray-400 text-sm">
                      Copie: {config.copy_percentage}% •
                      Depuis {new Date(config.created_at).toLocaleDateString()}
                    </div>
                  </div>

                  <button
                    onClick={() => disableCopyTrading(config.target_trader_address)}
                    className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm"
                  >
                    Désactiver
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pending Orders */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">
            Ordres en Attente ({pendingOrders.length})
          </h2>

          {pendingOrders.length === 0 ? (
            <p className="text-gray-400 text-center py-8">
              Aucun ordre en attente
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-gray-400 border-b border-gray-700">
                  <tr>
                    <th className="text-left p-2">Marché</th>
                    <th className="text-left p-2">Action</th>
                    <th className="text-right p-2">Size</th>
                    <th className="text-right p-2">Prix Cible</th>
                    <th className="text-right p-2">Prix Actuel</th>
                    <th className="text-right p-2">Âge</th>
                    <th className="text-center p-2">Status</th>
                  </tr>
                </thead>
                <tbody className="text-white">
                  {pendingOrders.map(order => (
                    <tr key={order.id} className="border-b border-gray-700">
                      <td className="p-2">{order.market_name || 'Unknown'}</td>
                      <td className="p-2">
                        <span className={order.order_side === 'BUY' ? 'text-green-400' : 'text-red-400'}>
                          {order.order_side}
                        </span>
                      </td>
                      <td className="text-right p-2">{order.target_size.toFixed(2)}</td>
                      <td className="text-right p-2">${order.target_price.toFixed(4)}</td>
                      <td className="text-right p-2">${order.current_price.toFixed(4)}</td>
                      <td className="text-right p-2">
                        {Math.floor((Date.now() - new Date(order.created_at).getTime()) / 3600000)}h
                      </td>
                      <td className="text-center p-2">
                        <span className="px-2 py-1 bg-yellow-900 text-yellow-200 rounded text-xs">
                          {order.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
```

**À Ajouter: Route dans `frontend/src/App.tsx`:**

```typescript
import CopyTradingPage from './pages/CopyTrading'

// Dans les routes:
<Route path="/copy-trading" element={<CopyTradingPage />} />
```

**À Ajouter: Lien dans la navigation:**

```typescript
<Link to="/copy-trading">Copy Trading</Link>
```

---

### Phase 5: Déploiement & Tests (30 min)

**1. Migrer la Database sur Railway:**

```bash
# Via Railway Console ou localement avec DATABASE_URL
python run_migration.py
```

**2. Vérifier les Variables d'Environnement:**

```bash
# Railway Dashboard > Variables
✅ POLYMARKET_PRIVATE_KEY
✅ POLYMARKET_WALLET_ADDRESS
✅ POLYMARKET_BUILDER_API_KEY
✅ DATABASE_URL
✅ APP_PASSWORD
```

**3. Tests Initiaux (AVEC SEULEMENT $2!):**

```
# Test 1: Activer copy trading
- Aller sur /copy-trading
- Sélectionner "25usdc"
- Mettre percentage à 0.1% (TRÈS PETIT!)
- Activer

# Test 2: Attendre que 25usdc trade
- Vérifier les logs Railway
- Attendre détection (max 5 min)
- Vérifier ordre créé dans "Ordres en Attente"

# Test 3: Vérifier ajustement prix
- Attendre 6h
- Vérifier que prix a été ajusté
- Vérifier logs

# Test 4: Vérifier exécution
- Attendre que l'ordre soit rempli
- Vérifier dans executed_copy_trades
- Vérifier PnL

# Test 5: Désactiver
- Cliquer "Désactiver"
- Vérifier ordres annulés
```

**4. Monitoring:**

```bash
# Logs Railway à surveiller:
- "🔍 Starting position monitoring cycle..."
- "Detected X position change(s)"
- "Creating BUY/SELL order: X shares @ $Y"
- "✅ Copy trade executed successfully"
- "🔧 Managing pending orders..."
- "Order price adjusted to $X"
```

---

## 📊 Récapitulatif Technique

### Fonctionnement Global

```
Toutes les 5 minutes:

1. MONITOR_POSITIONS()
   ├─ Fetch positions de tous les traders suivis
   ├─ Compare avec dernier snapshot
   ├─ Détecte changements (NEW/INCREASE/DECREASE/CLOSED)
   └─ Pour chaque changement:
       ├─ Calcul proportionnel (ex: 5% des shares)
       ├─ Vérification taille minimum ($1)
       ├─ Smart pricing (selon spread & temps)
       ├─ Création ordre via CLOB
       └─ Enregistrement dans pending_copy_orders

2. MANAGE_PENDING_ORDERS()
   ├─ Récupère tous les ordres pending/partial
   └─ Pour chaque ordre:
       ├─ Check status sur CLOB
       ├─ Si filled → move to executed_copy_trades
       ├─ Si pas filled:
       │   ├─ Calculate hours_elapsed
       │   ├─ Détermine si ajustement nécessaire
       │   ├─ 0-6h: Prix exact trader
       │   ├─ 6-12h: +10-20% vers marché
       │   ├─ 12-24h: Mid-market
       │   ├─ 24-36h: Best price
       │   └─ 36h+: Convert to MARKET ORDER
       └─ Update prix si nécessaire
```

### Cas d'Usage

**Exemple Réel:**

```
Config: Copy "25usdc" à 5%

T+0min:
- 25usdc achète 100 shares Trump 2024 @ 0.58¢

T+2min (prochain polling):
- ✅ Détection: NEW_POSITION, 100 shares
- ✅ Calcul: 5% = 5 shares
- ✅ Notional: 5 × 0.58 = $2.90 (> $1 ✅)
- ✅ Market data: spread 0.58-0.59 (tight)
- ✅ Smart pricing: 0.58¢ (exact price, 0-6h window)
- ✅ Ordre créé: BUY 5 shares @ 0.58¢

T+6h (ordre pas exécuté):
- ✅ Ajustement: 0.581¢ (+10% du spread)
- ✅ Annulation ancien ordre
- ✅ Création nouveau @ 0.581¢

T+12h (toujours pas exécuté):
- ✅ Ajustement: 0.585¢ (mid-market)

T+24h (toujours pas exécuté):
- ✅ Ajustement: 0.59¢ (ask price)

T+36h (toujours pas exécuté):
- ✅ Conversion MARKET ORDER
- ✅ Exécution garantie au meilleur prix disponible

--- Pendant ce temps ---

T+8h:
- 25usdc vend 80 shares @ 0.85¢

T+10min (prochain polling):
- ✅ Détection: SIZE_DECREASE, 20 shares restantes
- ✅ Calcul: 80 shares vendues × 5% = 4 shares à vendre
- ✅ MAIS: Ordre d'achat de 5 shares toujours pending!
- ✅ ANNULATION ordre achat (Option A: trader changed mind)
- ✅ Création ordre SELL: 4 shares @ 0.85¢
```

---

## 🎯 Actions Immédiates (Prochaine Session)

1. ✅ **Vérifier que les clés Railway sont bien configurées** (FAIT ✅)
2. ⏳ **Résoudre authentification Git** (pour pouvoir push)
3. ⏳ **Ajouter endpoints API dans api_server.py** (code fourni ci-dessus)
4. ⏳ **Intégrer au scheduler** (code fourni ci-dessus)
5. ⏳ **Migrer database sur Railway** (`python run_migration.py`)
6. ⏳ **Créer frontend CopyTrading.tsx** (code fourni ci-dessus)
7. ⏳ **Tests avec $2** (0.1% de copy percentage)
8. ⏳ **Monitoring et ajustements**

---

## 💡 Notes Importantes

- ⚠️ **Tests avec $2 seulement au départ!** (0.1% copy percentage)
- ⚠️ **Ne JAMAIS commit/push les private keys**
- ⚠️ **Surveiller les logs Railway pendant les premiers trades**
- ⚠️ **Commencer avec UN SEUL trader** (25usdc recommandé)
- ⚠️ **Vérifier balance USDC avant d'activer**

---

## 📝 Commits à Faire

Quand Git auth sera résolue:

```bash
git add copy_trading_engine.py
git commit -m "feat: Add Copy Trading Engine (Phase 2)"
git push

# Puis après ajout endpoints:
git add api_server.py scheduler.py
git commit -m "feat: Integrate copy trading with API and scheduler"
git push

# Puis après frontend:
git add frontend/src/pages/CopyTrading.tsx frontend/src/App.tsx
git commit -m "feat: Add copy trading frontend UI"
git push
```

---

**Prêt pour la suite!** 🚀

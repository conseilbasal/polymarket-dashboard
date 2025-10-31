# 🤖 Copy Trading Automatique - Polymarket Dashboard

## 📊 Vue d'Ensemble

Système de copy trading automatique permettant de répliquer proportionnellement les positions des meilleurs traders de Polymarket en temps réel.

### Caractéristiques Principales

- **Réplication Proportionnelle**: Copiez X% des positions d'un trader (ex: 5% de ses shares)
- **Multi-Trader Support**: Suivez plusieurs traders simultanément
- **Smart Pricing Algorithm**: Algorithme adaptatif basé sur la liquidité du marché
- **Ajustement Progressif**: Prix ajustés automatiquement sur 36h jusqu'à exécution garantie
- **Market Orders Automatiques**: Conversion en market order après 36h si non exécuté

## ✅ Phase 1: Infrastructure (COMPLÉTÉ)

### Fichiers Créés

#### 1. **smart_pricing.py** - Algorithme de Pricing Intelligent
```
Stratégies adaptatives selon liquidité:
- Tight Spread (<0.5%): Patient, stick au prix du trader
- Normal Spread (0.5-2%): Équilibré, ajustement progressif
- Wide Spread (>2%): Agressif, accepte plus de slippage

Ajustements temporels:
- 0-6h: Prix exact du trader
- 6-12h: +10-20% vers le marché
- 12-24h: Mid-market pricing
- 24-36h: Best price ou mieux
- 36h+: Market order (garantie d'exécution)
```

#### 2. **clob_client.py** - Wrapper Polymarket CLOB API
```
Fonctionnalités:
- Création d'ordres limites & market
- Signature avec private key
- Tracking du statut des ordres
- Annulation d'ordres
- Récupération market data (bid/ask/spread)
- Consultation positions & balance
```

#### 3. **migrations/001_copy_trading_schema.sql** - Schéma Database
```sql
Tables créées:
- copy_trading_config: Configuration par user/trader
- position_snapshots: Snapshots historiques pour détecter changements
- pending_copy_orders: Ordres en attente avec tracking
- executed_copy_trades: Historique trades avec PnL
```

#### 4. **run_migration.py** - Script de Migration
```
Automatise le déploiement du schéma sur PostgreSQL
```

### Dépendances Ajoutées

```txt
py-clob-client>=0.26.0  # Client officiel Polymarket
web3>=7.14.0            # Signature cryptographique
```

## 🚧 Phase 2: Core Engine (À FAIRE)

### Fichiers à Créer

#### 1. **copy_trading_engine.py** - Moteur Principal
```python
Composants nécessaires:

class CopyTradingEngine:
    # Position Monitoring (toutes les 5 min)
    async def monitor_positions()
        - Récupère positions actuelles des traders suivis
        - Compare avec dernier snapshot
        - Détecte: NEW_POSITION, SIZE_INCREASE, SIZE_DECREASE, POSITION_CLOSED

    # Order Execution
    async def execute_copy_trade()
        - Calcul proportionnel (ex: 5% des shares)
        - Vérification taille minimum ($1)
        - Smart pricing via SmartPricingEngine
        - Création & soumission ordre via ClobClient
        - Enregistrement dans pending_copy_orders

    # Pending Orders Management (toutes les 5 min)
    async def manage_pending_orders()
        - Vérification statut de chaque ordre
        - Ajustement prix si nécessaire
        - Annulation si trader a changé de position (Option A)
        - Gestion ordres partiellement remplis (Option A: retry)
        - Conversion en market order après 36h
```

#### 2. **Endpoints API** (modifications à api_server.py)
```python
@app.post("/api/copy-trading/enable")
    - Activer copy trading pour un trader
    - Paramètres: target_trader, copy_percentage

@app.post("/api/copy-trading/disable")
    - Désactiver et annuler tous les ordres en attente

@app.get("/api/copy-trading/status")
    - Traders suivis, ordres en attente, performance

@app.get("/api/copy-trading/history")
    - Historique des trades + PnL par trader

@app.get("/api/copy-trading/performance")
    - Stats détaillées: win rate, slippage moyen, attribution
```

#### 3. **Intégration Scheduler** (modifications à scheduler.py)
```python
# Ajouter 2 jobs:
scheduler.add_job(
    copy_engine.monitor_positions,
    'interval',
    minutes=5,
    id='copy_trading_monitor'
)

scheduler.add_job(
    copy_engine.manage_pending_orders,
    'interval',
    minutes=5,
    id='copy_trading_orders'
)
```

## 🎨 Phase 3: Interface Frontend (À FAIRE)

### Pages à Créer

#### 1. **frontend/src/pages/CopyTrading.tsx**
```typescript
Sections:
- Configuration Panel
  * Sélection trader (dropdown avec leaderboard)
  * Slider pourcentage à copier (0.1% - 20%)
  * Switch ON/OFF

- Active Configs
  * Liste traders suivis avec stats
  * PnL par trader
  * Nombre ordres en attente
  * Bouton désactiver

- Pending Orders Table
  * Marché, Action, Size, Prix Initial, Prix Actuel
  * Âge de l'ordre (countdown)
  * Status (pending/partial/filled)

- Trade History
  * Historique complet avec slippage
  * Filtres par trader/date/marché
  * PnL total

- Performance Dashboard
  * Attribution: "25usdc vous a fait gagner +$X"
  * Win rate, avg slippage
  * Charts PnL over time
```

## 🔐 Configuration Requise

### Railway Secrets (À AJOUTER)

```bash
# Dans Railway Dashboard > Variables:
POLYMARKET_PRIVATE_KEY=0x...         # Votre private key
POLYMARKET_WALLET_ADDRESS=0x...      # Votre adresse wallet
POLYMARKET_BUILDER_API_KEY=019a3c52... # Votre clé API Builder
```

### Migration Database

```bash
# Sur Railway, via console:
python run_migration.py
```

## 📋 Spécifications Techniques

### Logique de Copy Trading

**Exemple: Copier 25usdc à 5%**

```
1. 25usdc achète 100 shares Trump 2024 @ 0.58¢
   → Vous achetez 5 shares @ 0.58¢ (ordre limite)

2. Si ordre pas exécuté après 6h
   → Ajustement prix à 0.581¢ (via smart pricing)

3. Si ordre pas exécuté après 24h
   → Ajustement prix à 0.59¢ (mid-market)

4. Si ordre pas exécuté après 36h
   → Conversion en market order (exécution garantie)

5. 25usdc vend 80 shares @ 0.85¢
   → Vous vendez 4 shares @ 0.85¢ (5% de 80)
```

### Gestion des Cas Limites

**Ordre en attente + Trader change d'avis:**
```
Vous: Ordre d'achat 5 shares @ 0.58¢ (en attente)
25usdc: Vend sa position complètement
→ Annulation immédiate de votre ordre (Option A)
```

**Taille minimum:**
```
Si calcul proportionnel < $1
→ Trade ignoré automatiquement
```

**Ordres partiels:**
```
Ordre: Vendre 4 shares
Exécuté: Seulement 2 shares vendues
→ Continue à essayer de vendre les 2 restantes (Option A)
```

**Multi-positions (YES + NO):**
```
Si trader hedge en achetant YES et NO sur même marché
→ On copie les deux positions proportionnellement
```

## 🧪 Plan de Test

### Tests à Effectuer (Phase 4)

1. **Test Configuration**
   ```bash
   # Vérifier credentials
   python -c "from clob_client import PolymarketCLOBClient; c = PolymarketCLOBClient(); print('✅ OK')"
   ```

2. **Test Database**
   ```bash
   python run_migration.py
   # Vérifier tables créées
   ```

3. **Test Smart Pricing**
   ```python
   from smart_pricing import SmartPricingEngine
   engine = SmartPricingEngine()

   # Test tight spread
   result = engine.calculate_optimal_price(
       target_price=0.58,
       order_side='BUY',
       market_data={'best_bid': 0.58, 'best_ask': 0.59, ...},
       hours_elapsed=0
   )
   print(f"Prix optimal: {result['price']}")
   ```

4. **Test CLOB Client**
   ```python
   from clob_client import PolymarketCLOBClient
   client = PolymarketCLOBClient()

   # Vérifier balance
   balance = client.get_balance()
   print(f"Balance: ${balance}")

   # Vérifier positions
   positions = client.get_user_positions()
   print(f"Positions: {len(positions)}")
   ```

5. **Test End-to-End (Petite Somme)**
   ```
   - Activer copy trading pour 25usdc à 1%
   - Attendre qu'il trade
   - Vérifier ordre créé
   - Vérifier ajustement prix après 6h
   - Vérifier exécution finale
   ```

## 💰 Business Model (Phase 5)

### Tiers d'Abonnement

```
FREE:
- Voir leaderboard & stats
- ❌ Pas de copy automatique

PRO ($49/mois):
- Copy 1 trader jusqu'à 10%
- Alertes en temps réel
- Historique 30 jours

ELITE ($149/mois):
- Copy illimité jusqu'à 20%
- Multi-trader portfolios
- Analytics avancés
- API access

WHALE ($499/mois):
- Tout Elite +
- Stratégie personnalisée
- ML-optimized portfolios
- Support prioritaire
```

## 📚 Documentation Technique

### Architecture Globale

```
┌─────────────────────────────────────────────────────┐
│               COPY TRADING SYSTEM                    │
└─────────────────────────────────────────────────────┘

Railway Backend:
├─ scheduler.py (APScheduler)
│  ├─ monitor_positions() [every 5 min]
│  └─ manage_pending_orders() [every 5 min]
│
├─ copy_trading_engine.py
│  ├─ Position Monitor → Détecte changements
│  ├─ Order Executor → Crée & soumet ordres
│  └─ Order Manager → Ajuste prix, annule si nécessaire
│
├─ smart_pricing.py → Calcule prix optimaux
├─ clob_client.py → Interface Polymarket CLOB
└─ PostgreSQL → Stockage config + historique

Vercel Frontend (React):
└─ src/pages/CopyTrading.tsx
   ├─ Configuration UI
   ├─ Active Traders Panel
   ├─ Pending Orders Table
   └─ Performance Dashboard
```

## 🚀 Prochaines Étapes

### Session Suivante:

1. **Créer copy_trading_engine.py** (~1h)
2. **Ajouter endpoints API** (~30min)
3. **Intégrer avec scheduler** (~15min)
4. **Créer frontend CopyTrading.tsx** (~1h)
5. **Tests end-to-end** (~30min)
6. **Documentation finale** (~15min)

### Avant de Déployer:

1. ✅ Ajouter les 3 variables Railway Secrets
2. ✅ Lancer la migration database
3. ✅ Tester avec petites sommes ($50-100)
4. ✅ Monitorer les premiers trades
5. ✅ Ajuster pricing si nécessaire

## 📞 Support & Questions

**Note**: Ne partagez JAMAIS votre POLYMARKET_PRIVATE_KEY avec quiconque!

---

*Dernière mise à jour: 31 janvier 2025*
*Status: Phase 1 Complétée ✅ | Phase 2-3 En Attente*

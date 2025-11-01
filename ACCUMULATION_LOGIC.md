# Logique d'Accumulation des Positions Copy Trading

## Problème à Résoudre

Quand le pourcentage de copy trading est faible (ex: 0.2% pour 2$ sur un capital de 1000$), certaines positions du trader copié sont trop petites pour être placées immédiatement.

**Exemple concret de 25usdc** :
- Position 1 : $0.13 → Copie à 0.2% = $0.00026 (trop petit)
- Position 2 : $1.74 → Copie à 0.2% = $0.00348 (trop petit)
- Position 3 : $7.51 → Copie à 0.2% = $0.01502 (trop petit)
- Position 4 : $56.08 → Copie à 0.2% = $0.11216 (acceptable !)

Au lieu de perdre les 3 premières positions, on veut les **cumuler** jusqu'à atteindre un seuil minimum.

## Solution : Système d'Accumulation

### Paramètres Configurables

```python
MINIMUM_ORDER_SIZE = 0.50  # $0.50 USD minimum par ordre
```

### Logique d'Accumulation

#### Étape 1 : Détection Nouvelle Position

Quand une nouvelle position est détectée pour un trader copié :

1. **Calculer la taille de la copie**
   ```python
   copy_size = original_size * (copy_percentage / 100)
   copy_value_usd = copy_size * price
   ```

2. **Vérifier si accumulation existe déjà**
   ```sql
   SELECT * FROM pending_accumulation
   WHERE user_wallet_address = :user
   AND target_trader_address = :trader
   AND market_id = :market
   AND outcome = :outcome
   ```

#### Étape 2 : Décision de Placement

**CAS A : Position trop petite (< MINIMUM_ORDER_SIZE)**

```python
if copy_value_usd < MINIMUM_ORDER_SIZE:
    # Ajouter à l'accumulation (INSERT ou UPDATE)
    accumulated_size += copy_size
    accumulated_value += copy_value_usd

    # Vérifier si l'accumulation atteint maintenant le minimum
    if accumulated_value >= MINIMUM_ORDER_SIZE:
        # Placer l'ordre cumulé
        place_order(accumulated_size, price, market_id, outcome)
        # Vider l'accumulation
        DELETE FROM pending_accumulation WHERE id = ...
        LOG: "Ordre cumulé placé: {accumulated_value} USD"
    else:
        # Sauvegarder l'accumulation
        SAVE pending_accumulation
        LOG: "Position ajoutée à l'accumulation: {copy_value_usd} → Total: {accumulated_value}"
```

**CAS B : Position suffisamment grande (>= MINIMUM_ORDER_SIZE)**

```python
if copy_value_usd >= MINIMUM_ORDER_SIZE:
    # Vérifier s'il y a une accumulation en attente
    if accumulation_exists:
        # Cumuler avec l'accumulation
        total_size = copy_size + accumulated_size
        total_value = copy_value_usd + accumulated_value

        # Placer l'ordre total
        place_order(total_size, price, market_id, outcome)

        # Vider l'accumulation
        DELETE FROM pending_accumulation WHERE id = ...
        LOG: "Ordre placé avec accumulation: {total_value} USD (dont {accumulated_value} accumulé)"
    else:
        # Placer normalement
        place_order(copy_size, price, market_id, outcome)
        LOG: "Ordre placé: {copy_value_usd} USD"
```

### Exemple Concret avec 25usdc

Trader copié : 25usdc
Copy percentage : 0.2%
Marché : "US x Venezuela military engagement by November 1?"
Outcome : Yes

| Temps | Position 25usdc | Copie (0.2%) | Accumulation | Action |
|-------|----------------|--------------|--------------|--------|
| T+0 | $0.13 @ $0.02 | $0.00026 | $0.00026 | Accumuler (< $0.50) |
| T+10m | $1.74 @ $0.02 | $0.00348 | $0.00374 | Accumuler (< $0.50) |
| T+12m | $7.51 @ $0.02 | $0.01502 | $0.01876 | Accumuler (< $0.50) |
| T+20m | $0.56 @ $0.04 | $0.00112 | $0.01988 | Accumuler (< $0.50) |
| T+32m | $56.08 @ $0.02 | $0.11216 | - | **Placer ordre de $0.13204** (cumul + nouveau) |
| T+33m | $13.54 @ $0.02 | $0.02708 | $0.02708 | Accumuler (< $0.50) |
| T+1h | $0.13 @ $0.02 | $0.00026 | $0.02734 | Accumuler (< $0.50) |
| T+1h1m | $1.59 @ $0.02 | $0.00318 | $0.03052 | Accumuler (< $0.50) |

Résultat : Au lieu de perdre 7 positions trop petites, on place 1 ordre cumulé de $0.13 !

## Modifications de Code Nécessaires

### 1. Modifier `copy_trading_engine.py`

Dans la méthode `monitor_positions()` :

```python
async def _process_new_position(self, config, position):
    """Process a newly detected position"""
    # Calculer la taille de la copie
    copy_size = position['size'] * (config['copy_percentage'] / 100)
    copy_value = copy_size * position['price']

    # Vérifier l'accumulation existante
    accumulation = self._get_accumulation(
        config['user_wallet_address'],
        position['trader'],
        position['market_id'],
        position['outcome']
    )

    # LOGIQUE D'ACCUMULATION ICI
    if copy_value < MINIMUM_ORDER_SIZE:
        # Cas A : trop petit, accumuler
        self._add_to_accumulation(accumulation, copy_size, copy_value, ...)
    else:
        # Cas B : assez grand, placer (+ accumulation si existe)
        if accumulation:
            total_size = copy_size + accumulation['size']
            self._place_order(total_size, ...)
            self._clear_accumulation(accumulation['id'])
        else:
            self._place_order(copy_size, ...)
```

### 2. Nouvelles Méthodes à Ajouter

```python
def _get_accumulation(self, user, trader, market, outcome):
    """Get existing accumulation for this position"""
    # SELECT FROM pending_accumulation WHERE ...

def _add_to_accumulation(self, accumulation, size, value, ...):
    """Add or update accumulation"""
    # INSERT ON CONFLICT UPDATE pending_accumulation

def _clear_accumulation(self, accumulation_id):
    """Remove accumulation after order placed"""
    # DELETE FROM pending_accumulation WHERE id = ...
```

### 3. Ajouter Configuration

```python
# Dans copy_trading_engine.py
MINIMUM_ORDER_SIZE = float(os.getenv("COPY_TRADING_MIN_ORDER_SIZE", "0.50"))  # USD
```

## Tests à Effectuer

1. **Test avec petit capital** : 0.2% copy percentage, positions < $0.50
2. **Test accumulation progressive** : Plusieurs petites positions sur même marché
3. **Test déclenchement** : Accumulation + nouvelle position >= $0.50
4. **Test multi-marchés** : Accumulations séparées par marché
5. **Test multi-outcomes** : YES et NO accumulés séparément

## Avantages

1. ✅ Ne perd aucune position du trader copié
2. ✅ Optimise les frais (moins d'ordres, plus gros)
3. ✅ Meilleure liquidité (ordres plus gros)
4. ✅ Fonctionne avec de très petits capitaux (< $5)
5. ✅ Transparent : logs détaillés de l'accumulation

## Prochaines Étapes

1. [ ] Implémenter les 3 nouvelles méthodes dans `copy_trading_engine.py`
2. [ ] Ajouter la logique d'accumulation dans `_process_new_position()`
3. [ ] Ajouter variable d'environnement `COPY_TRADING_MIN_ORDER_SIZE`
4. [ ] Tester en local avec données simulées
5. [ ] Déployer sur Railway
6. [ ] Tester avec copy trading réel à 0.2%

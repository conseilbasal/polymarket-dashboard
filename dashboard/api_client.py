"""
Client API pour se connecter au backend Railway
"""

import requests
import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any


class PolymarketAPIClient:
    """Client pour interagir avec l'API Railway"""

    def __init__(self, base_url: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.password = password
        self.token: Optional[str] = None

    def login(self) -> bool:
        """Authentification sur l'API et récupération du token JWT"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"password": self.password},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                return True
            else:
                st.error(f"❌ Erreur d'authentification: {response.status_code}")
                return False

        except Exception as e:
            st.error(f"❌ Erreur de connexion: {str(e)}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Retourne les headers avec le token JWT"""
        if not self.token:
            raise ValueError("Non authentifié. Appelez login() d'abord.")
        return {"Authorization": f"Bearer {self.token}"}

    def get_latest_positions(self) -> Optional[pd.DataFrame]:
        """
        Récupère les dernières positions depuis l'API
        Returns: DataFrame avec toutes les positions ou None en cas d'erreur
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/positions/latest",
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                positions = data.get("positions", [])
                if positions:
                    return pd.DataFrame(positions)
                else:
                    return pd.DataFrame()
            else:
                st.error(f"❌ Erreur API: {response.status_code}")
                return None

        except Exception as e:
            st.error(f"❌ Erreur lors de la récupération des positions: {str(e)}")
            return None

    def get_copy_trading_comparison(
        self,
        target_trader: str = "25usdc",
        user_trader: str = "Shunky",
        copy_percentage: float = 10.0
    ) -> Optional[Dict[str, Any]]:
        """
        Récupère la comparaison copy trading depuis l'API
        Returns: Dict avec les actions à faire ou None en cas d'erreur
        """
        try:
            params = {
                "target_trader": target_trader,
                "user_trader": user_trader,
                "copy_percentage": copy_percentage
            }

            response = requests.get(
                f"{self.base_url}/api/copy-trading/comparison",
                headers=self._get_headers(),
                params=params,
                timeout=15
            )

            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"❌ Erreur API: {response.status_code}")
                return None

        except Exception as e:
            st.error(f"❌ Erreur lors de la comparaison: {str(e)}")
            return None

    def get_scheduler_status(self) -> Optional[Dict[str, Any]]:
        """
        Récupère le statut du scheduler
        Returns: Dict avec le statut ou None en cas d'erreur
        """
        try:
            # Pas besoin d'auth pour /api/scheduler/status
            response = requests.get(
                f"{self.base_url}/api/scheduler/status",
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception as e:
            st.warning(f"⚠️ Impossible de récupérer le statut du scheduler: {str(e)}")
            return None

    def trigger_refresh(self) -> bool:
        """
        Force un refresh manuel des données
        Returns: True si succès, False sinon
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/refresh",
                headers=self._get_headers(),
                timeout=120  # 2 minutes max pour le fetch
            )

            if response.status_code == 200:
                return True
            else:
                st.error(f"❌ Erreur lors du refresh: {response.status_code}")
                return False

        except Exception as e:
            st.error(f"❌ Erreur lors du refresh: {str(e)}")
            return False


def get_api_client() -> PolymarketAPIClient:
    """
    Crée et retourne un client API authentifié
    Utilise st.secrets pour la configuration
    """
    # Récupérer la configuration depuis st.secrets
    api_url = st.secrets.get("api", {}).get("url", "http://localhost:8000")
    api_password = st.secrets.get("api", {}).get("password", "polymarket2024")

    # Créer le client
    client = PolymarketAPIClient(api_url, api_password)

    # Authentification
    if not client.login():
        st.error("❌ Échec de l'authentification à l'API")
        st.stop()

    return client

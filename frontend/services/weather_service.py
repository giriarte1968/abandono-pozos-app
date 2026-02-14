import requests
import streamlit as st

class WeatherService:
    """
    Servicio de integración con Open-Meteo API.
    Provee datos climáticos actuales y pronóstico simple.
    """
    BASELINE_URL = "https://api.open-meteo.com/v1/forecast"

    @st.cache_data(ttl=3600) # Caché de 1 hora
    def get_weather(_self, lat, lon):
        """
        Obtiene clima actual y forecast 24h para coordenadas dadas.
        """
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
                "timezone": "America/Argentina/Buenos_Aires",
                "forecast_days": 1
            }
            
            response = requests.get(_self.BASELINE_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Formatear respuesta para la UI
            current = data.get("current", {})
            daily = data.get("daily", {})
            
            return {
                "temp_actual": f"{current.get('temperature_2m', 'N/A')} °C",
                "viento_actual": f"{current.get('wind_speed_10m', 'N/A')} km/h",
                "precip_actual": f"{current.get('precipitation', 'N/A')} mm",
                "max_temp": f"{daily.get('temperature_2m_max', ['N/A'])[0]} °C",
                "min_temp": f"{daily.get('temperature_2m_min', ['N/A'])[0]} °C",
                "alerta_viento": current.get('wind_speed_10m', 0) > 40 # Alerta visual si > 40kmh
            }
            
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return None

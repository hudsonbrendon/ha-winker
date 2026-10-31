"""Constants for the Winker (Beelive) integration."""

DOMAIN = "winker"

# Verificado por RE do app Beelive (br.com.winker.wl.beelive) + API ao vivo 2026-10-30.
BASE_URL = "https://api.winker.com.br/v1"
APP_KEY = "02172365163556734152324794784128972476"
APP_VERSION = "2.2.250"

CONF_ID_PORTAL = "id_portal"
CONF_PORTAL_NAME = "portal_name"

DEFAULT_SCAN_INTERVAL = 1800  # 30 min; a API não é sensor em tempo real.

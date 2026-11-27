#!/usr/bin/env bash
# Pubblica il generatore di etichette su un server (nginx + systemd + HTTPS).
# Da lanciare DAL TUO COMPUTER, nella cartella etichette/:
#   ./deploy.sh                       # default: nicolo@82.165.113.237, mindat.chicubo.it
#   ./deploy.sh utente@host dominio
set -euo pipefail

TARGET="${1:-nicolo@82.165.113.237}"
DOMAIN="${2:-mindat.chicubo.it}"
PORT=8765
DIR='$HOME/mindat-etichette'
cd "$(dirname "$0")"

read -rsp "Chiave API Mindat (invio = lascia quella già sul server): " KEY; echo
read -rp  "Proteggere il sito con password? [s/N] " PROTECT
if [[ "$PROTECT" =~ ^[sSyY] ]]; then
  read -rp  "  utente: " AUTH_USER
  read -rsp "  password: " AUTH_PASS; echo
fi

echo "==> Copio i file su $TARGET"
ssh "$TARGET" "mkdir -p $DIR"
rsync -az --delete --exclude .mindat_key --exclude deploy.sh --exclude '__pycache__' ./ "$TARGET:mindat-etichette/"
if [[ -n "$KEY" ]]; then
  printf '%s' "$KEY" | ssh "$TARGET" "umask 077; cat > $DIR/.mindat_key"
fi

echo "==> Configuro il server (ti chiederà la password di sudo)"
ssh -t "$TARGET" "DOMAIN='$DOMAIN' PORT='$PORT' AUTH_USER='${AUTH_USER:-}' AUTH_PASS='${AUTH_PASS:-}' bash -s" <<'REMOTE'
set -euo pipefail
APP="$HOME/mindat-etichette"
ME="$(id -un)"
command -v python3 >/dev/null || { echo "Manca python3"; exit 1; }

sudo tee /etc/systemd/system/mindat-etichette.service >/dev/null <<EOF
[Unit]
Description=Generatore etichette minerali (Mindat)
After=network-online.target

[Service]
User=$ME
WorkingDirectory=$APP
ExecStart=/usr/bin/env python3 $APP/server.py $PORT
Restart=always

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now mindat-etichette
sudo systemctl restart mindat-etichette

if ! command -v nginx >/dev/null; then
  echo "!! nginx non trovato: il servizio gira su 127.0.0.1:$PORT, configura tu il proxy per $DOMAIN"
  exit 0
fi

AUTH_CONF=""
if [[ -n "$AUTH_USER" ]]; then
  HASH="$(openssl passwd -apr1 "$AUTH_PASS")"
  echo "$AUTH_USER:$HASH" | sudo tee /etc/nginx/mindat-etichette.htpasswd >/dev/null
  sudo chmod 640 /etc/nginx/mindat-etichette.htpasswd
  sudo chgrp www-data /etc/nginx/mindat-etichette.htpasswd 2>/dev/null || true
  AUTH_CONF='auth_basic "Etichette"; auth_basic_user_file /etc/nginx/mindat-etichette.htpasswd;'
fi

CONF=/etc/nginx/sites-available/$DOMAIN
[[ -d /etc/nginx/sites-available ]] || CONF=/etc/nginx/conf.d/$DOMAIN.conf
if ! sudo test -f "$CONF"; then
  sudo tee "$CONF" >/dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    location / {
        $AUTH_CONF
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }
}
EOF
  [[ -d /etc/nginx/sites-enabled ]] && sudo ln -sf "$CONF" /etc/nginx/sites-enabled/
  NEW=1
else
  echo "   $CONF esiste già: non lo tocco"
fi
sudo nginx -t && sudo systemctl reload nginx

if [[ "${NEW:-}" == 1 ]] && command -v certbot >/dev/null; then
  sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --redirect --register-unsafely-without-email \
    || echo "!! certbot fallito: controlla che il DNS di $DOMAIN punti a questo server"
elif ! command -v certbot >/dev/null; then
  echo "!! certbot non installato: HTTPS non configurato (sudo apt install certbot python3-certbot-nginx)"
fi

sleep 1
curl -fsS "http://127.0.0.1:$PORT/api/__ping" && echo
echo "==> Fatto: https://$DOMAIN"
REMOTE

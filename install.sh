#!/usr/bin/env bash
# =============================================================================
# MySQL Workbench 26 em Português (BR) — instalador de 1 comando
#
# Baixa o MySQL Workbench 26.7.0 OFICIAL da Oracle, instala em /opt e aplica a
# tradução comunitária pt-BR. NÃO redistribui o binário da Oracle — baixa direto
# da fonte oficial. Projeto não-oficial, não afiliado à Oracle. Licença GPLv2.
#
# Uso:   sudo ./install.sh
# =============================================================================
set -euo pipefail

VERSION="26.7.0"
ZIP_NAME="mysql-workbench-${VERSION}-linux-glibc2.28-x86_64.zip"
URL="https://cdn.mysql.com/Downloads/MySQLGUITools/${ZIP_NAME}"
MD5_EXPECTED="8df1d426a8d0d8ce375c9ef38c0f2f28"
INSTALL_DIR="/opt/mysql-workbench-${VERSION}"
CACHE="/var/cache/workbench-ptbr"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

say(){ printf '\033[1;36m==>\033[0m %s\n' "$*"; }
err(){ printf '\033[1;31mERRO:\033[0m %s\n' "$*" >&2; exit 1; }

# --- checagens ---
[ "$(id -u)" -eq 0 ] || err "Rode com sudo:  sudo ./install.sh"
[ "$(uname -m)" = "x86_64" ] || err "Esta versão é para x86_64 (64-bit Intel/AMD). Sua arquitetura: $(uname -m)"
command -v python3 >/dev/null || err "python3 não encontrado."
command -v unzip   >/dev/null || err "unzip não encontrado. Instale:  sudo apt install unzip"

# --- download (com cache + verificação MD5) ---
mkdir -p "$CACHE"
ZIP="$CACHE/$ZIP_NAME"
if [ -f "$ZIP" ] && [ "$(md5sum "$ZIP" | awk '{print $1}')" = "$MD5_EXPECTED" ]; then
  say "Instalador já em cache (MD5 confere). Pulando download."
else
  say "Baixando MySQL Workbench ${VERSION} oficial da Oracle (~375 MB)..."
  if command -v wget >/dev/null; then
    wget -q --show-progress --user-agent="Mozilla/5.0" -O "$ZIP" "$URL"
  elif command -v curl >/dev/null; then
    curl -L --progress-bar -A "Mozilla/5.0" -o "$ZIP" "$URL"
  else
    err "Nem wget nem curl encontrados."
  fi
  say "Verificando integridade (MD5)..."
  GOT="$(md5sum "$ZIP" | awk '{print $1}')"
  [ "$GOT" = "$MD5_EXPECTED" ] || err "MD5 não confere (esperado $MD5_EXPECTED, obtido $GOT). Download corrompido."
fi

# --- instalação ---
say "Instalando em $INSTALL_DIR ..."
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
unzip -q -o "$ZIP" -d "$INSTALL_DIR"

say "Configurando sandbox e permissões..."
if [ -f "$INSTALL_DIR/chrome-sandbox" ]; then
  chown root:root "$INSTALL_DIR/chrome-sandbox"
  chmod 4755 "$INSTALL_DIR/chrome-sandbox"
fi

say "Criando atalho e comando..."
cat > /usr/local/bin/mysql-workbench-26 <<EOF
#!/bin/sh
exec $INSTALL_DIR/mysql-workbench "\$@"
EOF
chmod +x /usr/local/bin/mysql-workbench-26

cat > /usr/share/applications/mysql-workbench-26.desktop <<EOF
[Desktop Entry]
Name=MySQL Workbench 26 (PT-BR)
GenericName=Ferramenta de Banco de Dados
Comment=MySQL Workbench 26 em Português do Brasil
Exec=$INSTALL_DIR/mysql-workbench %U
Icon=$INSTALL_DIR/resources/app/images/app-icon.png
Terminal=false
Type=Application
Categories=Development;Database;
StartupNotify=true
StartupWMClass=mysql-workbench
EOF
update-desktop-database /usr/share/applications 2>/dev/null || true

say "Aplicando tradução pt-BR..."
python3 "$SCRIPT_DIR/patch.py" --install-dir "$INSTALL_DIR"

echo
say "✅ Pronto! MySQL Workbench 26 instalado e em Português do Brasil."
say "Abra pelo menu ('MySQL Workbench 26') ou rode:  mysql-workbench-26"
say "Reverter para inglês:  sudo python3 $SCRIPT_DIR/patch.py --revert"

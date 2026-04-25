#!/bin/bash

# ============================================================
#  FISI Toolbox — Installer
#  Developer: Cedric Thieme
#  Supports: Fedora, Debian, Ubuntu and derivatives
# ============================================================

set -e

APP_NAME="FISI Toolbox"
APP_ID="fisi-toolbox"
APP_VERSION="1.0.0"
INSTALL_DIR="/opt/fisi-toolbox"
DESKTOP_FILE="/usr/share/applications/fisi-toolbox.desktop"
ICON_DIR="/usr/share/icons/hicolor/256x256/apps"
BIN_LINK="/usr/local/bin/fisi-toolbox"

# ── Colors ──────────────────────────────────────────────────
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║        FISI Toolbox  v${APP_VERSION}  Installer      ║${NC}"
    echo -e "${CYAN}${BOLD}║        by Cedric Thieme                  ║${NC}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}[*]${NC} $1"
}

print_ok() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# ── Root check ───────────────────────────────────────────────
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Bitte mit sudo ausführen: sudo bash install.sh"
        exit 1
    fi
}

# ── Detect distro ────────────────────────────────────────────
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        DISTRO_LIKE=$ID_LIKE
    else
        DISTRO="unknown"
    fi

    case "$DISTRO" in
        fedora|rhel|centos|rocky|alma)
            PKG_MANAGER="dnf"
            ;;
        debian|ubuntu|linuxmint|pop|elementary|zorin|kali)
            PKG_MANAGER="apt"
            ;;
        *)
            # Fallback: check ID_LIKE
            if echo "$DISTRO_LIKE" | grep -q "fedora\|rhel"; then
                PKG_MANAGER="dnf"
            elif echo "$DISTRO_LIKE" | grep -q "debian\|ubuntu"; then
                PKG_MANAGER="apt"
            else
                print_warn "Unbekannte Distribution: $DISTRO — versuche apt..."
                PKG_MANAGER="apt"
            fi
            ;;
    esac

    print_ok "Distribution erkannt: ${DISTRO} (Paketmanager: ${PKG_MANAGER})"
}

# ── Install system dependencies ──────────────────────────────
install_dependencies() {
    print_step "Installiere System-Abhängigkeiten..."

    if [ "$PKG_MANAGER" = "dnf" ]; then
        dnf install -y python3 python3-pip python3-wheel \
            python3-qt6 python3-psutil \
            hicolor-icon-theme gtk-update-icon-cache 2>/dev/null || \
        dnf install -y python3 python3-pip python3-wheel hicolor-icon-theme 2>/dev/null
    else
        apt-get update -qq
        apt-get install -y python3 python3-pip python3-wheel \
            python3-pyqt6 python3-psutil \
            hicolor-icon-theme 2>/dev/null || \
        apt-get install -y python3 python3-pip python3-wheel hicolor-icon-theme 2>/dev/null
    fi

    print_ok "System-Pakete installiert"
}

# ── Install Python dependencies ──────────────────────────────
install_python_deps() {
    print_step "Installiere Python-Abhängigkeiten..."

    # Try system pip first, fallback to --break-system-packages
    if python3 -c "import PyQt6" 2>/dev/null; then
        print_ok "PyQt6 bereits vorhanden"
    else
        pip3 install PyQt6 --quiet 2>/dev/null || \
        pip3 install PyQt6 --quiet --break-system-packages 2>/dev/null || \
        pip3 install PyQt6 --quiet --user
        print_ok "PyQt6 installiert"
    fi

    if python3 -c "import psutil" 2>/dev/null; then
        print_ok "psutil bereits vorhanden"
    else
        pip3 install psutil --quiet 2>/dev/null || \
        pip3 install psutil --quiet --break-system-packages 2>/dev/null || \
        pip3 install psutil --quiet --user
        print_ok "psutil installiert"
    fi
}

# ── Copy app files ───────────────────────────────────────────
install_app_files() {
    print_step "Installiere App-Dateien nach ${INSTALL_DIR}..."

    if [ -d "$INSTALL_DIR" ]; then
        print_warn "Alte Installation gefunden — wird überschrieben"
        rm -rf "$INSTALL_DIR"
    fi

    mkdir -p "$INSTALL_DIR"

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"

    if [ -f "$SCRIPT_DIR/main.py" ]; then
        # Local install
        print_step "Lokale Dateien gefunden — kopiere..."
        cp -r "$SCRIPT_DIR/." "$INSTALL_DIR/"
    else
        # Remote install — download zip from GitHub
        print_step "Lade App von GitHub herunter..."
        TMP_ZIP=$(mktemp /tmp/fisi-toolbox-XXXX.zip)
        TMP_DIR=$(mktemp -d /tmp/fisi-extract-XXXX)

        if command -v curl &>/dev/null; then
            curl -sL "https://github.com/PassaratiV12/FISI-ToolBox/archive/refs/heads/main.zip" -o "$TMP_ZIP"
        elif command -v wget &>/dev/null; then
            wget -q "https://github.com/PassaratiV12/FISI-ToolBox/archive/refs/heads/main.zip" -O "$TMP_ZIP"
        else
            print_error "curl oder wget wird benötigt"
            exit 1
        fi

        unzip -q "$TMP_ZIP" -d "$TMP_DIR"
        cp -r "$TMP_DIR"/FISI-ToolBox-main/. "$INSTALL_DIR/"
        rm -rf "$TMP_ZIP" "$TMP_DIR"
    fi

    chmod -R 755 "$INSTALL_DIR"
    chmod +x "$INSTALL_DIR/main.py"
    print_ok "App-Dateien installiert"
}

# ── Install icon ─────────────────────────────────────────────
install_icon() {
    print_step "Installiere App-Icon..."

    mkdir -p "$ICON_DIR"

    if [ -f "$INSTALL_DIR/assets/icon.png" ]; then
        cp "$INSTALL_DIR/assets/icon.png" "$ICON_DIR/fisi-toolbox.png"
        # Also install smaller sizes if possible
        if command -v convert &>/dev/null; then
            for size in 16 32 48 64 128; do
                mkdir -p "/usr/share/icons/hicolor/${size}x${size}/apps"
                convert "$INSTALL_DIR/assets/icon.png" \
                    -resize "${size}x${size}" \
                    "/usr/share/icons/hicolor/${size}x${size}/apps/fisi-toolbox.png" 2>/dev/null || true
            done
        fi
        gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
        print_ok "Icon installiert"
    else
        print_warn "Icon nicht gefunden — übersprungen"
    fi
}

# ── Create launcher script ───────────────────────────────────
create_launcher() {
    print_step "Erstelle Launcher..."

    cat > "$BIN_LINK" << LAUNCHER
#!/bin/bash
cd "$INSTALL_DIR"
exec python3 "$INSTALL_DIR/main.py" "\$@"
LAUNCHER

    chmod +x "$BIN_LINK"
    print_ok "Launcher erstellt: $BIN_LINK"
}

# ── Create .desktop entry ─────────────────────────────────────
create_desktop_entry() {
    print_step "Erstelle Desktop-Eintrag..."

    cat > "$DESKTOP_FILE" << DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=FISI Toolbox
GenericName=IT Toolbox
Comment=All-in-one IT toolbox for FISI professionals
Exec=$BIN_LINK
Icon=fisi-toolbox
Terminal=false
Categories=Network;System;Utility;
Keywords=network;ping;port;hash;password;log;subnet;ssl;fisi;it;tools;
StartupNotify=true
StartupWMClass=fisi-toolbox
DESKTOP

    chmod 644 "$DESKTOP_FILE"

    # Update desktop database
    update-desktop-database /usr/share/applications/ 2>/dev/null || true

    print_ok "Desktop-Eintrag erstellt — App erscheint jetzt in der Systemsuche"
}

# ── Uninstaller ───────────────────────────────────────────────
create_uninstaller() {
    cat > "$INSTALL_DIR/uninstall.sh" << 'UNINSTALL'
#!/bin/bash
echo "Deinstalliere FISI Toolbox..."
rm -rf /opt/fisi-toolbox
rm -f /usr/share/applications/fisi-toolbox.desktop
rm -f /usr/local/bin/fisi-toolbox
rm -f /usr/share/icons/hicolor/256x256/apps/fisi-toolbox.png
update-desktop-database /usr/share/applications/ 2>/dev/null || true
gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
echo "✓ FISI Toolbox wurde deinstalliert."
UNINSTALL
    chmod +x "$INSTALL_DIR/uninstall.sh"
}

# ── Summary ───────────────────────────────────────────────────
print_summary() {
    echo ""
    echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║     Installation erfolgreich! ✓          ║${NC}"
    echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${BOLD}App starten:${NC}"
    echo -e "  • Terminal:      ${CYAN}fisi-toolbox${NC}"
    echo -e "  • App-Suche:     Nach ${CYAN}FISI Toolbox${NC} suchen"
    echo -e "  • Direkt:        ${CYAN}python3 $INSTALL_DIR/main.py${NC}"
    echo ""
    echo -e "  ${BOLD}Deinstallieren:${NC}"
    echo -e "  ${CYAN}sudo bash $INSTALL_DIR/uninstall.sh${NC}"
    echo ""
}

# ── Main ──────────────────────────────────────────────────────
main() {
    print_header
    check_root
    detect_distro
    install_dependencies
    install_python_deps
    install_app_files
    install_icon
    create_launcher
    create_desktop_entry
    create_uninstaller
    print_summary
}

main

#!/bin/bash
# =============================================================================
#  NightX v1.0.0 — Professional Web Penetration Testing Framework
#  Installer — Tested on Kali Linux 2024+
#  Fixes: pip externally-managed-environment error using Python venv
#  Usage: sudo bash install.sh
# =============================================================================

set -e

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Paths — everything is defined here, change only here ─────────────────────
SCRIPT_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd)"
INSTALL_DIR="/opt/nightx"
VENV_DIR="${INSTALL_DIR}/venv"
BIN_LINK="/usr/local/bin/nightx"
DESKTOP_FILE="/usr/share/applications/nightx.desktop"
ICON_SVG="${SCRIPT_DIR}/assets/nightx.svg"
LOG_FILE="/tmp/nightx_install.log"
REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(eval echo "~${REAL_USER}")

# ── Helpers ───────────────────────────────────────────────────────────────────
log()     { echo -e "${GREEN}[✓]${RESET} $1"; }
info()    { echo -e "${CYAN}[*]${RESET} $1"; }
warn()    { echo -e "${YELLOW}[!]${RESET} $1"; }
error()   {
    echo -e "${RED}[✗] ERROR: $1${RESET}"
    echo ""
    echo -e "${YELLOW}Full install log:${RESET}"
    cat "${LOG_FILE}" 2>/dev/null | tail -20
    exit 1
}
section() { echo -e "\n${BOLD}${BLUE}━━━ $1 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"; }

# ── Banner ────────────────────────────────────────────────────────────────────
print_banner() {
    clear
    echo ""
    echo -e "${BLUE}${BOLD}  ███╗   ██╗██╗ ██████╗ ██╗  ██╗████████╗██╗  ██╗${RESET}"
    echo -e "${BLUE}${BOLD}  ████╗  ██║██║██╔════╝ ██║  ██║╚══██╔══╝╚██╗██╔╝${RESET}"
    echo -e "${CYAN}${BOLD}  ██╔██╗ ██║██║██║  ███╗███████║   ██║    ╚███╔╝  ${RESET}"
    echo -e "${CYAN}${BOLD}  ██║╚██╗██║██║██║   ██║██╔══██║   ██║    ██╔██╗  ${RESET}"
    echo -e "${BLUE}${BOLD}  ██║ ╚████║██║╚██████╔╝██║  ██║   ██║   ██╔╝ ██╗ ${RESET}"
    echo -e "${BLUE}${BOLD}  ╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝${RESET}"
    echo ""
    echo -e "${BOLD}${CYAN}        NightX v1.0.0 — Web Penetration Testing Framework${RESET}"
    echo -e "${YELLOW}               FOR AUTHORIZED PENETRATION TESTING ONLY${RESET}"
    echo ""
    echo -e "  ${BOLD}Source :[/bold] ${CYAN}${SCRIPT_DIR}${RESET}"
    echo -e "  ${BOLD}Install:[/bold] ${CYAN}${INSTALL_DIR}${RESET}"
    echo -e "  ${BOLD}VEnv   :[/bold] ${CYAN}${VENV_DIR}${RESET}"
    echo -e "  ${BOLD}User   :[/bold] ${CYAN}${REAL_USER}${RESET}"
    echo ""
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 1 — Checks
# ═════════════════════════════════════════════════════════════════════════════
check_root() {
    section "Step 1 — Pre-flight Checks"
    if [[ $EUID -ne 0 ]]; then
        error "This installer must be run as root.\n  Use: sudo bash install.sh"
    fi
    log "Running as root"
}

check_python() {
    if ! command -v python3 &>/dev/null; then
        error "Python3 not found. Run: sudo apt install python3"
    fi
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
    if [[ ${PY_MINOR} -lt 9 ]]; then
        error "Python 3.9+ required. Found Python ${PY_VER}"
    fi
    log "Python ${PY_VER} found"
}

check_sources() {
    info "Checking source files in: ${SCRIPT_DIR}"

    [[ ! -f "${SCRIPT_DIR}/main.py" ]] && \
        error "main.py not found.\n  Make sure you run: sudo bash install.sh from INSIDE the nightx folder"

    [[ ! -d "${SCRIPT_DIR}/modules" ]] && \
        error "modules/ folder missing.\n  Re-clone: git clone https://github.com/hackops-academy/nightx.git"

    [[ ! -d "${SCRIPT_DIR}/utils" ]] && \
        error "utils/ folder missing.\n  Re-clone the repo."

    [[ ! -f "${ICON_SVG}" ]] && \
        error "Icon file not found: ${ICON_SVG}\n  Make sure assets/nightx.svg exists in the repo."

    MOD_COUNT=$(ls "${SCRIPT_DIR}/modules/"*.py 2>/dev/null | wc -l)
    UTL_COUNT=$(ls "${SCRIPT_DIR}/utils/"*.py 2>/dev/null | wc -l)

    log "main.py found"
    log "modules/ found — ${MOD_COUNT} Python files"
    log "utils/ found — ${UTL_COUNT} Python files"
    log "assets/nightx.svg found"
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 2 — System packages
# ═════════════════════════════════════════════════════════════════════════════
install_system_packages() {
    section "Step 2 — System Dependencies"
    info "Updating package list..."
    apt-get update -qq >> "${LOG_FILE}" 2>&1 || warn "apt-get update had issues — continuing"

    info "Installing: python3-venv python3-full git curl librsvg2-bin..."
    apt-get install -y \
        python3-venv \
        python3-full \
        python3-pip \
        git \
        curl \
        wget \
        librsvg2-bin \
        >> "${LOG_FILE}" 2>&1 || warn "Some packages had issues — continuing"

    log "System packages ready"
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 3 — Copy tool files FIRST (so INSTALL_DIR exists for venv)
# ═════════════════════════════════════════════════════════════════════════════
install_tool_files() {
    section "Step 3 — Installing NightX Files"

    # Remove any previous installation cleanly
    if [[ -d "${INSTALL_DIR}" ]]; then
        info "Removing old installation at ${INSTALL_DIR}..."
        rm -rf "${INSTALL_DIR}"
    fi

    # Create all needed directories
    mkdir -p \
        "${INSTALL_DIR}/modules" \
        "${INSTALL_DIR}/utils" \
        "${INSTALL_DIR}/assets" \
        "${INSTALL_DIR}/reports" \
        "${INSTALL_DIR}/wordlists"

    # Copy Python files
    cp "${SCRIPT_DIR}/main.py"           "${INSTALL_DIR}/main.py"
    cp "${SCRIPT_DIR}/modules/"*.py      "${INSTALL_DIR}/modules/"
    cp "${SCRIPT_DIR}/utils/"*.py        "${INSTALL_DIR}/utils/"

    # Copy assets (icon etc)
    cp -r "${SCRIPT_DIR}/assets/."       "${INSTALL_DIR}/assets/"

    # Copy optional files if they exist
    [[ -f "${SCRIPT_DIR}/README.md" ]]          && cp "${SCRIPT_DIR}/README.md"          "${INSTALL_DIR}/"
    [[ -f "${SCRIPT_DIR}/requirements.txt" ]]   && cp "${SCRIPT_DIR}/requirements.txt"   "${INSTALL_DIR}/"
    [[ -d "${SCRIPT_DIR}/wordlists" ]]          && cp -r "${SCRIPT_DIR}/wordlists/."     "${INSTALL_DIR}/wordlists/" 2>/dev/null || true

    # Set permissions
    chmod -R 755 "${INSTALL_DIR}"
    chmod 644 "${INSTALL_DIR}/modules/"*.py
    chmod 644 "${INSTALL_DIR}/utils/"*.py
    chmod 755 "${INSTALL_DIR}/main.py"

    log "All NightX files installed to ${INSTALL_DIR}"
    log "$(ls ${INSTALL_DIR}/modules/*.py | wc -l) module files"
    log "$(ls ${INSTALL_DIR}/utils/*.py | wc -l) utility files"
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 4 — Create venv AFTER files are copied (venv lives inside INSTALL_DIR)
# ═════════════════════════════════════════════════════════════════════════════
install_python_packages() {
    section "Step 4 — Python Virtual Environment & Packages"

    info "Creating virtual environment at ${VENV_DIR}..."
    # VENV_DIR is /opt/nightx/venv which now exists because install_tool_files ran first
    python3 -m venv "${VENV_DIR}" >> "${LOG_FILE}" 2>&1 || \
        error "Failed to create virtual environment.\n  Try: sudo apt install python3-venv python3-full"

    log "Virtual environment created"

    info "Upgrading pip inside venv..."
    "${VENV_DIR}/bin/pip" install --upgrade pip --quiet >> "${LOG_FILE}" 2>&1 || \
        warn "pip upgrade had issues — continuing"

    info "Installing Python packages: typer rich httpx beautifulsoup4..."
    "${VENV_DIR}/bin/pip" install --quiet \
        "typer>=0.9.0" \
        "rich>=13.0.0" \
        "httpx>=0.25.0" \
        "beautifulsoup4>=4.12.0" \
        >> "${LOG_FILE}" 2>&1 || \
        error "pip install failed.\n  Check log: cat ${LOG_FILE}"

    # Verify packages installed
    PKG_COUNT=$("${VENV_DIR}/bin/pip" list 2>/dev/null | grep -cE "^(typer|rich|httpx|beautifulsoup4)" || echo 0)
    log "Python packages installed — ${PKG_COUNT}/4 verified"
    log "Using: ${VENV_DIR}/bin/python3"
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 5 — Icons
# ═════════════════════════════════════════════════════════════════════════════
install_icons() {
    section "Step 5 — Installing Icons"

    local SIZES=(16 22 24 32 48 64 96 128 256)
    local DONE=0

    for SZ in "${SIZES[@]}"; do
        local DEST="/usr/share/icons/hicolor/${SZ}x${SZ}/apps"
        mkdir -p "${DEST}"

        if command -v rsvg-convert &>/dev/null; then
            rsvg-convert -w "${SZ}" -h "${SZ}" "${ICON_SVG}" \
                -o "${DEST}/nightx.png" >> "${LOG_FILE}" 2>&1 && DONE=$((DONE+1))
        elif command -v inkscape &>/dev/null; then
            inkscape \
                --export-filename="${DEST}/nightx.png" \
                --export-width="${SZ}" \
                --export-height="${SZ}" \
                "${ICON_SVG}" >> "${LOG_FILE}" 2>&1 && DONE=$((DONE+1))
        elif command -v convert &>/dev/null; then
            convert -background none -resize "${SZ}x${SZ}" \
                "${ICON_SVG}" "${DEST}/nightx.png" >> "${LOG_FILE}" 2>&1 && DONE=$((DONE+1))
        fi
    done

    # Scalable SVG (used by modern desktops — scales to any size perfectly)
    mkdir -p /usr/share/icons/hicolor/scalable/apps
    cp "${ICON_SVG}" /usr/share/icons/hicolor/scalable/apps/nightx.svg
    log "Scalable SVG icon installed"

    # Pixmaps fallback (used by some older Kali desktop versions)
    mkdir -p /usr/share/pixmaps
    if command -v rsvg-convert &>/dev/null; then
        rsvg-convert -w 64 -h 64 "${ICON_SVG}" \
            -o /usr/share/pixmaps/nightx.png >> "${LOG_FILE}" 2>&1 && \
            log "Pixmaps fallback icon installed"
    elif command -v convert &>/dev/null; then
        convert -background none -resize "64x64" \
            "${ICON_SVG}" /usr/share/pixmaps/nightx.png >> "${LOG_FILE}" 2>&1 && \
            log "Pixmaps fallback icon installed"
    fi

    # Refresh Kali's icon cache so the icon appears immediately
    if gtk-update-icon-cache -f -t /usr/share/icons/hicolor/ >> "${LOG_FILE}" 2>&1; then
        log "Icon cache refreshed — ${DONE} PNG sizes + scalable SVG installed"
    else
        warn "Icon cache refresh had issues — icon may appear after logout/login"
    fi
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 6 — Desktop entry (app menu)
# ═════════════════════════════════════════════════════════════════════════════
install_desktop_entry() {
    section "Step 6 — Registering in Kali App Menu"

    cat > "${DESKTOP_FILE}" << 'DESKTOPEOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=NightX
GenericName=Web Penetration Testing
Comment=Professional Web Penetration Testing Framework — NightX v1.0.0
Exec=bash -c '/opt/nightx/venv/bin/python3 /opt/nightx/main.py --help; exec bash'
Icon=nightx
Terminal=true
StartupNotify=true
Categories=Network;Security;System;
Keywords=pentest;security;web;scanner;vulnerability;nightx;recon;hacking;sqli;xss;
Actions=FullScan;VulnScan;HeadersCheck;Fingerprint;SubdomainEnum;APITest;ListScans;

[Desktop Action FullScan]
Name=Full Penetration Scan
Exec=bash -c 'clear; echo ""; read -p "  NightX > Target URL: " T; /opt/nightx/venv/bin/python3 /opt/nightx/main.py scan "$T" -v; read -p "  Done. Press Enter to close..."; exec bash'
Terminal=true

[Desktop Action VulnScan]
Name=Vulnerability Scan
Exec=bash -c 'clear; echo ""; read -p "  NightX > Target URL: " T; /opt/nightx/venv/bin/python3 /opt/nightx/main.py vuln "$T" -v; read -p "  Done. Press Enter to close..."; exec bash'
Terminal=true

[Desktop Action HeadersCheck]
Name=Security Headers Check
Exec=bash -c 'clear; echo ""; read -p "  NightX > Target URL: " T; /opt/nightx/venv/bin/python3 /opt/nightx/main.py headers "$T" -v; read -p "  Done. Press Enter to close..."; exec bash'
Terminal=true

[Desktop Action Fingerprint]
Name=Web Fingerprinting
Exec=bash -c 'clear; echo ""; read -p "  NightX > Target URL: " T; /opt/nightx/venv/bin/python3 /opt/nightx/main.py fingerprint "$T" -v; read -p "  Done. Press Enter to close..."; exec bash'
Terminal=true

[Desktop Action SubdomainEnum]
Name=Subdomain Enumeration
Exec=bash -c 'clear; echo ""; read -p "  NightX > Domain (e.g. example.com): " T; /opt/nightx/venv/bin/python3 /opt/nightx/main.py subdomains "$T" -v; read -p "  Done. Press Enter to close..."; exec bash'
Terminal=true

[Desktop Action APITest]
Name=API Security Testing
Exec=bash -c 'clear; echo ""; read -p "  NightX > Target URL: " T; /opt/nightx/venv/bin/python3 /opt/nightx/main.py api "$T" -v; read -p "  Done. Press Enter to close..."; exec bash'
Terminal=true

[Desktop Action ListScans]
Name=View Scan History
Exec=bash -c 'clear; /opt/nightx/venv/bin/python3 /opt/nightx/main.py list-scans; read -p "  Press Enter to close..."; exec bash'
Terminal=true
DESKTOPEOF

    chmod 644 "${DESKTOP_FILE}"

    # Register with Kali's app menu database
    update-desktop-database /usr/share/applications/ >> "${LOG_FILE}" 2>&1 && \
        log "App menu database updated"

    # Force desktop environment refresh
    xdg-desktop-menu forceupdate >> "${LOG_FILE}" 2>&1 || true

    log "NightX registered in Applications → Network / Security"
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 7 — Global terminal command
# ═════════════════════════════════════════════════════════════════════════════
create_global_command() {
    section "Step 7 — Creating Global Terminal Command"

    rm -f "${BIN_LINK}"

    # This launcher uses the venv python — bypasses all system pip issues
    cat > "${BIN_LINK}" << 'CMDEOF'
#!/bin/bash
exec /opt/nightx/venv/bin/python3 /opt/nightx/main.py "$@"
CMDEOF

    chmod +x "${BIN_LINK}"
    log "Global command created: nightx"
    log "Location: ${BIN_LINK}"
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 8 — Shell aliases
# ═════════════════════════════════════════════════════════════════════════════
add_shell_aliases() {
    section "Step 8 — Adding Shell Aliases"

    local ALIAS_BLOCK='
# ── NightX ────────────────────────────────────────────────
alias nightx-scan="/opt/nightx/venv/bin/python3 /opt/nightx/main.py scan"
alias nightx-vuln="/opt/nightx/venv/bin/python3 /opt/nightx/main.py vuln"
alias nightx-subs="/opt/nightx/venv/bin/python3 /opt/nightx/main.py subdomains"
alias nightx-headers="/opt/nightx/venv/bin/python3 /opt/nightx/main.py headers"
alias nightx-api="/opt/nightx/venv/bin/python3 /opt/nightx/main.py api"
alias nightx-fp="/opt/nightx/venv/bin/python3 /opt/nightx/main.py fingerprint"
alias nightx-history="/opt/nightx/venv/bin/python3 /opt/nightx/main.py list-scans"
# ──────────────────────────────────────────────────────────'

    # System-wide bashrc
    if ! grep -q "NightX" /etc/bash.bashrc 2>/dev/null; then
        echo "${ALIAS_BLOCK}" >> /etc/bash.bashrc
        log "Aliases added to /etc/bash.bashrc"
    else
        log "Aliases already present in /etc/bash.bashrc"
    fi

    # User's own shell configs
    for RCFILE in "${REAL_HOME}/.bashrc" "${REAL_HOME}/.zshrc"; do
        if [[ -f "${RCFILE}" ]] && ! grep -q "NightX" "${RCFILE}" 2>/dev/null; then
            echo "${ALIAS_BLOCK}" >> "${RCFILE}"
            log "Aliases added to ${RCFILE}"
        fi
    done
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 9 — Data directories
# ═════════════════════════════════════════════════════════════════════════════
setup_data_dirs() {
    section "Step 9 — Setting Up Data Directories"
    mkdir -p "${REAL_HOME}/.nightx/reports"
    chown -R "${REAL_USER}":"${REAL_USER}" "${REAL_HOME}/.nightx" 2>/dev/null || true
    log "Reports directory : ${REAL_HOME}/.nightx/reports/"
    log "Scan history DB   : ${REAL_HOME}/.nightx/scans.db  (created on first scan)"
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 10 — Uninstaller
# ═════════════════════════════════════════════════════════════════════════════
create_uninstaller() {
    cat > "${INSTALL_DIR}/uninstall.sh" << 'UNEOF'
#!/bin/bash
echo ""
echo "  Uninstalling NightX..."
rm -rf /opt/nightx
rm -f /usr/local/bin/nightx
rm -f /usr/share/applications/nightx.desktop
rm -f /usr/share/icons/hicolor/scalable/apps/nightx.svg
rm -f /usr/share/pixmaps/nightx.png
for SZ in 16 22 24 32 48 64 96 128 256; do
    rm -f "/usr/share/icons/hicolor/${SZ}x${SZ}/apps/nightx.png"
done
gtk-update-icon-cache -f -t /usr/share/icons/hicolor/ 2>/dev/null || true
update-desktop-database /usr/share/applications/ 2>/dev/null || true
sed -i '/── NightX ──/,/──────────────────────────────────────────────────────────/d' \
    /etc/bash.bashrc 2>/dev/null || true
echo "  ✓ NightX has been removed."
echo "  Your scan reports in ~/.nightx/ have been kept."
echo ""
UNEOF
    chmod +x "${INSTALL_DIR}/uninstall.sh"
    log "Uninstaller created: sudo bash /opt/nightx/uninstall.sh"
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 11 — Verify everything works
# ═════════════════════════════════════════════════════════════════════════════
verify_installation() {
    section "Step 11 — Verifying Installation"

    # Test 1: venv python runs the tool
    if "${VENV_DIR}/bin/python3" /opt/nightx/main.py --help > /dev/null 2>&1; then
        log "Tool runs correctly via venv Python"
    else
        error "Tool failed to run.\n  Try running manually:\n  ${VENV_DIR}/bin/python3 /opt/nightx/main.py --help"
    fi

    # Test 2: global command exists and is executable
    if [[ -x "${BIN_LINK}" ]]; then
        log "Global command works: nightx"
    else
        warn "Global command issue at ${BIN_LINK}"
    fi

    # Test 3: desktop file exists
    if [[ -f "${DESKTOP_FILE}" ]]; then
        log "Desktop entry exists: ${DESKTOP_FILE}"
    else
        warn "Desktop entry missing"
    fi

    # Test 4: icon installed
    if [[ -f "/usr/share/icons/hicolor/scalable/apps/nightx.svg" ]]; then
        log "Icon installed in system theme"
    else
        warn "Scalable icon missing — may not show in app menu"
    fi

    # Test 5: venv packages
    local PKG_COUNT
    PKG_COUNT=$("${VENV_DIR}/bin/pip" list 2>/dev/null | grep -cE "^(typer|rich|httpx|beautifulsoup4)" || echo 0)
    log "Venv packages verified: ${PKG_COUNT}/4"
}

# ═════════════════════════════════════════════════════════════════════════════
# Final success message
# ═════════════════════════════════════════════════════════════════════════════
print_success() {
    echo ""
    echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo -e "${GREEN}${BOLD}   ✅  NightX v1.0.0 Installed Successfully!${RESET}"
    echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo ""
    echo -e "${BOLD}${CYAN}  ── Use in terminal right now ──────────────────────────${RESET}"
    echo -e "  ${BOLD}nightx --help${RESET}"
    echo -e "  ${BOLD}nightx scan https://target.com${RESET}"
    echo -e "  ${BOLD}nightx headers https://target.com${RESET}"
    echo -e "  ${BOLD}nightx vuln https://target.com${RESET}"
    echo -e "  ${BOLD}nightx subdomains target.com${RESET}"
    echo -e "  ${BOLD}nightx api https://target.com${RESET}"
    echo -e "  ${BOLD}nightx fingerprint https://target.com${RESET}"
    echo -e "  ${BOLD}nightx list-scans${RESET}"
    echo ""
    echo -e "${BOLD}${CYAN}  ── Desktop App ─────────────────────────────────────────${RESET}"
    echo -e "  ${YELLOW}Applications → Kali Linux → Web Application Analysis → NightX${RESET}"
    echo -e "  ${YELLOW}Applications → Network → NightX${RESET}"
    echo -e "  Right-click the icon for 7 quick-action scan shortcuts"
    echo ""
    echo -e "${BOLD}${CYAN}  ── Icon not visible yet? ───────────────────────────────${RESET}"
    echo -e "  Run: ${BOLD}xdg-desktop-menu forceupdate${RESET}"
    echo -e "  Or:  Log out and log back in"
    echo ""
    echo -e "${BOLD}${CYAN}  ── File locations ──────────────────────────────────────${RESET}"
    echo -e "  Tool    : ${YELLOW}/opt/nightx/${RESET}"
    echo -e "  VEnv    : ${YELLOW}/opt/nightx/venv/${RESET}"
    echo -e "  Command : ${YELLOW}/usr/local/bin/nightx${RESET}"
    echo -e "  Reports : ${YELLOW}${REAL_HOME}/.nightx/reports/${RESET}"
    echo -e "  History : ${YELLOW}${REAL_HOME}/.nightx/scans.db${RESET}"
    echo ""
    echo -e "${BOLD}${CYAN}  ── Uninstall ────────────────────────────────────────────${RESET}"
    echo -e "  ${BOLD}sudo bash /opt/nightx/uninstall.sh${RESET}"
    echo ""
    echo -e "${RED}  ⚠  For authorized penetration testing only${RESET}"
    echo ""
}

# ═════════════════════════════════════════════════════════════════════════════
# MAIN — Run all steps in correct order
# ═════════════════════════════════════════════════════════════════════════════
main() {
    # Clear log file
    > "${LOG_FILE}"

    print_banner
    check_root
    check_python
    check_sources

    # IMPORTANT ORDER:
    # 1. Install system packages first
    # 2. Copy tool files (creates /opt/nightx/)
    # 3. Create venv INSIDE /opt/nightx/venv/ (after dir exists)
    # 4. Install packages into venv
    install_system_packages
    install_tool_files          # Creates /opt/nightx/
    install_python_packages     # Creates /opt/nightx/venv/ AFTER dir exists

    install_icons
    install_desktop_entry
    create_global_command
    add_shell_aliases
    setup_data_dirs
    create_uninstaller
    verify_installation
    print_success
}

main "$@"

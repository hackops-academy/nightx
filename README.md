<div align="center">

```
 ███╗   ██╗██╗ ██████╗ ██╗  ██╗████████╗██╗  ██╗
 ████╗  ██║██║██╔════╝ ██║  ██║╚══██╔══╝╚██╗██╔╝
 ██╔██╗ ██║██║██║  ███╗███████║   ██║    ╚███╔╝
 ██║╚██╗██║██║██║   ██║██╔══██║   ██║    ██╔██╗
 ██║ ╚████║██║╚██████╔╝██║  ██║   ██║   ██╔╝ ██╗
 ╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
```

### Professional Web Penetration Testing Framework

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-557C94?style=for-the-badge&logo=linux&logoColor=white)](https://kali.org)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-6366f1?style=for-the-badge)]()

> One tool. Every phase. Professional reports.

**⚠️ FOR AUTHORIZED PENETRATION TESTING ONLY ⚠️**

</div>

---

## ⚙️ Installation

```bash
git clone https://github.com/hackops-academy/nightx.git
cd nightx
sudo bash install.sh
```

Done. The installer handles everything automatically.

---

## 🚀 Usage

```bash
nightx --help
nightx scan https://target.com
nightx scan https://target.com -v -t 20
nightx headers https://target.com
nightx vuln https://target.com
nightx subdomains target.com
nightx fingerprint https://target.com
nightx api https://target.com
nightx list-scans
```

---

## 📋 Commands

| Command | Description |
|---------|-------------|
| `scan` | Full pentest — all 6 modules |
| `headers` | Security headers + score/100 |
| `vuln` | SQLi · XSS · SSRF · CORS · CMDi |
| `subdomains` | DNS brute-force + crt.sh |
| `fingerprint` | CMS · WAF · Frameworks · Paths |
| `api` | IDOR · GraphQL · Mass assignment |
| `list-scans` | View scan history |

---

## 🔍 scan — All Flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--output PATH` | `-o` | `./reports` | Report save directory |
| `--threads INT` | `-t` | `10` | Concurrent threads |
| `--wordlist PATH` | `-w` | built-in | Subdomain wordlist |
| `--format [html\|json\|txt]` | `-f` | `html` | Report format |
| `--verbose` | `-v` | off | Detailed output |
| `--skip-subdomains` | — | off | Skip subdomain phase |
| `--skip-vuln` | — | off | Skip vuln scan phase |
| `--skip-auth` | — | off | Skip auth test phase |
| `--skip-api` | — | off | Skip API test phase |

---

## 💡 Examples

```bash
# Full verbose scan
nightx scan https://target.com -v -t 20

# JSON report
nightx scan https://target.com -f json -o ~/reports

# Skip slow subdomain phase
nightx scan https://target.com --skip-subdomains -t 30

# Recon only
nightx scan https://target.com --skip-vuln --skip-auth --skip-api

# Subdomain enum with SecLists
nightx subdomains target.com \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  -t 100 -o subs.txt

# Legal practice target
nightx scan http://testphp.vulnweb.com --skip-subdomains -v
```

---

## 🧩 Modules

| Module | Detects |
|--------|---------|
| **headers** | HSTS · CSP · X-Frame-Options · X-Content-Type-Options · Referrer-Policy · Permissions-Policy · COOP · CORP · COEP · Cookie flags · Info-disclosure |
| **subdomains** | DNS brute-force · crt.sh CT logs · Live host detection · IP resolution |
| **fingerprint** | WordPress/Drupal/Joomla · Cloudflare/Akamai/Imperva/ModSecurity · React/Angular/Vue/Laravel/Django · 40+ sensitive paths |
| **vuln** | SQL Injection · XSS · Open Redirect · SSRF · Path Traversal · Command Injection · CORS · Clickjacking |
| **auth** | Default creds · JWT attacks · Session entropy · Brute-force protection |
| **api** | Swagger exposure · IDOR · GraphQL introspection · Mass assignment · Broken auth |

---

## 📁 Structure

```
nightx/
├── main.py                 ← CLI entry point
├── install.sh              ← One-command installer
├── requirements.txt
├── nightx.desktop          ← Desktop app entry
├── assets/
│   └── nightx.svg          ← App icon
├── modules/
│   ├── header_checker.py
│   ├── subdomain_enum.py
│   ├── fingerprint.py
│   ├── vuln_scanner.py
│   ├── auth_tester.py
│   ├── api_tester.py
│   └── reporter.py
└── utils/
    ├── db.py
    └── logger.py
```

---

## 🗑️ Uninstall

```bash
sudo bash /opt/nightx/uninstall.sh
```

---

## ⚖️ Legal

NightX is for authorized security testing only. Only test systems you own or have explicit written permission to test. Unauthorized use is illegal.

---

<div align="center">

**NightX v1.0.0** · Built by [HackOps Academy](https://github.com/hackops-academy) · MIT License

</div>

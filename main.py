#!/usr/bin/env python3
"""
NightX - Professional Web Penetration Testing Framework
Author  : HackOps Academy
GitHub  : https://github.com/hackops-academy/nightx
Version : 1.0.0
License : MIT
"""
import asyncio, sys, os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# ── Intercept --help / no args BEFORE typer so we show our custom menu ────────
if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ("--help", "-h", "help")):
    from rich.console import Console
    from rich.panel   import Panel
    from rich.table   import Table
    from rich         import box
    c = Console()

    BANNER = """\
 ███╗   ██╗██╗ ██████╗ ██╗  ██╗████████╗██╗  ██╗
 ████╗  ██║██║██╔════╝ ██║  ██║╚══██╔══╝╚██╗██╔╝
 ██╔██╗ ██║██║██║  ███╗███████║   ██║    ╚███╔╝ 
 ██║╚██╗██║██║██║   ██║██╔══██║   ██║    ██╔██╗ 
 ██║ ╚████║██║╚██████╔╝██║  ██║   ██║   ██╔╝ ██╗
 ╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝"""

    c.print(f"\n[bold #6366f1]{BANNER}[/bold #6366f1]")
    c.print(Panel(
        "[bold green]v1.0.0[/bold green]  [dim]│[/dim]  "
        "[#a5b4fc]Professional Web Penetration Testing Framework[/#a5b4fc]  "
        "[dim]│[/dim]  [yellow]⚠ Authorized Testing Only[/yellow]  "
        "[dim]│[/dim]  [dim]github.com/hackops-academy/nightx[/dim]",
        border_style="#6366f1", padding=(0,2)))
    c.print()

    # About
    c.print(Panel(
        "[white]NightX is a modular, async web penetration testing framework.\n"
        "It combines recon · fingerprinting · vuln scanning · auth testing · API auditing\n"
        "into one tool with professional HTML / JSON / TXT reports.[/white]",
        title="[bold #a5b4fc]About[/bold #a5b4fc]",
        border_style="#4338ca", padding=(0,2)))
    c.print()

    # Commands
    ct = Table(box=box.ROUNDED, border_style="#6366f1", header_style="bold #6366f1",
               title="[bold #6366f1]⚡ Commands[/bold #6366f1]",
               title_justify="left", padding=(0,1), show_lines=True, min_width=88)
    ct.add_column("Command",      style="bold #a5b4fc", min_width=14, no_wrap=True)
    ct.add_column("Description",  style="white",        min_width=48)
    ct.add_column("Example",      style="dim yellow",   min_width=36)
    ct.add_row("scan",        "Full pentest — runs ALL 6 modules in sequence",       "nightx scan https://target.com")
    ct.add_row("headers",     "Security headers check + cookie audit + score/100",   "nightx headers https://target.com")
    ct.add_row("vuln",        "SQLi · XSS · SSRF · CORS · Path Traversal · CMDi",   "nightx vuln https://target.com")
    ct.add_row("subdomains",  "DNS brute-force + certificate transparency (crt.sh)", "nightx subdomains target.com")
    ct.add_row("fingerprint", "CMS · WAF · Frameworks · 40+ sensitive path checks", "nightx fingerprint https://target.com")
    ct.add_row("api",         "IDOR · GraphQL · Mass assignment · Broken auth",      "nightx api https://target.com")
    ct.add_row("list-scans",  "View all previous scans from local database",         "nightx list-scans")
    c.print(ct)
    c.print()

    # Scan flags
    sf = Table(box=box.SIMPLE_HEAVY, border_style="yellow", header_style="bold yellow",
               title="[bold yellow]🔍 nightx scan — Flags[/bold yellow]",
               title_justify="left", padding=(0,1), show_lines=True, min_width=88)
    sf.add_column("Flag",                  style="bold green", min_width=26, no_wrap=True)
    sf.add_column("Short",                 style="#a5b4fc",    min_width=6,  no_wrap=True)
    sf.add_column("Default",              style="dim",        min_width=12)
    sf.add_column("Description",          style="white",      min_width=42)
    sf.add_row("--output PATH",           "-o", "./reports", "Directory to save the report")
    sf.add_row("--threads INT",           "-t", "10",        "Number of concurrent threads")
    sf.add_row("--wordlist PATH",         "-w", "built-in",  "Custom subdomain wordlist file")
    sf.add_row("--format [html|json|txt]","-f", "html",      "Report output format")
    sf.add_row("--verbose",               "-v", "off",       "Show detailed output for every phase")
    sf.add_row("--skip-subdomains",       "—",  "off",       "Skip subdomain enumeration phase")
    sf.add_row("--skip-vuln",             "—",  "off",       "Skip vulnerability scanning phase")
    sf.add_row("--skip-auth",             "—",  "off",       "Skip authentication testing phase")
    sf.add_row("--skip-api",              "—",  "off",       "Skip API security testing phase")
    c.print(sf)
    c.print()

    # Other flags
    of = Table(box=box.SIMPLE_HEAVY, border_style="#a5b4fc", header_style="bold #a5b4fc",
               title="[bold #a5b4fc]🔧 Other Commands — Flags[/bold #a5b4fc]",
               title_justify="left", padding=(0,1), show_lines=True, min_width=88)
    of.add_column("Command",     style="bold #a5b4fc", min_width=14, no_wrap=True)
    of.add_column("Flag",        style="bold green",   min_width=20, no_wrap=True)
    of.add_column("Short",       style="#a5b4fc",      min_width=6,  no_wrap=True)
    of.add_column("Default",     style="dim",          min_width=10)
    of.add_column("Description", style="white",        min_width=34)
    of.add_row("subdomains","--threads INT",   "-t","20",      "Concurrent DNS threads")
    of.add_row("subdomains","--wordlist PATH", "-w","built-in","Custom wordlist path")
    of.add_row("subdomains","--output PATH",   "-o","none",    "Save results to file")
    of.add_row("subdomains","--verbose",       "-v","off",     "Show every attempt")
    of.add_row("──────────","─────────────────","─", "────────","──────────────────────────────────")
    of.add_row("vuln",      "--threads INT",   "-t","10",      "Concurrent request threads")
    of.add_row("vuln",      "--verbose",       "-v","off",     "Show all payloads tested")
    of.add_row("──────────","─────────────────","─", "────────","──────────────────────────────────")
    of.add_row("headers",   "--verbose",       "-v","off",     "Show full header value details")
    of.add_row("──────────","─────────────────","─", "────────","──────────────────────────────────")
    of.add_row("fingerprint","--verbose",      "-v","off",     "Show every path probe attempt")
    of.add_row("──────────","─────────────────","─", "────────","──────────────────────────────────")
    of.add_row("api",       "--spec URL/PATH", "-s","auto",    "OpenAPI/Swagger spec URL or path")
    of.add_row("api",       "--verbose",       "-v","off",     "Show all API test details")
    c.print(of)
    c.print()

    # Examples
    c.print(Panel(
        "[dim]# Full scan — verbose, 20 threads[/dim]\n"
        "[bold green]nightx scan https://target.com -v -t 20[/bold green]\n\n"
        "[dim]# Full scan — JSON report to custom folder[/dim]\n"
        "[bold green]nightx scan https://target.com -f json -o ~/reports[/bold green]\n\n"
        "[dim]# Fast scan — skip subdomains (slowest phase)[/dim]\n"
        "[bold green]nightx scan https://target.com --skip-subdomains -t 30[/bold green]\n\n"
        "[dim]# Recon only — no vuln/auth/api[/dim]\n"
        "[bold green]nightx scan https://target.com --skip-vuln --skip-auth --skip-api[/bold green]\n\n"
        "[dim]# Subdomain enum with SecLists[/dim]\n"
        "[bold green]nightx subdomains target.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -t 100[/bold green]\n\n"
        "[dim]# Vulnerability scan only[/dim]\n"
        "[bold green]nightx vuln https://target.com -v -t 15[/bold green]\n\n"
        "[dim]# Security headers check[/dim]\n"
        "[bold green]nightx headers https://target.com -v[/bold green]\n\n"
        "[dim]# API test with Swagger spec[/dim]\n"
        "[bold green]nightx api https://target.com -s https://target.com/swagger.json -v[/bold green]\n\n"
        "[dim]# Legal practice target[/dim]\n"
        "[bold green]nightx scan http://testphp.vulnweb.com --skip-subdomains -v[/bold green]",
        title="[bold green]💡 Examples[/bold green]",
        border_style="green", padding=(1,2)))
    c.print()

    # Modules
    mt = Table(box=box.ROUNDED, border_style="dim", header_style="bold white",
               title="[bold white]🧩 What Each Module Detects[/bold white]",
               title_justify="left", padding=(0,1), show_lines=True, min_width=88)
    mt.add_column("Module",   style="bold #a5b4fc", min_width=14, no_wrap=True)
    mt.add_column("Detects",  style="white",        min_width=70)
    mt.add_row("headers",     "HSTS · CSP · X-Frame-Options · X-Content-Type-Options · Referrer-Policy · Permissions-Policy · COOP · CORP · COEP · Cookie flags · Info-disclosure headers")
    mt.add_row("subdomains",  "DNS brute-force (100+ built-in) · crt.sh CT logs · Live host detection · IP resolution · HTTP status")
    mt.add_row("fingerprint", "CMS: WordPress/Drupal/Joomla/Magento/Shopify · WAF: Cloudflare/Akamai/Imperva/Sucuri/ModSecurity/F5 · Frameworks: React/Angular/Vue/Laravel/Django · 40+ sensitive paths")
    mt.add_row("vuln",        "SQL Injection · Reflected XSS · Open Redirect · SSRF · Path Traversal · Command Injection · CORS Misconfiguration · Clickjacking")
    mt.add_row("auth",        "20 default credential pairs · JWT: alg:none/weak-secret/no-expiry · Session entropy · Brute-force protection · CAPTCHA detection")
    mt.add_row("api",         "Swagger/OpenAPI exposure · IDOR · GraphQL introspection · Mass assignment · Broken auth · Unauthenticated access · Verbose errors")
    c.print(mt)
    c.print()

    # Reports & Legal
    c.print(Panel(
        "[bold]HTML[/bold]  [#a5b4fc]-f html[/#a5b4fc] [dim](default)[/dim]  Dark-themed professional report · open in any browser\n"
        "[bold]JSON[/bold]  [#a5b4fc]-f json[/#a5b4fc]              Machine-readable · integrate with other tools\n"
        "[bold]TXT [/bold]  [#a5b4fc]-f txt [/#a5b4fc]              Plain text summary\n\n"
        "[dim]Reports:[/dim] [yellow]./reports/[/yellow]   "
        "[dim]History:[/dim] [yellow]~/.nightx/scans.db[/yellow]   "
        "[dim]Uninstall:[/dim] [yellow]sudo bash /opt/nightx/uninstall.sh[/yellow]",
        title="[bold #6366f1]📄 Reports & Info[/bold #6366f1]",
        border_style="#4338ca", padding=(0,2)))
    c.print()

    c.print(Panel(
        "[bold red]⚠  FOR AUTHORIZED PENETRATION TESTING ONLY[/bold red]\n"
        "[dim]Only test systems you own or have explicit written permission to test.\n"
        "Unauthorized scanning is illegal under CFAA, Computer Misuse Act and similar laws.[/dim]\n\n"
        "[dim]Legal practice targets:[/dim]\n"
        "  [#a5b4fc]http://testphp.vulnweb.com[/#a5b4fc]   Acunetix intentionally vulnerable site\n"
        "  [#a5b4fc]https://hackthebox.com[/#a5b4fc]       Professional CTF lab environment\n"
        "  [#a5b4fc]https://tryhackme.com[/#a5b4fc]        Beginner-friendly guided labs\n"
        "  [#a5b4fc]http://localhost/dvwa[/#a5b4fc]        DVWA — local vulnerable web app",
        title="[bold red]⚖  Legal Notice[/bold red]",
        border_style="red", padding=(0,2)))
    c.print()
    sys.exit(0)

# ── Version flag ──────────────────────────────────────────────────────────────
if len(sys.argv) == 2 and sys.argv[1] in ("--version", "-V"):
    from rich.console import Console
    Console().print("[bold #6366f1]NightX[/bold #6366f1] [bold green]v1.0.0[/bold green]")
    sys.exit(0)

# ── Normal imports (only when actually running a command) ─────────────────────
import typer
from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table
from rich         import box

from modules.subdomain_enum import SubdomainEnumerator
from modules.fingerprint    import WebFingerprinter
from modules.vuln_scanner   import VulnerabilityScanner
from modules.auth_tester    import AuthTester
from modules.api_tester     import APITester
from modules.reporter       import ReportGenerator
from modules.header_checker import HeaderChecker
from utils.db               import Database
from utils.logger           import setup_logger

console = Console()
logger  = setup_logger()

app = typer.Typer(
    name="nightx",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=False,
    rich_markup_mode=None,
)

BANNER = """\
 ███╗   ██╗██╗ ██████╗ ██╗  ██╗████████╗██╗  ██╗
 ████╗  ██║██║██╔════╝ ██║  ██║╚══██╔══╝╚██╗██╔╝
 ██╔██╗ ██║██║██║  ███╗███████║   ██║    ╚███╔╝ 
 ██║╚██╗██║██║██║   ██║██╔══██║   ██║    ██╔██╗ 
 ██║ ╚████║██║╚██████╔╝██║  ██║   ██║   ██╔╝ ██╗
 ╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝"""

def print_banner():
    console.print(f"\n[bold #6366f1]{BANNER}[/bold #6366f1]")
    console.print(Panel(
        "[bold green]v1.0.0[/bold green]  [dim]│[/dim]  "
        "[#a5b4fc]Professional Web Penetration Testing Framework[/#a5b4fc]  "
        "[dim]│[/dim]  [yellow]⚠ Authorized Testing Only[/yellow]  "
        "[dim]│[/dim]  [dim]github.com/hackops-academy/nightx[/dim]",
        border_style="#6366f1", padding=(0,2)))
    console.print()

def normalize(target: str) -> str:
    if not target.startswith(("http://","https://")):
        return f"https://{target}"
    return target

@app.callback()
def root(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        raise typer.Exit()

# ══ scan ══════════════════════════════════════════════════════════════════════
@app.command("scan", help="Run a full penetration test — all 6 modules — against the target.")
def full_scan(
    target:          str  = typer.Argument(..., metavar="TARGET"),
    output:          str  = typer.Option("./reports","--output",         "-o"),
    threads:         int  = typer.Option(10,        "--threads",         "-t"),
    wordlist:        str  = typer.Option(None,      "--wordlist",        "-w"),
    report_format:   str  = typer.Option("html",    "--format",          "-f"),
    verbose:         bool = typer.Option(False,     "--verbose",         "-v"),
    skip_subdomains: bool = typer.Option(False,     "--skip-subdomains"     ),
    skip_vuln:       bool = typer.Option(False,     "--skip-vuln"           ),
    skip_auth:       bool = typer.Option(False,     "--skip-auth"           ),
    skip_api:        bool = typer.Option(False,     "--skip-api"            ),
):
    print_banner()
    target = normalize(target)
    cfg = Table(box=box.SIMPLE, show_header=False, padding=(0,1))
    cfg.add_column(style="bold green", min_width=14)
    cfg.add_column(style="#a5b4fc")
    cfg.add_row("🎯 Target",  target)
    cfg.add_row("📁 Output",  output)
    cfg.add_row("🧵 Threads", str(threads))
    cfg.add_row("📄 Format",  report_format)
    cfg.add_row("🔍 Verbose", "yes" if verbose else "no")
    skipped = [s for s,f in [("subdomains",skip_subdomains),("vuln",skip_vuln),
                               ("auth",skip_auth),("api",skip_api)] if f]
    if skipped: cfg.add_row("⏭  Skipping", ", ".join(skipped))
    console.print(Panel(cfg, title="[bold yellow]Scan Configuration[/bold yellow]", border_style="yellow"))
    console.print()

    db      = Database()
    scan_id = db.create_scan(target)
    results = {
        "target":target,"scan_id":scan_id,"start_time":datetime.now().isoformat(),
        "subdomains":[],"fingerprint":{},"vulnerabilities":[],
        "auth_findings":[],"api_findings":[],"header_findings":[],
    }
    asyncio.run(_run(target,results,db,scan_id,threads,wordlist,
                     skip_subdomains,skip_vuln,skip_auth,skip_api,
                     verbose,output,report_format))

async def _run(target,results,db,scan_id,threads,wordlist,
               skip_subdomains,skip_vuln,skip_auth,skip_api,verbose,output,fmt):
    console.rule("[bold yellow]🔍 Phase 1 of 6 — Security Headers[/bold yellow]")
    results["header_findings"] = await HeaderChecker(target,verbose=verbose).check_all()
    db.save_findings(scan_id,"headers",results["header_findings"])

    if not skip_subdomains:
        console.rule("[bold yellow]🌐 Phase 2 of 6 — Subdomain Enumeration[/bold yellow]")
        results["subdomains"] = await SubdomainEnumerator(target,threads=threads,
                                    wordlist=wordlist,verbose=verbose).enumerate()
        db.save_findings(scan_id,"subdomains",results["subdomains"])
    else:
        console.print("[dim]⏭  Phase 2 skipped[/dim]")

    console.rule("[bold yellow]🔎 Phase 3 of 6 — Web Fingerprinting[/bold yellow]")
    results["fingerprint"] = await WebFingerprinter(target,verbose=verbose).fingerprint()
    db.save_findings(scan_id,"fingerprint",[results["fingerprint"]])

    if not skip_vuln:
        console.rule("[bold yellow]💥 Phase 4 of 6 — Vulnerability Scanning[/bold yellow]")
        results["vulnerabilities"] = await VulnerabilityScanner(target,threads=threads,
                                          verbose=verbose).scan_all()
        db.save_findings(scan_id,"vulnerabilities",results["vulnerabilities"])
    else:
        console.print("[dim]⏭  Phase 4 skipped[/dim]")

    if not skip_auth:
        console.rule("[bold yellow]🔐 Phase 5 of 6 — Authentication Testing[/bold yellow]")
        results["auth_findings"] = await AuthTester(target,verbose=verbose).test_all()
        db.save_findings(scan_id,"auth",results["auth_findings"])
    else:
        console.print("[dim]⏭  Phase 5 skipped[/dim]")

    if not skip_api:
        console.rule("[bold yellow]🔌 Phase 6 of 6 — API Security Testing[/bold yellow]")
        results["api_findings"] = await APITester(target,verbose=verbose).test_all()
        db.save_findings(scan_id,"api",results["api_findings"])
    else:
        console.print("[dim]⏭  Phase 6 skipped[/dim]")

    console.rule("[bold green]📊 Generating Report[/bold green]")
    results["end_time"] = datetime.now().isoformat()
    path = ReportGenerator(results,output_dir=output).generate(format=fmt)
    _summary(results, path)
    db.complete_scan(scan_id)

def _summary(results, path):
    console.print(); console.rule("[bold green]✅ Scan Complete[/bold green]")
    v = results.get("vulnerabilities",[])
    t = Table(title="Scan Summary",box=box.DOUBLE_EDGE,border_style="green",show_lines=True,min_width=55)
    t.add_column("Category",style="#a5b4fc",min_width=26)
    t.add_column("Count",style="white",justify="center",min_width=8)
    t.add_column("Details",style="dim",min_width=26)
    t.add_row("Subdomains Found",  str(len(results.get("subdomains",[]))),"Active hosts")
    t.add_row("Total Vulns",       str(len(v)),"All severities")
    t.add_row("[bold red]🔴 Critical[/bold red]",str(sum(1 for x in v if x.get("severity")=="CRITICAL")),"Immediate action")
    t.add_row("[red]🟠 High[/red]",             str(sum(1 for x in v if x.get("severity")=="HIGH")),"High priority")
    t.add_row("[yellow]🟡 Medium[/yellow]",     str(sum(1 for x in v if x.get("severity")=="MEDIUM")),"Should fix")
    t.add_row("[cyan]🟢 Low[/cyan]",            str(sum(1 for x in v if x.get("severity")=="LOW")),"Best practice")
    t.add_row("Header Issues",     str(len(results.get("header_findings",[]))),"Misconfigs")
    t.add_row("Auth Findings",     str(len(results.get("auth_findings",[]))),"Auth issues")
    t.add_row("API Findings",      str(len(results.get("api_findings",[]))),"API issues")
    console.print(t)
    console.print(f"\n[bold green]📄 Report:[/bold green] [#a5b4fc]{path}[/#a5b4fc]\n")

# ══ subdomains ════════════════════════════════════════════════════════════════
@app.command("subdomains",help="Enumerate subdomains via DNS brute-force + certificate transparency.")
def cmd_subdomains(
    target:   str  = typer.Argument(...,metavar="DOMAIN"),
    threads:  int  = typer.Option(20,  "--threads", "-t"),
    wordlist: str  = typer.Option(None,"--wordlist","-w"),
    output:   str  = typer.Option(None,"--output",  "-o"),
    verbose:  bool = typer.Option(False,"--verbose", "-v"),
):
    print_banner()
    asyncio.run(_subdomains(target,threads,wordlist,output,verbose))

async def _subdomains(target,threads,wordlist,output,verbose):
    target = normalize(target)
    subs   = await SubdomainEnumerator(target,threads=threads,wordlist=wordlist,verbose=verbose).enumerate()
    if output:
        with open(output,"w") as f:
            for s in subs: f.write(f"{s['subdomain']}\t{s['ip']}\t{s['status']}\n")
        console.print(f"[green]✓ Saved to {output}[/green]")

# ══ vuln ══════════════════════════════════════════════════════════════════════
@app.command("vuln",help="Scan for vulnerabilities: SQLi, XSS, SSRF, CORS, Path Traversal, CMDi.")
def cmd_vuln(
    target:  str  = typer.Argument(...,metavar="TARGET"),
    threads: int  = typer.Option(10,  "--threads","-t"),
    verbose: bool = typer.Option(False,"--verbose","-v"),
):
    print_banner()
    asyncio.run(VulnerabilityScanner(normalize(target),threads=threads,verbose=verbose).scan_all())

# ══ headers ═══════════════════════════════════════════════════════════════════
@app.command("headers",help="Analyse HTTP security headers and score the target out of 100.")
def cmd_headers(
    target:  str  = typer.Argument(...,metavar="TARGET"),
    verbose: bool = typer.Option(False,"--verbose","-v"),
):
    print_banner()
    asyncio.run(HeaderChecker(normalize(target),verbose=verbose).check_all())

# ══ fingerprint ═══════════════════════════════════════════════════════════════
@app.command("fingerprint",help="Detect CMS, WAF, frameworks, server tech and exposed sensitive files.")
def cmd_fingerprint(
    target:  str  = typer.Argument(...,metavar="TARGET"),
    verbose: bool = typer.Option(False,"--verbose","-v"),
):
    print_banner()
    asyncio.run(WebFingerprinter(normalize(target),verbose=verbose).fingerprint())

# ══ api ═══════════════════════════════════════════════════════════════════════
@app.command("api",help="Test API security: IDOR, GraphQL, mass assignment, broken auth.")
def cmd_api(
    target:  str  = typer.Argument(...,metavar="TARGET"),
    spec:    str  = typer.Option(None, "--spec",   "-s"),
    verbose: bool = typer.Option(False,"--verbose","-v"),
):
    print_banner()
    asyncio.run(APITester(normalize(target),spec_url=spec,verbose=verbose).test_all())

# ══ list-scans ════════════════════════════════════════════════════════════════
@app.command("list-scans",help="Show all previous scans stored in ~/.nightx/scans.db")
def cmd_list_scans():
    print_banner()
    db    = Database()
    scans = db.get_all_scans()
    if not scans:
        console.print(Panel("[yellow]No scans yet.\n\n[/yellow]"
                            "[bold green]nightx scan https://target.com[/bold green]",
                            border_style="yellow"))
        return
    t = Table(title=f"Scan History ({len(scans)} scans)",
              box=box.ROUNDED, border_style="#6366f1", show_lines=True)
    t.add_column("ID",      style="dim",    justify="center",min_width=5)
    t.add_column("Target",  style="#a5b4fc",min_width=38)
    t.add_column("Date",    style="green",  min_width=20)
    t.add_column("Findings",style="yellow", justify="center",min_width=10)
    for s in scans:
        t.add_row(str(s["id"]),s["target"],
                  s["created_at"][:19].replace("T"," "),str(s["finding_count"]))
    console.print(t)

if __name__ == "__main__":
    app()

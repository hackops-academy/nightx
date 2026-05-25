#!/usr/bin/env python3
"""NightX — Web Fingerprinting Module"""
import asyncio
from typing import Dict, List, Optional
from urllib.parse import urljoin
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

WAF_SIGNATURES = {
    "Cloudflare":  ["cf-ray","cloudflare","__cfduid"],
    "Akamai":      ["akamai","x-akamai-transformed"],
    "Imperva":     ["incapsula","visid_incap","x-iinfo"],
    "Sucuri":      ["x-sucuri-id","sucuri"],
    "ModSecurity": ["mod_security","modsecurity"],
    "F5 BIG-IP":   ["bigipserver","x-wa-info"],
    "AWS WAF":     ["awswaf","x-amzn-requestid"],
    "Barracuda":   ["barra_counter_session"],
}

CMS_BODY = {
    "WordPress": ["wp-content","wp-includes","WordPress"],
    "Drupal":    ["Drupal.settings","drupal.org"],
    "Joomla":    ["/media/jui/","Joomla!"],
    "Magento":   ["Mage.Cookies","magento"],
    "Shopify":   ["cdn.shopify.com","Shopify.theme"],
    "Laravel":   ["laravel_session","XSRF-TOKEN"],
    "Django":    ["csrfmiddlewaretoken","django"],
}

FRAMEWORKS = {
    "React":    ["react","ReactDOM","__NEXT_DATA__"],
    "Angular":  ["ng-version","ng-app","angular"],
    "Vue.js":   ["vue.min.js","__vue__"],
    "Next.js":  ["__NEXT_DATA__","_next/static"],
    "jQuery":   ["jquery.min.js","jQuery("],
    "Bootstrap":["bootstrap.min.css","bootstrap.min.js"],
}

SENSITIVE = [
    "/.git/config","/.git/HEAD","/.env","/.env.local","/.env.backup",
    "/wp-config.php","/config.php","/configuration.php","/config.yml",
    "/settings.py","/web.config","/appsettings.json",
    "/backup.zip","/backup.tar.gz","/backup.sql","/dump.sql",
    "/admin","/administrator","/phpmyadmin","/phpMyAdmin",
    "/api/swagger","/swagger.json","/api/openapi.json","/swagger-ui.html",
    "/actuator/env","/actuator/health","/.htpasswd","/.htaccess",
    "/phpinfo.php","/info.php","/server-status","/robots.txt",
    "/sitemap.xml","/.well-known/security.txt","/graphql","/graphiql",
]

class WebFingerprinter:
    def __init__(self, target: str, verbose: bool = False):
        self.target  = target.rstrip("/")
        self.verbose = verbose
        self.results: Dict = {}

    async def _get(self, path: str = "") -> Optional[httpx.Response]:
        url = f"{self.target}{path}" if path else self.target
        try:
            async with httpx.AsyncClient(timeout=8, verify=False, follow_redirects=True,
                headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"}) as c:
                return await c.get(url)
        except Exception:
            return None

    async def fingerprint(self) -> Dict:
        console.print(f"\n[bold cyan]🔎 Fingerprinting:[/bold cyan] [white]{self.target}[/white]")
        resp = await self._get()
        if not resp:
            console.print("[red]  ✗ Could not reach target[/red]")
            return {}

        h   = {k.lower(): v for k, v in resp.headers.items()}
        body = resp.text or ""

        waf  = next((w for w,sigs in WAF_SIGNATURES.items()
                     if any(s.lower() in str(h).lower() or s.lower() in body[:500].lower()
                            for s in sigs)), "None detected")
        cms  = [c for c,pats in CMS_BODY.items() if any(p.lower() in body.lower() for p in pats)]
        fw   = [f for f,pats in FRAMEWORKS.items() if any(p.lower() in body.lower() for p in pats)]

        sem  = asyncio.Semaphore(20)
        async def chk(p):
            async with sem:
                r = await self._get(p)
                if r and r.status_code in [200,301,302]:
                    sev = "CRITICAL" if p in ["/.env","/.git/config","/wp-config.php"] else "HIGH"
                    if self.verbose:
                        console.print(f"  [red]✓ Found: {p} ({r.status_code})[/red]")
                    return {"path":p,"url":f"{self.target}{p}","status":r.status_code,"severity":sev,"size":len(r.content)}
                return None

        results   = await asyncio.gather(*[chk(p) for p in SENSITIVE])
        sensitive = [r for r in results if r]

        self.results = {
            "target":self.target,"status_code":resp.status_code,
            "server":h.get("server","Unknown"),"powered_by":h.get("x-powered-by","Unknown"),
            "waf":waf,"cms":cms,"frameworks":fw,"sensitive_paths":sensitive,
        }
        self._print()
        return self.results

    def _print(self):
        r = self.results
        waf_col = "red" if r["waf"] != "None detected" else "green"
        console.print(Panel(
            f"[bold]Server    :[/bold] {r['server']}\n"
            f"[bold]Powered By:[/bold] {r['powered_by']}\n"
            f"[bold]Status    :[/bold] {r['status_code']}\n"
            f"[bold]WAF       :[/bold] [{waf_col}]{r['waf']}[/{waf_col}]\n"
            f"[bold]CMS       :[/bold] {', '.join(r['cms']) or 'None detected'}\n"
            f"[bold]Frameworks:[/bold] {', '.join(r['frameworks']) or 'None detected'}",
            title="[bold green]Fingerprint Results[/bold green]", border_style="green"))

        if r["sensitive_paths"]:
            t = Table(title=f"Exposed Paths ({len(r['sensitive_paths'])})", box=box.ROUNDED, border_style="red")
            t.add_column("Path", style="cyan")
            t.add_column("Status", justify="center")
            t.add_column("Severity", justify="center")
            for p in r["sensitive_paths"]:
                sc = "bold red" if p["severity"]=="CRITICAL" else "red"
                t.add_row(p["path"], str(p["status"]), f"[{sc}]{p['severity']}[/{sc}]")
            console.print(t)

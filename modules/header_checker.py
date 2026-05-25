#!/usr/bin/env python3
"""NightX — Security Headers Checker Module"""
import asyncio
from typing import Dict, List, Optional
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

SECURITY_HEADERS = {
    "strict-transport-security":     {"name":"HSTS",                      "severity":"HIGH",   "fix":"Strict-Transport-Security: max-age=31536000; includeSubDomains; preload"},
    "content-security-policy":       {"name":"Content-Security-Policy",   "severity":"HIGH",   "fix":"Content-Security-Policy: default-src 'self'"},
    "x-frame-options":               {"name":"X-Frame-Options",           "severity":"MEDIUM", "fix":"X-Frame-Options: DENY"},
    "x-content-type-options":        {"name":"X-Content-Type-Options",    "severity":"MEDIUM", "fix":"X-Content-Type-Options: nosniff"},
    "referrer-policy":               {"name":"Referrer-Policy",           "severity":"LOW",    "fix":"Referrer-Policy: strict-origin-when-cross-origin"},
    "permissions-policy":            {"name":"Permissions-Policy",        "severity":"LOW",    "fix":"Permissions-Policy: camera=(), microphone=(), geolocation=()"},
    "x-xss-protection":              {"name":"X-XSS-Protection",          "severity":"LOW",    "fix":"X-XSS-Protection: 1; mode=block"},
    "cross-origin-opener-policy":    {"name":"COOP",                      "severity":"LOW",    "fix":"Cross-Origin-Opener-Policy: same-origin"},
    "cross-origin-resource-policy":  {"name":"CORP",                      "severity":"LOW",    "fix":"Cross-Origin-Resource-Policy: same-origin"},
    "cross-origin-embedder-policy":  {"name":"COEP",                      "severity":"LOW",    "fix":"Cross-Origin-Embedder-Policy: require-corp"},
}

LEAKY_HEADERS = {
    "server":           "Reveals server software version",
    "x-powered-by":     "Reveals backend technology",
    "x-aspnet-version": "Reveals .NET version",
    "x-aspnetmvc-version": "Reveals ASP.NET MVC version",
}

class HeaderChecker:
    def __init__(self, target: str, verbose: bool = False):
        self.target  = target
        self.verbose = verbose
        self.findings: List[Dict] = []

    async def check_all(self) -> List[Dict]:
        console.print(f"\n[bold cyan]🛡️  Checking Security Headers:[/bold cyan] [white]{self.target}[/white]")
        try:
            async with httpx.AsyncClient(timeout=10, verify=False, follow_redirects=True,
                                         headers={"User-Agent":"NightX/1.0"}) as client:
                resp = await client.get(self.target)
        except Exception as e:
            console.print(f"[red]  ✗ Connection failed: {e}[/red]")
            return []

        h = {k.lower(): v for k, v in resp.headers.items()}
        score = 100
        missing, present, leaky = [], [], []

        for key, info in SECURITY_HEADERS.items():
            if key in h:
                present.append({"name": info["name"], "value": h[key][:70]})
            else:
                ded = {"HIGH":20,"MEDIUM":10,"LOW":5}.get(info["severity"],5)
                score -= ded
                missing.append(info)
                self.findings.append({"type":f"Missing {info['name']}","severity":info["severity"],
                                       "url":self.target,"detail":f"Header not set","remediation":info["fix"]})

        for key, desc in LEAKY_HEADERS.items():
            if key in h:
                leaky.append({"name":key,"value":h[key],"issue":desc})
                self.findings.append({"type":f"Info Disclosure: {key}","severity":"LOW",
                                       "url":self.target,"detail":desc})

        self._check_cookies(resp)
        score = max(0, score)
        grade = "A" if score>=80 else "B" if score>=60 else "C" if score>=40 else "F"
        col   = "green" if score>=80 else "yellow" if score>=60 else "orange3" if score>=40 else "red"

        console.print(Panel(f"[{col}]Security Score: {score}/100  (Grade: {grade})[/{col}]",
                            title="[bold]Header Analysis[/bold]", border_style=col))

        if missing:
            t = Table(title=f"Missing Headers ({len(missing)})", box=box.ROUNDED, border_style="red")
            t.add_column("Header", style="cyan", min_width=28)
            t.add_column("Severity", justify="center")
            t.add_column("Fix", style="dim")
            for m in missing:
                sc = {"HIGH":"red","MEDIUM":"yellow","LOW":"cyan"}.get(m["severity"],"white")
                t.add_row(m["name"], f"[{sc}]{m['severity']}[/{sc}]", m["fix"][:55])
            console.print(t)

        if leaky:
            t2 = Table(title=f"Info Disclosure ({len(leaky)})", box=box.ROUNDED, border_style="yellow")
            t2.add_column("Header", style="cyan")
            t2.add_column("Value",  style="red")
            t2.add_column("Issue",  style="dim")
            for l in leaky:
                t2.add_row(l["name"], l["value"], l["issue"])
            console.print(t2)

        return self.findings

    def _check_cookies(self, resp):
        import re
        raw = str(resp.headers)
        for ck in re.findall(r"set-cookie: ([^\r\n]+)", raw, re.IGNORECASE):
            name = ck.split("=")[0].strip()
            cl   = ck.lower()
            issues = []
            if "httponly" not in cl: issues.append("Missing HttpOnly")
            if "secure"   not in cl: issues.append("Missing Secure")
            if "samesite" not in cl: issues.append("Missing SameSite")
            if issues:
                self.findings.append({"type":"Insecure Cookie","severity":"MEDIUM",
                                       "url":self.target,"detail":f"{name}: {', '.join(issues)}"})

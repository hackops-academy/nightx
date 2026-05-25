#!/usr/bin/env python3
"""NightX — Authentication Security Testing Module"""
import asyncio, base64, json, re
from typing import Dict, List, Optional
import httpx
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

DEFAULT_CREDS = [
    ("admin","admin"),("admin","password"),("admin","123456"),("admin","admin123"),
    ("admin",""),("admin","letmein"),("admin","welcome"),("root","root"),
    ("root","password"),("root","toor"),("administrator","administrator"),
    ("administrator","password"),("test","test"),("user","user"),("guest","guest"),
    ("demo","demo"),("manager","manager"),("operator","operator"),("pi","raspberry"),
    ("ubnt","ubnt"),
]

LOGIN_PATHS = [
    "/login","/admin/login","/wp-login.php","/user/login","/auth/login",
    "/signin","/sign-in","/account/login","/api/login","/api/auth",
    "/api/v1/login","/administrator","/admin","/panel",
]

WEAK_JWT_SECRETS = [
    "secret","password","123456","jwt_secret","changeme","supersecret",
    "mysecret","admin","test","key","private","qwerty","letmein",
]

class AuthTester:
    def __init__(self, target: str, verbose: bool = False):
        self.target   = target.rstrip("/")
        self.verbose  = verbose
        self.findings: List[Dict] = []
        self.sem = asyncio.Semaphore(5)

    def _add(self, vtype, severity, url, detail):
        self.findings.append({"type":vtype,"severity":severity,"url":url,"detail":detail})
        c = {"CRITICAL":"bold red","HIGH":"red","MEDIUM":"yellow","LOW":"cyan"}.get(severity,"white")
        console.print(f"  [{c}]🔐 [{severity}] {vtype}[/{c}] — {detail[:70]}")

    async def _get(self, path: str = "") -> Optional[httpx.Response]:
        url = f"{self.target}{path}" if path else self.target
        async with self.sem:
            try:
                async with httpx.AsyncClient(timeout=8, verify=False,
                    follow_redirects=True,
                    headers={"User-Agent":"Mozilla/5.0 NightX/1.0"}) as c:
                    return await c.get(url)
            except Exception:
                return None

    async def _post(self, url: str, data: Dict = None,
                    json_data: Dict = None, headers: Dict = None) -> Optional[httpx.Response]:
        async with self.sem:
            try:
                h = {"User-Agent":"Mozilla/5.0 NightX/1.0", **(headers or {})}
                async with httpx.AsyncClient(timeout=8, verify=False,
                    follow_redirects=True, headers=h) as c:
                    if json_data:
                        return await c.post(url, json=json_data)
                    return await c.post(url, data=data)
            except Exception:
                return None

    async def _find_login_pages(self) -> List[str]:
        console.print("\n  [bold]Discovering login pages...[/bold]")
        found = []
        async def chk(path):
            r = await self._get(path)
            if r and r.status_code in [200,401,403]:
                body = r.text or ""
                if any(kw in body.lower() for kw in ["password","login","email","username","signin"]):
                    return f"{self.target}{path}"
            return None
        results = await asyncio.gather(*[chk(p) for p in LOGIN_PATHS])
        found   = [r for r in results if r]
        if found:
            console.print(f"  [green]Found {len(found)} login page(s)[/green]")
            for p in found:
                console.print(f"    [cyan]→ {p}[/cyan]")
        return found

    async def _test_default_creds(self, login_pages: List[str]):
        console.print("\n  [bold]Testing default credentials...[/bold]")
        for url in login_pages[:2]:
            for user, pw in DEFAULT_CREDS[:15]:
                await asyncio.sleep(0.15)
                for uf, pf in [("username","password"),("user","pass"),("email","password")]:
                    r = await self._post(url, data={uf:user, pf:pw})
                    if not r: continue
                    body = r.text or ""
                    fail = any(w in body.lower() for w in
                               ["invalid","incorrect","wrong","failed","error","denied"])
                    ok   = r.status_code==302 and any(
                        kw in r.headers.get("location","").lower()
                        for kw in ["dashboard","admin","home","welcome","panel"])
                    if ok or (not fail and r.status_code==200 and len(body)>500):
                        self._add("Default Credentials","CRITICAL",url,
                                  f"Login succeeded: {user}:{pw}")
                        return

    async def _test_jwt(self):
        console.print("\n  [bold]Testing JWT security...[/bold]")
        jwt_re = r"eyJ[A-Za-z0-9+/=]+\.eyJ[A-Za-z0-9+/=]+\.[A-Za-z0-9+/=_-]+"
        r = await self._get()
        if not r: return
        tokens = re.findall(jwt_re, (r.text or "") + str(r.headers))
        for path in ["/api/auth","/api/login","/api/token","/auth/token"]:
            rr = await self._post(f"{self.target}{path}",
                                  json_data={"username":"test","password":"test"})
            if rr and rr.status_code == 200:
                tokens.extend(re.findall(jwt_re, rr.text or ""))
        for token in tokens[:3]:
            await self._analyse_jwt(token)

    async def _analyse_jwt(self, token: str):
        parts = token.split(".")
        if len(parts) != 3: return
        try:
            def pad(s): return s + "=" * (4 - len(s) % 4)
            header  = json.loads(base64.b64decode(pad(parts[0])).decode("utf-8","ignore"))
            payload = json.loads(base64.b64decode(pad(parts[1])).decode("utf-8","ignore"))
            alg = header.get("alg","").upper()
            if alg == "NONE":
                self._add("JWT alg:none Attack","CRITICAL",self.target,
                          "JWT uses 'none' algorithm — signature not verified")
            elif alg == "HS256":
                secret = self._crack_jwt(token, parts)
                if secret:
                    self._add("Weak JWT Secret","CRITICAL",self.target,
                              f"JWT signed with weak secret: '{secret}'")
            if not payload.get("exp"):
                self._add("JWT No Expiration","MEDIUM",self.target,
                          "JWT has no expiration claim — token valid forever")
            for key in ["password","secret","ssn","credit","key"]:
                if key in str(payload).lower():
                    self._add("Sensitive Data in JWT","HIGH",self.target,
                              f"Sensitive field '{key}' found in JWT payload")
        except Exception:
            pass

    def _crack_jwt(self, token: str, parts: List[str]) -> Optional[str]:
        import hmac, hashlib
        try:
            msg      = f"{parts[0]}.{parts[1]}".encode()
            expected = base64.urlsafe_b64decode(parts[2] + "=" * (4 - len(parts[2]) % 4))
            for secret in WEAK_JWT_SECRETS:
                if hmac.new(secret.encode(), msg, hashlib.sha256).digest() == expected:
                    return secret
        except Exception:
            pass
        return None

    async def _test_session(self):
        console.print("\n  [bold]Testing session security...[/bold]")
        r = await self._get()
        if not r: return
        set_cookie = str(r.headers)
        for name, value in re.findall(
            r"([A-Za-z_-]*session[A-Za-z_-]*)=([^;]+)", set_cookie, re.IGNORECASE):
            value = value.strip()
            if len(value) < 16:
                self._add("Weak Session ID","HIGH",self.target,
                          f"Cookie '{name}' is too short ({len(value)} chars)")
            if value.isdigit() and int(value) < 1000000:
                self._add("Predictable Session ID","CRITICAL",self.target,
                          f"Session ID '{name}={value}' appears to be a simple integer")

    async def _test_bruteforce_protection(self, login_pages: List[str]):
        console.print("\n  [bold]Testing brute force protection...[/bold]")
        for url in login_pages[:1]:
            codes = []
            for _ in range(6):
                r = await self._post(url, data={"username":"admin","password":"wrongpass_test"})
                if r: codes.append(r.status_code)
                await asyncio.sleep(0.1)
            if all(c == 200 for c in codes):
                self._add("No Brute Force Protection","MEDIUM",url,
                          "Login endpoint does not rate-limit failed attempts")
            r = await self._post(url, data={"username":"admin","password":"wrongpass_test"})
            if r and r.text and "captcha" not in r.text.lower():
                self._add("No CAPTCHA on Login","LOW",url,
                          "No CAPTCHA detected after multiple failed attempts")

    async def test_all(self) -> List[Dict]:
        console.print(f"\n[bold cyan]🔐 Authentication Testing:[/bold cyan] [white]{self.target}[/white]")
        login_pages = await self._find_login_pages()
        if login_pages:
            await self._test_default_creds(login_pages)
            await self._test_bruteforce_protection(login_pages)
        await self._test_jwt()
        await self._test_session()
        self._print_summary()
        return self.findings

    def _print_summary(self):
        console.print()
        if not self.findings:
            console.print("[green]✅ No auth vulnerabilities found[/green]")
            return
        t = Table(title=f"Auth Findings ({len(self.findings)})",
                  box=box.ROUNDED, border_style="red")
        t.add_column("Type",     style="cyan",  min_width=28)
        t.add_column("Severity", justify="center")
        t.add_column("Detail",   style="dim")
        for f in self.findings:
            sc = {"CRITICAL":"bold red","HIGH":"red","MEDIUM":"yellow","LOW":"cyan"}.get(f["severity"],"white")
            t.add_row(f["type"], f"[{sc}]{f['severity']}[/{sc}]", f.get("detail","")[:55])
        console.print(t)

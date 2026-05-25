#!/usr/bin/env python3
"""NightX — API Security Testing Module"""
import asyncio, json, re
from typing import Dict, List, Optional
import httpx
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

API_PATHS = [
    "/api","/api/v1","/api/v2","/v1","/v2",
    "/swagger.json","/swagger.yaml","/api/swagger.json",
    "/openapi.json","/api/openapi.json","/api-docs",
    "/graphql","/graphiql","/playground",
    "/actuator","/actuator/health","/actuator/env",
    "/api/v1/users","/api/v1/admin","/api/users",
    "/api/v1/config","/api/v1/settings",
]

GQL_INTROSPECTION = '{"query":"{ __schema { types { name fields { name } } } }"}'

class APITester:
    def __init__(self, target: str, spec_url: Optional[str] = None, verbose: bool = False):
        self.target   = target.rstrip("/")
        self.spec_url = spec_url
        self.verbose  = verbose
        self.findings: List[Dict] = []
        self.endpoints: List[Dict] = []
        self.sem = asyncio.Semaphore(10)

    def _add(self, vtype, severity, url, detail):
        self.findings.append({"type":vtype,"severity":severity,"url":url,"detail":detail})
        c = {"CRITICAL":"bold red","HIGH":"red","MEDIUM":"yellow","LOW":"cyan"}.get(severity,"white")
        console.print(f"  [{c}]🔌 [{severity}] {vtype}[/{c}] — {detail[:70]}")

    async def _req(self, method: str, url: str, **kw) -> Optional[httpx.Response]:
        async with self.sem:
            try:
                h = {"User-Agent":"NightX/1.0","Accept":"application/json",
                     "Content-Type":"application/json", **kw.pop("headers",{})}
                async with httpx.AsyncClient(timeout=8, verify=False,
                    follow_redirects=True, headers=h) as c:
                    return await c.request(method, url, **kw)
            except Exception:
                return None

    async def _discover(self):
        console.print("\n  [bold]Discovering API endpoints...[/bold]")
        async def chk(path):
            url = f"{self.target}{path}"
            r   = await self._req("GET", url)
            if r and r.status_code not in [404]:
                if self.verbose:
                    console.print(f"  [green]✓ {r.status_code} {url}[/green]")
                return {"url":url,"path":path,"status":r.status_code,
                        "size":len(r.content)}
            return None
        results = await asyncio.gather(*[chk(p) for p in API_PATHS])
        self.endpoints = [r for r in results if r]
        console.print(f"  [green]Found {len(self.endpoints)} API endpoint(s)[/green]")

    async def _test_swagger(self):
        console.print("\n  [bold]Looking for API spec (Swagger/OpenAPI)...[/bold]")
        paths = ["/swagger.json","/api/swagger.json","/openapi.json",
                 "/api/openapi.json","/swagger.yaml","/api-docs"]
        if self.spec_url:
            paths.insert(0, self.spec_url if self.spec_url.startswith("http") else self.spec_url)
        for path in paths:
            url = f"{self.target}{path}" if not path.startswith("http") else path
            r   = await self._req("GET", url)
            if r and r.status_code == 200:
                try:
                    spec = r.json()
                    if "paths" in spec or "swagger" in spec or "openapi" in spec:
                        console.print(f"  [red]✓ API spec exposed at: {url}[/red]")
                        self._add("Exposed API Docs","MEDIUM",url,
                                  "Swagger/OpenAPI spec is publicly accessible")
                        return
                except Exception:
                    pass

    async def _test_idor(self):
        console.print("\n  [bold]Testing IDOR...[/bold]")
        templates = ["/api/v1/users/{id}","/api/users/{id}","/api/v1/orders/{id}",
                     "/user/{id}","/profile/{id}"]
        for tmpl in templates:
            responses = []
            for id_val in [1,2,3]:
                url = f"{self.target}{tmpl.replace('{id}',str(id_val))}"
                r   = await self._req("GET", url)
                if r: responses.append((id_val, r.status_code, len(r.content)))
            success = [(i,c,s) for i,c,s in responses if c == 200]
            if len(success) >= 2 and len({s for _,_,s in success}) > 1:
                self._add("Potential IDOR","HIGH",f"{self.target}{tmpl}",
                          f"Multiple records accessible without auth (IDs: {[i for i,_,_ in success]})")

    async def _test_graphql(self):
        console.print("\n  [bold]Testing GraphQL...[/bold]")
        for path in ["/graphql","/api/graphql","/graphiql"]:
            url = f"{self.target}{path}"
            r   = await self._req("POST", url, content=GQL_INTROSPECTION)
            if r and r.status_code == 200:
                try:
                    data = r.json()
                    if "__schema" in str(data):
                        self._add("GraphQL Introspection Enabled","MEDIUM",url,
                                  "Full schema exposed via introspection")
                        schema = data.get("data",{}).get("__schema",{})
                        sensitive = [t["name"] for t in schema.get("types",[])
                                     if any(k in t["name"].lower()
                                            for k in ["user","admin","password","secret","token"])]
                        if sensitive:
                            self._add("Sensitive GraphQL Types","HIGH",url,
                                      f"Sensitive types: {', '.join(sensitive[:5])}")
                except Exception:
                    pass
            r2 = await self._req("GET", url)
            if r2 and r2.status_code == 200 and "graphql" in (r2.text or "").lower():
                self._add("GraphQL Playground Exposed","LOW",url,
                          "Interactive GraphQL IDE publicly accessible")

    async def _test_mass_assignment(self):
        console.print("\n  [bold]Testing Mass Assignment...[/bold]")
        payload = {"username":"testuser","email":"test@test.com","password":"test1234",
                   "role":"admin","is_admin":True,"admin":True,"permissions":["admin"]}
        for ep in ["/api/v1/users/register","/api/register","/register","/api/user"]:
            url = f"{self.target}{ep}"
            r   = await self._req("POST", url, json=payload)
            if r and r.status_code in [200,201]:
                body = r.text or ""
                if any(f in body.lower() for f in ["admin","role","is_admin","permission"]):
                    self._add("Mass Assignment","HIGH",url,
                              "API may accept privileged fields (role, is_admin) in body")

    async def _test_unauth_access(self):
        console.print("\n  [bold]Testing unauthenticated access...[/bold]")
        for path in ["/api/v1/users","/api/v1/admin","/api/admin","/api/users","/api/v1/config"]:
            url = f"{self.target}{path}"
            r   = await self._req("GET", url)
            if r and r.status_code == 200:
                try:
                    data = r.json()
                    if data and (isinstance(data,list) or (isinstance(data,dict) and len(data)>0)):
                        self._add("Unauthenticated API Access","HIGH",url,
                                  f"Returns data without auth ({len(r.content)} bytes)")
                except Exception:
                    pass

    async def _test_verbose_errors(self):
        console.print("\n  [bold]Testing verbose error messages...[/bold]")
        test_urls = [f"{self.target}/api/v1/users?id='; DROP TABLE users--",
                     f"{self.target}/api/v1/users?limit=-1&offset=abc"]
        for url in test_urls:
            r = await self._req("GET", url)
            if r and r.text:
                for pattern in [r"Traceback \(most recent",r"at .+\.java:\d+",
                                r"NullPointerException",r"SQLSTATE",r"ORA-\d{5}"]:
                    if re.search(pattern, r.text, re.IGNORECASE):
                        self._add("Verbose Error Messages","MEDIUM",url,
                                  f"Stack trace or internal error exposed")
                        break

    async def test_all(self) -> List[Dict]:
        console.print(f"\n[bold cyan]🔌 API Security Testing:[/bold cyan] [white]{self.target}[/white]")
        await self._discover()
        await self._test_swagger()
        await self._test_idor()
        await self._test_graphql()
        await self._test_mass_assignment()
        await self._test_unauth_access()
        await self._test_verbose_errors()
        self._print_summary()
        return self.findings

    def _print_summary(self):
        console.print()
        if self.endpoints:
            t = Table(title=f"API Endpoints ({len(self.endpoints)})",
                      box=box.SIMPLE, border_style="cyan")
            t.add_column("URL",    style="cyan")
            t.add_column("Status", justify="center")
            for e in self.endpoints[:12]:
                sc = str(e["status"])
                c  = "green" if sc.startswith("2") else "yellow" if sc.startswith("3") else "red"
                t.add_row(e["url"], f"[{c}]{sc}[/{c}]")
            console.print(t)
        if not self.findings:
            console.print("[green]✅ No API vulnerabilities found[/green]")
            return
        t2 = Table(title=f"API Findings ({len(self.findings)})",
                   box=box.ROUNDED, border_style="red")
        t2.add_column("Type",     style="cyan",  min_width=28)
        t2.add_column("Severity", justify="center")
        t2.add_column("Detail",   style="dim")
        for f in self.findings:
            sc = {"CRITICAL":"bold red","HIGH":"red","MEDIUM":"yellow","LOW":"cyan"}.get(f["severity"],"white")
            t2.add_row(f["type"], f"[{sc}]{f['severity']}[/{sc}]", f.get("detail","")[:55])
        console.print(t2)

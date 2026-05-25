#!/usr/bin/env python3
"""NightX — Subdomain Enumeration Module"""
import asyncio, socket
from typing import Dict, List, Optional
from urllib.parse import urlparse
import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import box

console = Console()

BUILTIN = [
    "www","mail","ftp","api","app","admin","portal","blog","dev","staging","test",
    "vpn","smtp","pop","imap","ns1","ns2","ns3","webmail","cdn","static","img",
    "images","assets","media","upload","download","files","secure","login","auth",
    "oauth","sso","id","accounts","billing","pay","shop","store","support","help",
    "forum","wiki","docs","documentation","dashboard","monitor","status","health",
    "beta","preview","pre","uat","qa","sandbox","prod","production","live","origin",
    "edge","relay","git","gitlab","jenkins","grafana","kibana","prometheus","metrics",
    "db","database","mysql","postgres","redis","mongo","elastic","api2","api3","v1",
    "v2","v3","graphql","rest","internal","intranet","corp","mobile","m","wap","demo",
    "backup","old","new","web","server","remote","exchange","owa","outlook","mx","mx1",
]

class SubdomainEnumerator:
    def __init__(self, target: str, threads: int = 20,
                 wordlist: Optional[str] = None, verbose: bool = False):
        self.domain   = urlparse(target).netloc or target
        if self.domain.startswith("www."): self.domain = self.domain[4:]
        self.threads  = threads
        self.wordlist = wordlist
        self.verbose  = verbose
        self.found: List[Dict] = []
        self.sem = asyncio.Semaphore(threads)

    def _load_words(self) -> List[str]:
        if self.wordlist:
            try:
                with open(self.wordlist) as f:
                    words = [l.strip() for l in f if l.strip()]
                console.print(f"  [green]Loaded {len(words)} words from {self.wordlist}[/green]")
                return words
            except Exception as e:
                console.print(f"  [yellow]Could not load wordlist: {e} — using built-in[/yellow]")
        return BUILTIN

    async def _resolve(self, word: str) -> Optional[Dict]:
        async with self.sem:
            fqdn = f"{word}.{self.domain}"
            try:
                loop = asyncio.get_event_loop()
                ip   = await loop.run_in_executor(None, socket.gethostbyname, fqdn)
                st   = await self._http_status(fqdn)
                if self.verbose:
                    console.print(f"  [green]✓[/green] {fqdn} → {ip} ({st})")
                return {"subdomain":fqdn,"ip":ip,"status":st,"source":"bruteforce"}
            except Exception:
                return None

    async def _http_status(self, fqdn: str) -> str:
        for scheme in ["https","http"]:
            try:
                async with httpx.AsyncClient(timeout=4, verify=False,
                                             follow_redirects=True) as c:
                    r = await c.get(f"{scheme}://{fqdn}")
                    return str(r.status_code)
            except Exception:
                pass
        return "No HTTP"

    async def _crtsh(self) -> List[str]:
        console.print(f"  [cyan]Querying crt.sh for {self.domain}...[/cyan]")
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(f"https://crt.sh/?q=%.{self.domain}&output=json",
                                headers={"User-Agent":"NightX/1.0"})
                if r.status_code == 200:
                    names = []
                    for e in r.json():
                        for n in e.get("name_value","").split("\n"):
                            n = n.strip().lstrip("*.")
                            if n.endswith(f".{self.domain}") and n not in names:
                                names.append(n)
                    console.print(f"  [green]crt.sh returned {len(names)} entries[/green]")
                    return names
        except Exception as e:
            console.print(f"  [yellow]crt.sh failed: {e}[/yellow]")
        return []

    async def enumerate(self) -> List[Dict]:
        console.print(f"\n[bold cyan]🌐 Subdomain Enumeration:[/bold cyan] [white]{self.domain}[/white]")
        words = self._load_words()

        ct_names = await self._crtsh()

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                      BarColumn(), TaskProgressColumn(), console=console) as prog:
            task = prog.add_task("[cyan]Resolving...", total=len(words))
            tasks  = [self._resolve(w) for w in words]
            results = []
            for coro in asyncio.as_completed(tasks):
                r = await coro
                if r: results.append(r)
                prog.advance(task)

        if ct_names:
            async def resolve_fqdn(fqdn):
                async with self.sem:
                    try:
                        loop = asyncio.get_event_loop()
                        ip   = await loop.run_in_executor(None, socket.gethostbyname, fqdn)
                        st   = await self._http_status(fqdn)
                        return {"subdomain":fqdn,"ip":ip,"status":st,"source":"crt.sh"}
                    except Exception:
                        return None
            ct_results = await asyncio.gather(*[resolve_fqdn(n) for n in ct_names])
            results.extend([r for r in ct_results if r])

        seen, unique = set(), []
        for r in results:
            if r["subdomain"] not in seen:
                seen.add(r["subdomain"])
                unique.append(r)
        self.found = sorted(unique, key=lambda x: x["subdomain"])

        console.print(f"\n[bold green]Found {len(self.found)} subdomains[/bold green]")
        if self.found:
            t = Table(box=box.ROUNDED, border_style="cyan", show_lines=True)
            t.add_column("Subdomain", style="cyan",  min_width=30)
            t.add_column("IP",        style="white")
            t.add_column("Status",    justify="center")
            t.add_column("Source",    style="dim")
            for s in self.found:
                st = s["status"]
                sc = "green" if st.startswith("2") else "yellow" if st.startswith("3") else "red"
                t.add_row(s["subdomain"], s["ip"], f"[{sc}]{st}[/{sc}]", s["source"])
            console.print(t)
        return self.found

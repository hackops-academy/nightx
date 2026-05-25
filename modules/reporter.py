#!/usr/bin/env python3
"""NightX — Report Generator Module"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse
from rich.console import Console

console = Console()

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>NightX — Penetration Test Report</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
:root{--bg:#07071a;--surf:#0f0f2e;--surf2:#1a1a3a;--border:#2d2b6b;--accent:#6366f1;--accent2:#4338ca;--light:#a5b4fc;--text:#e0e7ff;--muted:#6b7280;--critical:#ff2020;--high:#ff6020;--medium:#ffd020;--low:#20c0ff;--info:#8080ff;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:'Syne',sans-serif;line-height:1.6;}
body::before{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(99,102,241,0.015) 2px,rgba(99,102,241,0.015) 4px);pointer-events:none;z-index:1000;}
.hdr{background:linear-gradient(135deg,#0d0d2e,#0a071a);border-bottom:2px solid var(--accent);padding:2.5rem 3rem;}
.hdr-grid{display:grid;grid-template-columns:1fr auto;align-items:center;gap:2rem;}
.tool-label{font-size:.7rem;letter-spacing:.4em;color:var(--accent);text-transform:uppercase;margin-bottom:.4rem;font-family:'JetBrains Mono',monospace;}
.title{font-size:2.5rem;font-weight:800;background:linear-gradient(135deg,#fff,var(--light));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.meta{margin-top:1.2rem;display:flex;gap:1.5rem;flex-wrap:wrap;}
.meta-item .label{font-size:.6rem;letter-spacing:.3em;color:var(--muted);text-transform:uppercase;font-family:'JetBrains Mono',monospace;}
.meta-item .val{font-family:'JetBrains Mono',monospace;font-size:.85rem;color:var(--light);}
.risk{padding:1.2rem 1.8rem;border-radius:8px;text-align:center;border:2px solid;min-width:130px;}
.risk .rl{font-size:.6rem;letter-spacing:.3em;text-transform:uppercase;margin-bottom:.4rem;opacity:.8;font-family:'JetBrains Mono',monospace;}
.risk .rs{font-size:2.8rem;font-weight:800;line-height:1;font-family:'JetBrains Mono',monospace;}
.risk .rn{font-size:.7rem;letter-spacing:.3em;text-transform:uppercase;margin-top:.4rem;}
.risk-CRITICAL{border-color:var(--critical);color:var(--critical);}
.risk-HIGH{border-color:var(--high);color:var(--high);}
.risk-MEDIUM{border-color:var(--medium);color:var(--medium);}
.risk-LOW{border-color:var(--low);color:var(--low);}
.main{max-width:1300px;margin:0 auto;padding:2.5rem 3rem;}
.disclaimer{background:rgba(255,32,32,.05);border:1px solid rgba(255,32,32,.2);border-radius:6px;padding:1.2rem;margin-bottom:2.5rem;font-size:.8rem;color:var(--muted);}
.disclaimer strong{color:var(--critical);}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.8rem;margin-bottom:2.5rem;}
.stat{background:var(--surf);border:1px solid var(--border);border-radius:8px;padding:1.2rem;position:relative;overflow:hidden;}
.stat::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;}
.stat.c::before{background:var(--critical);}
.stat.h::before{background:var(--high);}
.stat.m::before{background:var(--medium);}
.stat.l::before{background:var(--low);}
.stat.i::before{background:var(--accent);}
.stat-lbl{font-size:.6rem;letter-spacing:.3em;text-transform:uppercase;color:var(--muted);margin-bottom:.6rem;font-family:'JetBrains Mono',monospace;}
.stat-num{font-size:2.2rem;font-weight:800;font-family:'JetBrains Mono',monospace;}
.stat.c .stat-num{color:var(--critical);}
.stat.h .stat-num{color:var(--high);}
.stat.m .stat-num{color:var(--medium);}
.stat.l .stat-num{color:var(--low);}
.stat.i .stat-num{color:var(--accent);}
.sec{margin-bottom:2.5rem;}
.sec-hdr{display:flex;align-items:center;gap:.8rem;margin-bottom:1.2rem;padding-bottom:.8rem;border-bottom:1px solid var(--border);}
.sec-icon{font-size:1.3rem;}
.sec-title{font-size:1.2rem;font-weight:700;}
.sec-cnt{background:var(--surf2);border:1px solid var(--border);padding:.15rem .6rem;border-radius:20px;font-size:.7rem;font-family:'JetBrains Mono',monospace;color:var(--muted);margin-left:auto;}
.card{background:var(--surf);border:1px solid var(--border);border-left:4px solid;border-radius:4px;padding:1.1rem 1.4rem;margin-bottom:.6rem;transition:transform .1s;}
.card:hover{transform:translateX(3px);}
.card.CRITICAL{border-left-color:var(--critical);}
.card.HIGH{border-left-color:var(--high);}
.card.MEDIUM{border-left-color:var(--medium);}
.card.LOW{border-left-color:var(--low);}
.card.INFO{border-left-color:var(--info);}
.card-hdr{display:flex;align-items:center;gap:.8rem;margin-bottom:.4rem;flex-wrap:wrap;}
.card-title{font-weight:600;font-size:.9rem;flex:1;}
.badge{padding:.12rem .5rem;border-radius:3px;font-size:.6rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;font-family:'JetBrains Mono',monospace;}
.badge.CRITICAL{background:rgba(255,32,32,.15);color:var(--critical);border:1px solid var(--critical);}
.badge.HIGH{background:rgba(255,96,32,.15);color:var(--high);border:1px solid var(--high);}
.badge.MEDIUM{background:rgba(255,208,32,.15);color:var(--medium);border:1px solid var(--medium);}
.badge.LOW{background:rgba(32,192,255,.15);color:var(--low);border:1px solid var(--low);}
.badge.INFO{background:rgba(128,128,255,.15);color:var(--info);border:1px solid var(--info);}
.card-url{font-family:'JetBrains Mono',monospace;font-size:.7rem;color:var(--muted);word-break:break-all;margin-bottom:.4rem;}
.card-detail{font-size:.82rem;opacity:.85;}
.card-rem{font-size:.75rem;color:var(--light);margin-top:.5rem;font-style:italic;}
.fp-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:.8rem;}
.fp-card{background:var(--surf);border:1px solid var(--border);border-radius:6px;padding:1.1rem;}
.fp-lbl{font-size:.6rem;letter-spacing:.3em;text-transform:uppercase;color:var(--muted);margin-bottom:.4rem;font-family:'JetBrains Mono',monospace;}
.fp-val{font-family:'JetBrains Mono',monospace;font-size:.85rem;color:var(--light);word-break:break-all;}
table{width:100%;border-collapse:collapse;font-size:.82rem;}
th{text-align:left;padding:.6rem .9rem;background:var(--surf2);border-bottom:1px solid var(--border);font-size:.6rem;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);font-family:'JetBrains Mono',monospace;}
td{padding:.6rem .9rem;border-bottom:1px solid rgba(42,42,90,.5);font-family:'JetBrains Mono',monospace;font-size:.78rem;}
tr:hover td{background:var(--surf2);}
.s200{color:#22c55e;} .s3xx{color:#fbbf24;} .s4xx{color:#f97316;} .sdim{color:var(--muted);}
.empty{text-align:center;padding:2.5rem;color:var(--muted);border:1px dashed var(--border);border-radius:6px;font-family:'JetBrains Mono',monospace;font-size:.82rem;}
.ftr{background:var(--surf);border-top:1px solid var(--border);padding:1.5rem 3rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.8rem;}
.ftr-txt{font-size:.7rem;color:var(--muted);font-family:'JetBrains Mono',monospace;}
</style>
</head>
<body>
<header class="hdr">
  <div class="hdr-grid">
    <div>
      <div class="tool-label">NightX · Penetration Test Report</div>
      <h1 class="title">Security Assessment Report</h1>
      <div class="meta">
        <div class="meta-item"><span class="label">Target</span><div class="val">{{TARGET}}</div></div>
        <div class="meta-item"><span class="label">Scan ID</span><div class="val">#{{SCAN_ID}}</div></div>
        <div class="meta-item"><span class="label">Started</span><div class="val">{{START}}</div></div>
        <div class="meta-item"><span class="label">Finished</span><div class="val">{{END}}</div></div>
      </div>
    </div>
    <div class="risk risk-{{RISK_CLASS}}">
      <div class="rl">Risk Level</div>
      <div class="rs">{{RISK_SCORE}}</div>
      <div class="rn">{{RISK_LEVEL}}</div>
    </div>
  </div>
</header>
<main class="main">
  <div class="disclaimer"><strong>⚠ CONFIDENTIAL — AUTHORIZED USE ONLY</strong><br>
  This report contains sensitive security findings for authorized penetration testing only.</div>
  <div class="stats">
    <div class="stat c"><div class="stat-lbl">Critical</div><div class="stat-num">{{CC}}</div></div>
    <div class="stat h"><div class="stat-lbl">High</div><div class="stat-num">{{CH}}</div></div>
    <div class="stat m"><div class="stat-lbl">Medium</div><div class="stat-num">{{CM}}</div></div>
    <div class="stat l"><div class="stat-lbl">Low</div><div class="stat-num">{{CL}}</div></div>
    <div class="stat i"><div class="stat-lbl">Subdomains</div><div class="stat-num">{{CS}}</div></div>
  </div>
  {{FP_SEC}}
  <section class="sec">
    <div class="sec-hdr"><span class="sec-icon">💥</span><h2 class="sec-title">Vulnerabilities</h2><span class="sec-cnt">{{TV}} findings</span></div>
    {{VULN_CARDS}}
  </section>
  <section class="sec">
    <div class="sec-hdr"><span class="sec-icon">🔐</span><h2 class="sec-title">Authentication Issues</h2><span class="sec-cnt">{{TA}} findings</span></div>
    {{AUTH_CARDS}}
  </section>
  <section class="sec">
    <div class="sec-hdr"><span class="sec-icon">🔌</span><h2 class="sec-title">API Security Issues</h2><span class="sec-cnt">{{TAP}} findings</span></div>
    {{API_CARDS}}
  </section>
  <section class="sec">
    <div class="sec-hdr"><span class="sec-icon">🌐</span><h2 class="sec-title">Discovered Subdomains</h2><span class="sec-cnt">{{CS}} found</span></div>
    {{SUB_TABLE}}
  </section>
</main>
<footer class="ftr">
  <span class="ftr-txt">NightX v1.0.0 · Generated {{GEN}}</span>
  <span class="ftr-txt">FOR AUTHORIZED PENETRATION TESTING ONLY</span>
</footer>
</body></html>"""

class ReportGenerator:
    def __init__(self, results: Dict, output_dir: str = "./reports"):
        self.results    = results
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _risk(self):
        all_f = (self.results.get("vulnerabilities",[]) +
                 self.results.get("auth_findings",[]) +
                 self.results.get("api_findings",[]) +
                 self.results.get("header_findings",[]))
        c = sum(1 for f in all_f if f.get("severity")=="CRITICAL")
        h = sum(1 for f in all_f if f.get("severity")=="HIGH")
        m = sum(1 for f in all_f if f.get("severity")=="MEDIUM")
        score = min(c*40 + h*20 + m*10, 100)
        if c:   return score,"CRITICAL","CRITICAL"
        if h>2: return score,"HIGH","HIGH"
        if m or h: return score,"MEDIUM","MEDIUM"
        return score,"LOW","LOW"

    def _card(self, f: Dict) -> str:
        sev = f.get("severity","INFO")
        rem = f"<div class='card-rem'>Fix: {f['remediation']}</div>" if f.get("remediation") else ""
        return (f"<div class='card {sev}'>"
                f"<div class='card-hdr'><span class='card-title'>{f.get('type','')}</span>"
                f"<span class='badge {sev}'>{sev}</span></div>"
                f"<div class='card-url'>🔗 {f.get('url','')}</div>"
                f"<div class='card-detail'>{f.get('detail','')}</div>{rem}</div>")

    def _cards(self, findings: List[Dict]) -> str:
        if not findings:
            return "<div class='empty'>✅ No findings in this category</div>"
        order = {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3,"INFO":4}
        return "\n".join(self._card(f) for f in sorted(findings, key=lambda x: order.get(x.get("severity"),5)))

    def _fp_section(self) -> str:
        fp = self.results.get("fingerprint",{})
        if not fp: return ""
        items = [("Server",fp.get("server","?")),("X-Powered-By",fp.get("powered_by","?")),
                 ("WAF",fp.get("waf","None")),
                 ("CMS",", ".join(fp.get("cms",[])) or "None"),
                 ("Frameworks",", ".join(fp.get("frameworks",[])) or "None"),
                 ("Status",str(fp.get("status_code","?")))]
        cards = "".join(f"<div class='fp-card'><div class='fp-lbl'>{l}</div><div class='fp-val'>{v}</div></div>"
                        for l,v in items)
        return (f"<section class='sec'><div class='sec-hdr'>"
                f"<span class='sec-icon'>🔎</span><h2 class='sec-title'>Fingerprinting</h2></div>"
                f"<div class='fp-grid'>{cards}</div></section>")

    def _sub_table(self) -> str:
        subs = self.results.get("subdomains",[])
        if not subs: return "<div class='empty'>No subdomains discovered</div>"
        rows = ""
        for s in subs:
            st  = s.get("status","-")
            cls = "s200" if st.startswith("2") else "s3xx" if st.startswith("3") else "s4xx" if st.startswith("4") else "sdim"
            rows += f"<tr><td>{s.get('subdomain','-')}</td><td>{s.get('ip','-')}</td><td class='{cls}'>{st}</td><td>{s.get('source','-')}</td></tr>"
        return (f"<table><thead><tr><th>Subdomain</th><th>IP</th><th>Status</th><th>Source</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>")

    def generate(self, format: str = "html") -> str:
        domain    = urlparse(self.results.get("target","unknown")).netloc or "unknown"
        ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
        if format == "json": return self._json(domain, ts)
        if format == "txt":  return self._txt(domain, ts)
        return self._html(domain, ts)

    def _html(self, domain: str, ts: str) -> str:
        vulns = self.results.get("vulnerabilities",[])
        auth  = self.results.get("auth_findings",[])
        api   = self.results.get("api_findings",[])
        hdrs  = self.results.get("header_findings",[])
        subs  = self.results.get("subdomains",[])
        all_v = vulns + hdrs
        c = sum(1 for f in all_v+auth+api if f.get("severity")=="CRITICAL")
        h = sum(1 for f in all_v+auth+api if f.get("severity")=="HIGH")
        m = sum(1 for f in all_v+auth+api if f.get("severity")=="MEDIUM")
        l = sum(1 for f in all_v+auth+api if f.get("severity")=="LOW")
        score,level,cls = self._risk()
        html = HTML
        for k,v in {
            "{{TARGET}}":  self.results.get("target","?"),
            "{{SCAN_ID}}": str(self.results.get("scan_id","?")),
            "{{START}}":   self.results.get("start_time","?")[:19].replace("T"," "),
            "{{END}}":     self.results.get("end_time","?")[:19].replace("T"," "),
            "{{RISK_CLASS}}": cls, "{{RISK_SCORE}}": str(score), "{{RISK_LEVEL}}": level,
            "{{CC}}": str(c), "{{CH}}": str(h), "{{CM}}": str(m), "{{CL}}": str(l),
            "{{CS}}": str(len(subs)),
            "{{TV}}": str(len(all_v)), "{{TA}}": str(len(auth)), "{{TAP}}": str(len(api)),
            "{{FP_SEC}}":    self._fp_section(),
            "{{VULN_CARDS}}": self._cards(all_v),
            "{{AUTH_CARDS}}": self._cards(auth),
            "{{API_CARDS}}":  self._cards(api),
            "{{SUB_TABLE}}":  self._sub_table(),
            "{{GEN}}": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }.items():
            html = html.replace(k, str(v))
        fname = self.output_dir / f"nightx_{domain.replace('.','_')}_{ts}.html"
        fname.write_text(html, encoding="utf-8")
        console.print(f"[green]✅ HTML report: {fname}[/green]")
        return str(fname)

    def _json(self, domain: str, ts: str) -> str:
        fname = self.output_dir / f"nightx_{domain.replace('.','_')}_{ts}.json"
        fname.write_text(json.dumps(self.results, indent=2, default=str))
        console.print(f"[green]✅ JSON report: {fname}[/green]")
        return str(fname)

    def _txt(self, domain: str, ts: str) -> str:
        fname = self.output_dir / f"nightx_{domain.replace('.','_')}_{ts}.txt"
        all_f = (self.results.get("vulnerabilities",[]) + self.results.get("auth_findings",[]) +
                 self.results.get("api_findings",[]) + self.results.get("header_findings",[]))
        lines = ["="*60,"NIGHTX — PENETRATION TEST REPORT","="*60,
                 f"Target : {self.results.get('target','')}",
                 f"Started: {self.results.get('start_time','')}","","FINDINGS","-"*40]
        for f in all_f:
            lines.append(f"[{f.get('severity')}] {f.get('type')} — {f.get('detail','')}")
        lines.extend(["","SUBDOMAINS","-"*40])
        for s in self.results.get("subdomains",[]):
            lines.append(f"{s.get('subdomain')} → {s.get('ip')} ({s.get('status')})")
        fname.write_text("\n".join(lines))
        console.print(f"[green]✅ Text report: {fname}[/green]")
        return str(fname)

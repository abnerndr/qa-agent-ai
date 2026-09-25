#!/usr/bin/env python3
"""
qa_evidencias.py — captura de evidências e relatório PDF da skill qa-validacao-tasks.

Tudo gira em torno de uma pasta de execução (RUN_DIR) com:
  run.json        plano + status de cada caso (fonte do relatório)
  evidencias/     prints, vídeos, respostas HTTP
  relatorio.html  gerado por `relatorio`
  relatorio.pdf   gerado por `relatorio`

Subcomandos:
  init       cria RUN_DIR/run.json (ou importa um plano pronto com --plano)
  http       requisição HTTP sem seguir redirect; salva status, headers e trechos do body
  print      screenshot de uma URL (desktop/mobile, com ou sem JS, página inteira ou seletor)
  fluxo      sequência de ações no navegador (goto/click/fill/...) com vídeo e prints
  lighthouse auditoria Lighthouse (performance, SEO, acessibilidade, boas práticas)
  caso       cria/atualiza um caso no run.json (status, observado, esperado...)
  relatorio  gera relatorio.html + relatorio.pdf a partir do run.json

Toda evidência capturada com `--caso` é anexada automaticamente ao caso no run.json.
Rode com o Python do runtime da skill: <skill>/.venv/bin/python scripts/qa_evidencias.py ...
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

STATUS = ("confirmado", "divergente", "pendente", "pulado")
STATUS_COR = {
    "confirmado": "#1f7a3f",
    "divergente": "#b42318",
    "pendente": "#b54708",
    "pulado": "#667085",
}
VIEWPORTS = {"desktop": (1280, 800), "mobile": (375, 812)}
MAX_LINHAS_TEXTO = 60


# ---------------------------------------------------------------- run.json

def run_path(run_dir: Path) -> Path:
    return run_dir / "run.json"


def load_run(run_dir: Path) -> dict:
    p = run_path(run_dir)
    if not p.exists():
        sys.exit(f"[erro] {p} não existe — rode `init` primeiro")
    return json.loads(p.read_text(encoding="utf-8"))


def save_run(run_dir: Path, run: dict) -> None:
    run_path(run_dir).write_text(
        json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_caso(run: dict, caso_id: str) -> dict:
    for caso in run.setdefault("casos", []):
        if caso.get("id") == caso_id:
            return caso
    caso = {"id": caso_id, "status": "pendente", "evidencias": []}
    run["casos"].append(caso)
    return caso


def anexar(run_dir: Path, caso_id: str | None, arquivos: list[Path]) -> None:
    if not caso_id:
        return
    run = load_run(run_dir)
    caso = get_caso(run, caso_id)
    evid = caso.setdefault("evidencias", [])
    for arq in arquivos:
        rel = str(arq.relative_to(run_dir))
        if rel not in evid:
            evid.append(rel)
    save_run(run_dir, run)


def proximo_arquivo(run_dir: Path, caso_id: str | None, nome: str | None, ext: str) -> Path:
    pasta = run_dir / "evidencias"
    pasta.mkdir(parents=True, exist_ok=True)
    base = "-".join(p for p in (caso_id, slug(nome) if nome else None) if p) or "evidencia"
    alvo = pasta / f"{base}{ext}"
    n = 2
    while alvo.exists():
        alvo = pasta / f"{base}-{n}{ext}"
        n += 1
    return alvo


def slug(texto: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()[:60]


# ---------------------------------------------------------------- init / caso

def cmd_init(a: argparse.Namespace) -> None:
    run_dir = Path(a.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "evidencias").mkdir(exist_ok=True)
    if a.plano:
        run = json.loads(Path(a.plano).read_text(encoding="utf-8"))
    elif run_path(run_dir).exists():
        run = load_run(run_dir)
    else:
        run = {}
    for campo in ("titulo", "projeto", "pr", "branch", "ambiente", "responsavel"):
        valor = getattr(a, campo)
        if valor:
            run[campo] = valor
    run.setdefault("data", dt.date.today().isoformat())
    for chave in ("criterios", "divergencias", "pontos_em_aberto", "casos"):
        run.setdefault(chave, [])
    for caso in run["casos"]:
        caso.setdefault("status", "pendente")
        caso.setdefault("evidencias", [])
    save_run(run_dir, run)
    print(f"[ok] {run_path(run_dir)}")


def cmd_caso(a: argparse.Namespace) -> None:
    run_dir = Path(a.run_dir)
    run = load_run(run_dir)
    caso = get_caso(run, a.id)
    for campo in ("criterio", "titulo", "tipo", "passos", "esperado", "observado", "status"):
        valor = getattr(a, campo)
        if valor is not None:
            caso[campo] = valor
    for arq in a.evidencia or []:
        p = Path(arq)
        rel = str(p.relative_to(run_dir)) if p.is_absolute() else arq
        if rel not in caso.setdefault("evidencias", []):
            caso["evidencias"].append(rel)
    save_run(run_dir, run)
    print(f"[ok] {a.id}: {caso.get('status')}")


# ---------------------------------------------------------------- http

class _SemRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: D401 — não seguir
        return None


def cmd_http(a: argparse.Namespace) -> None:
    run_dir = Path(a.run_dir)
    headers = {"User-Agent": a.user_agent}
    for h in a.header or []:
        k, _, v = h.partition(":")
        headers[k.strip()] = v.strip()
    data = a.data.encode() if a.data else None
    req = urllib.request.Request(a.url, data=data, method=a.method, headers=headers)
    handlers = [] if a.follow else [_SemRedirect()]
    opener = urllib.request.build_opener(*handlers)
    try:
        resp = opener.open(req, timeout=a.timeout)
        status, reason, resp_headers, body = resp.status, resp.reason, resp.headers, resp.read()
    except urllib.error.HTTPError as e:  # 3xx sem follow, 4xx, 5xx
        status, reason, resp_headers, body = e.code, e.reason, e.headers, e.read()
    texto = body.decode("utf-8", errors="replace")

    linhas = [
        f"$ {a.method} {a.url}",
        *(f"> {k}: {v}" for k, v in headers.items() if k != "User-Agent"),
        "",
        f"HTTP {status} {reason}",
        *(f"{k}: {v}" for k, v in resp_headers.items()),
    ]
    for padrao in a.grep or []:
        achados = sorted({m.group(0) for m in re.finditer(padrao, texto)})
        linhas += ["", f"# grep /{padrao}/ → {len(achados)} ocorrência(s)"]
        linhas += [f"  {trecho[:300]}" for trecho in achados[:40]]
    if not a.grep:
        linhas += ["", "# body (início)", texto[:1500]]

    saida = proximo_arquivo(run_dir, a.caso, a.nome or "http", ".txt")
    saida.write_text("\n".join(linhas), encoding="utf-8")
    arquivos = [saida]
    if a.salvar_body:
        body_file = saida.with_suffix(".body.html")
        body_file.write_text(texto, encoding="utf-8")
        arquivos.append(body_file)
    anexar(run_dir, a.caso, [saida])
    print("\n".join(linhas[:12 + 3 * len(a.grep or [])]) if a.grep else "\n".join(linhas[:12]))
    print(f"\n[ok] evidência: {saida}")


# ---------------------------------------------------------------- navegador

def _playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit(
            "[erro] playwright não instalado neste Python. Rode o setup da skill: "
            "bash <skill>/scripts/setup.sh e use <skill>/.venv/bin/python"
        )
    return sync_playwright


def _contexto_opts(a: argparse.Namespace, video_dir: Path | None = None) -> dict:
    if a.viewport:
        w, _, h = a.viewport.partition("x")
        size = (int(w), int(h))
    else:
        size = VIEWPORTS["mobile" if a.mobile else "desktop"]
    opts = {
        "viewport": {"width": size[0], "height": size[1]},
        "java_script_enabled": not a.no_js,
        "locale": "pt-BR",
    }
    if a.mobile:
        opts.update(is_mobile=True, has_touch=True, device_scale_factor=2)
    if video_dir:
        opts["record_video_dir"] = str(video_dir)
        opts["record_video_size"] = opts["viewport"]
    return opts


def cmd_print(a: argparse.Namespace) -> None:
    run_dir = Path(a.run_dir)
    saida = proximo_arquivo(run_dir, a.caso, a.nome, ".png")
    with _playwright()() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(**_contexto_opts(a))
        page = ctx.new_page()
        resp = page.goto(a.url, wait_until=a.wait_until, timeout=a.timeout * 1000)
        if a.esperar:
            page.wait_for_selector(a.esperar, timeout=a.timeout * 1000)
        if a.selector:
            alvo = page.locator(a.selector).first
            alvo.scroll_into_view_if_needed()
            alvo.screenshot(path=str(saida))
        else:
            page.screenshot(path=str(saida), full_page=a.full_page)
        info = f"status={resp.status if resp else '?'} url_final={page.url}"
        browser.close()
    anexar(run_dir, a.caso, [saida])
    print(f"[ok] {info}\n[ok] evidência: {saida}")


def cmd_fluxo(a: argparse.Namespace) -> None:
    """Executa ações de um JSON: lista de objetos com UMA chave de ação cada.

    goto:URL · click:SELETOR · fill:[SELETOR, TEXTO] · press:[SELETOR, TECLA]
    wait_url:GLOB · wait_selector:SELETOR · wait_ms:N · scroll:"bottom"|SELETOR · wheel:PIXELS
    print:NOME (screenshot da viewport) · print_full:NOME · print_el:[SELETOR, NOME]
    eval:[EXPRESSAO_JS, NOME] (salva o resultado em .txt) · assert_url:REGEX
    """
    run_dir = Path(a.run_dir)
    acoes = json.loads(Path(a.acoes).read_text(encoding="utf-8")) if Path(a.acoes).exists() else json.loads(a.acoes)
    video_tmp = run_dir / "evidencias" / ".video-tmp"
    arquivos: list[Path] = []
    log: list[str] = []
    erro = None

    with _playwright()() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(**_contexto_opts(a, video_tmp if a.video else None))
        page = ctx.new_page()
        page.set_default_timeout(a.timeout * 1000)

        def rotulo(nome: str) -> str:
            # prefixa com --nome: fluxos do mesmo caso (ex.: uma seção por fluxo) não se misturam
            return f"{a.nome}-{nome}" if a.nome else nome

        def shot(nome: str, **kw) -> None:
            arq = proximo_arquivo(run_dir, a.caso, rotulo(nome), ".png")
            page.screenshot(path=str(arq), **kw)
            arquivos.append(arq)

        try:
            for i, acao in enumerate(acoes, 1):
                (tipo, valor), = acao.items()
                log.append(f"{i:02d}. {tipo} {json.dumps(valor, ensure_ascii=False)}")
                if tipo == "goto":
                    r = page.goto(valor, wait_until=a.wait_until)
                    log.append(f"    → status={r.status if r else '?'} url={page.url}")
                elif tipo == "click":
                    page.locator(valor).first.click()
                elif tipo == "fill":
                    page.locator(valor[0]).first.fill(valor[1])
                elif tipo == "press":
                    page.locator(valor[0]).first.press(valor[1])
                elif tipo == "wait_url":
                    page.wait_for_url(valor)
                elif tipo == "wait_selector":
                    page.wait_for_selector(valor)
                elif tipo == "wait_ms":
                    page.wait_for_timeout(int(valor))
                elif tipo == "wheel":
                    # rolagem real de usuário (roda do mouse no centro da tela)
                    vp = page.viewport_size or {"width": 1280, "height": 800}
                    page.mouse.move(vp["width"] / 2, vp["height"] / 2)
                    restante = int(valor)
                    while restante > 0:
                        page.mouse.wheel(0, min(400, restante))
                        restante -= 400
                        page.wait_for_timeout(50)
                    page.wait_for_timeout(500)
                    pos = page.evaluate(
                        "({winY: Math.round(scrollY), bodyTop: document.body.scrollTop})"
                    )
                    log.append(f"    → {json.dumps(pos)}")
                elif tipo == "scroll":
                    if valor == "bottom":
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    else:
                        page.locator(valor).first.scroll_into_view_if_needed()
                elif tipo == "print":
                    shot(valor)
                elif tipo == "print_full":
                    shot(valor, full_page=True)
                elif tipo == "print_el":
                    arq = proximo_arquivo(run_dir, a.caso, rotulo(valor[1]), ".png")
                    page.locator(valor[0]).first.screenshot(path=str(arq))
                    arquivos.append(arq)
                elif tipo == "eval":
                    resultado = page.evaluate(valor[0])
                    arq = proximo_arquivo(run_dir, a.caso, rotulo(valor[1]), ".txt")
                    arq.write_text(
                        f"// {page.url}\n// {valor[0]}\n"
                        + json.dumps(resultado, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    arquivos.append(arq)
                    log.append(f"    → {json.dumps(resultado, ensure_ascii=False)[:300]}")
                elif tipo == "assert_url":
                    if not re.search(valor, page.url):
                        raise AssertionError(f"URL {page.url!r} não casa com /{valor}/")
                    log.append(f"    → ok {page.url}")
                else:
                    raise ValueError(f"ação desconhecida: {tipo}")
        except Exception as e:  # falha também é evidência
            erro = f"{type(e).__name__}: {e}"
            log.append(f"    ✗ {erro}")
            try:
                shot("falha")
            except Exception:
                pass
        finally:
            video = page.video
            ctx.close()
            if video:
                destino = proximo_arquivo(run_dir, a.caso, a.nome or "fluxo", ".webm")
                Path(video.path()).rename(destino)
                arquivos.append(destino)
            browser.close()

    log_file = proximo_arquivo(run_dir, a.caso, (a.nome or "fluxo") + "-log", ".txt")
    log_file.write_text("\n".join(log), encoding="utf-8")
    arquivos.insert(0, log_file)
    anexar(run_dir, a.caso, arquivos)
    try:
        video_tmp.rmdir()
    except OSError:
        pass
    print("\n".join(log))
    print("\n".join(f"[ok] evidência: {f}" for f in arquivos))
    if erro:
        sys.exit(1)


# ---------------------------------------------------------------- lighthouse

LH_VERSAO = "12"
LH_METRICAS = (
    ("first-contentful-paint", "FCP"),
    ("largest-contentful-paint", "LCP"),
    ("total-blocking-time", "TBT"),
    ("cumulative-layout-shift", "CLS"),
    ("speed-index", "Speed Index"),
)
LH_MODOS_IGNORADOS = {"notApplicable", "manual", "informative", "error"}


def cmd_lighthouse(a: argparse.Namespace) -> None:
    import shutil
    import subprocess

    run_dir = Path(a.run_dir)
    if not shutil.which("npx"):
        sys.exit("[erro] Lighthouse precisa de Node/npx no PATH")
    with _playwright()() as p:
        chrome = p.chromium.executable_path
    if not Path(chrome).exists():
        sys.exit(f"[erro] Chromium do Playwright não encontrado em {chrome} — rode scripts/setup.sh")

    preset = "desktop" if a.desktop else "mobile"
    base = proximo_arquivo(run_dir, a.caso, f"{a.nome or 'lighthouse'}-{preset}", "")

    # O Chrome é iniciado aqui, e não pelo chrome-launcher do Lighthouse: no WSL o
    # chrome-launcher cria pastas lighthouse.XXXX no AppData\Local do Windows.
    # Perfil temporário em /tmp (Linux) e sem DISPLAY/WAYLAND_DISPLAY: nada toca o
    # Windows e nenhuma janela abre via WSLg, mesmo que o --headless seja ignorado.
    import os
    import socket
    import tempfile
    import time
    import urllib.request as _ur

    env = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY")}
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0))
        porta = sk.getsockname()[1]
    perfil = tempfile.mkdtemp(prefix="qa-lighthouse-")
    chrome_proc = subprocess.Popen(
        [chrome, "--headless=new", f"--remote-debugging-port={porta}", f"--user-data-dir={perfil}",
         "--no-sandbox", "--disable-dev-shm-usage", "--no-first-run", "--no-default-browser-check",
         "about:blank"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    cmd = [
        "npx", "-y", f"lighthouse@{LH_VERSAO}", a.url, "--quiet", f"--port={porta}",
        "--output=json", "--output=html", f"--output-path={base}",
        f"--only-categories={a.categorias}",
    ]
    if a.desktop:
        cmd.append("--preset=desktop")
    try:
        for _ in range(60):  # até ~15 s para o DevTools responder
            try:
                _ur.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=1).read()
                break
            except OSError:
                time.sleep(0.25)
        else:
            sys.exit("[erro] Chromium não abriu a porta de depuração")
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=a.timeout)
    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            chrome_proc.kill()
        shutil.rmtree(perfil, ignore_errors=True)
    json_file = base.with_name(base.name + ".report.json")
    html_file = base.with_name(base.name + ".report.html")
    if proc.returncode != 0 or not json_file.exists():
        erro = proximo_arquivo(run_dir, a.caso, f"{a.nome or 'lighthouse'}-{preset}-erro", ".txt")
        erro.write_text(f"$ {' '.join(cmd)}\n\n{proc.stdout}\n{proc.stderr}", encoding="utf-8")
        anexar(run_dir, a.caso, [erro])
        sys.exit(f"[erro] Lighthouse falhou (código {proc.returncode}) — ver {erro}")

    lhr = json.loads(json_file.read_text(encoding="utf-8"))
    audits = lhr.get("audits", {})
    linhas = [
        f"# Lighthouse {lhr.get('lighthouseVersion')} — {preset}",
        f"URL: {lhr.get('finalDisplayedUrl') or a.url}",
        f"Data: {lhr.get('fetchTime')}",
        "",
        "## Scores (0–100)",
    ]
    for cat in lhr.get("categories", {}).values():
        score = cat.get("score")
        linhas.append(f"  {cat.get('title'):<16} {'—' if score is None else round(score * 100)}")
    if "performance" in lhr.get("categories", {}):
        linhas += ["", "## Métricas"]
        for chave, rotulo in LH_METRICAS:
            au = audits.get(chave, {})
            linhas.append(f"  {rotulo:<12} {au.get('displayValue', '—')}")
    for cat_id, cat in lhr.get("categories", {}).items():
        falhas = []
        for ref in cat.get("auditRefs", []):
            au = audits.get(ref.get("id"), {})
            if au.get("scoreDisplayMode") in LH_MODOS_IGNORADOS or au.get("score") is None:
                continue
            if au["score"] < 0.9 and (ref.get("weight", 0) > 0 or cat_id == "seo"):
                falhas.append(f"  - [{round(au['score'] * 100):>3}] {au.get('title')}"
                              + (f" — {au['displayValue']}" if au.get("displayValue") else ""))
        if falhas:
            linhas += ["", f"## {cat.get('title')}: audits abaixo de 90"] + falhas[:12]
    avisos = lhr.get("runWarnings") or []
    if avisos:
        linhas += ["", "## Avisos do Lighthouse"] + [f"  - {w}" for w in avisos]
    linhas += ["", f"Relatório completo: {html_file.name} (anexo) · JSON: {json_file.name}"]

    resumo = base.with_name(base.name + ".txt")
    resumo.write_text("\n".join(linhas), encoding="utf-8")
    anexar(run_dir, a.caso, [resumo, html_file])
    print("\n".join(linhas))
    print(f"\n[ok] evidência: {resumo}\n[ok] evidência: {html_file}")


# ---------------------------------------------------------------- relatório

def _esc(v) -> str:
    return html.escape(str(v or ""))


def _multiline(v) -> str:
    return _esc(v).replace("\n", "<br>")


def _status_criterio(casos: list[dict]) -> str:
    st = [c.get("status", "pendente") for c in casos]
    if not st:
        return "pendente"
    if "divergente" in st:
        return "divergente"
    if all(s == "confirmado" for s in st):
        return "confirmado"
    return "pendente"


def _badge(status: str) -> str:
    cor = STATUS_COR.get(status, "#667085")
    return f'<span class="badge" style="background:{cor}">{_esc(status)}</span>'


def _evidencia_html(run_dir: Path, rel: str) -> str:
    arq = run_dir / rel
    nome = _esc(rel)
    if not arq.exists():
        return f'<div class="ev"><div class="ev-nome">{nome} — <b>arquivo não encontrado</b></div></div>'
    ext = arq.suffix.lower()
    if ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        mime = "image/png" if ext == ".png" else f"image/{ext[1:].replace('jpg', 'jpeg')}"
        b64 = base64.b64encode(arq.read_bytes()).decode()
        return f'<div class="ev"><div class="ev-nome">{nome}</div><img src="data:{mime};base64,{b64}"></div>'
    if ext in (".txt", ".log", ".json", ".md"):
        linhas = arq.read_text(encoding="utf-8", errors="replace").splitlines()
        corte = len(linhas) > MAX_LINHAS_TEXTO
        corpo = "\n".join(linhas[:MAX_LINHAS_TEXTO]) + (f"\n… (+{len(linhas) - MAX_LINHAS_TEXTO} linhas no arquivo)" if corte else "")
        return f'<div class="ev"><div class="ev-nome">{nome}</div><pre>{_esc(corpo)}</pre></div>'
    if ext in (".webm", ".mp4", ".mov"):
        return f'<div class="ev"><div class="ev-nome">🎥 {nome} — vídeo anexo na pasta da execução</div></div>'
    return f'<div class="ev"><div class="ev-nome">📎 {nome} — anexo</div></div>'


CSS = """
@page { size: A4; margin: 16mm 14mm 18mm; }
* { box-sizing: border-box; }
body { font: 10.5pt/1.45 -apple-system, "Segoe UI", Roboto, Arial, sans-serif; color: #101828; margin: 0; }
h1 { font-size: 19pt; margin: 0 0 4px; }
h2 { font-size: 13.5pt; margin: 22px 0 8px; padding-bottom: 4px; border-bottom: 2px solid #101828; }
h3 { font-size: 11.5pt; margin: 0; }
.sub { color: #475467; margin: 0 0 12px; }
.meta { display: grid; grid-template-columns: 110px 1fr; gap: 2px 10px; font-size: 9.5pt; margin-bottom: 10px; }
.meta b { color: #475467; font-weight: 600; }
.aviso { background: #f2f4f7; border-left: 4px solid #475467; padding: 8px 10px; font-size: 9.5pt; margin: 10px 0; }
table { width: 100%; border-collapse: collapse; font-size: 9.5pt; margin: 6px 0; }
th, td { border: 1px solid #d0d5dd; padding: 5px 7px; text-align: left; vertical-align: top; }
th { background: #f2f4f7; }
.badge { display: inline-block; color: #fff; border-radius: 10px; padding: 1px 8px; font-size: 8.5pt; font-weight: 600; white-space: nowrap; }
.caso { border: 1px solid #d0d5dd; border-radius: 6px; padding: 10px 12px; margin: 12px 0; page-break-inside: auto; }
.caso-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 6px; }
.campo { margin: 4px 0; font-size: 9.5pt; }
.campo b { color: #475467; }
.ev { margin-top: 8px; page-break-inside: avoid; }
.ev-nome { font-size: 8.5pt; color: #475467; margin-bottom: 3px; font-family: ui-monospace, Menlo, monospace; }
.ev img { max-width: 100%; max-height: 120mm; border: 1px solid #d0d5dd; }
pre { background: #0b1220; color: #e4e7ec; padding: 8px; border-radius: 4px; font-size: 7.8pt; white-space: pre-wrap; word-break: break-all; margin: 0; }
.cards { display: flex; gap: 8px; margin: 8px 0 4px; }
.card { flex: 1; border: 1px solid #d0d5dd; border-radius: 6px; padding: 6px 8px; }
.card .n { font-size: 16pt; font-weight: 700; }
.task { white-space: pre-wrap; font-size: 8.8pt; background: #f9fafb; border: 1px solid #eaecf0; padding: 8px; border-radius: 4px; }
"""


def montar_html(run_dir: Path, run: dict) -> str:
    casos = run.get("casos", [])
    criterios = run.get("criterios", [])
    contagem = {s: sum(1 for c in casos if c.get("status", "pendente") == s) for s in STATUS}

    partes = [f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><title>{_esc(run.get('titulo'))}</title><style>{CSS}</style></head><body>"]
    partes.append(f"<h1>Relatório de QA</h1><p class='sub'>{_esc(run.get('titulo'))}</p>")
    meta = [
        ("Projeto", run.get("projeto")), ("PR", run.get("pr")), ("Branch", run.get("branch")),
        ("Ambiente", run.get("ambiente")), ("Responsável", run.get("responsavel")),
        ("Data", run.get("data")), ("Gerado em", dt.datetime.now().strftime("%Y-%m-%d %H:%M")),
    ]
    partes.append("<div class='meta'>" + "".join(f"<b>{k}</b><span>{_esc(v)}</span>" for k, v in meta if v) + "</div>")
    partes.append(
        "<div class='aviso'>Evidências capturadas pelo agente de QA contra o ambiente indicado. "
        "Este relatório <b>não é veredito de aprovação</b>: casos divergentes e pendentes estão incluídos "
        "com a evidência do que foi observado. A decisão de aprovar a task é do dev/PM.</div>"
    )

    # 1. Resumo
    partes.append("<h2>1. Resumo</h2><div class='cards'>")
    for s in STATUS:
        partes.append(f"<div class='card'><div class='n' style='color:{STATUS_COR[s]}'>{contagem[s]}</div>{s}</div>")
    partes.append("</div>")
    if criterios:
        partes.append("<table><tr><th>Critério</th><th>Descrição</th><th>Casos</th><th>Situação</th></tr>")
        for cr in criterios:
            dos = [c for c in casos if c.get("criterio") == cr.get("id")]
            ids = ", ".join(c["id"] for c in dos) or "—"
            partes.append(
                f"<tr><td><b>{_esc(cr.get('id'))}</b></td><td>{_multiline(cr.get('texto'))}</td>"
                f"<td>{_esc(ids)}</td><td>{_badge(_status_criterio(dos))}</td></tr>"
            )
        partes.append("</table>")

    # 2. Divergências e pontos em aberto
    sec = 2
    if run.get("divergencias"):
        partes.append(f"<h2>{sec}. Divergências entre entrega e task</h2>")
        partes.append("<table><tr><th>#</th><th>Divergência</th><th>Decisão</th></tr>")
        for d in run["divergencias"]:
            partes.append(
                f"<tr><td><b>{_esc(d.get('id'))}</b></td><td>{_multiline(d.get('descricao'))}</td>"
                f"<td>{_multiline(d.get('decisao') or 'em aberto')}</td></tr>"
            )
        partes.append("</table>")
        sec += 1
    if run.get("pontos_em_aberto"):
        partes.append(f"<h2>{sec}. Pontos em aberto</h2><ul>")
        partes += [f"<li>{_multiline(p)}</li>" for p in run["pontos_em_aberto"]]
        partes.append("</ul>")
        sec += 1

    # Tabela de casos
    partes.append(f"<h2>{sec}. Casos de teste</h2>")
    partes.append("<table><tr><th>Caso</th><th>Critério</th><th>Tipo</th><th>Título</th><th>Status</th></tr>")
    for c in casos:
        partes.append(
            f"<tr><td><b>{_esc(c.get('id'))}</b></td><td>{_esc(c.get('criterio'))}</td><td>{_esc(c.get('tipo'))}</td>"
            f"<td>{_esc(c.get('titulo'))}</td><td>{_badge(c.get('status', 'pendente'))}</td></tr>"
        )
    partes.append("</table>")
    sec += 1

    # Detalhe + evidências
    partes.append(f"<h2>{sec}. Detalhe e evidências</h2>")
    for c in casos:
        partes.append("<div class='caso'>")
        partes.append(
            f"<div class='caso-head'><h3>{_esc(c.get('id'))} — {_esc(c.get('titulo'))}</h3>{_badge(c.get('status', 'pendente'))}</div>"
        )
        for rotulo, campo in (("Critério", "criterio"), ("Tipo", "tipo"), ("Passos", "passos"), ("Esperado", "esperado"), ("Observado", "observado")):
            if c.get(campo):
                partes.append(f"<div class='campo'><b>{rotulo}:</b> {_multiline(c.get(campo))}</div>")
        evid = c.get("evidencias") or []
        if not evid:
            partes.append("<div class='campo'><b>Evidências:</b> nenhuma capturada</div>")
        partes += [_evidencia_html(run_dir, rel) for rel in evid]
        partes.append("</div>")

    if run.get("task"):
        sec += 1
        partes.append(f"<h2>{sec}. Texto original da task</h2><div class='task'>{_esc(run['task'])}</div>")

    partes.append("</body></html>")
    return "".join(partes)


def cmd_relatorio(a: argparse.Namespace) -> None:
    run_dir = Path(a.run_dir).resolve()
    run = load_run(run_dir)
    html_file = run_dir / "relatorio.html"
    pdf_file = run_dir / (a.saida or "relatorio.pdf")
    html_file.write_text(montar_html(run_dir, run), encoding="utf-8")
    with _playwright()() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_file.as_uri(), wait_until="load")
        page.pdf(
            path=str(pdf_file),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template="<span></span>",
            footer_template=(
                "<div style='font-size:7pt;color:#667085;width:100%;padding:0 14mm;display:flex;justify-content:space-between'>"
                f"<span>{_esc(run.get('titulo'))}</span>"
                "<span><span class='pageNumber'></span>/<span class='totalPages'></span></span></div>"
            ),
            margin={"top": "16mm", "bottom": "18mm", "left": "14mm", "right": "14mm"},
        )
        browser.close()
    print(f"[ok] {html_file}\n[ok] {pdf_file}")


# ---------------------------------------------------------------- CLI

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def nav_args(sp):
        sp.add_argument("--mobile", action="store_true", help="viewport 375x812 com touch")
        sp.add_argument("--viewport", help="LxA, ex.: 1440x900")
        sp.add_argument("--no-js", action="store_true", help="desliga JavaScript (checa HTML do servidor)")
        sp.add_argument("--wait-until", default="load", choices=["load", "domcontentloaded", "networkidle", "commit"])
        sp.add_argument("--timeout", type=int, default=45, help="segundos")

    sp = sub.add_parser("init", help="cria/atualiza run.json")
    sp.add_argument("run_dir")
    sp.add_argument("--plano", help="JSON com o plano completo (criterios, casos, divergencias...)")
    for campo in ("titulo", "projeto", "pr", "branch", "ambiente", "responsavel"):
        sp.add_argument(f"--{campo}")
    sp.set_defaults(fn=cmd_init)

    sp = sub.add_parser("caso", help="cria/atualiza um caso")
    sp.add_argument("run_dir")
    sp.add_argument("id")
    for campo in ("criterio", "titulo", "tipo", "passos", "esperado", "observado"):
        sp.add_argument(f"--{campo}")
    sp.add_argument("--status", choices=STATUS)
    sp.add_argument("--evidencia", action="append", help="caminho relativo ao run_dir (repetível)")
    sp.set_defaults(fn=cmd_caso)

    sp = sub.add_parser("http", help="requisição HTTP sem seguir redirect")
    sp.add_argument("run_dir")
    sp.add_argument("url")
    sp.add_argument("--caso")
    sp.add_argument("--nome")
    sp.add_argument("--method", default="GET")
    sp.add_argument("--header", action="append", help="'Nome: valor' (repetível)")
    sp.add_argument("--data", help="body da requisição")
    sp.add_argument("--grep", action="append", help="regex a extrair do body (repetível)")
    sp.add_argument("--follow", action="store_true", help="seguir redirects")
    sp.add_argument("--salvar-body", action="store_true", help="salva o body completo em .body.html")
    sp.add_argument("--timeout", type=int, default=45)
    sp.add_argument("--user-agent", default="Mozilla/5.0 (qa-validacao-tasks)")
    sp.set_defaults(fn=cmd_http)

    sp = sub.add_parser("print", help="screenshot de uma URL")
    sp.add_argument("run_dir")
    sp.add_argument("url")
    sp.add_argument("--caso")
    sp.add_argument("--nome")
    sp.add_argument("--full-page", action="store_true")
    sp.add_argument("--selector", help="print só deste elemento")
    sp.add_argument("--esperar", help="seletor a aguardar antes do print")
    nav_args(sp)
    sp.set_defaults(fn=cmd_print)

    sp = sub.add_parser("fluxo", help="ações no navegador com vídeo/prints")
    sp.add_argument("run_dir")
    sp.add_argument("acoes", help="arquivo .json ou string JSON com a lista de ações")
    sp.add_argument("--caso")
    sp.add_argument("--nome")
    sp.add_argument("--video", action="store_true")
    nav_args(sp)
    sp.set_defaults(fn=cmd_fluxo)

    sp = sub.add_parser("lighthouse", help="auditoria Lighthouse (performance, SEO, acessibilidade, boas práticas)")
    sp.add_argument("run_dir")
    sp.add_argument("url")
    sp.add_argument("--caso")
    sp.add_argument("--nome")
    sp.add_argument("--desktop", action="store_true", help="preset desktop (padrão: mobile)")
    sp.add_argument("--categorias", default="performance,seo,accessibility,best-practices")
    sp.add_argument("--timeout", type=int, default=240, help="segundos")
    sp.set_defaults(fn=cmd_lighthouse)

    sp = sub.add_parser("relatorio", help="gera relatorio.html + relatorio.pdf")
    sp.add_argument("run_dir")
    sp.add_argument("--saida", help="nome do PDF (padrão relatorio.pdf)")
    sp.set_defaults(fn=cmd_relatorio)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

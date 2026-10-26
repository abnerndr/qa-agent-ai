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
  explorar   varre a aplicação sozinho (só GET, sem IA) e registra erros como casos
  caso       cria/atualiza um caso no run.json (status, observado, esperado...)
  status     lista os casos e o status de cada um (uma linha por caso)
  relatorio  gera relatorio.html + relatorio.pdf a partir do run.json

Toda evidência capturada com `--caso` é anexada automaticamente ao caso no run.json.
Vários agentes podem rodar comandos na mesma RUN_DIR ao mesmo tempo: o run.json é
gravado com trava de arquivo e os nomes de evidência são reservados atomicamente.
Rode com o Python do runtime da skill: <skill>/.venv/bin/python scripts/qa_evidencias.py ...
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
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
    # grava num temporário e troca: quem lê nunca vê o arquivo pela metade
    tmp = run_path(run_dir).with_name(f".run.json.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, run_path(run_dir))


@contextlib.contextmanager
def trava_run(run_dir: Path):
    """Trava exclusiva do run.json: vários agentes atualizam casos diferentes em paralelo."""
    run_dir.mkdir(parents=True, exist_ok=True)
    with open(run_dir / ".run.lock", "a+") as f:
        if os.name == "nt":
            import msvcrt
            while True:
                try:
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.05)
            try:
                yield
            finally:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)


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
    with trava_run(run_dir):
        run = load_run(run_dir)
        caso = get_caso(run, caso_id)
        evid = caso.setdefault("evidencias", [])
        for arq in arquivos:
            rel = arq.relative_to(run_dir).as_posix()
            if rel not in evid:
                evid.append(rel)
        save_run(run_dir, run)


def proximo_arquivo(run_dir: Path, caso_id: str | None, nome: str | None, ext: str,
                    reservar: bool = True) -> Path:
    pasta = run_dir / "evidencias"
    pasta.mkdir(parents=True, exist_ok=True)
    base = "-".join(p for p in (caso_id, slug(nome) if nome else None) if p) or "evidencia"
    alvo = pasta / f"{base}{ext}"
    n = 2
    while True:
        try:
            if not reservar:
                if alvo.exists():
                    raise FileExistsError
                return alvo
            # cria o arquivo vazio de forma exclusiva: dois agentes nunca pegam o mesmo nome
            with open(alvo, "x"):
                return alvo
        except FileExistsError:
            alvo = pasta / f"{base}-{n}{ext}"
            n += 1


def slug(texto: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()[:60]


# ---------------------------------------------------------------- init / caso

def cmd_init(a: argparse.Namespace) -> None:
    run_dir = Path(a.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "evidencias").mkdir(exist_ok=True)
    with trava_run(run_dir):
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

    def rel(arq: str) -> str:
        p = Path(arq)
        return p.relative_to(run_dir.resolve()).as_posix() if p.is_absolute() else arq

    with trava_run(run_dir):
        run = load_run(run_dir)
        caso = get_caso(run, a.id)
        for campo in ("criterio", "titulo", "tipo", "passos", "esperado", "observado", "resumo", "status"):
            valor = getattr(a, campo)
            if valor is not None:
                caso[campo] = valor
        for arq in (a.evidencia or []) + (a.destaque or []):
            if rel(arq) not in caso.setdefault("evidencias", []):
                caso["evidencias"].append(rel(arq))
        if a.destaque:
            # destaque = evidência mostrada no PDF; o resto fica só listado (ou no --completo)
            caso["destaques"] = [rel(arq) for arq in a.destaque]
        save_run(run_dir, run)
    print(f"[ok] {a.id}: {caso.get('status')}")


def cmd_status(a: argparse.Namespace) -> None:
    """Uma linha por caso: o orquestrador consolida o trabalho dos agentes sem ler o run.json."""
    run = load_run(Path(a.run_dir))
    casos = run.get("casos", [])
    if a.so:
        casos = [c for c in casos if c.get("status", "pendente") in a.so]
    for c in casos:
        print(f"{c.get('id', '?'):<7} {c.get('status', 'pendente'):<11} {_resumo(c) or c.get('titulo', '')}")
    todos = run.get("casos", [])
    print(" · ".join(f"{s}={sum(1 for c in todos if c.get('status', 'pendente') == s)}" for s in STATUS))


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
    eval:EXPRESSAO_JS ou [EXPRESSAO_JS, NOME] (resultado vai para o log, não gera arquivo)
    assert_url:REGEX · assert_visible:SELETOR · assert_hidden:SELETOR
    assert_text:[SELETOR, REGEX] · assert_count:[SELETOR, N] · assert_eval:[EXPRESSAO_JS, VALOR_ESPERADO]
    Cada assert grava "✓ ok"/"✗" no log; o primeiro que falhar encerra o fluxo com print da falha.
    """
    run_dir = Path(a.run_dir)
    acoes = json.loads(Path(a.acoes).read_text(encoding="utf-8")) if Path(a.acoes).exists() else json.loads(a.acoes)
    video_tmp = run_dir / "evidencias" / f".video-tmp-{os.getpid()}"  # por processo: fluxos paralelos
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
                    expr, nome = (valor, None) if isinstance(valor, str) else (valor[0], valor[1])
                    resultado = page.evaluate(expr)
                    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
                    log.append(f"    → {nome + ' = ' if nome else ''}{texto[:2000]}")
                elif tipo == "assert_url":
                    if not re.search(valor, page.url):
                        raise AssertionError(f"URL {page.url!r} não casa com /{valor}/")
                    log.append(f"    ✓ ok {page.url}")
                elif tipo == "assert_visible":
                    page.locator(valor).first.wait_for(state="visible")
                    log.append("    ✓ ok visível")
                elif tipo == "assert_hidden":
                    if page.locator(valor).first.is_visible():
                        raise AssertionError(f"{valor!r} está visível")
                    log.append("    ✓ ok não visível")
                elif tipo == "assert_text":
                    loc = page.locator(valor[0]).first
                    loc.wait_for(state="attached")
                    txt = loc.inner_text()
                    if not re.search(valor[1], txt):
                        raise AssertionError(f"texto {txt[:200]!r} não casa com /{valor[1]}/")
                    log.append(f"    ✓ ok {txt[:120]!r}")
                elif tipo == "assert_count":
                    n = page.locator(valor[0]).count()
                    if n != int(valor[1]):
                        raise AssertionError(f"{valor[0]!r}: {n} elementos, esperado {valor[1]}")
                    log.append(f"    ✓ ok {n} elementos")
                elif tipo == "assert_eval":
                    resultado = page.evaluate(valor[0])
                    if resultado != valor[1]:
                        raise AssertionError(f"resultado {resultado!r}, esperado {valor[1]!r}")
                    log.append(f"    ✓ ok {json.dumps(resultado, ensure_ascii=False)[:120]}")
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
                os.replace(video.path(), destino)
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
    npx = shutil.which("npx")  # caminho completo: no Windows é npx.cmd, que o subprocess não acha sozinho
    if not npx:
        sys.exit("[erro] Lighthouse precisa de Node/npx no PATH")
    with _playwright()() as p:
        chrome = p.chromium.executable_path
    if not Path(chrome).exists():
        sys.exit(f"[erro] Chromium do Playwright não encontrado em {chrome} — rode scripts/setup.sh")

    preset = "desktop" if a.desktop else "mobile"
    base = proximo_arquivo(run_dir, a.caso, f"{a.nome or 'lighthouse'}-{preset}", "", reservar=False)

    # O Chrome é iniciado aqui, e não pelo chrome-launcher do Lighthouse: no WSL o
    # chrome-launcher cria pastas lighthouse.XXXX no AppData\Local do Windows.
    # Perfil temporário em /tmp (Linux) e sem DISPLAY/WAYLAND_DISPLAY: nada toca o
    # Windows e nenhuma janela abre via WSLg, mesmo que o --headless seja ignorado.
    import socket
    import tempfile
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
        npx, "-y", f"lighthouse@{LH_VERSAO}", a.url, "--quiet", f"--port={porta}",
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


# ---------------------------------------------------------------- explorar

EXP_IGNORAR = r"(?i)(logout|log-out|signout|sign-out|sair|excluir|delete|remover|unsubscribe|descadastr)"
EXP_ARQUIVOS = re.compile(r"(?i)\.(pdf|zip|rar|gz|jpe?g|png|gif|webp|avif|svg|ico|mp4|webm|mp3|docx?|xlsx?|pptx?|csv|xml|txt|json)$")
# (id, título, esperado, chave em cada página). Mesmo check em N páginas = um caso só.
EXP_CHECKS = (
    ("01", "Páginas e links internos respondem sem erro", "nenhuma página/link interno com status ≥ 400 ou falha de navegação", "pagina"),
    ("02", "Sem exceções JavaScript não tratadas", "0 eventos pageerror", "js"),
    ("03", "Sem erros no console", "0 console.error", "console"),
    ("04", "Requisições da própria origem sem falha", "nenhuma requisição same-origin com status ≥ 400 ou falha de rede", "rede"),
    ("05", "Imagens carregam", "nenhuma <img> quebrada (naturalWidth = 0)", "imagens"),
    ("06", "Sem rolagem horizontal", "scrollWidth ≤ largura da viewport", "overflow"),
)


def cmd_explorar(a: argparse.Namespace) -> None:
    """Teste autônomo: navega a aplicação a partir de URLs-semente seguindo só links (GET).

    Não clica em botões nem envia formulário. Em cada página coleta status, exceções JS,
    console.error, requisições com erro, imagens quebradas e rolagem horizontal. O resultado
    vira um caso por tipo de problema (prefixo --prefixo, ex.: EX01..EX06), com status
    `divergente` quando algo foi achado. A saída no terminal é curta de propósito: a IA lê
    o resumo e só abre o log (evidencias/<prefixo>-explorar-log.txt) quando precisa.
    """
    run_dir = Path(a.run_dir)
    sementes = [a.url] + (a.semente or [])
    origem = urllib.parse.urlsplit(a.url)
    ignorar = re.compile(a.ignorar) if a.ignorar else None

    def normalizar(u: str) -> str:
        p = urllib.parse.urlsplit(u)
        return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path or "/", p.query if a.com_query else "", ""))

    def aceita(u: str) -> bool:
        p = urllib.parse.urlsplit(u)
        return (p.scheme in ("http", "https") and p.netloc == origem.netloc
                and p.path.startswith(a.prefixo_url) and not EXP_ARQUIVOS.search(p.path)
                and not (ignorar and ignorar.search(u)))

    fila = deque((normalizar(s), 0, None) for s in sementes)
    vistos = {f[0] for f in fila}
    paginas: list[dict] = []
    prints: dict[str, Path] = {}

    with _playwright()() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(**_contexto_opts(a))
        page = ctx.new_page()
        page.set_default_timeout(a.timeout * 1000)
        atual: dict = {}

        def mesma_origem(u: str) -> bool:
            return urllib.parse.urlsplit(u).netloc == origem.netloc

        def on_console(m):
            # "Failed to load resource" repete o que os checks de página/rede já registram
            if m.type == "error" and not m.text.startswith("Failed to load resource"):
                atual["console"].append(m.text[:300])

        def on_falha(r):
            erro = r.failure or ""
            if "ERR_ABORTED" in erro or r.url == atual.get("url"):  # navegação cancelada não é bug
                return
            alvo = "rede" if mesma_origem(r.url) else "terceiros"
            atual[alvo].append(f"falha {r.method} {r.url[:200]} ({erro})")

        def on_resposta(r):
            if r.status >= 400 and r.request.resource_type != "document":
                alvo = "rede" if mesma_origem(r.url) else "terceiros"
                atual[alvo].append(f"{r.status} {r.request.method} {r.url[:200]}")

        page.on("console", on_console)
        page.on("pageerror", lambda e: atual["js"].append(str(e)[:300]))
        page.on("requestfailed", on_falha)
        page.on("response", on_resposta)

        while fila and len(paginas) < a.max_paginas:
            url, prof, origem_link = fila.popleft()
            atual.clear()
            atual.update(url=url, js=[], console=[], rede=[], terceiros=[], imagens=[], overflow=[], pagina=[])
            status = None
            try:
                resp = page.goto(url, wait_until=a.wait_until)
                status = resp.status if resp else None
                page.wait_for_timeout(a.espera_ms)  # deixa hidratação/efeitos dispararem erros
                if status and status >= 400:
                    atual["pagina"].append(f"HTTP {status}" + (f" (link vindo de {origem_link})" if origem_link else ""))
                if not mesma_origem(page.url):
                    atual["pagina"].append(f"redirecionou para fora: {page.url[:200]}")
                atual["imagens"] += page.evaluate(
                    "[...document.images].filter(i => i.complete && i.currentSrc && i.naturalWidth === 0)"
                    ".map(i => i.currentSrc.slice(0, 200))")
                largura = page.evaluate("[document.documentElement.scrollWidth, innerWidth]")
                if largura[0] > largura[1] + 1:
                    atual["overflow"].append(f"scrollWidth {largura[0]}px > viewport {largura[1]}px")
                if prof < a.profundidade and mesma_origem(page.url):
                    for href in page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)"):
                        alvo = normalizar(href)
                        if alvo not in vistos and aceita(alvo):
                            vistos.add(alvo)
                            fila.append((alvo, prof + 1, url))
            except Exception as e:  # falha de navegação também é achado
                atual["pagina"].append(f"{type(e).__name__}: {str(e).splitlines()[0][:200]}")
            problemas = {k: list(atual[k]) for k in [c[3] for c in EXP_CHECKS] + ["terceiros"]}
            achou = any(problemas[c[3]] for c in EXP_CHECKS)
            if achou and len(prints) < a.max_prints:
                try:
                    arq = proximo_arquivo(run_dir, a.prefixo, f"explorar-{len(paginas) + 1:02d}", ".png")
                    page.screenshot(path=str(arq))
                    prints[url] = arq
                except Exception:
                    pass
            paginas.append({"url": url, "status": status, "profundidade": prof, **problemas})
        browser.close()

    # log completo para quem precisar investigar; o terminal só recebe o resumo
    log = [f"# Exploração autônoma — {a.url}", f"{len(paginas)} página(s), profundidade ≤ {a.profundidade}, "
           f"{'mobile' if a.mobile else 'desktop'}, JS {'off' if a.no_js else 'on'}", ""]
    for pg in paginas:
        itens = [(k, v) for k, v in pg.items() if isinstance(v, list) and v]
        log.append(f"[{pg['status'] or '—'}] {pg['url']}" + ("" if itens else "  ✓"))
        for k, v in itens:
            log += [f"    {k}: {x}" for x in v[:10]] + ([f"    {k}: … +{len(v) - 10}"] if len(v) > 10 else [])
    log_file = proximo_arquivo(run_dir, a.prefixo, "explorar-log", ".txt")
    log_file.write_text("\n".join(log), encoding="utf-8")
    json_file = proximo_arquivo(run_dir, a.prefixo, "explorar", ".json")
    json_file.write_text(json.dumps(paginas, ensure_ascii=False, indent=2), encoding="utf-8")

    with trava_run(run_dir):
        run = load_run(run_dir) if run_path(run_dir).exists() else {
            "titulo": f"Exploração autônoma — {origem.netloc}", "ambiente": a.url,
            "data": dt.date.today().isoformat(), "escopo": {"tipo": "exploratorio"},
            "criterios": [], "divergencias": [], "pontos_em_aberto": [], "casos": []}
        criterio = a.prefixo
        if not any(c.get("id") == criterio for c in run.setdefault("criterios", [])):
            run["criterios"].append({"id": criterio, "texto": (
                f"Exploração autônoma a partir de {', '.join(sementes)}: a aplicação navega sem erros "
                "de página, JavaScript, console, rede, imagem ou layout (não vem da task)")})
        saida = []
        checks = list(EXP_CHECKS)
        if any(pg["terceiros"] for pg in paginas):
            checks.append(("07", "Recursos de terceiros (informativo)", "sem erro em domínios de terceiros", "terceiros"))
        for num, titulo, esperado, chave in checks:
            com = [pg for pg in paginas if pg[chave]]
            mensagens: dict[str, int] = {}
            for pg in com:
                for m in set(pg[chave]):
                    mensagens[m] = mensagens.get(m, 0) + 1
            top = sorted(mensagens.items(), key=lambda kv: -kv[1])[:5]
            caso = get_caso(run, f"{a.prefixo}{num}")
            caso.update(criterio=criterio, titulo=titulo, tipo="Exploratório",
                        passos=f"`explorar` em {len(paginas)} página(s)", esperado=esperado)
            if not com:
                caso.update(status="confirmado", resumo=f"0 de {len(paginas)} páginas com problema",
                            observado=f"Nenhum problema em {len(paginas)} página(s).")
            else:
                caso.update(
                    status="pendente" if chave == "terceiros" else "divergente",
                    resumo=f"{len(com)} de {len(paginas)} páginas: {top[0][0][:110]}",
                    observado="\n".join(f"{n}× página(s): {m}" for m, n in top)
                              + "\nPáginas: " + ", ".join(pg["url"] for pg in com[:8])
                              + (f" … +{len(com) - 8}" if len(com) > 8 else ""))
            evid = [log_file] + [prints[pg["url"]] for pg in com if pg["url"] in prints][:2]
            caso["evidencias"] = [e.relative_to(run_dir).as_posix() for e in evid]
            caso["destaques"] = caso["evidencias"][1:2] or caso["evidencias"][:1]
            saida.append(f"{caso['id']} {'✓' if caso['status'] == 'confirmado' else '✗'} {caso['status']}: {caso['resumo']}")
        save_run(run_dir, run)

    print(f"[ok] {len(paginas)} página(s) exploradas, {len(prints)} print(s)")
    print("\n".join(saida))
    print(f"[ok] log: {log_file}")
    if a.falhar and any(" divergente:" in linha for linha in saida):
        sys.exit(1)  # para CI/cron: código 1 quando a exploração acha erro


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
.ev img { max-width: 100%; max-height: 95mm; border: 1px solid #d0d5dd; }
pre { background: #0b1220; color: #e4e7ec; padding: 8px; border-radius: 4px; font-size: 7.8pt; white-space: pre-wrap; word-break: break-all; margin: 0; }
.cards { display: flex; gap: 8px; margin: 8px 0 4px; }
.card { flex: 1; border: 1px solid #d0d5dd; border-radius: 6px; padding: 6px 8px; }
.card .n { font-size: 16pt; font-weight: 700; }
.task { white-space: pre-wrap; font-size: 8.8pt; background: #f9fafb; border: 1px solid #eaecf0; padding: 8px; border-radius: 4px; }
"""


IMAGENS = (".png", ".jpg", ".jpeg", ".webp", ".gif")
VIDEOS = (".webm", ".mp4", ".mov")


def _resumo(c: dict) -> str:
    """Uma linha para a tabela: --resumo, ou a primeira frase do observado."""
    if c.get("resumo"):
        return c["resumo"]
    obs = (c.get("observado") or "").strip()
    frase = re.split(r"(?<=[.!?])\s|\n", obs, maxsplit=1)[0]
    return frase if len(frase) <= 160 else frase[:157] + "…"


def _principais(c: dict) -> list[str]:
    """Evidências exibidas no PDF enxuto: destaques, ou a primeira imagem, ou o primeiro texto."""
    if c.get("destaques"):
        return c["destaques"]
    evid = c.get("evidencias") or []
    for exts in (IMAGENS, (".txt", ".log", ".json", ".md")):
        achou = [e for e in evid if Path(e).suffix.lower() in exts and "-log" not in Path(e).stem]
        if achou:
            return achou[:1]
    return evid[:1] if evid and Path(evid[0]).suffix.lower() not in VIDEOS else []


def _bloco_caso(run_dir: Path, c: dict, completo: bool) -> str:
    partes = ["<div class='caso'>"]
    partes.append(
        f"<div class='caso-head'><h3>{_esc(c.get('id'))} — {_esc(c.get('titulo'))}</h3>{_badge(c.get('status', 'pendente'))}</div>"
    )
    campos = (("Critério", "criterio"), ("Tipo", "tipo"), ("Passos", "passos")) if completo else ()
    for rotulo, campo in campos + (("Esperado", "esperado"), ("Observado", "observado")):
        if c.get(campo):
            partes.append(f"<div class='campo'><b>{rotulo}:</b> {_multiline(c.get(campo))}</div>")
    evid = c.get("evidencias") or []
    mostrar = evid if completo else _principais(c)
    partes += [_evidencia_html(run_dir, rel) for rel in mostrar]
    resto = [e for e in evid if e not in mostrar]
    if not evid:
        partes.append("<div class='campo'><b>Evidências:</b> nenhuma capturada</div>")
    elif resto:
        videos = [e for e in resto if Path(e).suffix.lower() in VIDEOS]
        txt = f"+{len(resto)} arquivo(s) em <code>evidencias/</code>"
        if videos:
            txt += " — vídeo: " + ", ".join(f"<code>{_esc(Path(v).name)}</code>" for v in videos)
        partes.append(f"<div class='ev-nome'>{txt}</div>")
    partes.append("</div>")
    return "".join(partes)


def montar_html(run_dir: Path, run: dict, completo: bool = False) -> str:
    casos = run.get("casos", [])
    criterios = run.get("criterios", [])
    contagem = {s: sum(1 for c in casos if c.get("status", "pendente") == s) for s in STATUS}

    partes = [f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><title>{_esc(run.get('titulo'))}</title><style>{CSS}</style></head><body>"]
    partes.append(f"<h1>Relatório de QA</h1><p class='sub'>{_esc(run.get('titulo'))}</p>")
    meta = [
        ("Projeto", run.get("projeto")), ("PR", run.get("pr")), ("Branch", run.get("branch")),
        ("Ambiente", run.get("ambiente")), ("Responsável", run.get("responsavel")),
        ("Data", run.get("data")),
    ]
    escopo = run.get("escopo") or {}
    if escopo.get("tipo") == "funcionalidade":
        meta.insert(4, ("Escopo", f"Funcionalidade: {escopo.get('funcionalidade') or '—'} (o resto da página não foi validado)"))
        if escopo.get("como_testar"):
            meta.insert(5, ("Como testar", escopo["como_testar"]))
    elif escopo.get("tipo") == "exploratorio":
        meta.insert(4, ("Escopo", "Exploração autônoma (sem task): erros de página, JS, console, rede, imagem e layout"))
    else:
        meta.insert(4, ("Escopo", "Task completa"))
    fontes = run.get("fontes") or {}
    meta += [("Task (Slack)", fontes.get("slack")), ("PRD", fontes.get("prd"))]
    partes.append("<div class='meta'>" + "".join(f"<b>{k}</b><span>{_esc(v)}</span>" for k, v in meta if v) + "</div>")
    partes.append(
        "<div class='aviso'>Evidências capturadas pelo agente de QA. <b>Não é veredito de aprovação</b>: "
        "a decisão de aprovar a task é do dev/PM.</div>"
    )

    # 1. Resumo: contagem + critérios
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

    # 2. Achados: o que o dev precisa ler primeiro
    sec = 2
    achados = [c for c in casos if c.get("status", "pendente") in ("divergente", "pendente")]
    if achados:
        partes.append(f"<h2>{sec}. Achados (divergentes e pendentes)</h2>")
        partes += [_bloco_caso(run_dir, c, completo) for c in achados]
        sec += 1

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

    # Tabela de casos, uma linha cada
    partes.append(f"<h2>{sec}. Casos de teste</h2>")
    partes.append("<table><tr><th>Caso</th><th>Crit.</th><th>Tipo</th><th>Título</th><th>Resultado</th><th>Status</th></tr>")
    for c in casos:
        partes.append(
            f"<tr><td><b>{_esc(c.get('id'))}</b></td><td>{_esc(c.get('criterio'))}</td><td>{_esc(c.get('tipo'))}</td>"
            f"<td>{_esc(c.get('titulo'))}</td><td>{_esc(_resumo(c))}</td><td>{_badge(c.get('status', 'pendente'))}</td></tr>"
        )
    partes.append("</table>")
    sec += 1

    # Evidências dos demais casos (os achados já apareceram acima)
    resto = [c for c in casos if c not in achados]
    if resto:
        partes.append(f"<h2>{sec}. Evidências dos casos {'' if completo else 'confirmados/pulados'}</h2>")
        partes += [_bloco_caso(run_dir, c, completo) for c in resto]
        sec += 1

    if completo and run.get("task"):
        partes.append(f"<h2>{sec}. Texto original da task</h2><div class='task'>{_esc(run['task'])}</div>")

    partes.append("</body></html>")
    return "".join(partes)


def _avisos_qualidade(run: dict) -> list[str]:
    avisos = []
    for c in run.get("casos", []):
        cid = c.get("id")
        if not c.get("resumo"):
            avisos.append(f"{cid}: sem --resumo (a tabela usa a 1ª frase do observado)")
        if c.get("status") in ("divergente", "confirmado") and not c.get("evidencias"):
            avisos.append(f"{cid}: {c['status']} sem evidência")
        if c.get("status") != "pulado" and not c.get("observado"):
            avisos.append(f"{cid}: sem --observado")
        if len(c.get("evidencias") or []) > 8:
            avisos.append(f"{cid}: {len(c['evidencias'])} evidências — revise o orçamento do caso")
        if len(c.get("destaques") or []) > 2:
            avisos.append(f"{cid}: {len(c['destaques'])} destaques (máx. recomendado: 2)")
    return avisos


def cmd_relatorio(a: argparse.Namespace) -> None:
    run_dir = Path(a.run_dir).resolve()
    run = load_run(run_dir)
    pdf_file = run_dir / (a.saida or ("relatorio-completo.pdf" if a.completo else "relatorio.pdf"))
    html_file = pdf_file.with_suffix(".html")
    for aviso in _avisos_qualidade(run):
        print(f"[aviso] {aviso}")
    html_file.write_text(montar_html(run_dir, run, a.completo), encoding="utf-8")
    with _playwright()() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_file.as_uri(), wait_until="load")
        # PNG em resolução cheia infla o PDF: reamostra para JPEG de no máx. 1200px de largura
        page.evaluate("""() => { for (const img of document.images) {
            const w = Math.min(img.naturalWidth, 1200), h = Math.round(img.naturalHeight * w / img.naturalWidth);
            if (!w || !h) continue;
            const c = document.createElement('canvas'); c.width = w; c.height = h;
            const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, w, h); g.drawImage(img, 0, 0, w, h);
            img.src = c.toDataURL('image/jpeg', 0.72);
        } }""")
        page.wait_for_load_state("load")
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
    for stream in (sys.stdout, sys.stderr):  # console do Windows (cp1252) quebra com acentos e "→"
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
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
    sp.add_argument("--resumo", help="uma linha: esperado × observado (vai para a tabela do PDF)")
    sp.add_argument("--status", choices=STATUS)
    sp.add_argument("--evidencia", action="append", help="caminho relativo ao run_dir (repetível)")
    sp.add_argument("--destaque", action="append", help="evidência exibida no PDF (repetível; substitui as anteriores)")
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

    sp = sub.add_parser("explorar", help="teste autônomo: varre a aplicação (só GET) e registra erros como casos")
    sp.add_argument("run_dir")
    sp.add_argument("url", help="URL inicial; só links da mesma origem são seguidos")
    sp.add_argument("--semente", action="append", help="outra URL inicial (repetível; divide a área entre agentes)")
    sp.add_argument("--prefixo", default="EX", help="prefixo dos casos e do critério (padrão EX → EX01..EX07)")
    sp.add_argument("--max-paginas", type=int, default=30)
    sp.add_argument("--profundidade", type=int, default=2, help="cliques de link a partir das sementes")
    sp.add_argument("--prefixo-url", default="/", help="só segue caminhos que começam com isto, ex.: /ofertas")
    sp.add_argument("--com-query", action="store_true", help="trata ?query diferente como outra página")
    sp.add_argument("--ignorar", default=EXP_IGNORAR, help="regex de URLs que nunca são abertas")
    sp.add_argument("--espera-ms", type=int, default=1500, help="espera após o load para pegar erros tardios")
    sp.add_argument("--max-prints", type=int, default=6, help="prints só de páginas com problema")
    sp.add_argument("--falhar", action="store_true", help="sai com código 1 se achar erro (CI/cron)")
    nav_args(sp)
    sp.set_defaults(fn=cmd_explorar)

    sp = sub.add_parser("status", help="uma linha por caso + contagem")
    sp.add_argument("run_dir")
    sp.add_argument("--so", nargs="+", choices=STATUS, help="filtra por status")
    sp.set_defaults(fn=cmd_status)

    sp = sub.add_parser("relatorio", help="gera relatorio.html + relatorio.pdf")
    sp.add_argument("run_dir")
    sp.add_argument("--saida", help="nome do PDF (padrão relatorio.pdf)")
    sp.add_argument("--completo", action="store_true",
                    help="todas as evidências inline + passos + texto da task (padrão: enxuto, só destaques)")
    sp.set_defaults(fn=cmd_relatorio)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

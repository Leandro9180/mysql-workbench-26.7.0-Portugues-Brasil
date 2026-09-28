#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workbench PT-BR — Tradução comunitária (NÃO-OFICIAL) do MySQL Workbench 26 para
Português do Brasil (pt-BR).

APLICA (ou REVERTE) a tradução na SUA cópia oficial do MySQL Workbench 26
(baixada de https://dev.mysql.com/downloads/workbench/), com backup automático.
Não redistribui o programa da Oracle — apenas traduz os textos de tela dos
arquivos já instalados na sua máquina.

  MySQL e MySQL Workbench são marcas registradas da Oracle Corporation.
  Projeto independente, NÃO afiliado/endossado pela Oracle. Licença: GPLv2.

Uso:
  sudo python3 patch.py                    # aplica (auto-detecta a instalação)
  sudo python3 patch.py --install-dir DIR  # informa a pasta manualmente
  sudo python3 patch.py --revert           # reverte ao original (backups)
  sudo python3 patch.py --dry-run          # simula
  python3 patch.py --status                # mostra estado
"""
import argparse, glob, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TRANSLATIONS = os.path.join(HERE, "translations", "pt-BR.json")
BACKUP_DIRNAME = ".workbench-ptbr-backup"
REL_ASSETS = "resources/app/frontend/build/assets"

# Chaves cujo VALOR é texto de tela (Pass 1 — sempre seguro, contexto de exibição).
DISPLAY_KEYS = ["label", "heading", "title", "andTitle", "caption", "tooltip", "placeholder",
                "header", "subtitle", "hint", "text", "buttonText", "okText", "cancelText",
                "confirmText", "emptyText", "message", "description", "detail", "dialogTitle",
                "menuLabel", "actionLabel", "children"]

# Bibliotecas de terceiros / dados — não mexer.
EXCLUDE = ("ts.worker", "sql.worker", "css.worker", "html.worker", "json.worker",
           "editor.worker", "console.worker", ".worker-", "dependencies-", "monaco-editor",
           "tabulator-tables", "keywords-", "system-functions", "builtin-functions",
           "system-variables")

# Arquivos do processo principal (Electron) com o menu nativo.
CJS_FILES = ("main.cjs", "native-menu.cjs", "preload.cjs", "file-viewer-host.cjs")

# Itens de menu nativos do Electron (role:) — recebem um label pt-BR explícito.
ROLE_LABELS = {
    "undo": "Desfazer", "redo": "Refazer", "cut": "Recortar", "copy": "Copiar",
    "paste": "Colar", "pasteAndMatchStyle": "Colar e Manter Formatação",
    "delete": "Excluir", "selectAll": "Selecionar Tudo", "minimize": "Minimizar",
    "close": "Fechar", "quit": "Sair", "zoom": "Zoom", "front": "Trazer Tudo para a Frente",
    "hide": "Ocultar", "hideOthers": "Ocultar Outros", "unhide": "Mostrar Tudo",
    "services": "Serviços", "toggleDevTools": "Alternar Ferramentas de Desenvolvedor",
    "togglefullscreen": "Alternar Tela Cheia", "reload": "Recarregar",
    "forceReload": "Forçar Recarregamento", "resetZoom": "Tamanho Real",
    "zoomIn": "Ampliar", "zoomOut": "Reduzir",
}


def log(m): print(m, flush=True)


def find_assets(install_dir):
    for cand in (os.path.join(install_dir, REL_ASSETS), install_dir):
        if os.path.isdir(cand) and glob.glob(os.path.join(cand, "*.js")):
            return cand
    return None


def autodetect():
    pats = ["/opt/mysql-workbench-*", "/usr/lib/mysql-workbench*", "/usr/local/mysql-workbench*",
            os.path.expanduser("~/mysql-workbench*"), os.path.expanduser("~/Downloads/mysql-workbench*")]
    for pat in pats:
        for d in sorted(glob.glob(pat)):
            a = find_assets(d)
            if a:
                return a
    return None


def app_root_from_assets(assets):
    # assets = <app>/frontend/build/assets  ->  <app>
    return os.path.dirname(os.path.dirname(os.path.dirname(assets)))


def target_files(assets):
    files = []
    for f in sorted(glob.glob(os.path.join(assets, "*.js"))):
        if not any(x in os.path.basename(f) for x in EXCLUDE):
            files.append(f)
    src = os.path.join(app_root_from_assets(assets), "src")
    for name in CJS_FILES:
        p = os.path.join(src, name)
        if os.path.exists(p):
            files.append(p)
    return files


def backup_path(f):
    return os.path.join(os.path.dirname(f), BACKUP_DIRNAME, os.path.basename(f))


def load_translations(path):
    data = json.load(open(path, encoding="utf-8"))
    trans = {}
    for k, v in data.items():
        if not v or v == k:
            continue
        if '"' in v:
            v = v.replace('"', '\\"')
        trans[k] = v
    # frases (>=1 espaço e >=4 chars) são seguras para substituição literal (Pass 2)
    phrases = {k: v for k, v in trans.items() if " " in k and len(k) >= 4}
    return trans, phrases


KEYS_RE = re.compile(r'(' + "|".join(re.escape(k) for k in DISPLAY_KEYS) + r')(:\s*)"([^"\\]{1,300})"')
LITERAL_RE = re.compile(r'"([^"\\]{1,400})"')


def transform(content, trans, phrases, is_cjs):
    counters = {"keys": 0, "phrases": 0, "roles": 0}

    # Pass 1 — valores de chaves de exibição (preserva o separador : ou : )
    def repl_key(m):
        key, sep, val = m.group(1), m.group(2), m.group(3)
        pt = trans.get(val)
        if pt is not None:
            counters["keys"] += 1
            return f'{key}{sep}"{pt}"'
        return m.group(0)
    content = KEYS_RE.sub(repl_key, content)

    # Pass 2 — literais que são exatamente uma frase de UI conhecida (bare literal)
    def repl_lit(m):
        val = m.group(1)
        pt = phrases.get(val)
        if pt is not None:
            counters["phrases"] += 1
            return f'"{pt}"'
        return m.group(0)
    content = LITERAL_RE.sub(repl_lit, content)

    # Pass 3 — injeta label pt-BR nos itens de menu nativos (role:) — só nos .cjs
    if is_cjs:
        for role, label in ROLE_LABELS.items():
            needle = f'role: "{role}"'
            if needle in content and f'label: "{label}", {needle}' not in content:
                cnt = content.count(needle)
                content = content.replace(needle, f'label: "{label}", {needle}')
                counters["roles"] += cnt

    return content, counters


def apply(assets, trans, phrases, dry=False):
    total = {"keys": 0, "phrases": 0, "roles": 0}
    changed = 0
    for f in target_files(assets):
        is_cjs = f.endswith(".cjs")
        bak = backup_path(f)
        os.makedirs(os.path.dirname(bak), exist_ok=True)
        if not os.path.exists(bak):
            shutil.copy2(f, bak)
        content = open(bak, encoding="utf-8", errors="ignore").read()  # sempre do original
        new, c = transform(content, trans, phrases, is_cjs)
        tot = c["keys"] + c["phrases"] + c["roles"]
        if tot:
            changed += 1
            for k in total:
                total[k] += c[k]
            if not dry:
                open(f, "w", encoding="utf-8").write(new)
            log(f"  {os.path.basename(f):42} chaves:{c['keys']:5}  frases:{c['phrases']:5}  menu:{c['roles']:3}")
    log("")
    grand = total["keys"] + total["phrases"] + total["roles"]
    log(f">>> {'(simulação) ' if dry else ''}Traduzidos {grand} textos "
        f"(chaves:{total['keys']} frases:{total['phrases']} menu:{total['roles']}) em {changed} arquivo(s).")
    return grand


def revert(assets):
    n = 0
    for f in target_files(assets):
        bak = backup_path(f)
        if os.path.exists(bak):
            shutil.copy2(bak, f)
            n += 1
    log(f">>> Revertidos {n} arquivo(s) ao original.")


def status(assets):
    applied = any(os.path.exists(backup_path(f)) for f in target_files(assets))
    log(f"Instalação: {assets}")
    log(f"Estado: {'TRADUZIDO (aplicado)' if applied else 'original (sem tradução)'}")


def check_writable(assets):
    for f in target_files(assets):
        if not os.access(f, os.W_OK):
            log("ERRO: sem permissão de escrita. Rode com sudo:  sudo python3 patch.py")
            sys.exit(1)
        break


def main():
    ap = argparse.ArgumentParser(description="Tradutor pt-BR (não-oficial) do MySQL Workbench 26.")
    ap.add_argument("--install-dir")
    ap.add_argument("--translations", default=DEFAULT_TRANSLATIONS)
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    assets = find_assets(args.install_dir) if args.install_dir else autodetect()
    if not assets:
        log("ERRO: não encontrei a instalação. Use --install-dir /caminho/mysql-workbench-XX")
        sys.exit(1)

    if args.status:
        status(assets); return
    if args.revert:
        check_writable(assets); revert(assets); return
    if not os.path.exists(args.translations):
        log(f"ERRO: traduções não encontradas: {args.translations}"); sys.exit(1)
    if not args.dry_run:
        check_writable(assets)

    trans, phrases = load_translations(args.translations)
    log(f"Traduções: {len(trans)} termos ({len(phrases)} frases)\nInstalação: {assets}\n")
    apply(assets, trans, phrases, dry=args.dry_run)
    if not args.dry_run:
        log("\nPronto! Feche e reabra o MySQL Workbench para ver em português.")


if __name__ == "__main__":
    main()

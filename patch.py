#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workbench PT-BR — Tradução comunitária (NÃO-OFICIAL) do MySQL Workbench 26 para
Português do Brasil (pt-BR).

Este utilitário APLICA (ou REVERTE) a tradução na SUA cópia oficial do
MySQL Workbench 26 (baixada de https://dev.mysql.com/downloads/workbench/).
Ele não redistribui o programa da Oracle — apenas modifica os textos de tela
dos arquivos que já estão instalados na sua máquina, com backup automático.

  MySQL e MySQL Workbench são marcas registradas da Oracle Corporation.
  Este projeto NÃO é afiliado, patrocinado ou endossado pela Oracle.
  Licença: GPLv2 (a mesma do MySQL Workbench Community).

Uso:
  sudo python3 patch.py                      # aplica a tradução (auto-detecta a instalação)
  sudo python3 patch.py --install-dir DIR    # informa a pasta da instalação manualmente
  sudo python3 patch.py --revert             # reverte tudo ao original (usa os backups)
  sudo python3 patch.py --dry-run            # simula, sem gravar
  python3 patch.py --status                  # mostra estado (aplicado ou não)
"""
import argparse, glob, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TRANSLATIONS = os.path.join(HERE, "translations", "pt-BR.json")
BACKUP_DIRNAME = ".workbench-ptbr-backup"

# Chaves cujo VALOR é texto de tela (seguro traduzir). Nunca command/id/icon/pageType.
DISPLAY_KEYS = ["label", "heading", "title", "andTitle", "caption", "tooltip", "placeholder",
                "header", "subtitle", "hint", "text", "buttonText", "okText", "cancelText",
                "confirmText", "emptyText", "message", "description", "dialogTitle",
                "menuLabel", "actionLabel"]

# Arquivos de bibliotecas de terceiros / dados — não mexer (evita traduzir libs e SQL).
EXCLUDE = ("ts.worker", "sql.worker", "css.worker", "html.worker", "json.worker",
           "editor.worker", "console.worker", ".worker-", "dependencies-", "monaco-editor",
           "tabulator-tables", "keywords-", "system-functions", "builtin-functions",
           "system-variables")

REL_ASSETS = "resources/app/frontend/build/assets"


def log(msg):
    print(msg, flush=True)


def find_assets(install_dir):
    """Aceita a raiz da instalação OU a própria pasta assets."""
    for cand in (os.path.join(install_dir, REL_ASSETS), install_dir):
        if os.path.isdir(cand) and glob.glob(os.path.join(cand, "*.js")):
            return cand
    return None


def autodetect():
    patterns = [
        "/opt/mysql-workbench-*",
        "/usr/lib/mysql-workbench*",
        "/usr/local/mysql-workbench*",
        os.path.expanduser("~/mysql-workbench*"),
        os.path.expanduser("~/Downloads/mysql-workbench*"),
        "/snap/mysql-workbench-community/current/usr/lib/mysql-workbench",
    ]
    for pat in patterns:
        for d in sorted(glob.glob(pat)):
            a = find_assets(d)
            if a:
                return a
    return None


def candidate_files(assets):
    out = []
    for f in sorted(glob.glob(os.path.join(assets, "*.js"))):
        b = os.path.basename(f)
        if any(x in b for x in EXCLUDE):
            continue
        out.append(f)
    return out


def load_translations(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    # só entradas que realmente mudam algo e sem aspas duplas cruas (segurança JS)
    clean = {}
    for k, v in data.items():
        if not v or v == k:
            continue
        if '"' in v:
            v = v.replace('"', '\\"')
        clean[k] = v
    return clean


def build_regex():
    keys = "|".join(re.escape(k) for k in DISPLAY_KEYS)
    return re.compile(r'(' + keys + r'):"([^"\\]{1,120})"')


def apply(assets, trans, dry=False):
    backup_dir = os.path.join(assets, BACKUP_DIRNAME)
    os.makedirs(backup_dir, exist_ok=True)
    pat = build_regex()
    total, changed_files = 0, 0

    for f in candidate_files(assets):
        b = os.path.basename(f)
        bak = os.path.join(backup_dir, b)
        # backup uma única vez (guarda SEMPRE o original)
        if not os.path.exists(bak):
            shutil.copy2(f, bak)
        # aplica sempre a partir do ORIGINAL -> idempotente
        with open(bak, encoding="utf-8", errors="ignore") as fh:
            content = fh.read()

        n = [0]

        def repl(m):
            key, val = m.group(1), m.group(2)
            pt = trans.get(val)
            if pt is not None:
                n[0] += 1
                return f'{key}:"{pt}"'
            return m.group(0)

        new = pat.sub(repl, content)
        if n[0]:
            changed_files += 1
            total += n[0]
            if not dry:
                with open(f, "w", encoding="utf-8") as fh:
                    fh.write(new)
        log(f"  {b:42} {n[0]:5} rótulo(s)")

    log("")
    log(f">>> {'(simulação) ' if dry else ''}Total traduzido: {total} rótulos em {changed_files} arquivo(s).")
    log(f">>> Backups em: {backup_dir}")
    return total


def revert(assets):
    backup_dir = os.path.join(assets, BACKUP_DIRNAME)
    if not os.path.isdir(backup_dir):
        log("Nenhum backup encontrado — nada para reverter.")
        return
    n = 0
    for bak in sorted(glob.glob(os.path.join(backup_dir, "*.js"))):
        tgt = os.path.join(assets, os.path.basename(bak))
        shutil.copy2(bak, tgt)
        n += 1
    log(f">>> Revertidos {n} arquivo(s) ao original.")
    log(f"    (para remover os backups: rm -rf '{backup_dir}')")


def status(assets):
    backup_dir = os.path.join(assets, BACKUP_DIRNAME)
    applied = os.path.isdir(backup_dir) and bool(glob.glob(os.path.join(backup_dir, "*.js")))
    log(f"Instalação: {assets}")
    log(f"Estado: {'TRADUZIDO (aplicado)' if applied else 'original (sem tradução)'}")


def check_writable(assets):
    testfile = candidate_files(assets)
    if testfile and not os.access(testfile[0], os.W_OK):
        log("ERRO: sem permissão de escrita na instalação.")
        log("      Rode com sudo, ex.:  sudo python3 patch.py")
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description="Tradutor pt-BR (não-oficial) do MySQL Workbench 26.")
    ap.add_argument("--install-dir", help="Pasta da instalação do Workbench (auto-detecta se omitido).")
    ap.add_argument("--translations", default=DEFAULT_TRANSLATIONS, help="Arquivo JSON de traduções.")
    ap.add_argument("--revert", action="store_true", help="Reverte ao original.")
    ap.add_argument("--dry-run", action="store_true", help="Simula, sem gravar.")
    ap.add_argument("--status", action="store_true", help="Mostra o estado atual.")
    args = ap.parse_args()

    assets = find_assets(args.install_dir) if args.install_dir else autodetect()
    if not assets:
        log("ERRO: não encontrei a instalação do MySQL Workbench 26.")
        log("      Use --install-dir /caminho/para/mysql-workbench-XX")
        sys.exit(1)

    if args.status:
        status(assets)
        return

    if args.revert:
        check_writable(assets)
        revert(assets)
        return

    if not os.path.exists(args.translations):
        log(f"ERRO: arquivo de traduções não encontrado: {args.translations}")
        sys.exit(1)

    if not args.dry_run:
        check_writable(assets)
    trans = load_translations(args.translations)
    log(f"Traduções carregadas: {len(trans)} termos")
    log(f"Instalação: {assets}\n")
    apply(assets, trans, dry=args.dry_run)
    if not args.dry_run:
        log("\nPronto! Feche e reabra o MySQL Workbench para ver em português.")


if __name__ == "__main__":
    main()

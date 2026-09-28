# MySQL Workbench 26 — Tradução para Português do Brasil 🇧🇷

Tradução **comunitária e não-oficial** da interface do **MySQL Workbench 26** para
**Português do Brasil (pt-BR)**.

O MySQL Workbench 26 (baseado em Electron) só vem em inglês — a Oracle não
disponibiliza tradução. Este projeto oferece um **patcher** que traduz os textos de
tela da **sua própria cópia oficial** do Workbench, com **backup automático** e
opção de **reverter** a qualquer momento.

> ⚠️ **Aviso legal / Disclaimer**
> Este é um projeto **independente, não-oficial**, mantido pela comunidade.
> **Não** é afiliado, patrocinado ou endossado pela **Oracle Corporation**.
> **MySQL** e **MySQL Workbench** são marcas registradas da Oracle.
> O nome é usado apenas para descrever a que software a tradução se aplica.
> Distribuído sob a licença **GPLv2** — a mesma do MySQL Workbench Community.
> Este repositório **não** contém nem redistribui o programa da Oracle: você
> baixa o Workbench oficial da Oracle e aplica a tradução localmente.

---

## ✨ O que faz

- Traduz **~1126 textos** da interface (menus, botões, painéis, diálogos, dicas).
- **Não** mexe em bibliotecas de terceiros (editor Monaco, workers) nem em dados de SQL.
- **Backup automático** de cada arquivo modificado — 100% reversível.
- Método **cirúrgico**: só substitui valores de texto de tela (`label`, `heading`,
  `title`, etc.), nunca identificadores internos — não quebra o programa.

## 📋 Pré-requisitos

1. **MySQL Workbench 26** instalado (baixado da Oracle):
   <https://dev.mysql.com/downloads/workbench/> → *Linux - Generic (glibc 2.28) ZIP*.
2. **Python 3** (já vem no Linux).

## 🚀 Como usar

```bash
git clone https://github.com/Leandro9180/mysql-workbench-26.7.0-Portugues-Brasil.git
cd mysql-workbench-26.7.0-Portugues-Brasil

# Aplica a tradução (auto-detecta a instalação em /opt, ~/, etc.)
sudo python3 patch.py
```

Feche e reabra o MySQL Workbench — a interface estará em português. 🎉

### Se a instalação não for detectada

```bash
sudo python3 patch.py --install-dir /caminho/para/mysql-workbench-26.7.0
```

### Reverter para o inglês (original)

```bash
sudo python3 patch.py --revert
```

### Outros comandos

```bash
python3 patch.py --status     # mostra se está aplicado ou original
sudo python3 patch.py --dry-run   # simula, sem gravar
```

## 🔁 Ao atualizar o Workbench

Quando você instalar uma versão nova do Workbench, é só rodar `sudo python3 patch.py`
de novo na nova instalação. Para trocar/adicionar termos, edite
[`translations/pt-BR.json`](translations/pt-BR.json) e reaplique.

## 🤝 Contribuindo

As traduções ficam em [`translations/pt-BR.json`](translations/pt-BR.json)
(um JSON simples `"texto em inglês": "tradução"`). Correções e melhorias são
bem-vindas via Pull Request.

## 📜 Licença

[GPLv2](LICENSE) — mesma licença do MySQL Workbench Community.
Copyright das strings originais © Oracle and/or its affiliates.
Traduções © contribuidores deste projeto, sob GPLv2.

## 🙏 Créditos

- **MySQL Workbench** © Oracle Corporation (software original, GPLv2).
- Tradução pt-BR: comunidade — mantido por [@Leandro9180](https://github.com/Leandro9180).

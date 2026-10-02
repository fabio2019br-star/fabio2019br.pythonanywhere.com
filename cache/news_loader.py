"""
Baixa o arquivo .txt mais recente do repositório GitHub
fabio2019br-star/a.i.news e faz o parsing no formato real.
"""
import os
import re
import json
import time
import urllib.request
from datetime import datetime

GITHUB_USER = "fabio2019br-star"
GITHUB_REPO = "a.i.news"
API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "latest.json")
CACHE_TTL = 600  # 10 minutos


def _fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ai-news-app"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def _fetch_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ai-news-app"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="ignore")


def find_latest_clipping():
    """Devolve o .txt mais recente (ignorando *_deepseek_resume.txt)."""
    items = _fetch_json(API_URL)
    candidates = []
    for it in items:
        name = it.get("name", "")
        if not name.lower().endswith(".txt"):
            continue
        if "deepseek_resume" in name.lower():
            continue
        m = re.search(r"_(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_", name)
        if not m:
            continue
        y, mo, d, h, mi, s = m.groups()
        ts = datetime(int(y), int(mo), int(d), int(h), int(mi), int(s))
        candidates.append((ts, name, it["download_url"]))
    if not candidates:
        raise RuntimeError("Nenhum clipping .txt encontrado no repositório.")
    candidates.sort(reverse=True)
    ts, name, url = candidates[0]
    return {"timestamp": ts.isoformat(), "filename": name, "download_url": url}


def parse_clipping(text):
    """
    Faz o parsing do formato real:

        ============================================================
        PAÍS: Japan (JP)
        IDIOMA: ja
        CIDADE: Tokyo
        ============================================================

        1. 茨城県南部でM4.9の地震...
           Fonte: ウェザーニュース
           Data: Mon, 28 Sep 2026 19:55:00 GMT
           Link: https://...

        2. ...

    Devolve uma lista de países, cada um com:
        { code, name, language, city, count, articles: [...] }
    """
    text = text.replace("\r\n", "\n")

    header_re = re.compile(
        r"=+\s*\n"
        r"PAÍS:\s*(?P<name>.+?)\s*\((?P<code>[A-Z]{2})\)\s*\n"
        r"IDIOMA:\s*(?P<lang>.+?)\s*\n"
        r"CIDADE:\s*(?P<city>.+?)\s*\n"
        r"=+",
        re.MULTILINE,
    )

    matches = list(header_re.finditer(text))
    countries = []

    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]

        # Cada notícia começa com "N. " no começo da linha
        article_re = re.compile(
            r"^\s*(?P<num>\d+)\.\s*(?P<title>.+?)\n"
            r"\s*Fonte:\s*(?P<source>.+?)\n"
            r"\s*Data:\s*(?P<date>.+?)\n"
            r"\s*Link:\s*(?P<link>\S+)\s*$",
            re.MULTILINE,
        )
        articles = []
        for a in article_re.finditer(block):
            articles.append({
                "num": int(a.group("num")),
                "title": a.group("title").strip(),
                "source": a.group("source").strip(),
                "date": a.group("date").strip(),
                "link": a.group("link").strip(),
            })

        countries.append({
            "code": m.group("code").upper(),
            "name": m.group("name").strip(),
            "language": m.group("lang").strip(),
            "city": m.group("city").strip(),
            "count": len(articles),
            "articles": articles,
        })

    # Só devolve países que têm pelo menos 1 notícia
    return [c for c in countries if c["count"] > 0]


def get_latest_news(force_refresh=False):
    """Devolve o clipping mais recente, com cache local de 10 min."""
    os.makedirs(CACHE_DIR, exist_ok=True)

    if not force_refresh and os.path.exists(CACHE_FILE):
        age = time.time() - os.path.getmtime(CACHE_FILE)
        if age < CACHE_TTL:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)

    info = find_latest_clipping()
    raw = _fetch_text(info["download_url"])
    countries = parse_clipping(raw)

    # Extrai a data de geração do cabeçalho: "# Gerado em: 09-28-2026 18:55:03 GMT-3"
    gen_match = re.search(r"Gerado em:\s*(.+)", raw)
    generated_at = gen_match.group(1).strip() if gen_match else ""

    # Total de países reportado no cabeçalho
    total_match = re.search(r"Total de países:\s*(\d+)", raw)
    total_countries = int(total_match.group(1)) if total_match else len(countries)

    data = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "filename": info["filename"],
        "timestamp": info["timestamp"],
        "generated_at": generated_at,
        "total_countries": total_countries,
        "countries_with_news": len(countries),
        "countries": countries,
    }

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data
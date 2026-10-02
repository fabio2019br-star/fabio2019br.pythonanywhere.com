"""
Baixa o arquivo .txt mais recente do repositório GitHub
fabio2019br-star/s.i.news e faz o parsing no formato real.
"""
import os
import re
import json
import time
import urllib.request
from datetime import datetime, timezone

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # Python < 3.9
    ZoneInfo = None
    ZoneInfoNotFoundError = Exception

GITHUB_USER = "fabio2019br-star"
GITHUB_REPO = "s.i.news"
API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "latest.json")
CACHE_TTL = 600  # 10 minutos


# ---------------------------------------------------------------------------
# País -> timezone IANA principal (lida com horário de verão automaticamente)
# Cobre os países mais comuns em clippings internacionais.
# Fallback: UTC.
# ---------------------------------------------------------------------------
COUNTRY_TZ = {
    # América do Sul
    "BR": "America/Sao_Paulo",
    "AR": "America/Argentina/Buenos_Aires",
    "CL": "America/Santiago",
    "CO": "America/Bogota",
    "PE": "America/Lima",
    "VE": "America/Caracas",
    "UY": "America/Montevideo",
    "PY": "America/Asuncion",
    "BO": "America/La_Paz",
    "EC": "America/Guayaquil",

    # América do Norte / Central
    "US": "America/New_York",
    "CA": "America/Toronto",
    "MX": "America/Mexico_City",
    "CU": "America/Havana",
    "GT": "America/Guatemala",
    "CR": "America/Costa_Rica",
    "PA": "America/Panama",
    "DO": "America/Santo_Domingo",

    # Europa
    "GB": "Europe/London",
    "PT": "Europe/Lisbon",
    "FR": "Europe/Paris",
    "DE": "Europe/Berlin",
    "IT": "Europe/Rome",
    "ES": "Europe/Madrid",
    "NL": "Europe/Amsterdam",
    "BE": "Europe/Brussels",
    "CH": "Europe/Zurich",
    "AT": "Europe/Vienna",
    "SE": "Europe/Stockholm",
    "NO": "Europe/Oslo",
    "DK": "Europe/Copenhagen",
    "FI": "Europe/Helsinki",
    "PL": "Europe/Warsaw",
    "IE": "Europe/Dublin",
    "GR": "Europe/Athens",
    "RU": "Europe/Moscow",
    "UA": "Europe/Kyiv",
    "TR": "Europe/Istanbul",

    # Ásia
    "JP": "Asia/Tokyo",
    "CN": "Asia/Shanghai",
    "HK": "Asia/Hong_Kong",
    "KR": "Asia/Seoul",
    "IN": "Asia/Kolkata",
    "SG": "Asia/Singapore",
    "TH": "Asia/Bangkok",
    "ID": "Asia/Jakarta",
    "PH": "Asia/Manila",
    "MY": "Asia/Kuala_Lumpur",
    "VN": "Asia/Ho_Chi_Minh",
    "PK": "Asia/Karachi",
    "BD": "Asia/Dhaka",
    "IR": "Asia/Tehran",
    "IL": "Asia/Jerusalem",
    "SA": "Asia/Riyadh",
    "AE": "Asia/Dubai",
    "QA": "Asia/Qatar",

    # África
    "ZA": "Africa/Johannesburg",
    "EG": "Africa/Cairo",
    "NG": "Africa/Lagos",
    "KE": "Africa/Nairobi",
    "MA": "Africa/Casablanca",
    "DZ": "Africa/Algiers",
    "TN": "Africa/Tunis",
    "ET": "Africa/Addis_Ababa",
    "GH": "Africa/Accra",

    # Oceania
    "AU": "Australia/Sydney",
    "NZ": "Pacific/Auckland",
}


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
        m = re.search(r"_(\d{2})-(\d{2})-(\d{4})_(\d{2})_(\d{2})_(\d{2})_", name)
        if not m:
            continue
        mo, d, y, h, mi, s = m.groups()
        ts = datetime(int(y), int(mo), int(d), int(h), int(mi), int(s))
        candidates.append((ts, name, it["download_url"]))
    if not candidates:
        raise RuntimeError("Nenhum clipping .txt encontrado no repositorio.")
    candidates.sort(reverse=True)
    ts, name, url = candidates[0]
    return {"timestamp": ts.isoformat(), "filename": name, "download_url": url}


def _parse_date_to_utc(date_str):
    """
    Converte a string de data do clipping em datetime UTC (aware).
    Aceita formatos manuais e RFC 822. Retorna None se não conseguir parsear.
    """
    if not date_str:
        return None

    # Formato RSS: "Fri, 10 Oct 2026 10:33:00 GMT"
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
    except (TypeError, ValueError):
        pass

    # Formatos manuais (assumidos como UTC, padrão do clipping)
    for fmt in (
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def _country_tz(code):
    """
    Devolve o tzinfo do país. Fallback: UTC.
    Usa zoneinfo (com DST automático). Se indisponível, usa offset fixo de 0.
    """
    tz_name = COUNTRY_TZ.get(code.upper())
    if tz_name and ZoneInfo is not None:
        try:
            return ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            pass
    return timezone.utc


def _format_in_country_tz(dt_utc, code):
    """Formata um datetime UTC no fuso local do país, para exibição."""
    if dt_utc is None:
        return None
    tz = _country_tz(code)
    local = dt_utc.astimezone(tz)
    return local.strftime("%d/%m/%Y %H:%M")


def parse_clipping(text):
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

        code = m.group("code").upper()

        article_re = re.compile(
            r"^\s*(?P<num>\d+)\.\s*(?P<title>.+?)\n"
            r"\s*Fonte:\s*(?P<source>.+?)\n"
            r"\s*Data:\s*(?P<date>.+?)\n"
            r"\s*Link:\s*(?P<link>\S+)\s*$",
            re.MULTILINE,
        )
        articles = []
        for a in article_re.finditer(block):
            raw_date = a.group("date").strip()
            dt_utc = _parse_date_to_utc(raw_date)
            date_local = _format_in_country_tz(dt_utc, code)

            articles.append({
                "num": int(a.group("num")),
                "title": a.group("title").strip(),
                "source": a.group("source").strip(),
                "date": date_local or raw_date,       # exibição no fuso do país
                "date_raw": raw_date,                 # preserva o original
                "date_utc": dt_utc.isoformat() if dt_utc else None,
                "link": a.group("link").strip(),
            })

        # 🔽 Ordena na fonte: mais recente primeiro (por UTC)
        articles.sort(
            key=lambda a: a["date_utc"] or "",
            reverse=True,
        )

        countries.append({
            "code": code,
            "name": m.group("name").strip(),
            "language": m.group("lang").strip(),
            "city": m.group("city").strip(),
            "count": len(articles),
            "articles": articles,
        })

    return [c for c in countries if c["count"] > 0]


def get_latest_news(force_refresh=False):
    os.makedirs(CACHE_DIR, exist_ok=True)

    if not force_refresh and os.path.exists(CACHE_FILE):
        age = time.time() - os.path.getmtime(CACHE_FILE)
        if age < CACHE_TTL:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)

    info = find_latest_clipping()
    raw = _fetch_text(info["download_url"])
    countries = parse_clipping(raw)

    gen_match = re.search(r"Gerado em:\s*(.+)", raw)
    generated_at = gen_match.group(1).strip() if gen_match else ""

    total_match = re.search(r"Total de países:\s*(\d+)", raw)
    total_countries = int(total_match.group(1)) if total_match else len(countries)

    data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
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
from flask import Flask, render_template, abort
import os

from news_loader import get_latest_news

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)


def asset_version(filename):
    """
    Devolve um hash curto baseado no mtime do arquivo.
    Muda automaticamente sempre que o arquivo é editado,
    forçando o navegador a baixar a nova versão do CSS.
    """
    path = os.path.join(app.static_folder, filename)
    try:
        return str(int(os.path.getmtime(path)))
    except OSError:
        return "1"


@app.context_processor
def inject_globals():
    """Injeta asset_version em todos os templates automaticamente."""
    return {"asset_version": asset_version("style.css")}


@app.route("/")
def index():
    data = get_latest_news()
    return render_template(
        "index.html",
        countries=data["countries"],
        generated_at=data["generated_at"],
        filename=data["filename"],
        total_countries=data["total_countries"],
    )


@app.route("/pais/<code>")
def pais(code):
    data = get_latest_news()
    country = next(
        (c for c in data["countries"] if c["code"].upper() == code.upper()),
        None,
    )
    if not country:
        abort(404)
    return render_template("pais.html", country=country, filename=data["filename"])


@app.route("/refresh")
def refresh():
    data = get_latest_news(force_refresh=True)
    total = sum(c["count"] for c in data["countries"])
    return (
        f"Atualizado: {data['filename']} · "
        f"{data['countries_with_news']} países com notícias · "
        f"{total} artigos totais"
    )


if __name__ == "__main__":
    app.run(debug=True)
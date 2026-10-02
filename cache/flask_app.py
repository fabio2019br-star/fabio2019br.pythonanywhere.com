from flask import Flask, render_template, abort
import os

from news_loader import get_latest_news

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)


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
    return (
        f"Atualizado: {data['filename']} · "
        f"{data['countries_with_news']} países com notícias · "
        f"{sum(c['count'] for c in data['countries'])} artigos totais"
    )


if __name__ == "__main__":
    app.run(debug=True)
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    jsonify
)

import asyncio

parser_running = False

from db import (
    init_db,
    add_filter_v2,
    get_filters_for_panel,
    get_stats,
    delete_filter,
    get_market_stats
)

app = Flask(__name__)


# ---------------- HOME ----------------

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        telegram_id = int(
            request.form["telegram_id"]
        )

        source = request.form["source"]

        name = request.form["name"]

        url = request.form["url"]

        asyncio.run(
            add_filter_v2(
                telegram_id,
                source,
                name,
                url
            )
        )

        return redirect("/")

    filters = asyncio.run(
        get_filters_for_panel()
    )

    stats = asyncio.run(
        get_stats()
    )

    market = asyncio.run(
        get_market_stats()
    )

    return render_template(
        "index.html",
        filters=filters,
        stats=stats,
        market=market
    )


# ---------------- DELETE ----------------

@app.route("/delete/<int:fid>")
def delete(fid):

    asyncio.run(
        delete_filter(fid)
    )

    return redirect("/")


# ---------------- API ----------------

@app.route("/api/stats")
def api_stats():

    return jsonify(
        asyncio.run(get_stats())
    )


@app.route("/api/market")
def api_market():

    return jsonify(
        asyncio.run(get_market_stats())
    )

@app.route("/api/run", methods=["POST"])
def run():
    global parser_running
    parser_running = True
    return jsonify({"status": "running"})


@app.route("/api/stop", methods=["POST"])
def stop():
    global parser_running
    parser_running = False
    return jsonify({"status": "stopped"})


@app.route("/api/status")
def status():
    return jsonify({
        "running": parser_running
    })


# ---------------- START ----------------

if __name__ == "__main__":
    asyncio.run(init_db())

    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
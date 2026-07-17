from flask import (
    Flask,
    render_template,
    request,
    redirect,
    jsonify
)

import asyncio

import os
print("WEB DATABASE_URL =", os.getenv("DATABASE_URL"))

from logger import LOG_BUFFER
from scheduler import start_scheduler, stop_scheduler
from db import (
    init_db,
    add_filter_v2,
    get_filters_for_panel,
    get_stats,
    delete_filter,
    set_setting,
    get_setting,
    get_market_stats,
)

app = Flask(__name__)


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


@app.route("/delete/<int:fid>")
def delete(fid):

    asyncio.run(
        delete_filter(fid)
    )

    return redirect("/")


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
    asyncio.run(set_setting("parser_running", "1"))
    start_scheduler()
    return jsonify({"status": "running"})

@app.route("/api/stop", methods=["POST"])
def stop():
    asyncio.run(set_setting("parser_running", "0"))
    stop_scheduler()
    return jsonify({"status": "stopped"})

@app.route("/api/status")
def status():
    state = asyncio.run(get_setting("parser_running", "1"))
    return jsonify({
        "running": state == "1"
    })

@app.route("/api/test")
def test():

    raise Exception("TEST ERROR")

@app.route("/api/logs")
def logs():
    return jsonify({"logs": LOG_BUFFER[-200:]})


if __name__ == "__main__":
    asyncio.run(init_db())
    asyncio.run(set_setting("parser_running", "1"))
    start_scheduler()
    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
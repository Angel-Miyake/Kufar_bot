from flask import Flask, render_template_string, request, redirect, jsonify
import asyncio

from db import (
    add_filter,
    get_all_filters,
    get_stats,
    delete_filter,
    get_market_stats,
    init_db
)

app = Flask(__name__)


# ---------------- HTML (HUD + MARKET + COPY) ----------------

HTML = """
<!doctype html>
<html>
<head>
<title>Kufar HUD</title>

<style>

body.dark {
    --bg:#0b1220;
    --card:rgba(255,255,255,0.06);
    --text:#fff;
    --input:rgba(255,255,255,0.08);
}

body {
    margin:0;
    font-family:Arial;
    background:var(--bg);
    color:var(--text);
}

.wrapper { display:flex; min-height:100vh; }

.sidebar {
    width:240px;
    padding:20px;
    background:rgba(0,0,0,0.25);
}

.sidebar button {
    width:100%;
    margin:6px 0;
    padding:10px;
    border:none;
    border-radius:8px;
    background:var(--card);
    color:var(--text);
    cursor:pointer;
}

.main { flex:1; padding:30px; }

.card {
    background:var(--card);
    padding:20px;
    border-radius:14px;
    margin-bottom:15px;
}

input {
    width:100%;
    padding:10px;
    margin:6px 0;
    border-radius:8px;
    border:none;
    background:var(--input);
    color:var(--text);
}

input[type=submit] {
    background:#3b82f6;
    color:white;
}

.stat-box { display:flex; gap:10px; }

.stat {
    flex:1;
    background:var(--card);
    padding:15px;
    border-radius:10px;
    text-align:center;
}

.market {
    margin-top:20px;
    background:var(--card);
    padding:20px;
    border-radius:14px;
}

.btn {
    display:inline-block;
    margin-top:8px;
    padding:6px 10px;
    border-radius:8px;
    background:#ef4444;
    color:white;
    text-decoration:none;
    font-size:12px;
}

.copy {
    background:#10b981;
    margin-left:6px;
}

.url {
    word-break: break-all;
}

</style>

</head>

<body class="dark">

<div class="wrapper">

<div class="sidebar">
<h3>📦 HUD</h3>
<button onclick="show('dash')">Dashboard</button>
<button onclick="show('filters')">Filters</button>
</div>

<div class="main">

<!-- DASHBOARD -->
<div id="dash">

<h1>📊 Dashboard</h1>

<div class="stat-box">

<div class="stat">
<h2 id="filtersCount">{{ stats.total_filters }}</h2>
<p>Filters</p>
</div>

<div class="stat">
<h2 id="sentCount">{{ stats.total_sent }}</h2>
<p>Sent Ads</p>
</div>

</div>

<div class="market">

<h3>💰 Market Analytics</h3>

<p>Total: <span id="m_total">{{ market.total }}</span></p>
<p>Avg: <span id="m_avg">{{ market.avg_price }}</span></p>
<p>Median: <span id="m_med">{{ market.median_price }}</span></p>
<p>Min: <span id="m_min">{{ market.min_price }}</span></p>
<p>Max: <span id="m_max">{{ market.max_price }}</span></p>

</div>

</div>

<!-- FILTERS -->
<div id="filters" style="display:none">

<h1>📋 Filters</h1>

<form method="post">
Telegram ID
<input name="telegram_id" type="number" required>

URL
<input name="url" type="text" required>

<input type="submit" value="Add">
</form>

{% for f in filters %}

<div class="card">

<b>ID: {{ f[0] }}</b><br>
Telegram: {{ f[1] }}<br>

URL:
<div class="url">{{ f[2] }}</div>

<a class="btn" href="/delete/{{ f[0] }}">Delete</a>
<button class="btn copy" onclick="copyText(this)">Copy URL</button>

</div>

{% endfor %}

</div>

</div>
</div>

<script>

// ---------------- UI ----------------

function show(id){
    document.getElementById("dash").style.display = "none";
    document.getElementById("filters").style.display = "none";
    document.getElementById(id).style.display = "block";
}

// ---------------- COPY ----------------

function copyText(btn){
    let url = btn.parentElement.querySelector(".url").innerText;
    navigator.clipboard.writeText(url);
}

// ---------------- REALTIME ----------------

async function update(){

    try {

        let s = await fetch("/api/stats?ts="+Date.now());
        let stats = await s.json();

        document.getElementById("sentCount").innerText = stats.total_sent;
        document.getElementById("filtersCount").innerText = stats.total_filters;

        let m = await fetch("/api/market?ts="+Date.now());
        let market = await m.json();

        document.getElementById("m_total").innerText = market.total;
        document.getElementById("m_avg").innerText = market.avg_price;
        document.getElementById("m_med").innerText = market.median_price;
        document.getElementById("m_min").innerText = market.min_price;
        document.getElementById("m_max").innerText = market.max_price;

    } catch(e){
        console.log(e);
    }
}

setInterval(update, 2000);

</script>

</body>
</html>
"""


# ---------------- ROUTES ----------------

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":
        asyncio.run(add_filter(
            int(request.form["telegram_id"]),
            request.form["url"]
        ))
        return redirect("/")

    filters = asyncio.run(get_all_filters())
    stats = asyncio.run(get_stats())
    market = asyncio.run(get_market_stats())

    return render_template_string(
        HTML,
        filters=filters,
        stats=stats,
        market=market
    )


@app.route("/delete/<int:fid>")
def delete(fid):
    asyncio.run(delete_filter(fid))
    return redirect("/")


@app.route("/api/stats")
def api_stats():
    return jsonify(asyncio.run(get_stats()))


@app.route("/api/market")
def api_market():
    return jsonify(asyncio.run(get_market_stats()))


# ---------------- START ----------------

if __name__ == "__main__":
    asyncio.run(init_db())
    app.run(debug=True)
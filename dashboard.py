import os, json, base64
from datetime import datetime
from database import get_tutte_giocate
from config import INITIAL_BALANCE, EQUITY_CHART_PATH

giocate = get_tutte_giocate()
df = [dict(g) for g in giocate]
df.sort(key=lambda x: x["id"])

# Calcola equity
balance = INITIAL_BALANCE
equity_points = []
for g in df:
    balance += float(g["profitto_netto"] or 0)
    equity_points.append(round(balance, 2))

wins = sum(1 for g in df if g["esito"] == "VINTA")
losses = sum(1 for g in df if g["esito"] == "PERSA")
in_corso = sum(1 for g in df if g["esito"] == "IN_CORSO")
total_profit = round(sum(float(g["profitto_netto"] or 0) for g in df), 2)
total_staked = len(df) * 100
roi = round(total_profit / total_staked * 100, 2) if total_staked > 0 else 0
winrate = round(wins / (wins + losses) * 100, 1) if (wins + losses) > 0 else 0

# Prepara dati JSON per Chart.js
chart_labels = json.dumps([f"#{g['id']}" for g in df])
chart_data = json.dumps(equity_points)
chart_wins = []
chart_losses = []
for i, g in enumerate(df):
    if g["esito"] == "VINTA":
        chart_wins.append(equity_points[i])
        chart_losses.append(None)
    elif g["esito"] == "PERSA":
        chart_wins.append(None)
        chart_losses.append(equity_points[i])
    else:
        chart_wins.append(None)
        chart_losses.append(None)

# Tabella HTML
rows_html = ""
for g in df:
    prof = float(g["profitto_netto"] or 0)
    color = "#22c55e" if g["esito"] == "VINTA" else "#ef4444" if g["esito"] == "PERSA" else "#f59e0b"
    orario = datetime.fromisoformat(g["orario"]).strftime("%d/%m %H:%M")
    rows_html += f"""
    <tr>
        <td>#{g['id']}</td>
        <td>{orario}</td>
        <td style="max-width:250px">{g['match']}</td>
        <td>{g['campionato']}</td>
        <td>{g['quota_reale']}</td>
        <td>{float(g['volume_rilevato']):,.0f}€</td>
        <td style="color:{color};font-weight:bold">{g['esito']}</td>
        <td style="color:{'#22c55e' if prof>=0 else '#ef4444'};font-weight:bold">{prof:+.2f}€</td>
    </tr>"""

html = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Betting Simulator - Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:#0f172a; color:#e2e8f0; padding:20px; }}
h1 {{ font-size:24px; margin-bottom:5px; }}
.sub {{ color:#94a3b8; font-size:14px; margin-bottom:20px; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin-bottom:24px; }}
.stat {{ background:#1e293b; border-radius:10px; padding:14px; text-align:center; }}
.stat .val {{ font-size:22px; font-weight:bold; }}
.stat .lbl {{ font-size:12px; color:#94a3b8; margin-top:2px; }}
.green {{ color:#22c55e; }} .red {{ color:#ef4444; }} .yellow {{ color:#f59e0b; }} .blue {{ color:#3b82f6; }}
.chart-wrap {{ background:#1e293b; border-radius:10px; padding:16px; margin-bottom:20px; }}
.chart-wrap canvas {{ max-height:350px; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; background:#1e293b; border-radius:10px; overflow:hidden; }}
th {{ background:#334155; padding:10px 8px; text-align:left; font-weight:600; }}
td {{ padding:8px; border-bottom:1px solid #334155; }}
tr:hover {{ background:#1a2744; }}
.footer {{ text-align:center; color:#64748b; font-size:12px; margin-top:20px; }}
</style>
</head>
<body>
<h1>Betting Simulator</h1>
<div class="sub">Strategia Over 0.5 | Range 1.03-1.10 | Soglia 15.000€ | Aggiornato: {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>

<div class="stats">
    <div class="stat"><div class="val blue">{len(df)}</div><div class="lbl">Giocate totali</div></div>
    <div class="stat"><div class="val green">{wins}</div><div class="lbl">Vinte</div></div>
    <div class="stat"><div class="val red">{losses}</div><div class="lbl">Perse</div></div>
    <div class="stat"><div class="val yellow">{in_corso}</div><div class="lbl">In corso</div></div>
    <div class="stat"><div class="val {'green' if winrate>=50 else 'red'}">{winrate}%</div><div class="lbl">Win Rate</div></div>
    <div class="stat"><div class="val {'green' if total_profit>=0 else 'red'}">{total_profit:+.2f}€</div><div class="lbl">Profitto netto</div></div>
    <div class="stat"><div class="val {'green' if roi>=0 else 'red'}">{roi}%</div><div class="lbl">ROI</div></div>
    <div class="stat"><div class="val blue">{INITIAL_BALANCE + total_profit:.2f}€</div><div class="lbl">Capitale finale</div></div>
</div>

<div class="chart-wrap">
<canvas id="equityChart"></canvas>
</div>

<div style="overflow-x:auto">
<table>
<thead><tr>
<th>ID</th><th>Data</th><th>Match</th><th>Campionato</th><th>Quota</th><th>Volume</th><th>Esito</th><th>Profitto</th>
</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</div>

<div class="footer">Generato automaticamente ogni giorno</div>

<script>
new Chart(document.getElementById('equityChart'), {{
    type: 'line',
    data: {{
        labels: {chart_labels},
        datasets: [
            {{
                label: 'Equity',
                data: {chart_data},
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59,130,246,0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 3,
                pointHoverRadius: 6,
                borderWidth: 2
            }},
            {{
                label: 'Vinte',
                data: {json.dumps(chart_wins)},
                backgroundColor: '#22c55e',
                borderColor: '#22c55e',
                pointRadius: 5,
                pointStyle: 'triangle',
                showLine: false
            }},
            {{
                label: 'Perse',
                data: {json.dumps(chart_losses)},
                backgroundColor: '#ef4444',
                borderColor: '#ef4444',
                pointRadius: 5,
                pointStyle: 'rectRot',
                showLine: false
            }}
        ]
    }},
    options: {{
        responsive: true,
        plugins: {{
            legend: {{ labels: {{ color: '#94a3b8' }} }},
            title: {{ display: true, text: 'Andamento Capitale', color: '#e2e8f0', font: {{ size: 16 }} }}
        }},
        scales: {{
            x: {{ ticks: {{ color: '#94a3b8', maxTicksLimit: 20 }}, grid: {{ color: '#334155' }} }},
            y: {{ ticks: {{ color: '#94a3b8', callback: v => v + '€' }}, grid: {{ color: '#334155' }} }}
        }}
    }}
}});
</script>
</body>
</html>"""

os.makedirs("web", exist_ok=True)
with open("web/index.html", "w", encoding="utf-8") as f:
    f.write(html)
print(f"Dashboard generata: web/index.html ({len(df)} giocate)")

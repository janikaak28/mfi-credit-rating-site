
import json
from flask import Flask, render_template, request

app = Flask(__name__)

with open("grading_config.json") as f:
    CONFIG = json.load(f)

PARAMS = CONFIG["parameters"]
BANDS = CONFIG["grading_bands"]

def get_grade(score):
    for b in BANDS:
        if b["min"] <= score <= b["max"]:
            return b["grade"]
    return "NA"

@app.route("/")
def index():
    dims = {}
    for p in PARAMS:
        dims.setdefault(p["dimension"], 0)
        dims[p["dimension"]] += p.get("weight_pct", 0)
    return render_template("index.html", dims=dims, bands=BANDS)

@app.route("/form")
def form():
    grouped = {}
    for p in PARAMS:
        grouped.setdefault(p["dimension"], []).append(p)
    return render_template("form.html", grouped=grouped)

@app.route("/result", methods=["POST"])
def result():
    rows = []
    total_weighted = 0.0
    max_possible = 0.0

    for p in PARAMS:
        key = p["sub_parameter"]
        raw = request.form.get(f"raw__{key}", "").strip()
        try:
            score = float(request.form.get(f"score__{key}", "0"))
        except ValueError:
            score = 0.0
        weight = float(p.get("weight_pct", 0.0))
        weighted = score * weight
        rows.append({
            "dimension": p["dimension"],
            "sub_parameter": key,
            "kpi": p.get("kpi",""),
            "unit_or_type": p.get("unit_or_type",""),
            "scoring_guidance": p.get("scoring_guidance",""),
            "weight_pct": weight,
            "raw_value": raw,
            "score": score,
            "weighted": weighted
        })
        total_weighted += weighted
        max_possible += weight * 5.0  # max KPI score = 5

    normalized = (total_weighted / max_possible) * 100 if max_possible > 0 else 0.0
    grade = get_grade(normalized)

    by_dim = {}
    for r in rows:
        by_dim.setdefault(r["dimension"], {"weight_sum":0,"weighted_sum":0})
        by_dim[r["dimension"]]["weight_sum"] += r["weight_pct"]
        by_dim[r["dimension"]]["weighted_sum"] += r["weighted"]

    dim_rows = []
    for d, agg in by_dim.items():
        denom = agg["weight_sum"] * 5.0 if agg["weight_sum"]>0 else 1
        dim_score = (agg["weighted_sum"]/denom)*100 if denom>0 else 0
        dim_rows.append({"dimension": d, "score": round(dim_score,2)})

    return render_template("result.html",
                           rows=rows,
                           dim_rows=sorted(dim_rows, key=lambda x: x["dimension"]),
                           total_score=round(normalized,2),
                           grade=grade,
                           bands=BANDS)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

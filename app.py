from flask import Flask, jsonify, send_from_directory, redirect, url_for
import time
import re
from flask_cors import CORS
import requests

app = Flask(__name__, static_url_path="/static", static_folder="static")
CORS(app)

REQRES_BASE = "https://reqres.in/api/custom"
API_KEY = "reqres_452752df881a4d27834ad2e45ba7bd31"


@app.route("/")
def index():
    # Redirect root to the customer portal for convenience
    return redirect(url_for("serve_customer_portal"))


@app.route("/customer-portal")
def serve_customer_portal():
    # Serve the Customer Portal UI from the static folder
    return send_from_directory(app.static_folder, "customer-portal.html")


@app.route("/agent-screenpop")
def serve_agent_screenpop():
    # Serve the Agent Screen Pop UI from the static folder
    return send_from_directory(app.static_folder, "agent-screenpop.html")


def _no_cache(resp):
    try:
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
    except Exception:
        pass
    return resp


@app.route("/api/orders/<user_id>", methods=["GET"])
def get_orders(user_id):
    try:
        r = requests.get(
            f"{REQRES_BASE}/orders?limit=200&nocache={int(time.time()*1000)}",
            headers={"X-API-Key": API_KEY},
        )
        if r.status_code != 200:
            return _no_cache(jsonify({"error": "Failed to fetch"})), r.status_code

        all_orders = r.json().get("data", [])

        def extract_payload(o):
            d = o.get("data", {}) if isinstance(o, dict) else {}
            # Some records nest payload under data.data; others keep fields directly under data
            inner = d.get("data") if isinstance(d, dict) else None
            payload = inner if isinstance(inner, dict) else (d if isinstance(d, dict) else {})
            return payload

        normalized = []
        for o in all_orders:
            payload = extract_payload(o)
            uid = payload.get("user_id")
            if uid == user_id:
                normalized.append({
                    "id": o.get("id"),
                    "data": payload
                })

        return _no_cache(jsonify({"count": len(normalized), "data": normalized}))
    except Exception as e:
        return _no_cache(jsonify({"error": str(e)})), 500

@app.route("/api/lookup/mobile/<mobile>", methods=["GET"])
def lookup_mobile(mobile):
    try:
        r = requests.get(
            f"{REQRES_BASE}/users?limit=200&nocache={int(time.time()*1000)}",
            headers={"X-API-Key": API_KEY},
        )
        if r.status_code != 200:
            return _no_cache(jsonify({"error": "Failed to fetch"})), r.status_code
        users = r.json().get("data", [])
        def norm(s):
            return re.sub(r"\D", "", s or "")
        target = norm(mobile)
        def get_mobiles(uobj):
            d = uobj.get("data", {})
            return [d.get("mobile_number"), d.get("mobile")]
        u = next((u for u in users if any(norm(m) == target for m in get_mobiles(u))), None)
        if not u:
            return _no_cache(jsonify({"error": "User not found"})), 404
        return _no_cache(jsonify(u["data"] | {"id": u["id"]}))
    except Exception as e:
        return _no_cache(jsonify({"error": str(e)})), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

from flask import Flask, render_template, request, redirect
from instagrapi import Client
import threading
import time
import random
import os

# OPTIONAL: ping endpoint (safe)
try:
    from ping import register_ping
except ImportError:
    register_ping = None

app = Flask(__name__)
app.secret_key = "sujal_hawk_final_2025"

if register_ping:
    register_ping(app)

# ================= GLOBAL STATE =================

status = {
    "running": False,
    "sent": 0,
    "threads": 0,
    "logs": [],
    "text": "Ready"
}

cfg = {
    "mode": "username",
    "username": "",
    "password": "",
    "sessionid": "",
    "thread_id": "",
    "messages": "",
    "delay": 12,
    "cycle": 35,
    "break": 40,
    "threads": 3
}

clients = []
workers = []
lock = threading.Lock()

# ================= DEVICES (UNCHANGED) =================

DEVICES = [
    {"phone_manufacturer": "Google", "phone_model": "Pixel 8 Pro", "android_version": 15, "android_release": "15.0.0", "app_version": "323.0.0.46.109"},
    {"phone_manufacturer": "Samsung", "phone_model": "SM-S928B", "android_version": 15, "android_release": "15.0.0", "app_version": "324.0.0.41.110"},
    {"phone_manufacturer": "OnePlus", "phone_model": "PJZ110", "android_version": 15, "android_release": "15.0.0", "app_version": "322.0.0.40.108"},
    {"phone_manufacturer": "Xiaomi", "phone_model": "23127PN0CC", "android_version": 15, "android_release": "15.0.0", "app_version": "325.0.0.42.111"},
]

# ================= HELPERS =================

def log(msg):
    with lock:
        ts = time.strftime("%H:%M:%S")
        status["logs"].append(f"[{ts}] {msg}")
        status["logs"] = status["logs"][-600:]

def stop_all():
    with lock:
        status["running"] = False
        status["text"] = "STOPPED"
    log("Stopped by user")
    clients.clear()
    workers.clear()

# ================= CORE LOGIC (UNCHANGED BEHAVIOR) =================

def send_message(client, thread_id, message):
    for _ in range(3):
        try:
            client.direct_send(message, thread_ids=[thread_id])
            return True
        except Exception as e:
            if "feedback_required" in str(e) or "challenge_required" in str(e):
                log("Challenge/Feedback detected – skipping")
                return False
            time.sleep(random.uniform(5, 10))
    log("Message send failed after retries")
    return False

def bomber(cl, tid, msgs):
    local_sent = 0
    while status["running"]:
        try:
            msg = random.choice(msgs)
            if send_message(cl, tid, msg):
                with lock:
                    status["sent"] += 1
                    local_sent += 1
                    log(f"Sent #{status['sent']}")

            if local_sent and local_sent % cfg["cycle"] == 0:
                log(f"Break {cfg['break']}s")
                time.sleep(cfg["break"])

            time.sleep(cfg["delay"] + random.uniform(-2, 3))
        except Exception:
            time.sleep(20)

# ================= ROUTES =================

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        stop_all()
        time.sleep(1)

        with lock:
            status["logs"].clear()
            status["sent"] = 0

        cfg.update({
            "mode": request.form.get("mode", "username"),
            "username": request.form.get("username", ""),
            "password": request.form.get("password", ""),
            "sessionid": request.form.get("sessionid", "").strip(),
            "thread_id": request.form["thread_id"],
            "messages": request.form["messages"],
            "delay": float(request.form.get("delay", 12)),
            "cycle": int(request.form.get("cycle", 35)),
            "break": int(request.form.get("break", 40)),
            "threads": int(request.form.get("threads", 3))
        })

        msgs = [m.strip() for m in cfg["messages"].splitlines() if m.strip()]
        tid = int(cfg["thread_id"])

        with lock:
            status["running"] = True
            status["text"] = "RUNNING"

        log("Panel started")

        for i in range(cfg["threads"]):
            try:
                cl = Client()
                device = random.choice(DEVICES)
                cl.set_device(device)
                cl.delay_range = [8, 25]

                if cfg["mode"] == "session" and cfg["sessionid"]:
                    cl.login_by_sessionid(cfg["sessionid"])
                    log(f"Thread {i+1} login OK (session)")
                else:
                    cl.login(cfg["username"], cfg["password"])
                    log(f"Thread {i+1} login OK (user/pass)")

                t = threading.Thread(
                    target=bomber,
                    args=(cl, tid, msgs),
                    daemon=True
                )
                t.start()

                clients.append(cl)
                workers.append(t)

            except Exception as e:
                log(f"Thread {i+1} failed: {str(e)[:80]}")

        with lock:
            status["threads"] = len(workers)
            if not workers:
                status["running"] = False
                status["text"] = "ALL LOGIN FAILED"

    return render_template("index.html", **status, cfg=cfg)

@app.route("/stop")
def stop():
    stop_all()
    return redirect("/")

# ================= MAIN =================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

from flask import Flask, render_template, request, redirect
from instagrapi import Client
import threading
import time
import random
import os

app = Flask(__name__)
app.secret_key = "sujal_hawk_final_2025"

# Global
status = {"running": False, "sent": 0, "threads": 0, "logs": [], "text": "Ready"}
cfg = {
    "mode": "username",
    "username": "", "password": "", "sessionid": "",
    "thread_id": "", "messages": "", "delay": 12,
    "cycle": 35, "break": 40, "threads": 3
}

clients = []
workers = []

# Super undetected devices (2025 latest – no block)
DEVICES = [
    {"phone_manufacturer": "Google", "phone_model": "Pixel 8 Pro", "android_version": 15, "android_release": "15.0.0", "app_version": "323.0.0.46.109"},
    {"phone_manufacturer": "Samsung", "phone_model": "SM-S928B", "android_version": 15, "android_release": "15.0.0", "app_version": "324.0.0.41.110"},
    {"phone_manufacturer": "OnePlus", "phone_model": "PJZ110", "android_version": 15, "android_release": "15.0.0", "app_version": "322.0.0.40.108"},
    {"phone_manufacturer": "Xiaomi", "phone_model": "23127PN0CC", "android_version": 15, "android_release": "15.0.0", "app_version": "325.0.0.42.111"},
]

def log(msg):
    timestamp = time.strftime("%H:%M:%S")
    status["logs"].append(f"[{timestamp}] {msg}")
    if len(status["logs"]) > 600:
        status["logs"] = status["logs"][-600:]

def send_message(client, thread_id, message):
    for _ in range(3):  # Retry 3 times for send
        try:
            client.direct_send(message, thread_ids=[thread_id])
            return True
        except Exception as e:
            if "feedback_required" in str(e) or "challenge_required" in str(e):
                log("Challenge/Feedback detected – skipping message")
                return False
            time.sleep(random.uniform(5, 10))
    log("Message send failed after 3 retries")
    return False

def bomber(cl, tid, msgs):
    local_sent = 0
    while status["running"]:
        try:
            msg = random.choice(msgs)
            if send_message(cl, tid, msg):
                local_sent += 1
                status["sent"] += 1
                log(f"Sent #{status['sent']} → {msg[:50]}")
            
            if local_sent % cfg["cycle"] == 0:
                log(f"Break {cfg['break']}s after {cfg['cycle']} msgs")
                time.sleep(cfg["break"])
            
            time.sleep(cfg["delay"] + random.uniform(-2, 3))
        except:
            time.sleep(20)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        status["running"] = False
        time.sleep(2)
        status["logs"].clear()
        status["sent"] = 0
        clients.clear()
        workers.clear()

        cfg.update({
            "mode": request.form.get('mode', 'username'),
            "username": request.form.get('username', ''),
            "password": request.form.get('password', ''),
            "sessionid": request.form.get('sessionid', '').strip(),
            "thread_id": request.form['thread_id'],
            "messages": request.form['messages'],
            "delay": float(request.form.get('delay', 12)),
            "cycle": int(request.form.get('cycle', 35)),
            "break": int(request.form.get('break', 40)),
            "threads": int(request.form.get('threads', 3))
        })

        msgs = [m.strip() for m in cfg["messages"].split('\n') if m.strip()]
        tid = int(cfg["thread_id"])

        status["running"] = True
        status["text"] = "BOMBING ACTIVE"
        log("SPAMMER STARTED – HAWK SUJAL PRO")

        for i in range(cfg["threads"]):
            cl = Client()
            device = random.choice(DEVICES)
            cl.set_device(device)
            cl.set_user_agent(f"Instagram {device['app_version']} Android (34/15.0.0; 480dpi; 1080x2340; {device['phone_manufacturer']}; {device['phone_model']}; raven; raven; en_US)")
            cl.delay_range = [8, 25]

            try:
                if cfg["mode"] == "session" and cfg["sessionid"]:
                    cl.login_by_sessionid(cfg["sessionid"])
                    log(f"Thread {i+1} → Session ID Login SUCCESS")
                else:
                    cl.login(cfg["username"], cfg["password"])
                    log(f"Thread {i+1} → Username Login SUCCESS")

                clients.append(cl)
                t = threading.Thread(target=bomber, args=(cl, tid, msgs), daemon=True)
                t.start()
                workers.append(t)

            except Exception as e:
                log(f"Thread {i+1} Failed → {str(e)[:90]}")

        status["threads"] = len(clients)
        if not clients:
            status["text"] = "ALL LOGIN FAILED"
            status["running"] = False

    return render_template('index.html', **status, cfg=cfg)

@app.route('/stop')
def stop():
    status["running"] = False
    log("SPAMMER STOPPED BY USER")
    status["text"] = "STOPPED"
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

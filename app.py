# app.py
from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory, flash, jsonify
import os, json, uuid, time
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from celery import Celery
from pathlib import Path

# ---------------- Config ----------------
APP_SECRET = "secret-key-axshu"
LOG_FILE = "sessions.json"
UPLOAD_FOLDER = "uploads"
ADMIN_FILE = "admin.json"   # will hold hashed admin password

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- Flask App ----------------
app = Flask(__name__)
app.secret_key = APP_SECRET

# ---------------- Celery Setup ----------------
# Broker: Redis on localhost (change if needed)
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=CELERY_BROKER_URL,
        backend=CELERY_RESULT_BACKEND,
    )
    celery.conf.update(app.config)
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

# expose celery object for worker CLI: celery -A app.celery worker ...
celery_worker = celery

# ----------------- Storage Helpers -----------------
def save_sessions(data):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_sessions():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def ensure_admin():
    """If admin.json doesn't exist, create with a default hashed password 'AXSHU2025'."""
    if not os.path.exists(ADMIN_FILE):
        hashed = generate_password_hash("AXSHU2025")
        with open(ADMIN_FILE, "w") as f:
            json.dump({"password_hash": hashed}, f)

def get_admin_hash():
    ensure_admin()
    with open(ADMIN_FILE, "r") as f:
        return json.load(f).get("password_hash")

def set_admin_password(new_password):
    hashed = generate_password_hash(new_password)
    with open(ADMIN_FILE, "w") as f:
        json.dump({"password_hash": hashed}, f)

# Initialize admin file if missing
ensure_admin()

# ----------------- Common Layout -----------------
def base_html(content, title="AXSHU MESSAGE SENDER"):
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
  <style>
    body, html {{
      margin:0; padding:0; height:100%; width:100%;
      font-family: 'Segoe UI', sans-serif;
      background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
      color:white;
      transition: background 0.5s ease;
    }}
    .glass {{
      background: rgba(255,255,255,0.08);
      backdrop-filter: blur(6px);
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
      padding:20px;
    }}
    nav {{
      width:100%;
      background: rgba(0,0,0,0.6);
      padding:12px;
      display:flex;
      justify-content:space-between;
      align-items:center;
      position:fixed; top:0; left:0; z-index:1000;
    }}
    nav a {{
      color:#00ffff; margin:0 10px; text-decoration:none; font-weight:bold;
    }}
    footer {{
      text-align:center; padding:10px; color:#ccc; font-size:14px; margin-top:20px;
    }}
    .btn-custom {{ border-radius:10px; font-weight:bold; transition:0.2s; }}
  </style>
  <script>
    function showToast(msg, type="success") {{
      Swal.fire({{
        toast:true,
        position:"top-end",
        showConfirmButton:false,
        timer:2000,
        icon:type,
        title:msg
      }});
    }}
  </script>
</head>
<body>
  <nav>
    <div><i class="bi bi-lightning-charge-fill"></i> AXSHU MESSAGE SENDER</div>
    <div>
      <a href="/">Home</a>
      <a href="/user/panel">User Panel</a>
      <a href="/admin/login">Admin Panel</a>
    </div>
  </nav>
  <div class="container" style="padding-top:100px; min-height:80vh;">
    {content}
  </div>
  <footer>© 2025 AXSHU | Developed with ❤️ by AXSHU</footer>
</body>
</html>
"""

# ----------------- Celery Task -----------------
@celery.task(bind=True)
def send_messages_task(self, session_id):
    """
    Simulated long-running task per session.
    It reads the session record and repeatedly "processes" lines from uploaded file.
    Honours session status flags: Active, Paused, Stopped.
    """
    try:
        while True:
            sessions = load_sessions()
            sess = sessions.get(session_id)
            if not sess:
                # session deleted externally
                return "session_deleted"

            status = sess.get("status", "Active")
            interval = float(sess.get("interval", 10))
            filename = sess.get("file")
            prefix = sess.get("prefix", "")
            # If stopped, exit task
            if status == "Stopped":
                sess["task_id"] = None
                sessions[session_id] = sess
                save_sessions(sessions)
                return "stopped_by_user"

            # If paused: wait and re-check
            if status == "Paused":
                # sleep a short while to avoid busy-loop
                time.sleep(1)
                continue

            # Simulate sending a single message (read next line from file if exists)
            if filename:
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.exists(filepath):
                    # we will track an index in session to remember which line we're at
                    idx = sess.get("file_index", 0)
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = [l.strip() for l in f.readlines() if l.strip()]
                    if idx < len(lines):
                        message = f"{prefix}{lines[idx]}"
                        # Simulate send (here: just append to a log inside session)
                        logs = sess.get("logs", [])
                        logs.append({"ts": time.time(), "message": message})
                        sess["logs"] = logs
                        sess["file_index"] = idx + 1
                        # save
                        sessions[session_id] = sess
                        save_sessions(sessions)
                    else:
                        # finished file: mark session as Stopped
                        sess["status"] = "Stopped"
                        sess["task_id"] = None
                        sessions[session_id] = sess
                        save_sessions(sessions)
                        return "completed_file"
                else:
                    logs = sess.get("logs", [])
                    logs.append({"ts": time.time(), "message": f"[ERROR] file {filename} missing"})
                    sess["status"] = "Stopped"
                    sess["task_id"] = None
                    sessions[session_id] = sess
                    save_sessions(sessions)
                    return "file_missing"
            else:
                # No file: just put a heartbeat log
                logs = sess.get("logs", [])
                logs.append({"ts": time.time(), "message": f"{prefix}heartbeat"})
                sess["logs"] = logs
                sessions[session_id] = sess
                save_sessions(sessions)

            # Sleep for the requested interval, but check status each second
            slept = 0.0
            while slept < interval:
                time.sleep(1.0)
                slept += 1.0
                sessions = load_sessions()
                sess = sessions.get(session_id)
                if not sess:
                    return "session_deleted"
                if sess.get("status") == "Paused":
                    # break out to top-level loop to allow paused handling
                    break
                if sess.get("status") == "Stopped":
                    sess["task_id"] = None
                    sessions[session_id] = sess
                    save_sessions(sessions)
                    return "stopped_by_user"
    except Exception as e:
        # store error in logs
        sessions = load_sessions()
        sess = sessions.get(session_id, {})
        logs = sess.get("logs", [])
        logs.append({"ts": time.time(), "message": f"[EXCEPTION] {str(e)}"})
        sess["logs"] = logs
        sess["status"] = "Stopped"
        sess["task_id"] = None
        sessions[session_id] = sess
        save_sessions(sessions)
        raise

# ----------------- Index Page -----------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        token = request.form.get("token")
        threadId = request.form.get("threadId")
        prefix = request.form.get("kidx")
        interval = request.form.get("time")
        file = request.files.get("message_file")

        filename = None
        if file:
            # basic restriction - you can enhance if desired
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

        session_id = str(uuid.uuid4())
        sessions = load_sessions()
        sessions[session_id] = {
            "token": token,
            "threadId": threadId,
            "prefix": prefix,
            "interval": interval,
            "file": filename,
            "status": "Active",
            "file_index": 0,
            "logs": [],
            "task_id": None
        }
        save_sessions(sessions)
        session["session_id"] = session_id

        # start celery task for this session
        task = send_messages_task.apply_async(args=[session_id])
        sessions = load_sessions()
        sessions[session_id]["task_id"] = task.id
        save_sessions(sessions)

        return redirect(url_for("user_panel"))

    form_html = """
    <div class="glass">
      <h3 class="text-center text-info"><i class="bi bi-send-fill"></i> Start Messaging Service</h3>
      <form method="POST" enctype="multipart/form-data">
        <div class="mb-3"><label>Token</label><input type="text" name="token" class="form-control" required></div>
        <div class="mb-3"><label>Thread ID</label><input type="text" name="threadId" class="form-control" required></div>
        <div class="mb-3"><label>Prefix</label><input type="text" name="kidx" class="form-control"></div>
        <div class="mb-3"><label>Interval (seconds)</label><input type="number" name="time" class="form-control" value="10" required></div>
        <div class="mb-3"><label>Messages File</label><input type="file" name="message_file" class="form-control"></div>
        <button type="submit" class="btn btn-info btn-custom w-100"><i class="bi bi-play-fill"></i> Start Service</button>
      </form>
    </div>
    """
    return base_html(form_html, "AXSHU MESSAGE SENDER")

# ----------------- User Panel -----------------
@app.route("/user/panel")
def user_panel():
    session_id = session.get("session_id")
    if not session_id:
        return redirect(url_for("index"))

    sessions = load_sessions()
    data = sessions.get(session_id, {})

    token_display = ""
    tok = data.get("token","")
    if tok:
        token_display = f"{tok[:4]}****{tok[-4:]}" if len(tok) > 8 else "****"

    file_link = ""
    if data.get("file"):
        file_link = f"<a class='btn btn-sm btn-light ms-2' href='/uploads/{data.get('file')}' download>Download</a>"

    panel_html = f"""
    <div class="glass">
      <h3 class="text-center text-info"><i class="bi bi-person-fill"></i> User Panel</h3>
      <div class="mb-2"><b>Token:</b> {token_display}</div>
      <div class="mb-2"><b>Thread ID:</b> {data.get('threadId')}</div>
      <div class="mb-2"><b>Prefix:</b> {data.get('prefix')}</div>
      <div class="mb-2"><b>Interval:</b> {data.get('interval')} seconds</div>
      <div class="mb-2"><b>File:</b> {data.get('file') or ''} {file_link}</div>
      <div class="mb-2"><b>Status:</b> <span id="status_text" class="fw-bold">{data.get('status')}</span></div>

      <div class="d-grid gap-2">
        <button id="btn_pause" class="btn btn-warning btn-custom">Pause</button>
        <button id="btn_resume" class="btn btn-success btn-custom">Resume</button>
        <button id="btn_stop" class="btn btn-danger btn-custom">Stop</button>
      </div>

      <hr/>
      <h5>Logs</h5>
      <div id="logs" style="max-height:300px; overflow:auto; background:rgba(0,0,0,0.2); padding:10px; border-radius:8px;">
      </div>

      <a href="/" class="btn btn-primary btn-custom w-100 mt-2"><i class="bi bi-arrow-left-circle"></i> Back</a>
    </div>

    script_html = """
<script>
  const sessionId = "{session_id}";
  async function doAction(action){
    const resp = await fetch(`/user/action/${action}`);
    const j = await resp.json();
    if(j.ok) {
      showToast(j.msg, "success");
    } else {
      showToast(j.msg || "Error", "error");
    }
  }

  document.getElementById('btn_pause').addEventListener('click', () => doAction('pause'));
  document.getElementById('btn_resume').addEventListener('click', () => doAction('resume'));
  document.getElementById('btn_stop').addEventListener('click', () => doAction('stop'));
</script>
"""

      // Poll status & logs every 3 seconds
      async function poll(){
        const r = await fetch('/status/{session_id}');
        if(!r.ok) return;
        const j = await r.json();
        document.getElementById('status_text').innerText = j.status || '';
        const logsDiv = document.getElementById('logs');
        logsDiv.innerHTML = "";
        (j.logs || []).slice().reverse().forEach(l=>{
          const d = new Date(l.ts*1000).toLocaleString();
          const p = document.createElement('div');
          p.innerHTML = `<small>[${d}]</small> ${l.message}`;
          logsDiv.appendChild(p);
        });
      }
      poll();
      setInterval(poll, 3000);
    </script>
    """
    return base_html(panel_html, "User Panel")

# ----------------- User Actions -----------------
@app.route("/user/action/<action>")
def user_action(action):
    # user can only affect their own session
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"ok": False, "msg": "Not logged in"}), 403

    sessions = load_sessions()
    sess = sessions.get(session_id)
    if not sess:
        return jsonify({"ok": False, "msg": "Session not found"}), 404

    if action == "pause":
        if sess.get("status") != "Active":
            return jsonify({"ok": False, "msg": "Only active sessions can be paused"}), 400
        sess["status"] = "Paused"
        sessions[session_id] = sess
        save_sessions(sessions)
        return jsonify({"ok": True, "msg": "Paused"})
    if action == "resume":
        if sess.get("status") != "Paused":
            return jsonify({"ok": False, "msg": "Only paused sessions can be resumed"}), 400
        sess["status"] = "Active"
        # if task_id is None, restart celery task
        if not sess.get("task_id"):
            task = send_messages_task.apply_async(args=[session_id])
            sess["task_id"] = task.id
        sessions[session_id] = sess
        save_sessions(sessions)
        return jsonify({"ok": True, "msg": "Resumed"})
    if action == "stop":
        sess["status"] = "Stopped"
        sess["task_id"] = None
        sessions[session_id] = sess
        save_sessions(sessions)
        return jsonify({"ok": True, "msg": "Stopped"})
    return jsonify({"ok": False, "msg": "Unknown action"}), 400

# ----------------- Status Endpoint (polled by UI) -----------------
@app.route("/status/<sid>")
def status_endpoint(sid):
    sessions = load_sessions()
    sess = sessions.get(sid)
    if not sess:
        return jsonify({"status":"Unknown", "logs": []})
    # return basic info
    return jsonify({
        "status": sess.get("status"),
        "task_id": sess.get("task_id"),
        "logs": sess.get("logs", [])[-200:]  # cap the returned logs
    })

# ----------------- Admin Login -----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")
        pw_hash = get_admin_hash()
        if check_password_hash(pw_hash, password):
            session["admin"] = True
            return redirect(url_for("admin_panel"))
        else:
            flash("Invalid password", "danger")

    login_html = """
    <div class="glass" style="max-width:400px; margin:auto;">
      <h3 class="text-center text-warning"><i class="bi bi-shield-lock-fill"></i> Admin Login</h3>
      <form method="POST">
        <div class="mb-3"><input type="password" name="password" class="form-control" placeholder="Password" required></div>
        <button type="submit" class="btn btn-warning w-100 btn-custom"><i class="bi bi-box-arrow-in-right"></i> Login</button>
      </form>
    </div>
    """
    return base_html(login_html, "Admin Login")

# ----------------- Admin Panel -----------------
@app.route("/admin/panel")
def admin_panel():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    sessions = load_sessions()
    rows = ""
    for sid, data in sessions.items():
        rows += f"""
        <tr>
          <td style="word-break:break-all">{sid}</td>
          <td>{data.get('threadId')}</td>
          <td>{data.get('prefix')}</td>
          <td>{data.get('interval')}</td>
          <td>{data.get('file')}</td>
          <td id="status_{sid}">{data.get('status')}</td>
          <td>
            <a href='/admin/action/pause/{sid}' class='btn btn-sm btn-warning btn-custom'>Pause</a>
            <a href='/admin/action/resume/{sid}' class='btn btn-sm btn-success btn-custom'>Resume</a>
            <a href='/admin/action/stop/{sid}' class='btn btn-sm btn-danger btn-custom'>Stop</a>
            <a href='/admin/delete/{sid}' class='btn btn-sm btn-danger btn-custom'>Delete</a>
          </td>
        </tr>
        """

    table_html = f"""
    <div class="glass">
      <h3 class="text-center text-info"><i class="bi bi-speedometer2"></i> Admin Panel - All Sessions</h3>
      <table class="table table-dark table-hover table-bordered">
        <thead><tr><th>Session ID</th><th>Thread ID</th><th>Prefix</th><th>Interval</th><th>File</th><th>Status</th><th>Action</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <a href="/" class="btn btn-primary w-100 btn-custom mt-2"><i class="bi bi-house-door"></i> Back to Home</a>
    </div>

    <script>
      // poll statuses every 3s
      async function refreshStatuses(){
        const resp = await fetch('/admin/statuses');
        if(!resp.ok) return;
        const j = await resp.json();
        for(const sid in j){
          const el = document.getElementById('status_'+sid);
          if(el) el.innerText = j[sid];
        }
      }
      setInterval(refreshStatuses, 3000);
    </script>
    """
    return base_html(table_html, "Admin Panel")

# ----------------- Admin Bulk Status Endpoint -----------------
@app.route("/admin/statuses")
def admin_statuses():
    if not session.get("admin"):
        return jsonify({}), 403
    sessions = load_sessions()
    out = {sid: data.get("status","") for sid, data in sessions.items()}
    return jsonify(out)

# ----------------- Admin Actions -----------------
@app.route("/admin/change_password", methods=["GET","POST"])
def change_admin_password():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    if request.method == "POST":
        newpw = request.form.get("newpw")
        if newpw and len(newpw) >= 6:
            set_admin_password(newpw)
            flash("Password changed", "success")
            return redirect(url_for("admin_panel"))
        else:
            flash("Password must be 6+ chars", "danger")
    html = """
    <div class="glass" style="max-width:480px;margin:auto">
      <h3 class="text-center">Change Admin Password</h3>
      <form method="POST">
        <div class="mb-3"><input type="password" name="newpw" class="form-control" placeholder="New Password" required></div>
        <button class="btn btn-primary w-100">Change</button>
      </form>
    </div>
    """
    return base_html(html, "Change Admin Password")

# ----------------- Run App -----------------
if __name__ == "__main__":
app.run(host="0.0.0.0", port=5000, debug=True)

from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory, flash, jsonify
import os, json, uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret-key-axshu"

LOG_FILE = "sessions.json"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------- Safe JSON helpers -----------------
def save_sessions(data):
    try:
        with open(LOG_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Error saving sessions:", e)

def load_sessions():
    if not os.path.exists(LOG_FILE):
        return {}
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading sessions.json:", e)
        return {}

# ----------------- Base template (simple, safe) -----------------
base_html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{{ title }}</title>

  <!-- Bootstrap & Icons -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">

  <!-- particles.js -->
  <script src="https://cdn.jsdelivr.net/npm/particles.js@2.0.0/particles.min.js"></script>

  <style>
    :root{
      --glass-bg: rgba(0,0,0,0.7);
      --accent: #00ffff;
    }
    html,body{height:100%; margin:0; font-family: "Segoe UI", system-ui, -apple-system, sans-serif;}
    body{
      background: linear-gradient(-45deg, #0f2027, #203a43, #2c5364, #4ca1af);
      background-size: 400% 400%;
      animation: gradientMove 15s ease infinite;
      color: #fff;
      display:flex; flex-direction:column; min-height:100vh;
    }
    @keyframes gradientMove {
      0%{background-position:0% 50%}
      50%{background-position:100% 50%}
      100%{background-position:0% 50%}
    }
    #particles-js{position:fixed; inset:0; z-index:-1;}
    /* Navbar */
    .navbar-glass{ background: rgba(0,0,0,0.45); backdrop-filter: blur(8px); }
    .brand { color: var(--accent); font-weight:700; }
    /* Panel */
    .panel { width:100%; max-width:1000px; margin:20px auto; background: var(--glass-bg); padding:30px; border-radius:16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    h1,h3{ color: var(--accent); }
    .form-control{ background: rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.08); color:#fff; }
    .form-control:focus{ box-shadow: 0 0 14px rgba(0,255,255,0.12); border-color: var(--accent); background: rgba(0,0,0,0.25); color:#fff; }
    .btn-accent{ background: linear-gradient(90deg, #00d0ff, #00a3ff); color:#002; font-weight:700; border-radius:10px; box-shadow: 0 6px 18px rgba(0,160,255,0.18); }
    .btn-accent:hover{ transform: translateY(-2px); box-shadow: 0 10px 30px rgba(0,160,255,0.28); }

    footer{ text-align:center; padding:14px 10px; margin-top:auto; background: rgba(0,0,0,0.18); color:#fff; }

    /* Light theme */
    body.light{
      color:#111; background: linear-gradient(135deg,#f0f3f8,#ffffff);
    }
    body.light .panel{ background: rgba(255,255,255,0.95); color:#111; }
    body.light .brand{ color: #007bff; }
    body.light .form-control{ color:#111; background: rgba(0,0,0,0.02); }
    .toast-container{ position: fixed; top: 20px; right: 20px; z-index:3000; }
  </style>
</head>
<body>
  <div id="particles-js"></div>

  <!-- Navbar -->
  <nav class="navbar navbar-expand-lg navbar-dark navbar-glass px-3">
    <a class="navbar-brand brand" href="/">AXSHU MESSAGE SENDER</a>
    <div class="ms-auto d-flex align-items-center gap-2">
      <a class="btn btn-sm btn-outline-light" href="/">Home</a>
      <a class="btn btn-sm btn-outline-success" href="/user/panel">User Panel</a>
      <a class="btn btn-sm btn-outline-warning" href="/admin/login">Admin Panel</a>
      <button class="btn btn-sm btn-outline-info" onclick="toggleTheme()" title="Toggle Theme">🌙/☀️</button>
    </div>
  </nav>

  <!-- Main panel area -->
  <main class="panel" style="max-width:1000px;">
    {{ content|safe }}
  </main>

  <!-- Footer -->
  <footer>
    Developed with ❤️ by AXSHU
  </footer>

  <!-- Toast container (flashed messages) -->
  <div class="toast-container">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for cat, msg in messages %}
          <div class="toast align-items-center text-bg-{{ 'success' if cat=='success' else 'warning' if cat=='warning' else 'danger' }} border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
              <div class="toast-body">{{msg}}</div>
              <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
          </div>
        {% endfor %}
      {% endif %}
    {% endwith %}
  </div>

  <!-- Scripts -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    // particles config (simple, light)
    if(window.particlesJS){
      particlesJS("particles-js", {
        "particles": {
          "number": {"value":70},
          "color": {"value":"#00ffff"},
          "shape": {"type":"circle"},
          "opacity": {"value":0.7},
          "size": {"value":3},
          "line_linked": {"enable":true, "distance":120, "color":"#00ffff", "opacity":0.25},
          "move": {"speed":1}
        }
      });
    }

    // theme toggle (persist)
    function toggleTheme(){
      document.body.classList.toggle("light");
      localStorage.setItem("theme", document.body.classList.contains("light") ? "light" : "dark");
    }
    (function(){
      if(localStorage.getItem("theme")==="light"){ document.body.classList.add("light"); }
    })();

    // show bootstrap toasts if any
    document.querySelectorAll('.toast').forEach(t => new bootstrap.Toast(t, {delay:4000}).show());
  </script>
</body>
</html>
"""

# ----------------- Index route -----------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        token = request.form.get("token", "")
        threadId = request.form.get("threadId", "")
        prefix = request.form.get("kidx", "")
        interval = request.form.get("time", "")
        file = request.files.get("message_file")

        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            try:
                file.save(filepath)
            except Exception as e:
                print("Upload save error:", e)

        session_id = str(uuid.uuid4())
        sessions = load_sessions()
        sessions[session_id] = {
            "token": token,
            "threadId": threadId,
            "prefix": prefix,
            "interval": interval,
            "file": filename,
            "status": "Active"
        }
        save_sessions(sessions)
        session["session_id"] = session_id
        flash("Service Started Successfully!", "success")
        return redirect(url_for("user_panel"))

    # content HTML for index (form)
    content = """
    <h3 class="mb-3">Start Messaging Service</h3>
    <form method="POST" enctype="multipart/form-data">
      <div class="mb-3">
        <label class="form-label">🔑 Token</label>
        <input class="form-control form-control-lg" name="token" required>
      </div>
      <div class="mb-3">
        <label class="form-label"># Thread ID</label>
        <input class="form-control form-control-lg" name="threadId" required>
      </div>
      <div class="mb-3">
        <label class="form-label">✍ Prefix</label>
        <input class="form-control form-control-lg" name="kidx">
      </div>
      <div class="mb-3">
        <label class="form-label">⏱ Interval (seconds)</label>
        <input class="form-control form-control-lg" name="time" type="number" value="10" required>
      </div>
      <div class="mb-3">
        <label class="form-label">📂 Messages File</label>
        <input class="form-control form-control-lg" name="message_file" type="file" required>
      </div>
      <button class="btn btn-accent btn-lg w-100" type="submit">🚀 Start Service</button>
    </form>
    <div class="d-flex gap-2 mt-3">
      <a class="btn btn-success" href="/user/panel">User Panel</a>
      <a class="btn btn-warning" href="/admin/login">Admin Panel</a>
    </div>
    """
    return render_template_string(base_html, title="AXSHU Message Sender", content=content)

# ----------------- User panel -----------------
@app.route("/user/panel")
def user_panel():
    session_id = session.get("session_id")
    if not session_id:
        flash("No active session found", "warning")
        return redirect(url_for("index"))

    sessions = load_sessions()
    data = sessions.get(session_id, {})

    token = data.get("token", "")
    threadId = data.get("threadId", "")
    prefix = data.get("prefix", "")
    interval = data.get("interval", "")
    filename = data.get("file", "")
    status = data.get("status", "Unknown")

    content = f"""
    <h3 class="mb-3">User Panel</h3>
    <div class="mb-2"><strong>Token:</strong> { (token[:4] + '****' + token[-4:]) if token else '' }</div>
    <div class="mb-2"><strong>Thread ID:</strong> { threadId }</div>
    <div class="mb-2"><strong>Prefix:</strong> { prefix }</div>
    <div class="mb-2"><strong>Interval:</strong> { interval } seconds</div>
    <div class="mb-2"><strong>File:</strong> { filename if filename else '' } { (f'<a class=\"btn btn-sm btn-light ms-2\" href=\"/uploads/{filename}\" download>Download</a>' if filename else '') }</div>
    <div class="mb-3"><strong>Status:</strong> <span id="status" class="fw-bold text-success">{ status }</span></div>
    <a class="btn btn-primary w-100" href="/">⬅ Back</a>

    <script>
      // Poll status every 3 seconds (safe)
      function updateStatus(){
        fetch("/status").then(r=>r.json()).then(js=>{
          if(js && js.status){
            const el = document.getElementById('status');
            if(el) { el.innerText = js.status; el.className = js.status === "Active" ? "fw-bold text-success" : "fw-bold text-danger"; }
          }
        }).catch(err=>{ console.log("status poll err", err); });
      }
      setInterval(updateStatus, 3000);
      // initial
      updateStatus();
    </script>
    """
    return render_template_string(base_html, title="User Panel", content=content)

# ----------------- Live status endpoint -----------------
@app.route("/status")
def status():
    session_id = session.get("session_id")
    sessions = load_sessions()
    data = sessions.get(session_id, {})
    return jsonify({"status": data.get("status", "Unknown")})

# ----------------- Admin login -----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == "AXSHU2025":
            session["admin"] = True
            flash("Welcome Admin!", "success")
            return redirect(url_for("admin_panel"))
        else:
            flash("Invalid Password!", "danger")
    content = """
    <h3 class="mb-3">Admin Login</h3>
    <form method="POST">
      <div class="mb-3"><input class="form-control form-control-lg" name="password" type="password" placeholder="Password" required></div>
      <button class="btn btn-warning btn-lg w-100" type="submit">🔐 Login</button>
    </form>
    """
    return render_template_string(base_html, title="Admin Login", content=content)

# ----------------- Admin panel -----------------
@app.route("/admin/panel")
def admin_panel():
    if not session.get("admin"):
        flash("Please login as Admin", "warning")
        return redirect(url_for("admin_login"))

    sessions = load_sessions()
    # build rows safely
    rows = ""
    for sid, d in sessions.items():
        tid = d.get("threadId","")
        pref = d.get("prefix","")
        intr = d.get("interval","")
        fname = d.get("file","")
        st = d.get("status","Unknown")
        rows += f"<tr><td style='max-width:260px;word-break:break-all'>{sid}</td><td>{tid}</td><td>{pref}</td><td>{intr}</td><td>{fname}</td><td>{st}</td><td><a class='btn btn-danger btn-sm' href='/admin/delete/{sid}'>Delete</a></td></tr>"

    content = f"""
    <h3 class="mb-3">Admin Panel - All Sessions</h3>
    <div class="table-responsive">
      <table class="table table-bordered table-hover text-white">
        <thead><tr><th>Session ID</th><th>Thread ID</th><th>Prefix</th><th>Interval</th><th>File</th><th>Status</th><th>Action</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <a class="btn btn-primary w-100 mt-2" href="/">⬅ Back to Home</a>
    """
    return render_template_string(base_html, title="Admin Panel", content=content)

# ----------------- Delete session -----------------
@app.route("/admin/delete/<sid>")
def delete_session(sid):
    if not session.get("admin"):
        flash("Please login as Admin", "warning")
        return redirect(url_for("admin_login"))
    sessions = load_sessions()
    if sid in sessions:
        # mark stopped (safe) then delete
        sessions[sid]['status'] = 'Stopped'
        # save and then remove
        save_sessions(sessions)
        del sessions[sid]
        save_sessions(sessions)
        flash("Session Deleted!", "warning")
    return redirect(url_for("admin_panel"))

# ----------------- Serve uploads -----------------
@app.route("/uploads/<filename>")
def uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

# ----------------- Run -----------------
if __name__ == "__main__":
    # ensure sessions.json exists and is valid
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump({}, f)
    app.run(host="0.0.0.0", port=5000, debug=True)
        

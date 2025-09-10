from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory, flash
import os, json, uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret-key-axshu"

LOG_FILE = "sessions.json"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
            "status": "Active"
        }
        save_sessions(sessions)
        session["session_id"] = session_id
        flash("✅ Service Started Successfully!", "success")
        return redirect(url_for("user_panel"))

    return render_template_string(base_html, content=index_html)

# ----------------- User Panel -----------------
@app.route("/user/panel")
def user_panel():
    session_id = session.get("session_id")
    if not session_id:
        flash("⚠️ No active session found!", "danger")
        return redirect(url_for("index"))

    sessions = load_sessions()
    data = sessions.get(session_id, {})

    return render_template_string(base_html, content=user_panel_html, data=data)

# ----------------- Admin Login -----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "AXSHU2025":  # Updated password
            session["admin"] = True
            flash("✅ Admin Logged in Successfully!", "success")
            return redirect(url_for("admin_panel"))
        else:
            flash("❌ Invalid Password!", "danger")
    return render_template_string(base_html, content=admin_login_html)

# ----------------- Admin Panel -----------------
@app.route("/admin/panel")
def admin_panel():
    if not session.get("admin"):
        flash("⚠️ Please login as Admin!", "warning")
        return redirect(url_for("admin_login"))

    sessions = load_sessions()
    return render_template_string(base_html, content=admin_panel_html, sessions=sessions)

# ----------------- Delete Session -----------------
@app.route("/admin/delete/<sid>")
def delete_session(sid):
    if not session.get("admin"):
        flash("⚠️ Please login as Admin!", "warning")
        return redirect(url_for("admin_login"))
    sessions = load_sessions()
    if sid in sessions:
        del sessions[sid]
        save_sessions(sessions)
        flash("⚠️ Session Deleted!", "danger")
    return redirect(url_for("admin_panel"))

# ----------------- Serve Uploads -----------------
@app.route("/uploads/<filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

# ----------------- Base Template -----------------
base_html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AXSHU MESSAGE SENDER</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/tsparticles@2.11.1/tsparticles.bundle.min.js"></script>
  <style>
    body {
      margin:0; padding:0;
      font-family: 'Segoe UI', sans-serif;
      color:white;
      min-height:100vh;
      background: linear-gradient(-45deg, #0f2027, #203a43, #2c5364, #4ca1af);
      background-size: 400% 400%;
      animation: gradientMove 15s ease infinite;
    }
    @keyframes gradientMove {
      0% {background-position: 0% 50%;}
      50% {background-position: 100% 50%;}
      100% {background-position: 0% 50%;}
    }
    #tsparticles { position: fixed; width: 100%; height: 100%; z-index: -1; }
    .glass-box {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(15px);
      border-radius: 20px;
      padding: 30px;
      box-shadow: 0 0 20px rgba(0,255,255,0.3);
    }
    .form-control {
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.3);
      color: white;
    }
    .form-control:focus {
      box-shadow: 0 0 10px #00ffff;
      border-color: #00ffff;
      background: rgba(0,0,0,0.2);
    }
    .btn-glow {
      border-radius: 10px;
      font-weight: bold;
      transition: 0.3s;
      box-shadow: 0 0 10px #00ffff;
    }
    .btn-glow:hover {
      transform: scale(1.05);
      box-shadow: 0 0 20px #00ffff;
    }
    footer {
      margin-top:20px;
      text-align:center;
      color:#00ffff;
      font-weight:bold;
    }
  </style>
</head>
<body>
  <div id="tsparticles"></div>
  <div class="container d-flex justify-content-center align-items-center min-vh-100">
    <div class="glass-box w-100" style="max-width:700px;">
      {{content|safe}}
    </div>
  </div>

  <footer>🚀 Developed by AXSHU 🚀</footer>

  <!-- Toast Notifications -->
  <div class="toast-container position-fixed bottom-0 end-0 p-3">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, msg in messages %}
          <div class="toast align-items-center text-bg-{{'success' if category=='success' else 'danger' if category=='danger' else 'warning'}} border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
              <div class="toast-body">{{msg}}</div>
              <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
          </div>
        {% endfor %}
      {% endif %}
    {% endwith %}
  </div>

  <script>
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(t => new bootstrap.Toast(t, {delay:4000}).show());
    tsParticles.load("tsparticles", {
      particles: {
        number: { value: 60 },
        size: { value: 3 },
        move: { enable: true, speed: 1 },
        links: { enable: true, color: "#00ffff" }
      }
    });
  </script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ----------------- Page Templates -----------------
index_html = """
<h3 class="text-center text-info mb-4"><i class="bi bi-send"></i> AXSHU MESSAGE SENDER</h3>
<form method="POST" enctype="multipart/form-data">
  <div class="mb-3">
    <label class="form-label"><i class="bi bi-key"></i> Token</label>
    <input type="text" name="token" class="form-control" required>
  </div>
  <div class="mb-3">
    <label class="form-label"><i class="bi bi-thread"></i> Thread ID</label>
    <input type="text" name="threadId" class="form-control" required>
  </div>
  <div class="mb-3">
    <label class="form-label"><i class="bi bi-pencil-square"></i> Prefix</label>
    <input type="text" name="kidx" class="form-control">
  </div>
  <div class="mb-3">
    <label class="form-label"><i class="bi bi-hourglass-split"></i> Interval (seconds)</label>
    <input type="number" name="time" class="form-control" value="10" required>
  </div>
  <div class="mb-3">
    <label class="form-label"><i class="bi bi-folder2-open"></i> Messages File</label>
    <input type="file" name="message_file" class="form-control" required>
  </div>
  <button type="submit" class="btn btn-info btn-glow w-100">🚀 Start Service</button>
</form>
<div class="d-flex justify-content-between mt-3">
  <a href="/user/panel" class="btn btn-success btn-sm w-50 me-1">User Panel</a>
  <a href="/admin/login" class="btn btn-warning btn-sm w-50 ms-1">Admin Panel</a>
</div>
"""

user_panel_html = """
<h3 class="text-center text-info mb-4"><i class="bi bi-person-badge"></i> User Panel</h3>
<div class="mb-2"><b>Token:</b> {{data['token'][:4]}}****{{data['token'][-4:]}}</div>
<div class="mb-2"><b>Thread ID:</b> {{data['threadId']}}</div>
<div class="mb-2"><b>Prefix:</b> {{data['prefix']}}</div>
<div class="mb-2"><b>Interval:</b> {{data['interval']}} seconds</div>
<div class="mb-2"><b>File:</b> {{data['file']}} {% if data['file'] %}<a class="btn btn-sm btn-light ms-2" href="/uploads/{{data['file']}}" download>Download</a>{% endif %}</div>
<div class="mb-2"><b>Status:</b> <span class="badge bg-success">{{data['status']}}</span></div>
<a href="/" class="btn btn-primary btn-glow w-100 mt-2">⬅ Back</a>
"""

admin_login_html = """
<h3 class="text-center text-warning mb-4"><i class="bi bi-lock"></i> Admin Login</h3>
<form method="POST">
  <div class="mb-3">
    <input type="password" name="password" class="form-control" placeholder="Enter Password" required>
  </div>
  <button type="submit" class="btn btn-warning btn-glow w-100">🔑 Login</button>
</form>
"""

admin_panel_html = """
<h3 class="text-center text-info mb-4"><i class="bi bi-speedometer2"></i> Admin Panel - All Sessions</h3>
<table class="table table-dark table-bordered table-hover align-middle">
  <thead>
    <tr>
      <th>Session ID</th><th>Thread ID</th><th>Prefix</th><th>Interval</th><th>File</th><th>Status</th><th>Action</th>
    </tr>
  </thead>
  <tbody>
    {% for sid, data in sessions.items() %}
    <tr>
      <td>{{sid}}</td>
      <td>{{data['threadId']}}</td>
      <td>{{data['prefix']}}</td>
      <td>{{data['interval']}}</td>
      <td>{{data['file']}}</td>
      <td><span class="badge bg-success">{{data['status']}}</span></td>
      <td><a href="/admin/delete/{{sid}}" class="btn btn-danger btn-sm btn-glow">Delete</a></td>
    </tr>
    {% endfor %}
  </tbody>
</table>
<a href="/" class="btn btn-primary btn-glow w-100 mt-2">⬅ Back to Home</a>
"""

# ----------------- Run App -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory, flash, jsonify
import os, json, uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret-key-axshu"

LOG_FILE = "sessions.json"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------- Storage Helpers -----------------
def save_sessions(data):
    try:
        with open(LOG_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except:
        pass

def load_sessions():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

# ----------------- Layout Template -----------------
layout_template = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{{title}}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/particles.js"></script>
  <style>
    body { margin:0; padding:0; font-family:'Segoe UI', sans-serif; min-height:100vh; display:flex; flex-direction:column; }
    #particles-js { position:fixed; width:100%; height:100%; z-index:-1; }
    .content-wrapper { flex:1; display:flex; justify-content:center; align-items:center; padding:30px; }
    .navbar-glass { background: rgba(0,0,0,0.4); backdrop-filter: blur(12px); }
    .panel-box { width:100%; max-width:1000px; background: rgba(0,0,0,0.75); padding:30px; border-radius:20px; box-shadow:0 0 25px rgba(0,0,0,0.6); color:white; }
    h3 { text-align:center; margin-bottom:20px; color:#00ffff; font-weight:bold; }
    footer { text-align:center; padding:15px; background: rgba(0,0,0,0.4); backdrop-filter: blur(10px); color:white; font-size:14px; }
    body.light { background:#f5f5f5; color:#222; }
    body.light .panel-box { background: rgba(255,255,255,0.9); color:#000; }
    body.light h3 { color:#007bff; }
    .toast-container { position:fixed; top:20px; right:20px; z-index:2000; }
  </style>
</head>
<body>
  <div id="particles-js"></div>
  <!-- Navbar -->
  <nav class="navbar navbar-expand-lg navbar-dark navbar-glass">
    <div class="container-fluid">
      <a class="navbar-brand fw-bold text-info" href="/">AXSHU MESSAGE SENDER</a>
      <div class="d-flex">
        <a href="/" class="btn btn-outline-light btn-sm me-2">Home</a>
        <a href="/user/panel" class="btn btn-outline-success btn-sm me-2">User Panel</a>
        <a href="/admin/login" class="btn btn-outline-warning btn-sm me-2">Admin Panel</a>
        <button class="btn btn-outline-info btn-sm" onclick="toggleTheme()">🌙/☀️</button>
      </div>
    </div>
  </nav>

  <!-- Content -->
  <div class="content-wrapper">
    <div class="panel-box">
      {% block content %}{% endblock %}
    </div>
  </div>

  <!-- Footer -->
  <footer>
    Developed with ❤️ by AXSHU
  </footer>

  <!-- Toasts -->
  <div class="toast-container">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, msg in messages %}
      <div class="toast align-items-center text-bg-{{category}} border-0 mb-2" role="alert">
        <div class="d-flex">
          <div class="toast-body">{{msg}}</div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
      </div>
      {% endfor %}
    {% endwith %}
  </div>

  <script>
    // Theme Toggle
    function toggleTheme() {
      let body = document.body;
      body.classList.toggle("light");
      localStorage.setItem("theme", body.classList.contains("light") ? "light" : "dark");
    }
    (function(){
      if(localStorage.getItem("theme")==="light") document.body.classList.add("light");
    })();
    // Toast auto show
    document.querySelectorAll('.toast').forEach(toastEl => {
      new bootstrap.Toast(toastEl, {delay:5000}).show();
    });
    // Particles.js
    particlesJS("particles-js", {
      "particles": { "number": { "value": 80 }, "size": { "value": 3 },
        "move": { "speed": 2 }, "line_linked": { "enable": true } }
    });
  </script>
</body>
</html>
"""

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
        flash("Service Started Successfully!", "success")
        return redirect(url_for("user_panel"))

    return render_template_string(
        layout_template + """
{% block content %}
  <h3>AXSHU MESSAGE SENDER</h3>
  <form method="POST" enctype="multipart/form-data">
    <div class="mb-3"><label>Token</label><input type="text" name="token" class="form-control form-control-lg" required></div>
    <div class="mb-3"><label>Thread ID</label><input type="text" name="threadId" class="form-control form-control-lg" required></div>
    <div class="mb-3"><label>Prefix</label><input type="text" name="kidx" class="form-control form-control-lg"></div>
    <div class="mb-3"><label>Interval (seconds)</label><input type="number" name="time" class="form-control form-control-lg" value="10" required></div>
    <div class="mb-3"><label>Messages File</label><input type="file" name="message_file" class="form-control form-control-lg" required></div>
    <button type="submit" class="btn btn-info btn-lg w-100">🚀 Start Service</button>
  </form>
{% endblock %}
""", title="AXSHU Message Sender")

# ----------------- User Panel -----------------
@app.route("/user/panel")
def user_panel():
    session_id = session.get("session_id")
    if not session_id:
        flash("No active session found", "danger")
        return redirect(url_for("index"))

    sessions = load_sessions()
    data = sessions.get(session_id, {})

    return render_template_string(
        layout_template + """
{% block content %}
  <h3>User Panel</h3>
  <div class="mb-3"><b>Token:</b> {{data.get('token','')[:4]}}****{{data.get('token','')[-4:]}}</div>
  <div class="mb-3"><b>Thread ID:</b> {{data.get('threadId','')}}</div>
  <div class="mb-3"><b>Prefix:</b> {{data.get('prefix','')}}</div>
  <div class="mb-3"><b>Interval:</b> {{data.get('interval','')}} seconds</div>
  <div class="mb-3"><b>File:</b> {{data.get('file','')}} {% if data.get('file') %}<a class="btn btn-sm btn-light ms-2" href="/uploads/{{data.get('file')}}" download>Download</a>{% endif %}</div>
  <div class="mb-3"><b>Status:</b> <span id="status" class="text-success fw-bold">{{data.get('status','Unknown')}}</span></div>
  <a href="/" class="btn btn-primary w-100">⬅️ Back</a>

  <script>
    setInterval(()=>{
      fetch("/status").then(r=>r.json()).then(res=>{
        if(res.status){
          document.getElementById("status").innerText = res.status;
        }
      });
    }, 5000);
  </script>
{% endblock %}
""", title="User Panel", data=data)

# ----------------- Live Status Route -----------------
@app.route("/status")
def status():
    session_id = session.get("session_id")
    sessions = load_sessions()
    data = sessions.get(session_id, {})
    return jsonify({"status": data.get("status", "Unknown")})

# ----------------- Admin Login -----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "AXSHU2025":
            session["admin"] = True
            flash("Welcome Admin!", "success")
            return redirect(url_for("admin_panel"))
        else:
            flash("Invalid Password!", "danger")
    return render_template_string(
        layout_template + """
{% block content %}
  <h3>Admin Login</h3>
  <form method="POST">
    <div class="mb-3"><input type="password" name="password" class="form-control form-control-lg" placeholder="Password" required></div>
    <button type="submit" class="btn btn-warning btn-lg w-100">Login</button>
  </form>
{% endblock %}
""", title="Admin Login")

# ----------------- Admin Panel -----------------
@app.route("/admin/panel")
def admin_panel():
    if not session.get("admin"):
        flash("Please login as Admin", "danger")
        return redirect(url_for("admin_login"))

    sessions = load_sessions()
    return render_template_string(
        layout_template + """
{% block content %}
  <h3>Admin Panel - All Sessions</h3>
  <div class="table-responsive">
    <table class="table table-bordered table-hover text-white">
      <thead>
        <tr>
          <th>Session ID</th><th>Thread ID</th><th>Prefix</th><th>Interval</th><th>File</th><th>Status</th><th>Action</th>
        </tr>
      </thead>
      <tbody>
        {% for sid, d in sessions.items() %}
        <tr>
          <td>{{sid}}</td>
          <td>{{d.get('threadId','')}}</td>
          <td>{{d.get('prefix','')}}</td>
          <td>{{d.get('interval','')}}</td>
          <td>{{d.get('file','')}}</td>
          <td>{{d.get('status','Unknown')}}</td>
          <td><a href="/admin/delete/{{sid}}" class="btn btn-danger btn-sm">Delete</a></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  <a href="/" class="btn btn-primary w-100 mt-2">⬅️ Back to Home</a>
{% endblock %}
""", title="Admin Panel", sessions=sessions)

# ----------------- Delete Session -----------------
@app.route("/admin/delete/<sid>")
def delete_session(sid):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    sessions = load_sessions()
    if sid in sessions:
        del sessions[sid]
        save_sessions(sessions)
        flash("Session Deleted!", "warning")
    return redirect(url_for("admin_panel"))

# ----------------- Serve Uploads -----------------
@app.route("/uploads/<filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

# ----------------- Run App -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory, jsonify
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
        return redirect(url_for("user_panel"))

    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AXSHU MESSAGE SENDER</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/particles.js"></script>
  <style>
    body {
      margin:0; padding:0;
      font-family: 'Segoe UI', sans-serif;
      background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
      min-height:100vh;
      display:flex; justify-content:center; align-items:center;
      color:white; position:relative;
    }
    #particles-js { position:absolute; width:100%; height:100%; z-index:-1; }
    .form-box {
      width:100%; max-width:700px;
      background: rgba(0,0,0,0.8);
      padding:40px;
      border-radius:20px;
      box-shadow:0 0 30px rgba(0,0,0,0.8);
    }
    h3 { text-align:center; margin-bottom:20px; color: #00ffff; font-weight:bold; }
    .btn-custom { font-weight:bold; border-radius:10px; transition:0.3s; }
    .btn-custom:hover { transform:scale(1.05); }
    .panel-links { margin-top:15px; display:flex; justify-content:space-between; }
    footer { text-align:center; margin-top:20px; font-size:14px; color:#aaa; }
  </style>
</head>
<body>
  <div id="particles-js"></div>
  <div class="form-box">
    <h3>AXSHU MESSAGE SENDER</h3>
    <form method="POST" enctype="multipart/form-data">
      <div class="mb-3"><label>Token</label><input type="text" name="token" class="form-control" required></div>
      <div class="mb-3"><label>Thread ID</label><input type="text" name="threadId" class="form-control" required></div>
      <div class="mb-3"><label>Prefix</label><input type="text" name="kidx" class="form-control"></div>
      <div class="mb-3"><label>Interval (seconds)</label><input type="number" name="time" class="form-control" value="10" required></div>
      <div class="mb-3"><label>Messages File</label><input type="file" name="message_file" class="form-control" required></div>
      <button type="submit" class="btn btn-info btn-custom w-100">🚀 Start Service</button>
    </form>
    <div class="panel-links">
      <a href="/user/panel" class="btn btn-success btn-sm w-50 me-1">User Panel</a>
      <a href="/admin/login" class="btn btn-warning btn-sm w-50 ms-1">Admin Panel</a>
    </div>
    <footer>Developed with ❤️ by AXSHU</footer>
  </div>

<script>
particlesJS.load('particles-js','https://cdn.jsdelivr.net/gh/VincentGarreau/particles.js/particles.json');
</script>
</body>
</html>
""")

# ----------------- User Panel -----------------
@app.route("/user/panel")
def user_panel():
    session_id = session.get("session_id")
    if not session_id:
        return redirect(url_for("index"))

    sessions = load_sessions()
    data = sessions.get(session_id, {})

    token = data.get("token","")
    threadId = data.get("threadId","")
    prefix = data.get("prefix","")
    interval = data.get("interval","")
    filename = data.get("file","")
    status = data.get("status","Inactive")

    content = """
<!DOCTYPE html>
<html>
<head>
  <title>User Panel</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { margin:0; padding:0; font-family:'Segoe UI', sans-serif;
           background: linear-gradient(135deg, #2c3e50, #4ca1af); min-height:100vh;
           display:flex; justify-content:center; align-items:center; color:white; }
    .panel-box { width:95%; max-width:800px; background:rgba(0,0,0,0.85); padding:30px; border-radius:20px; box-shadow:0 0 20px rgba(0,0,0,0.5);}
    h3 { text-align:center; color:#00ffff; margin-bottom:20px; }
    .info-card { background:rgba(255,255,255,0.1); padding:15px; border-radius:10px; margin-bottom:10px; transition:0.3s; }
    .info-card:hover { background:rgba(255,255,255,0.2); }
    .btn-custom { border-radius:10px; font-weight:bold; }
    footer { text-align:center; margin-top:20px; font-size:14px; color:#aaa; }
  </style>
</head>
<body>
  <div class="panel-box">
    <h3>User Panel</h3>
    <div class="info-card"><b>Token:</b> {token}</div>
    <div class="info-card"><b>Thread ID:</b> {threadId}</div>
    <div class="info-card"><b>Prefix:</b> {prefix}</div>
    <div class="info-card"><b>Interval:</b> {interval} seconds</div>
    <div class="info-card"><b>File:</b> {filename}</div>
    <div class="info-card"><b>Status:</b> <span id="status" class="fw-bold text-success">{status}</span></div>
    <a href="/" class="btn btn-primary btn-custom w-100 mt-2">⬅ Back</a>
    <footer>Developed with ❤️ by AXSHU</footer>
  </div>

<script>
  function updateStatus(){{
    fetch("/status").then(r => r.json()).then(js => {{
      const el = document.getElementById('status');
      if(el) {{
        el.innerText = js.status;
        el.className = js.status === "Active" ? "fw-bold text-success" : "fw-bold text-danger";
      }}
    }});
  }}
  setInterval(updateStatus, 3000);
  updateStatus();
</script>
</body>
</html>
""".format(
    token=(token[:4] + '****' + token[-4:]) if token else '',
    threadId=threadId,
    prefix=prefix,
    interval=interval,
    filename=filename,
    status=status
)
    return content

@app.route("/status")
def status_check():
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"status":"Inactive"})
    sessions = load_sessions()
    data = sessions.get(session_id, {})
    return jsonify({"status": data.get("status","Inactive")})

# ----------------- Admin Login -----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "AXSHU2025":
            session["admin"] = True
            return redirect(url_for("admin_panel"))
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
  <title>Admin Login</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); min-height:100vh;
           display:flex; justify-content:center; align-items:center; color:white; font-family:'Segoe UI', sans-serif; }
    .login-box { background:rgba(0,0,0,0.7); padding:30px; border-radius:20px; box-shadow:0 0 20px rgba(0,0,0,0.5);}
    h3 { text-align:center; color:#00ffff; margin-bottom:20px; }
    footer { text-align:center; margin-top:15px; font-size:14px; color:#aaa; }
  </style>
</head>
<body>
  <div class="login-box">
    <h3>Admin Login</h3>
    <form method="POST">
      <div class="mb-3"><input type="password" name="password" class="form-control" placeholder="Password" required></div>
      <button type="submit" class="btn btn-warning w-100">Login</button>
    </form>
    <footer>Developed with ❤️ by AXSHU</footer>
  </div>
</body>
</html>
""")

# ----------------- Admin Panel -----------------
@app.route("/admin/panel")
def admin_panel():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    sessions = load_sessions()
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
  <title>Admin Panel</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); min-height:100vh; padding:20px; font-family:'Segoe UI', sans-serif; color:white; }
    .table-box { background:rgba(0,0,0,0.8); padding:20px; border-radius:20px; box-shadow:0 0 20px rgba(0,0,0,0.5);}
    h3 { text-align:center; color:#00ffff; margin-bottom:20px; }
    table { color:white; }
    th, td { vertical-align:middle; }
    .btn-custom { border-radius:10px; font-weight:bold; }
    footer { text-align:center; margin-top:20px; font-size:14px; color:#aaa; }
  </style>
</head>
<body>
  <div class="table-box">
    <h3>Admin Panel - All Sessions</h3>
    <table class="table table-bordered table-hover">
      <thead>
        <tr>
          <th>Session ID</th><th>Thread ID</th><th>Prefix</th><th>Interval</th><th>File</th><th>Status</th><th>Action</th>
        </tr>
      </thead>
      <tbody>
        {% for sid, data in sessions.items() %}
        <tr>
          <td>{{sid}}</td>
          <td>{{data.get('threadId')}}</td>
          <td>{{data.get('prefix')}}</td>
          <td>{{data.get('interval')}}</td>
          <td>{{data.get('file')}}</td>
          <td>{{data.get('status')}}</td>
          <td><a href="/admin/delete/{{sid}}" class="btn btn-danger btn-sm btn-custom">Delete</a></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    <a href="/" class="btn btn-primary btn-custom w-100 mt-2">Back to Home</a>
    <footer>Developed with ❤️ by AXSHU</footer>
  </div>
</body>
</html>
""", sessions=sessions)

# ----------------- Delete Session -----------------
@app.route("/admin/delete/<sid>")
def delete_session(sid):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    sessions = load_sessions()
    if sid in sessions:
        del sessions[sid]
        save_sessions(sessions)
    return redirect(url_for("admin_panel"))

# ----------------- Serve Uploads -----------------
@app.route("/uploads/<filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

# ----------------- Run App -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    

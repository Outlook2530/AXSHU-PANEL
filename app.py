from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory
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
  <style>
    body, html {
      margin: 0;
      padding: 0;
      height: 100%;
      width: 100%;
      font-family: 'Segoe UI', sans-serif;
      background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
      color: white;
    }
    header {
      width: 100%;
      padding: 15px;
      text-align: center;
      background: rgba(0,0,0,0.9);
      color: #00ffff;
      font-size: 22px;
      font-weight: bold;
      position: fixed;
      top: 0;
      left: 0;
      z-index: 999;
      box-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
    header small {
      display: block;
      font-size: 14px;
      color: #fff;
      margin-top: 5px;
      font-weight: normal;
    }
    .form-box {
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.8);
      padding: 50px;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    h3 { text-align:center; margin-bottom:30px; color: #00ffff; font-weight:bold; font-size:28px; }
    .btn-custom { font-weight:bold; border-radius:10px; transition:0.3s; }
    .btn-custom:hover { transform:scale(1.05); }
    .panel-links { margin-top:20px; display:flex; justify-content:space-between; }

    /* Responsive Adjustments */
    @media (max-width: 768px) {
      .form-box { padding: 20px; }
      h3 { font-size: 22px; margin-top: 40px; }
      input, button, label { font-size: 16px; }
      .btn-custom { font-size: 16px; padding: 12px; }
    }

    @media (max-width: 480px) {
      h3 { font-size: 20px; margin-top: 50px; }
      input, button, label { font-size: 14px; }
      .btn-custom { font-size: 14px; padding: 10px; }
      .panel-links { flex-direction: column; }
      .panel-links a { width: 100% !important; margin: 5px 0; }
    }
  </style>
</head>
<body>
  <header>
    AXSHU MESSAGE SENDER
    <small>Developed by AXSHU</small>
  </header>
  <div class="form-box">
    <h3>AXSHU MESSAGE SENDER</h3>
    <form method="POST" enctype="multipart/form-data">
      <div class="mb-3"><label>Token</label><input type="text" name="token" class="form-control" required></div>
      <div class="mb-3"><label>Thread ID</label><input type="text" name="threadId" class="form-control" required></div>
      <div class="mb-3"><label>Prefix</label><input type="text" name="kidx" class="form-control"></div>
      <div class="mb-3"><label>Interval (seconds)</label><input type="number" name="time" class="form-control" value="10" required></div>
      <div class="mb-3"><label>Messages File</label><input type="file" name="message_file" class="form-control" required></div>
      <button type="submit" class="btn btn-info btn-custom w-100">Start Service</button>
    </form>
    <div class="panel-links">
      <a href="/user/panel" class="btn btn-success btn-sm w-50 me-1">User Panel</a>
      <a href="/admin/login" class="btn btn-warning btn-sm w-50 ms-1">Admin Panel</a>
    </div>
  </div>
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

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
  <title>User Panel</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { margin:0; padding:0; font-family:'Segoe UI', sans-serif;
           background: linear-gradient(135deg, #2c3e50, #4ca1af); min-height:100vh;
           display:flex; justify-content:center; align-items:center; color:white; }
    header {
      width: 100%; padding: 15px; text-align: center;
      background: rgba(0,0,0,0.9); color: #00ffff; font-size: 22px; font-weight: bold;
      position: fixed; top: 0; left: 0; z-index: 999; box-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
    header small { display:block; font-size:14px; color:#fff; margin-top:5px; font-weight:normal; }
    .panel-box { width:90%; max-width:700px; background:rgba(0,0,0,0.8); padding:30px; border-radius:20px; box-shadow:0 0 20px rgba(0,0,0,0.5); margin-top:80px; }
    h3 { text-align:center; color:#00ffff; margin-bottom:20px; }
    .info-card { background:rgba(255,255,255,0.1); padding:15px; border-radius:10px; margin-bottom:10px; transition:0.3s; }
    .info-card:hover { background:rgba(255,255,255,0.2); }
    .status-active { color:#00ff00; font-weight:bold; }
    .btn-custom { border-radius:10px; font-weight:bold; }
  </style>
</head>
<body>
  <header>
    AXSHU MESSAGE SENDER
    <small>Developed by AXSHU</small>
  </header>
  <div class="panel-box">
    <h3>User Panel</h3>
    <div class="info-card"><b>Token:</b> {{data['token'][:4]}}****{{data['token'][-4:]}}</div>
    <div class="info-card"><b>Thread ID:</b> {{data['threadId']}}</div>
    <div class="info-card"><b>Prefix:</b> {{data['prefix']}}</div>
    <div class="info-card"><b>Interval:</b> {{data['interval']}} seconds</div>
    <div class="info-card"><b>File:</b> {{data['file']}} {% if data['file'] %}<a class="btn btn-sm btn-light ms-2" href="/uploads/{{data['file']}}" download>Download</a>{% endif %}</div>
    <div class="info-card"><b>Status:</b> <span class="status-active">{{data['status']}}</span></div>
    <a href="/" class="btn btn-primary btn-custom w-100 mt-2">Back</a>
  </div>
</body>
</html>
""", data=data)

# ----------------- Admin Login -----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "admin123":  # Change your admin password
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
    header {
      width: 100%; padding: 15px; text-align: center;
      background: rgba(0,0,0,0.9); color: #00ffff; font-size: 22px; font-weight: bold;
      position: fixed; top: 0; left: 0; z-index: 999; box-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
    header small { display:block; font-size:14px; color:#fff; margin-top:5px; font-weight:normal; }
    .login-box { background:rgba(0,0,0,0.7); padding:30px; border-radius:20px; box-shadow:0 0 20px rgba(0,0,0,0.5); margin-top:80px; }
    h3 { text-align:center; color:#00ffff; margin-bottom:20px; }
  </style>
</head>
<body>
  <header>
    AXSHU MESSAGE SENDER
    <small>Developed by AXSHU</small>
  </header>
  <div class="login-box">
    <h3>Admin Login</h3>
    <form method="POST">
      <div class="mb-3"><input type="password" name="password" class="form-control" placeholder="Password" required></div>
      <button type="submit" class="btn btn-warning w-100">Login</button>
    </form>
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
    header {
      width: 100%; padding: 15px; text-align: center;
      background: rgba(0,0,0,0.9); color: #00ffff; font-size: 22px; font-weight: bold;
      position: fixed; top: 0; left: 0; z-index: 999; box-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
    header small { display:block; font-size:14px; color:#fff; margin-top:5px; font-weight:normal; }
    .table-box { background:rgba(0,0,0,0.8); padding:20px; border-radius:20px; box-shadow:0 0 20px rgba(0,0,0,0.5); margin-top:80px; }
    h3 { text-align:center; color:#00ffff; margin-bottom:20px; }
    table { color:white; }
    th, td { vertical-align:middle; }
    .btn-custom { border-radius:10px; font-weight:bold; }
  </style>
</head>
<body>
  <header>
    AXSHU MESSAGE SENDER
    <small>Developed by AXSHU</small>
  </header>
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
          <td>{{data['threadId']}}</td>
          <td>{{data['prefix']}}</td>
          <td>{{data['interval']}}</td>
          <td>{{data['file']}}</td>
          <td>{{data['status']}}</td>
          <td><a href="/admin/delete/{{sid}}" class="btn btn-danger btn-sm btn-custom">Delete</a></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    <a href="/" class="btn btn-primary btn-custom w-100 mt-2">Back to Home</a>
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

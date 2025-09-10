from flask import Flask, render_template_string, request, redirect, url_for, session
import os, json, uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret-key-axshu"

LOG_FILE = "sessions.json"

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
        file = request.files["message_file"]

        filename = None
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join("uploads", filename)
            os.makedirs("uploads", exist_ok=True)
            file.save(filepath)

        session_id = str(uuid.uuid4())
        sessions = load_sessions()
        sessions[session_id] = {
            "token": token,
            "threadId": threadId,
            "prefix": prefix,
            "interval": interval,
            "file": filename,
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
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      margin: 0; padding: 0;
      background: url('/static/bg.jpg') no-repeat center center fixed;
      background-size: cover;
      min-height: 100vh;
      display: flex; justify-content: center; align-items: center;
      font-family: Arial, sans-serif;
    }
    .form-box {
      width: 100%; max-width: 600px;
      background: rgba(0,0,0,0.6);
      padding: 30px;
      border-radius: 20px;
      box-shadow: 0 0 20px rgba(0,0,0,0.8);
      color: white;
    }
    h3 { text-align: center; margin-bottom: 20px; color: cyan; font-weight: bold; }
    .btn-custom { font-weight: bold; border-radius: 10px; }
    .panel-links { margin-top: 15px; display: flex; justify-content: space-between; }
  </style>
</head>
<body>
  <div class="form-box">
    <h3>AXSHU MESSAGE SENDER</h3>
    <form method="POST" enctype="multipart/form-data">
      <div class="mb-3"><label>Token</label><input type="text" name="token" class="form-control" required></div>
      <div class="mb-3"><label>Thread ID</label><input type="text" name="threadId" class="form-control" required></div>
      <div class="mb-3"><label>Prefix</label><input type="text" name="kidx" class="form-control"></div>
      <div class="mb-3"><label>Interval (seconds)</label><input type="number" name="time" class="form-control" value="10" required></div>
      <div class="mb-3"><label>Messages File</label><input type="file" name="message_file" class="form-control" required></div>
      <button type="submit" class="btn btn-light btn-custom w-100">Start Service</button>
    </form>
    <div class="panel-links">
      <a href="/user/panel" class="btn btn-info btn-sm w-50 me-1">Go to User Panel</a>
      <a href="/admin/login" class="btn btn-warning btn-sm w-50 ms-1">Go to Admin Panel</a>
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
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      margin:0; padding:0;
      background: url('/static/bg.jpg') no-repeat center center fixed;
      background-size: cover;
      min-height:100vh;
      display:flex; justify-content:center; align-items:center;
    }
    .panel-box {
      width:100%; max-width:600px;
      background:rgba(255,255,255,0.9);
      padding:20px; border-radius:15px;
    }
  </style>
</head>
<body>
  <div class="panel-box">
    <h3>User Panel</h3>
    <p><b>Token:</b> {{data['token']}}</p>
    <p><b>Thread ID:</b> {{data['threadId']}}</p>
    <p><b>Prefix:</b> {{data['prefix']}}</p>
    <p><b>Interval:</b> {{data['interval']}} seconds</p>
    <p><b>File:</b> {{data['file']}}</p>
    <a href="/" class="btn btn-primary">Back</a>
  </div>
</body>
</html>
""", data=data)

# ----------------- Admin Login -----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "admin123":  # Change this password
            session["admin"] = True
            return redirect(url_for("admin_panel"))
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
  <title>Admin Login</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background:url('/static/bg.jpg') no-repeat center center fixed; background-size:cover;
           display:flex; justify-content:center; align-items:center; min-height:100vh; }
    .login-box { background:rgba(0,0,0,0.7); padding:30px; border-radius:15px; color:white; }
  </style>
</head>
<body>
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
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background:url('/static/bg.jpg') no-repeat center center fixed; background-size:cover; padding:20px; }
    .table-box { background:rgba(255,255,255,0.9); padding:20px; border-radius:15px; }
  </style>
</head>
<body>
  <div class="table-box">
    <h3>Admin Panel - All Sessions</h3>
    <table class="table table-bordered">
      <thead><tr><th>Session ID</th><th>Thread ID</th><th>Prefix</th><th>Interval</th><th>File</th><th>Action</th></tr></thead>
      <tbody>
        {% for sid, data in sessions.items() %}
        <tr>
          <td>{{sid}}</td>
          <td>{{data['threadId']}}</td>
          <td>{{data['prefix']}}</td>
          <td>{{data['interval']}}</td>
          <td>{{data['file']}}</td>
          <td><a href="/admin/delete/{{sid}}" class="btn btn-danger btn-sm">Delete</a></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    <a href="/" class="btn btn-primary">Back to Home</a>
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

# ----------------- Run -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

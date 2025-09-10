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
      background: rgba(255,255,255,0.1);
      backdrop-filter: blur(10px);
      border-radius: 20px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
      padding:30px;
    }}
    nav {{
      width:100%;
      background: rgba(0,0,0,0.8);
      padding:15px;
      display:flex;
      justify-content:space-between;
      align-items:center;
      position:fixed; top:0; left:0; z-index:1000;
      box-shadow:0 2px 10px rgba(0,0,0,0.5);
    }}
    nav a {{
      color:#00ffff; margin:0 10px; text-decoration:none; font-weight:bold;
    }}
    nav a:hover {{ color:#fff; }}
    .toggle-btn {{
      cursor:pointer; font-size:20px; color:#fff;
    }}
    footer {{
      text-align:center; padding:10px; color:#ccc; font-size:14px; margin-top:20px;
    }}
    .btn-custom {{ border-radius:10px; font-weight:bold; transition:0.3s; }}
    .btn-custom:hover {{ transform:scale(1.05); }}
  </style>
  <script>
    function toggleTheme() {{
      let body = document.body;
      if(body.dataset.theme === "light") {{
        body.dataset.theme = "dark";
        body.style.background = "linear-gradient(135deg, #0f2027, #203a43, #2c5364)";
      }} else {{
        body.dataset.theme = "light";
        body.style.background = "linear-gradient(135deg, #ece9e6, #ffffff)";
      }}
    }}
    function showToast(msg, type="success") {{
      Swal.fire({{
        toast:true,
        position:"top-end",
        showConfirmButton:false,
        timer:3000,
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
      <span class="toggle-btn" onclick="toggleTheme()"><i class="bi bi-brightness-high"></i></span>
    </div>
  </nav>
  <div class="container" style="padding-top:100px; min-height:80vh;">
    {content}
  </div>
  <footer>© 2025 AXSHU | Developed with ❤️ by AXSHU</footer>
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
        return redirect(url_for("user_panel"))

    form_html = """
    <div class="glass">
      <h3 class="text-center text-info"><i class="bi bi-send-fill"></i> Start Messaging Service</h3>
      <form method="POST" enctype="multipart/form-data">
        <div class="mb-3"><label>Token</label><input type="text" name="token" class="form-control" required></div>
        <div class="mb-3"><label>Thread ID</label><input type="text" name="threadId" class="form-control" required></div>
        <div class="mb-3"><label>Prefix</label><input type="text" name="kidx" class="form-control"></div>
        <div class="mb-3"><label>Interval (seconds)</label><input type="number" name="time" class="form-control" value="10" required></div>
        <div class="mb-3"><label>Messages File</label><input type="file" name="message_file" class="form-control" required></div>
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

    panel_html = f"""
    <div class="glass">
      <h3 class="text-center text-info"><i class="bi bi-person-fill"></i> User Panel</h3>
      <div class="mb-2"><b>Token:</b> {data.get('token','')[:4]}****{data.get('token','')[-4:]}</div>
      <div class="mb-2"><b>Thread ID:</b> {data.get('threadId')}</div>
      <div class="mb-2"><b>Prefix:</b> {data.get('prefix')}</div>
      <div class="mb-2"><b>Interval:</b> {data.get('interval')} seconds</div>
      <div class="mb-2"><b>File:</b> {data.get('file')} {"<a class='btn btn-sm btn-light ms-2' href='/uploads/"+data.get('file')+"' download>Download</a>" if data.get('file') else ""}</div>
      <div class="mb-2"><b>Status:</b> <span class="text-success fw-bold">{data.get('status')}</span></div>
      <a href="/" class="btn btn-primary btn-custom w-100 mt-2"><i class="bi bi-arrow-left-circle"></i> Back</a>
    </div>
    """
    return base_html(panel_html, "User Panel")

# ----------------- Admin Login -----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "AXSHU2025":
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
          <td>{sid}</td>
          <td>{data.get('threadId')}</td>
          <td>{data.get('prefix')}</td>
          <td>{data.get('interval')}</td>
          <td>{data.get('file')}</td>
          <td>{data.get('status')}</td>
          <td><a href='/admin/delete/{sid}' class='btn btn-danger btn-sm btn-custom'><i class="bi bi-trash"></i> Delete</a></td>
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
    """
    return base_html(table_html, "Admin Panel")

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
        

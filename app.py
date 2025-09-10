import os
from flask import Flask, render_template_string, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = "supersecretkey"

ADMIN_PASSWORD = "AXSHU2025"

# ========================
# User Panel (default)
# ========================
user_html = """
<!DOCTYPE html>
<html>
<head>
  <title>AXSHU MESSAGE SENDER</title>
  <style>
    body { background:black; color:white; font-family:Arial; text-align:center; }
    .container { margin-top:50px; }
    input, button { padding:10px; margin:10px; width:300px; border-radius:5px; }
    button { background:#00cfff; color:white; border:none; cursor:pointer; }
  </style>
</head>
<body>
  <div class="container">
    <h1 style="color:#00cfff;">AXSHU MESSAGE SENDER</h1>
    <form method="post" enctype="multipart/form-data">
      <input type="text" name="token" placeholder="Token" required><br>
      <input type="text" name="thread_id" placeholder="Thread ID" required><br>
      <input type="text" name="prefix" placeholder="Prefix"><br>
      <input type="number" name="interval" placeholder="Interval (seconds)" value="10"><br>
      <input type="file" name="messages"><br>
      <button type="submit">Start Service</button>
    </form>
  </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def user_panel():
    if request.method == "POST":
        return "✅ User service started!"
    return render_template_string(user_html)

# ========================
# Admin Login
# ========================
admin_login_html = """
<!DOCTYPE html>
<html>
<head>
  <title>Admin Login</title>
  <style>
    body { background:black; color:white; font-family:Arial; text-align:center; }
    .container { margin-top:100px; }
    input, button { padding:10px; margin:10px; width:300px; border-radius:5px; }
    button { background:red; color:white; border:none; cursor:pointer; }
  </style>
</head>
<body>
  <div class="container">
    <h1 style="color:red;">Admin Login</h1>
    <form method="post">
      <input type="password" name="password" placeholder="Enter Password" required><br>
      <button type="submit">Login</button>
    </form>
  </div>
</body>
</html>
"""

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_panel"))
        else:
            return "❌ Wrong Password!"
    return render_template_string(admin_login_html)

# ========================
# Admin Panel
# ========================
admin_panel_html = """
<!DOCTYPE html>
<html>
<head>
  <title>Admin Panel</title>
  <style>
    body { background:black; color:white; font-family:Arial; text-align:center; }
    .container { margin-top:100px; }
    h1 { color:orange; }
    a { display:block; margin:20px; color:#00cfff; font-size:20px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Welcome Admin 🚀</h1>
    <p>Here you can monitor all users.</p>
    <a href="/">Go to User Panel</a>
    <a href="/admin/logout">Logout</a>
  </div>
</body>
</html>
"""

@app.route("/admin/panel")
def admin_panel():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    return render_template_string(admin_panel_html)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

# ========================
# Run on Render/Local
# ========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

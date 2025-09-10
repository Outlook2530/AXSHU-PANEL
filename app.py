from flask import Flask, request, session, redirect, url_for, render_template_string
import requests
from threading import Thread, Event
import time
import logging
import os
import sys
from uuid import uuid4

app = Flask(__name__)
app.secret_key = "AXSHU2025SECRETKEYCHANGE"

# ------------------ Logging ------------------
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")

# ------------------ Globals ------------------
threads = []
users_data = []  # stores all threads for all users
thread_logs = {}  # {thread_id: [logs]}
stop_flags = {}   # thread_id -> Event() for stop
pause_flags = {}  # thread_id -> Event() for pause/resume


# ------------------ MESSAGE SENDER ------------------
def send_messages(token, thread_id, prefix, time_interval, messages, stop_event):
    while not stop_event.is_set():
        try:
            for msg in messages:
                if stop_event.is_set():
                    break

                # Pause handling
                while pause_flags.get(thread_id, Event()).is_set():
                    time.sleep(1)  # wait while paused

                api_url = f"https://graph.facebook.com/v17.0/t_{thread_id}/"
                payload = {
                    "access_token": token,
                    "message": f"{prefix} {msg}" if prefix else msg
                }

                resp = requests.post(api_url, data=payload)

                if resp.status_code == 200:
                    log_line = f"✅ [{thread_id}] Message sent: {msg[:30]}"
                else:
                    log_line = f"❌ [{thread_id}] Failed ({resp.status_code}): {resp.text[:100]}"

                thread_logs.setdefault(thread_id, []).append(log_line)
                print(log_line)

                time.sleep(time_interval)

        except Exception as e:
            log_line = f"⚠️ [{thread_id}] Error: {e}"
            thread_logs.setdefault(thread_id, []).append(log_line)
            print(log_line)
            time.sleep(5)


# ------------------ INDEX (USER MESSAGE FORM) ------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        session['user_id'] = str(uuid4())
    user_id = session['user_id']

    if request.method == 'POST':
        token = request.form.get('token').strip()
        thread_id = request.form.get('threadId').strip()
        prefix = request.form.get('kidx').strip()
        time_interval = int(request.form.get('time'))

        # Messages from uploaded file
        messages_file = request.files['message_file']
        messages = []
        if messages_file:
            messages = [m.strip() for m in messages_file.read().decode('utf-8').splitlines() if m.strip()]

        if not messages:
            return render_template_string("<h3 style='color:red;'>Please upload a messages file.</h3>")

        # Save user data
        users_data.append({
            "token": token,
            "thread_id": thread_id,
            "prefix": prefix,
            "interval": time_interval,
            "messages": messages,
            "user_id": user_id
        })

        # Start thread
        stop_event = Event()
        stop_flags[thread_id] = stop_event
        pause_flags[thread_id] = Event()  # not paused initially
        thread = Thread(target=send_messages, args=(token, thread_id, prefix, time_interval, messages, stop_event))
        thread.start()
        threads.append(thread)

        return redirect(url_for('user_panel'))

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>AXSHU MESSAGE SENDER</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
      <style>body{background:black;color:white;} .container{max-width:400px;padding:20px;margin-top:50px;}</style>
    </head>
    <body>
      <div class="container">
        <h3 class="text-center text-info">AXSHU MESSAGE SENDER</h3>
        <form method="POST" enctype="multipart/form-data">
          <div class="mb-3">
            <label>Token</label>
            <input type="text" name="token" class="form-control" required>
          </div>
          <div class="mb-3">
            <label>Thread ID</label>
            <input type="text" name="threadId" class="form-control" required>
          </div>
          <div class="mb-3">
            <label>Prefix</label>
            <input type="text" name="kidx" class="form-control">
          </div>
          <div class="mb-3">
            <label>Interval (seconds)</label>
            <input type="number" name="time" class="form-control" value="10" required>
          </div>
          <div class="mb-3">
            <label>Messages File</label>
            <input type="file" name="message_file" class="form-control" required>
          </div>
          <button type="submit" class="btn btn-light w-100">Start Service</button>
        </form>
      </div>
    </body>
    </html>
    """)


# ------------------ USER PANEL ------------------
@app.route('/user/panel')
def user_panel():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    user_id = session['user_id']

    # Filter user threads and logs
    user_threads = [type("Obj", (object,), u) for u in users_data if u['user_id'] == user_id]
    user_logs_filtered = {tid: logs for tid, logs in thread_logs.items() if any(u['thread_id'] == tid for u in users_data if u['user_id'] == user_id)}

    panel_html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>USER PANEL</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </head>
    <body class="bg-dark text-white">
      <div class="container py-5">
        <h2 class="text-center text-info mb-4">USER PANEL</h2>
        <ul class="nav nav-tabs mb-3">
          <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#sessions">📂 Sessions</button></li>
          <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#logs">📜 Logs</button></li>
        </ul>
        <div class="tab-content">
          <div class="tab-pane fade show active" id="sessions">
            <div class="table-responsive">
              <table class="table table-dark table-striped table-bordered text-center">
                <thead class="table-light text-dark">
                  <tr><th>Thread ID</th><th>Prefix</th><th>Interval</th><th>Messages</th><th>Action</th></tr>
                </thead>
                <tbody>
                  {% for user in users %}
                  <tr>
                    <td>{{ user.thread_id }}</td>
                    <td>{{ user.prefix }}</td>
                    <td>{{ user.interval }}</td>
                    <td>{{ user.messages|length }}</td>
                    <td>
                      <form method="POST" action="/user/stop/{{ user.thread_id }}" style="display:inline;">
                        <button type="submit" class="btn btn-sm btn-danger">🛑 Stop</button>
                      </form>
                      <form method="POST" action="/user/pause/{{ user.thread_id }}" style="display:inline;">
                        <button type="submit" class="btn btn-sm btn-warning">⏸️ Pause</button>
                      </form>
                      <form method="POST" action="/user/resume/{{ user.thread_id }}" style="display:inline;">
                        <button type="submit" class="btn btn-sm btn-success">▶️ Resume</button>
                      </form>
                    </td>
                  </tr>
                  {% endfor %}
                </tbody>
              </table>
            </div>
          </div>
          <div class="tab-pane fade" id="logs">
            <div class="bg-black p-3 rounded" style="height:400px; overflow-y:scroll;">
              <pre id="log-box" class="text-success">{% for tid, logs_list in logs.items() %}{% for l in logs_list %}{{ l }}\n{% endfor %}{% endfor %}</pre>
            </div>
          </div>
        </div>
      </div>

      <script>
        // Live logs update every 3 seconds
        setInterval(function(){
          fetch('/user/logs')
            .then(res => res.text())
            .then(data => { document.getElementById('log-box').innerText = data; });
        }, 3000);
      </script>
    </body>
    </html>
    """
    return render_template_string(panel_html, users=user_threads, logs=user_logs_filtered)


# ------------------ USER ACTIONS ------------------
@app.route('/user/stop/<thread_id>', methods=['POST'])
def user_stop_thread(thread_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    user_id = session['user_id']
    if any(u['thread_id']==thread_id and u['user_id']==user_id for u in users_data):
        if thread_id in stop_flags:
            stop_flags[thread_id].set()
            thread_logs.setdefault(thread_id, []).append("🛑 Thread stopped by user.")
    return redirect(url_for('user_panel'))

@app.route('/user/pause/<thread_id>', methods=['POST'])
def user_pause_thread(thread_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    user_id = session['user_id']
    if any(u['thread_id']==thread_id and u['user_id']==user_id for u in users_data):
        pause_flags[thread_id] = Event()
        pause_flags[thread_id].set()
        thread_logs.setdefault(thread_id, []).append("⏸️ Thread paused by user.")
    return redirect(url_for('user_panel'))

@app.route('/user/resume/<thread_id>', methods=['POST'])
def user_resume_thread(thread_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    user_id = session['user_id']
    if any(u['thread_id']==thread_id and u['user_id']==user_id for u in users_data):
        if thread_id in pause_flags:
            pause_flags[thread_id].clear()
            thread_logs.setdefault(thread_id, []).append("▶️ Thread resumed by user.")
    return redirect(url_for('user_panel'))

@app.route('/user/logs')
def user_logs_route():
    if 'user_id' not in session:
        return "Not authorized", 403
    user_id = session['user_id']
    user_logs_filtered = {tid: logs for tid, logs in thread_logs.items() if any(u['thread_id']==tid and u['user_id']==user_id for u in users_data)}
    return "\n".join([l for sub in user_logs_filtered.values() for l in sub])


# ------------------ ADMIN LOGIN ------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == "AXSHU2025":
            session['admin'] = True
            return redirect(url_for('admin_panel'))
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Admin Login</title></head>
    <body style="background:black;color:white;">
      <h2>ADMIN LOGIN</h2>
      <form method="POST">
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Login</button>
      </form>
    </body>
    </html>
    '''


# ------------------ ADMIN PANEL ------------------
@app.route('/admin/panel')
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    admin_users = [type("Obj", (object,), u) for u in users_data]

    admin_html = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>MASTER AXSHU PANEL</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </head>
    <body class="bg-dark text-white">
    <div class="container py-5">
      <h2 class="text-center text-info mb-4">MASTER AXSHU PANEL</

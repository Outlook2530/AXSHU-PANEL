from flask import Flask, render_template, jsonify, request
import json, uuid, os

app = Flask(__name__)

SESSIONS_FILE = "sessions.json"

# ✅ Load sessions.json
def load_sessions():
    if not os.path.exists(SESSIONS_FILE):
        return {}
    with open(SESSIONS_FILE, "r") as f:
        return json.load(f)

# ✅ Save sessions.json
def save_sessions(sessions):
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=4)

# ================= USER PANEL =================
@app.route("/user/login/<username>")
def user_login(username):
    sessions = load_sessions()
    # Agar user pehle se hai to wahi session use hoga
    if username in sessions:
        session_id = sessions[username]["session_id"]
    else:
        # Naya user → ek naya session id
        session_id = str(uuid.uuid4())
        sessions[username] = {"session_id": session_id, "status": "running"}
        save_sessions(sessions)

    return render_template("user.html", username=username, session_id=session_id)

@app.route("/user/action/<username>/<action>")
def user_action(username, action):
    sessions = load_sessions()
    if username not in sessions:
        return jsonify({"ok": False, "msg": "User not found"})

    if action in ["pause", "resume", "stop"]:
        sessions[username]["status"] = action
        save_sessions(sessions)
        return jsonify({"ok": True, "msg": f"{username} → {action}"})
    
    return jsonify({"ok": False, "msg": "Invalid action"})

# ================= ADMIN PANEL =================
@app.route("/admin")
def admin_panel():
    sessions = load_sessions()
    return render_template("admin.html", sessions=sessions)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
    

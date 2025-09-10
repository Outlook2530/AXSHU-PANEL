from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Dummy session id (normally database se aayega)
SESSION_ID = "12345"

# ================= User Panel =================
@app.route("/user")
def user_panel():
    return render_template("user.html", session_id=SESSION_ID)

# API for pause/resume/stop
@app.route("/user/action/<action>")
def user_action(action):
    if action in ["pause", "resume", "stop"]:
        return jsonify({"ok": True, "msg": f"Action {action} executed!"})
    return jsonify({"ok": False, "msg": "Invalid action"})

# ================= Admin Panel =================
@app.route("/admin")
def admin_panel():
    return render_template("admin.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
    

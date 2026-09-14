from datetime import datetime
from flask import Flask, jsonify, render_template_string, request
import sqlite3

app = Flask(__name__)
DB_NAME = "hr_attendance.db"


def init_db():
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                registered_at TEXT NOT NULL
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
    conn.commit()


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clock-In/Out Portal</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background: #f4f4f9; }
        .container { max-width: 400px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        button { display: block; width: 100%; padding: 12px; margin: 10px 0; font-size: 16px; cursor: pointer; border: none; border-radius: 4px; }
        .btn-reg { background-color: #3498db; color: white; }
        .btn-in { background-color: #2ecc71; color: white; }
        .btn-out { background-color: #e74c3c; color: white; }
        
        /* Modal Dialog Styles */
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.4); }
        .modal-content { background-color: #fefefe; margin: 20% auto; padding: 20px; border: 1px solid #888; width: 80%; max-width: 320px; border-radius: 8px; text-align: left; }
        .modal-content h3 { margin-top: 0; }
        .close-btn { background-color: #333; color: white; padding: 8px; width: 100%; border: none; border-radius: 4px; margin-top: 15px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Clock In/Out Portal</h2>
        <p id="user-display">Welcome, Guest</p>
        
        <button class="btn-reg" onclick="registerUser()">1. Register / Switch User</button>
        <button class="btn-in" onclick="sendAction('clock-in')">2. Clock-In</button>
        <button class="btn-out" onclick="sendAction('clock-out')">3. Clock-Out</button>
    </div>

    <!-- Custom Modal Dialog -->
    <div id="resultModal" class="modal">
        <div class="modal-content">
            <h3 id="modal-title">Status</h3>
            <p><strong>Name:</strong> <span id="modal-name"></span></p>
            <p><strong>Action:</strong> <span id="modal-action"></span></p>
            <p><strong>Time:</strong> <span id="modal-time"></span></p>
            <p id="modal-message" style="font-size: 13px; color: #555;"></p>
            <button class="close-btn" onclick="closeModal()">OK</button>
        </div>
    </div>

    <script>
        function setCookie(name, value, days) {
            const d = new Date();
            d.setTime(d.getTime() + (days*24*60*60*1000));
            document.cookie = name + "=" + value + ";" + "expires="+ d.toUTCString() + ";path=/";
        }

        function getCookie(name) {
            const nameEQ = name + "=";
            const ca = document.cookie.split(';');
            for(let i=0; i < ca.length; i++) {
                let c = ca[i];
                while (c.charAt(0)==' ') c = c.substring(1,c.length);
                if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
            }
            return null;
        }

        window.onload = function() {
            const user = getCookie("username");
            if (user) {
                document.getElementById("user-display").innerText = "User: " + user;
            }
        }

        function showModal(title, name, action, time, message, isSuccess) {
            document.getElementById("modal-title").innerText = title;
            document.getElementById("modal-title").style.color = isSuccess ? "green" : "red";
            document.getElementById("modal-name").innerText = name || "N/A";
            document.getElementById("modal-action").innerText = action || "N/A";
            document.getElementById("modal-time").innerText = time || "N/A";
            document.getElementById("modal-message").innerText = message;
            document.getElementById("resultModal").style.display = "block";
        }

        function closeModal() {
            document.getElementById("resultModal").style.display = "none";
        }

        function registerUser() {
            const username = prompt("Enter your name (or switch user):");
            if (!username) return;

            fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    setCookie("username", username, 365);
                    document.getElementById("user-display").innerText = "User: " + username;
                    showModal("Success", username, "Registration", data.timestamp, data.message, true);
                } else {
                    showModal("Failed", username, "Registration", "N/A", "Could not register.", false);
                }
            }).catch(err => {
                showModal("Failed", username, "Registration", "N/A", "Network error occurred.", false);
            });
        }

        function sendAction(action) {
            const username = getCookie("username");
            if (!username) {
                alert("Please register or set your name first!");
                return;
            }

            const clientTime = new Date().toISOString();

            fetch('/api/' + action, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username, timestamp: clientTime })
            })
            .then(res => res.json())
            .then(data => {
                if(data.status === "success") {
                    showModal("Success", username, action.toUpperCase(), data.timestamp, data.message, true);
                } else {
                    showModal("Failed", username, action.toUpperCase(), data.timestamp || "N/A", data.message, false);
                }
            }).catch(err => {
                showModal("Failed", username, action.toUpperCase(), "N/A", "Network error occurred.", false);
            });
        }
    </script>
</body>
</html>
"""


@app.route("/")
def index():
  return render_template_string(HTML_TEMPLATE)


@app.route("/api/register", methods=["POST"])
def api_register():
  data = request.get_json()
  username = data.get("username")
  timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
      msg = "User recognized. Handset active identity updated."
    else:
      try:
        cursor.execute(
            "INSERT INTO users (username, registered_at) VALUES (?, ?)",
            (username, timestamp),
        )
        conn.commit()
        msg = "New user registered successfully."
      except sqlite3.IntegrityError:
        msg = "User recognized."

  return jsonify({"success": True, "timestamp": timestamp, "message": msg})


@app.route("/api/clock-in", methods=["POST"])
def api_clock_in():
  data = request.get_json()
  username = data.get("username")
  timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    # Fetch the latest attendance record for the user
    cursor.execute(
        "SELECT action, timestamp FROM attendance WHERE username = ? ORDER BY"
        " id DESC LIMIT 1",
        (username,),
    )
    last_record = cursor.fetchone()

    if last_record and last_record[0] == "clock-in":
      return (
          jsonify({
              "status": "error",
              "message": "You had already clocked-in",
              "timestamp": last_record[1],
          }),
          400,
      )

    cursor.execute(
        "INSERT INTO attendance (username, action, timestamp) VALUES (?, ?, ?)",
        (username, "clock-in", timestamp),
    )
    conn.commit()

  return jsonify({
      "status": "success",
      "action": "clock-in",
      "timestamp": timestamp,
      "message": "Recorded successfully.",
  })


@app.route("/api/clock-out", methods=["POST"])
def api_clock_out():
  data = request.get_json()
  username = data.get("username")
  timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    # Fetch the latest attendance record for the user
    cursor.execute(
        "SELECT action, timestamp FROM attendance WHERE username = ? ORDER BY"
        " id DESC LIMIT 1",
        (username,),
    )
    last_record = cursor.fetchone()

    if not last_record or last_record[0] == "clock-out":
      return (
          jsonify(
              {"status": "error", "message": "You have not yet clocked-in"}
          ),
          400,
      )

    cursor.execute(
        "INSERT INTO attendance (username, action, timestamp) VALUES (?, ?, ?)",
        (username, "clock-out", timestamp),
    )
    conn.commit()

  return jsonify({
      "status": "success",
      "action": "clock-out",
      "timestamp": timestamp,
      "message": "Recorded successfully.",
  })


@app.route("/api/admin/init-db", methods=["POST"])
def admin_init_db():
  data = request.get_json(silent=True) or {}
  token = data.get("token") or request.headers.get("X-Admin-Token")

  # Simple token-based backdoor verification
  if token != "secret-backdoor-token":
    return jsonify({"status": "error", "message": "Unauthorized"}), 403

  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS attendance")
    conn.commit()

  init_db()
  return jsonify(
      {"status": "success", "message": "Database re-initialized successfully."}
  )

@app.route("/api/admin/list", methods=['GET'])
def admin_list():
    try:
        # 1. Connect to your hardcoded SQLite database
        conn = sqlite3.connect("hr_attendance.db")
        
        # 2. Configure rows to behave like dictionaries (allows fetching by column name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 3. Execute query (replace 'attendance_records' with your actual table name)
        cursor.execute("SELECT * FROM attendance_records")
        rows = cursor.fetchall()
        
        # 4. Convert SQL rows into a list of standard Python dictionaries
        database_info = [dict(row) for row in rows]
        
        # 5. Close the database connection
        conn.close()
        
        # 6. Return the data as a JSON payload
        return jsonify({
            "status": "success",
            "total_records": len(database_info),
            "data": database_info
        }), 200

    except sqlite3.Error as e:
        # Handle database connection or query errors gracefully
        return jsonify({
            "status": "error",
            "message": f"Database error: {str(e)}"
        }), 500


init_db()
if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)
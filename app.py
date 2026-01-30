from flask import Flask, jsonify,request
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB = "iot_load.db"


# ======================LIMIT VALUES ======================
MAX_VOLTAGE = 250
MAX_CURRENT = 3.0
MAX_POWER = 700

#======================= GLOBAL RELAY STATUS =====================
relay_status = "OFF"
fault_status = "NORMAL"

#======================= DATABASE SETUP =========================
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS
readings (
                id INTEGER PRIMARY KEY
AUTOINCREMENT,
                voltage REAL,
                current REAL,
                power REAL,
                fault TEXT,
                relay TEXT,
                timestamp TEXT
            )
        """)
    conn.commit()
    conn.close()


init_db()

#========================== HOME =================================
@app.route("/")
def home():
    return "IoT Load Monitoring Backend Running"

#========================== ESP32 SEND DATA =============================
@app.route("/api/data", methods=["POST"])
def receive_data():
    global relay_status, fault_status

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

        voltage = float(data.get("voltage", 0))
        current = float(data.get("current", 0))
        power = float(data.get("power, 0"))

        #------------------- FAULT CHECK --------------------
        fault_status = "NORMAL"
        relay_status = "ON"

        if voltage > MAX_VOLTAGE:
            fault_status = "OVER VOLTAGE"
            relay_status = "OFF"

        elif current > MAX_CURRENT:
            fault_status = "OVER CURRENT"
            relay_status = "OFF"

        elif power > MAX_POWER:
            fault_status = "OVER POWER"
            relay_status = "OFF"

        timestampt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #--------------------- SAVE TO DATABASE -------------------
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.executw("""
            INSERT INTO readings (voltage, current, power, fault, relay, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (voltage, current, power, fault_status, relay_status, timestamp))
        conn.commit()
        conn.close()

        print("DATA:", voltage, current, power, fault_status, relay_status)

        #-------------------- RESPONSE TO ESP32 --------------------
        return jsonify({
            "relay": relay_status,
            "fault": fault_status
        }), 200
# ============================ FRONTEND FETCH LATEST DATA =====================================
@app.route("/api/data/latest",
methods=["GET"])
def latest_data():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM readings ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"message": "No data yet"}), 404
    
    return jsonify({
        "voltage": row[1],
        "current": row[2],
        "power": row[3],
        "fault": row[4],
        "relay": row[5],
        "timestamp": row[6]
    })
# ====================== MANUAL RELAY CONTROL FROM UI ===============================
@app.route("/api/control",
methods=["POST"])
def control_relay():
    global relay_status, MAX_VOLTAGE
    command = request.json.get("status")

    if command == "OFF":
        relay_status = "OFF"
        MAX_VOLTAGE = 0   # voltage becomes 0 when OFF

    elif command == "ON" and fault_status == "NORMAL":
        relay_status = "ON"
        MAX_VOLTAGE = 250   # voltage limit normal when ON

    return jsonify({
        "relay": relay_status,
        "MAX_VOLTAGE": MAX_VOLTAGE
    })
#============================ RUN SERVER ==========================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0",port=5000)


            
    
    



 

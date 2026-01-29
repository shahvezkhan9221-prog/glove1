import serial
import time
import win32com.client
import threading
from flask import Flask, jsonify
from flask_cors import CORS

PORT = "COM27"
BAUD = 115200
SPEAK_DELAY = 1.2   # must be LESS than Arduino delay

global_state = {
    "text": "",
    "sensors": [0, 0, 0, 0, 0]
}

def serial_worker():
    global global_state

    # Speaker setup
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Rate = 0
        speaker.Volume = 100
    except:
        speaker = None
        print("❌ Speaker error")

    # Serial setup
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        print(f"✅ Connected to {PORT}")
        time.sleep(2)  # let ESP32 reset
    except:
        print("❌ Connect Glove first!")
        return

    last_word = ""
    last_time = 0

    while True:
        try:
            line = ser.readline().decode(errors="ignore").strip()
            now = time.time()

            if line:
                print("📩 From ESP32:", line)

                # Update global state
                global_state["text"] = line
                global_state["sensors"] = [90, 90, 90, 90, 90]

                # SPEAK ONLY IF NEW WORD
                if line != last_word and speaker:
                    print(f"🗣️ Speaking: {line}")
                    speaker.Speak(line)   # blocking, safe
                    last_word = line
                    last_time = now

            # ❌ DO NOT CLEAR TEXT IMMEDIATELY
            # Keep last word visible

        except Exception as e:
            print("Serial error:", e)

        time.sleep(0.05)  # small stability delay

# ---------------- FLASK ----------------
app = Flask(__name__)
CORS(app)

@app.route('/data')
def get_data():
    return jsonify(global_state)

if __name__ == '__main__':
    t = threading.Thread(target=serial_worker, daemon=True)
    t.start()
    print("🌐 Server Ready. Open communication.html")
    app.run(host='0.0.0.0', port=5000)

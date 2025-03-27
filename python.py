import serial
import json
import threading
from flask import Flask, render_template_string
from flask_socketio import SocketIO

ser = serial.Serial('/dev/cu.usbmodem101', 9600, timeout=1) #replace with own serial port

app = Flask(__name__)
socketio = SocketIO(app)

status = "Waiting for scan..."
username = ""

def load_approved_cards():
    try:
        with open("approvedrf.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

approvedrf = load_approved_cards()

@app.route('/')
def home():
    global status, username
    status = "Waiting for scan..."
    username = ""
    return render_template_string('''
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <script>
            var socket = io();
            socket.on('update_status', function(data) {
                document.getElementById("status").innerText = data.status;
                document.getElementById("status").style.color = data.status === "APPROVED" ? "green" : "red";
                document.getElementById("username").innerText = data.username ? "Welcome, " + data.username + "!" : "";
            });
        </script>

        <h1 id="status" style="color: red">{{ status }}</h1>
        <h3 id="username">{% if username %}Welcome, {{ username }}!{% endif %}</h3>
    ''', status=status, username=username)

def listen_to_arduino():
    global status, username
    while True:
        line = ser.readline().decode('utf-8').strip()
        if line:
            print(f"Received: {line}")

        if line.startswith("CARD:"):
            card_id = line.split(":")[1] 
            print(f"Received Card ID: '{card_id}'") 

            
            if card_id == "12345678":  #replace with own id
                status = "APPROVED"
                username = "admin"  
            else:
                status = "DENIED"
                username = ""

            socketio.emit('update_status', {"status": status, "username": username})

if __name__ == '__main__':
    t = threading.Thread(target=listen_to_arduino, daemon= True)
    t.start()
    socketio.run(app, host='192.168.1.169', port=5000, debug=False) #replace with own ip and port

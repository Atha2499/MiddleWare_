from flask import Flask, render_template, request, redirect, url_for,jsonify
import os
import subprocess
import platform
import re
import json
import socket
import TCP_Mqtt as t
import threading
from flask_socketio import SocketIO


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  
global tcp
global Interfacelist
pushdata=False
Header=[]
Data=[]
global Sep

# Route to show the IP change form
@app.route("/", methods=["GET", "POST"])
def index():
    global Interfacelist

    a=(get_network_info())
    #Interfacelist=a
    device_name = socket.gethostname()
    Header=[]
    Data=[]
    print(a)
    

# Get all keys
    keys = list(a.keys())
    print(keys)
 
    interfaces = []
    for i in range(len(keys)):
        interfaces.append({"name": keys[i], "ip": a[keys[i]]})
    #for net in a:
       # print(net["name"], net["ip"])
    #print(a)
   #data=json.loads(a[0])
    print(interfaces)
    Interfacelist=interfaces

    
    new_ip = request.form.get("ip_address")
    print(f"New IP {new_ip}")
        #interface=request.form.get("Interface")
        #if interface==None:
            #return "Interface NoNe"
        #if new_ip==None:
            #return "IP none"
        # Validate IP address format
        
        
       # return f"IP changed successfully to {new_ip}. Please reconnect."

    return render_template("index.html",networks=interfaces,devicename=device_name)

# Function to apply the new IP address
def set_ethernet_ip(interface, ip):
    c1=f"sudo ip addr flush dev {interface}"
    print(c1)
    os.system(c1)
    c2=f"sudo ip addr add {ip}/24 dev {interface}"
    print(c2)
    os.system(c2)
    a=get_network_info()
    keys = list(a.keys())
    print(keys)

    interfaces = []
    for i in range(len(keys)):
        interfaces.append({"name": keys[i], "ip": a[keys[i]]})

    socketio.emit("Refresh", {"message":interfaces})

    #os.system(f"sudo systemctl restart networking")  # Restart networking service

# Function to validate an IPv4 address
def validate_ip(ip):
    import re
    pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    return bool(re.match(pattern, ip))


@app.route('/About')  # When user visits "/second"
def second_page():
    return render_template('About.html')

@app.route('/graph')  # When user visits "/second"
def graph():
    return render_template('graph.html')

@app.route('/update_ip', methods=['POST'])
def update_ip():
    try:
        # Get JSON data from request
        data = request.get_json()
        interface = data.get("interface")
        ip_address = data.get("ip_address")

        if not interface or not ip_address:
            return jsonify({"message": "Missing interface or IP address"}), 400
        if not validate_ip(ip_address):
            return jsonify({"message":"Invalid IP Address. Please enter a valid IPv4 address."}), 400
        
        # Apply the new IP address
        print(f"interface {interface}")
        print (f"ip {ip_address}")
        set_ethernet_ip(interface, ip_address)
        return jsonify({"message": "IP updated successfully"}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@app.route('/setprotocol')
def protocol():
    global tcp
   # data = request.get_json()
    protocol =  request.args.get("protocol")
    Actas = request.args.get("actas")
    Port=request.args.get("port")
    ip=request.args.get("Ip")

    if(protocol=='0'):
        tcp=TCPIp(Actas,Port,ip)

    return jsonify({"message": "Protocol set successfully", "protocol": protocol, "actas": Actas, "port": Port, "ip": ip})

@app.route('/startserver')
def start():
    global tcp
    thread = threading.Thread(target=tcp.Startserver, daemon=True)
    thread.start()

    return jsonify({"message": "Communication Open"})

@app.route('/startclient')
def startclient():
    global tcp
    tcp.connect()
    thread = threading.Thread(target=tcp.startreciving(), daemon=True)
    thread.start()


def on_message_received(message):
    print(f"Message received in app.py: {message}")
    global Sep
    if(pushdata!=False):
        from datetime import datetime
        msg =message.split(Sep)
        Data.clear()
        for i in range(len(msg)):
            Data.append(msg[i])
# Get current date and time
        now = datetime.now().isoformat()
        
        socketio.emit("update_tbl", {"headers": Header,"data":Data,"logdatetime":now}) 
        print(f"Data Sent={Data}")
    else:
       
        socketio.emit("update_label", {"message": message}) 


def onconnecton(status):
    print(f"Connection Status {status}")
    socketio.emit("update_status",{"Status":status})

@app.route('/get_message')
def get_message():
    global tcp
   
    cnt=tcp.ConnectionStatus()
    if(cnt>0):
        msg=tcp.get_message()
        return jsonify({"message": msg})  
    return jsonify({"message":"Connect Client"})  

@app.route("/get_device_info")
def getspecifedinterface():
    global Interfacelist
    interface = request.args.get("device")
    inte = [item for item in Interfacelist if interface in item["name"]]
    print(inte)

    for i in range(len(inte)):
       v=inte[i]["ip"][i]
       print(f"darad *{v}*")
       #for j in range(len(v[j])):
           #if validate_ip(v[j]):
       return jsonify(v)
        

def Set():
 interface = request.args.get("device")   

def TCPIp(serverclient,port,ip):
    global tcp
    if serverclient=='0':
        tcp=t.TCPServer(port)
        tcp.set_callback(on_message_received)
        tcp.set_connection(onconnecton)
        tcp.set_disconnection(on_disconnection)

    elif serverclient=='1':
        tcp=t.TCPClient(ip,port)
        tcp.set_callback(on_message_received)
        tcp.set_connection(onconnecton)
    else:
        return None
    return tcp
        
def on_disconnection(status):
    print(f"Disconnection Status: {status}")
    socketio.emit("update_status", {"Status": status})  # Notify UI
import subprocess
import json
import platform

def get_network_info():
    system = platform.system()
    interfaces = {}

    if system == "Linux":
        # Use 'ip -j a' for structured JSON output
        result = subprocess.run(["ip", "-j", "a"], capture_output=True, text=True)
        data = json.loads(result.stdout)

        for entry in data:
            interface = entry["ifname"]
            ip_addresses = []

            # Extract IPv4 addresses
            if "addr_info" in entry:
                for addr in entry["addr_info"]:
                    ip_addresses.append(f'{addr["local"]}/{addr["prefixlen"]}')

            # Store the IPs in a list
            interfaces[interface] = ip_addresses

    elif system == "Windows":
        result = subprocess.run(["powershell", "-Command", "Get-NetIPAddress | ConvertTo-Json"], capture_output=True, text=True)
        try:
            interfaces = json.loads(result.stdout)
            interfaces = {iface["InterfaceAlias"]: [iface["IPAddress"]] for iface in interfaces}
        except:
            interfaces = {}

    else:
        interfaces = {"Unknown OS": ["Not Supported"]}

    return interfaces

# Example Usage
network_info = get_network_info()
print(network_info)

def get_network_info_():
    system = platform.system()

    if system == "Linux":
        # Run 'ip a' command to get network details
        result = subprocess.run(["ip", "-brief", "a"], capture_output=True, text=True)
        interfaces = []
        
        for line in result.stdout.split("\n"):
            parts = line.split()
            if len(parts) >= 3:
                interface = parts[0]
                ip_address = parts[2] if parts[2] != "UNKNOWN" else "No IP"
                interfaces.append({"name": interface, "ip": ip_address})

    elif system == "Windows":
        # Run PowerShell command to get network details
        result = subprocess.run(["powershell", "-Command", "Get-NetIPAddress | ConvertTo-Json"], capture_output=True, text=True)
        
        try:
            import json
            interfaces = json.loads(result.stdout)
            interfaces = [{"name": iface["InterfaceAlias"], "ip": iface["IPAddress"]} for iface in interfaces]
        except:
            interfaces = []

    else:
        interfaces = [{"name": "Unknown OS", "ip": "Not Supported"}]

    return interfaces

@app.route('/savealias')
def Setalias():
    #data = request.get_json()
    global pushdata
    global Header
    global Data
    global Sep
    sep = request.args.get("seprator")  # Default separator to ','
    Alias = request.args.get("alias")  # Get alias values
    data = request.args.get("data")  
    result=data.split(sep)
    result2=Alias.split(sep)
    Sep=sep
    print(result)
    print(result2)
    finalres=[]
    if len(result2)==len(result):
        pushdata=True
        for i in range(len(result)):
            Header.append(result2[i])
            Data.append(result[i])
            finalres.append(f"{result2[i]}={result[i]}") 
        return jsonify({"Result":finalres})
    else:
        pushdata=False
        return jsonify({"Result":"No of alias does'nt match no of data"})

    





if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
    
#202967294


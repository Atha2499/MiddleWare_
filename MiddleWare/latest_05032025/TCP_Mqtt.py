import socket
import threading
#import paho.mqtt.client as mqtt
import app as a
from flask import Flask, render_template, request, redirect, url_for,jsonify
class TCPServer:
    global server_socket
    global Host
    global port
  
    def __init__(self, Port,host='0.0.0.0'):
        global server_socket
        global Host
        global port
        Host = host
        port = int(Port)
        self.received_msg = ""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((Host, port))
        self.active_clients = []
        self.callback = None  # Callback function
        self.onconnection=None
        self.on_disconnect = None

    def set_callback(self, callback_function):
        """Set a callback function to be called when a message is received."""
        self.callback = callback_function
    
    def set_disconnection(self, callback_function):
        """Set a callback function to be called when a connection is lost."""
        self.on_disconnect = callback_function  
    
    def set_connection(self,callback_function):
        self.onconnection=callback_function

    def Startserver(self):
        self.server_socket.listen(5)
        print(f"Server listening on {Host}:{port}")
        
        while True:
            client_socket, address = self.server_socket.accept()
            print(f"New connection from {address}")
            
            self.active_clients.append(address) 

            if self.onconnection:
                self.onconnection(f"Connected to {address}")

            threading.Thread(target=self.handle_client, args=(client_socket, address), daemon=True).start()
    



    def handle_client(self, server_socket, address):
        global recivedmsg
        print(f"Connection established with {address}")
        while True:
            try:
                message = server_socket.recv(1024).decode('utf-8')  

                if not message:
                    break
                print(f"Received from {address}: {message}")
                response = f"Echo: {message}"
                self.received_msg = message

                # Call the callback function in app.py
                if self.callback:
                    self.callback(message)

                
                #return jsonify({f"message": {message}})
                #self.send(client_socket,address,"hello")
                #mqttclient=Mqtt(message)
                #client_socket.send(response.encode('utf-8'))
            except (ConnectionResetError,BrokenPipeError):
                if self.on_disconnect:
                    self.on_disconnect(f"Disconnected: {address}") 
                break
        print(f"Connection closed with {address}")
        server_socket.close()

    def send(self,client_socket,address,msg):
        client_socket.send(msg.encode('utf-8'))
        print(f"Msg sent to {address} {msg}")

    def ConnectionStatus(self):
        return len(self.active_clients)

   
    def get_message(self):
        return self.received_msg 

class TCPClient:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = int(server_port)
        self.onconnection=None
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def connect(self):
        self.client_socket.connect((self.server_host, self.server_port))
        print(f"Connected to server at {self.server_host}:{self.server_port}")
        if self.onconnection:
                self.onconnection(f"Connected to {self.server_host}")

    def set_connection(self,callback_function):
        self.onconnection=callback_function

    def set_callback(self, callback_function):
        """Set a callback function to be called when a message is received."""
        self.callback = callback_function

    def send_message(self, message):
        self.client_socket.send(message.encode('utf-8'))
       # response = self.client_socket.recv(1024).decode('utf-8')
        print(f"Message Sent: {message}")

    def startreciving(self):
        while True:
            try:
                 self.recive()
            except (ConnectionResetError,BrokenPipeError):
                return "Exception Connection Lost possibly"

    
    def recive(self):
        response = self.client_socket.recv(1024).decode('utf-8')
        print(f"Server response: {response}")
        if self.callback:
                self.callback(response)

    def close(self):
        self.client_socket.close()
        print("Disconnected from server")

class Mqtt:
    global TOPIC
    global broker
    global client
    global port,payload
    

    def on_subscribe(client, userdata, mid, granted_qos):

        print("Subscribed: " + str(mid) + " " + str(granted_qos))

# print message, useful for checking if it was successful
    def on_message(client, userdata, msg):
        print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    def on_connect(client, userdata, flags, rc,properties=None):
        # if rc == 0:
            print("Connected!")
        # else:
        # #print(f"Failed to connect, return code: {rc} (Check MQTT credentials)")
        #     print(f"Not Connected with result code {rc}")
   
    def on_publish(client, userdata, mid):
        print(f"Data published with message ID: {mid}")


    def publish(self,client,payload):
        client.loop_start()
        #client.subscribe(TOPIC)
        result = client.publish(TOPIC, payload,0,False,None)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(" Publish successful!")
        else:
            print(f" Publish failed! MQTT Error Code: {result.rc}")

        client.loop_stop()
     
     #Mqtt Subscription
     #     
    def Subscribe(self):
        global client
        global TOPIC
        if client.is_connected:
            client.subscribe(TOPIC)
        else:
            return("client CLosed")
        # def on_message(client, userdata, msg):
#     print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")
    
    def __init__(self,payload_,Broker,Port,topic):
        global Topic
        global TOPIC
        global broker
        global client
        global port,payload
        broker = Broker
        port = Port
        TOPIC = topic
        payload=payload_
        client = mqtt.Client()
        client.on_connect = self.on_connect
# client.on_message = on_message
        client.on_subscribe = self.on_subscribe
        client.on_message = self.on_message
        #client.on_publish = self.on_publish
        client.connect(broker, port, 60)
        
       

# Example usage
if __name__ == "__main__":
    import sys
    client=TCPServer(123)
    #client.start()
    client.Startserver()
    #client.send_message("hi")
  

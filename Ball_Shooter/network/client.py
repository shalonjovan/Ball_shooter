import socket
import json
import threading
from config import PORT

class GameClient:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.game_state_callback = None
        self.disconnect_callback = None
        
    def connect(self, host_ip):
        """Connect to game server"""
        try:
            self.socket = socket.socket()
            self.socket.connect((host_ip, PORT))
            self.connected = True
            print(f"Connected to {host_ip}:{PORT}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def send_data(self, data):
        """Send data to server"""
        if not self.socket or not self.connected:
            return False
        
        try:
            message = json.dumps(data) + "\n"
            self.socket.sendall(message.encode())
            return True
        except:
            self.connected = False
            return False
    
    def receive_data(self):
        """Receive data from server"""
        try:
            data = self.socket.recv(4096).decode()
            if not data:
                return []
            return [json.loads(msg) for msg in data.split('\n') if msg.strip()]
        except:
            return []
    
    def start_receiving(self, game_state_callback, disconnect_callback=None):
        """Start receiving game state updates"""
        self.game_state_callback = game_state_callback
        self.disconnect_callback = disconnect_callback
        
        def receive_loop():
            while self.connected:
                try:
                    messages = self.receive_data()
                    for msg in messages:
                        if self.game_state_callback:
                            self.game_state_callback(msg)
                except:
                    self.connected = False
                    break
            
            if self.disconnect_callback:
                self.disconnect_callback()
        
        threading.Thread(target=receive_loop, daemon=True).start()
    
    def send_player_update(self, player, new_bullets):
        """Send player state and new bullets to server"""
        data = {
            "players": {player.id: player.to_dict()},
            "new_bullets": [b.to_dict() if hasattr(b, 'to_dict') else b for b in new_bullets]
        }
        return self.send_data(data)
    
    def send_respawn_request(self, player_id):
        """Send respawn request to server"""
        data = {
            "respawn_request": player_id
        }
        return self.send_data(data)
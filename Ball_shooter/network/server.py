import socket
import json
import threading
import time
import random
from config import *
from game.entities import Bullet, Player

class GameServer:
    def __init__(self):
        self.server_socket = None
        self.clients = []
        self.client_players = {}
        self.running = False
        self.game_state = {"players": {}, "bullets": {}, "used_colors": []}
        self.used_colors = set()
    
    def start(self):
        """Start the game server"""
        self.server_socket = socket.socket()
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(("0.0.0.0", PORT))
            self.server_socket.listen(5)
            self.running = True
            print(f"Server started on port {PORT}")
            
            threading.Thread(target=self._accept_clients, daemon=True).start()
            threading.Thread(target=self._game_loop, daemon=True).start()
            
            return True
        except Exception as e:
            print(f"Failed to start server: {e}")
            return False
    
    def stop(self):
        """Stop the game server"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        for client in self.clients[:]:
            try:
                client.close()
            except:
                pass
        self.clients.clear()
    
    def _accept_clients(self):
        """Accept incoming client connections"""
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                client_socket, addr = self.server_socket.accept()
                self.clients.append(client_socket)
                print(f"Client connected from {addr}")
                threading.Thread(target=self._handle_client, args=(client_socket,), daemon=True).start()
            except socket.timeout:
                continue
            except:
                break
    
    def _handle_client(self, client_socket):
        """Handle individual client communication"""
        client_id = None
        
        while self.running:
            try:
                data = client_socket.recv(4096).decode()
                if not data:
                    break
                
                for msg_str in data.split('\n'):
                    if not msg_str.strip():
                        continue
                    
                    try:
                        msg = json.loads(msg_str)
                        self._process_client_message(msg, client_socket)
                        
                        if "players" in msg:
                            for pid in msg["players"]:
                                self.client_players[pid] = client_socket
                                client_id = pid
                    except json.JSONDecodeError:
                        continue
                        
            except:
                break
        
        self._cleanup_client(client_socket, client_id)
    
    def _process_client_message(self, msg, client_socket):
        """Process message from client"""
        if "respawn_request" in msg:
            player_id = msg["respawn_request"]
            if player_id in self.game_state["players"]:
                player_data = self.game_state["players"][player_id]
                if not player_data.get("alive", True):
                    player_data["hp"] = 100
                    player_data["alive"] = True
                    player_data["x"] = random.randint(PLAYER_RADIUS * 2, MAP_WIDTH - PLAYER_RADIUS * 2)
                    player_data["y"] = random.randint(PLAYER_RADIUS * 2, MAP_HEIGHT - PLAYER_RADIUS * 2)
                    print(f"Player {player_id} respawned at ({player_data['x']}, {player_data['y']})")
            return
        
        if "players" in msg:
            for pid, pdata in msg["players"].items():
                if pid in self.game_state["players"]:
                    server_player = self.game_state["players"][pid]
                    
                    if server_player.get("alive", True):
                        server_player["x"] = pdata["x"]
                        server_player["y"] = pdata["y"]
                        server_player["angle"] = pdata["angle"]
                    
                    server_player["connected"] = pdata.get("connected", True)
                    server_player["name"] = pdata.get("name", "Player")
                else:
                    self.game_state["players"][pid] = pdata
                    self.used_colors.add(tuple(pdata["color"]))
            
            self.game_state["used_colors"] = list(self.used_colors)
        
        if "new_bullets" in msg:
            for bullet_data in msg["new_bullets"]:
                bullet = Bullet.from_dict(bullet_data)
                self.game_state["bullets"][bullet.id] = bullet.to_dict()
    
    def _cleanup_client(self, client_socket, client_id):
        """Clean up disconnected client"""
        if client_id and client_id in self.game_state["players"]:
            del self.game_state["players"][client_id]
        
        if client_id in self.client_players:
            del self.client_players[client_id]
        
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        
        try:
            client_socket.close()
        except:
            pass
    
    def _game_loop(self):
        """Main game simulation loop"""
        while self.running:
            self._update_bullets()
            self._check_collisions()
            self._broadcast_game_state()
            time.sleep(1/60) 
    
    def _update_bullets(self):
        """Update bullet positions and remove out-of-bounds bullets"""
        to_remove = []
        
        for bullet_id, bullet_data in list(self.game_state["bullets"].items()):
            bullet = Bullet.from_dict(bullet_data)
            bullet.update()
            
            if bullet.out_of_bounds():
                to_remove.append(bullet_id)
            else:
                self.game_state["bullets"][bullet_id] = bullet.to_dict()
        
        for bullet_id in to_remove:
            self.game_state["bullets"].pop(bullet_id, None)
    
    def _check_collisions(self):
        """Check bullet-player collisions"""
        bullets_to_remove = []
        
        for bullet_id, bullet_data in list(self.game_state["bullets"].items()):
            bullet = Bullet.from_dict(bullet_data)
            
            for player_id, player_data in self.game_state["players"].items():
                if bullet.owner_id == player_id or not player_data.get("alive", True):
                    continue
                
                temp_player = Player(player_id, player_data["x"], player_data["y"], 
                                   player_data["color"])
                temp_player.update_from_dict(player_data)
                
                if bullet.distance_to(temp_player) <= PLAYER_RADIUS + BULLET_RADIUS:
                    self.game_state["players"][player_id]["hp"] -= BULLET_DAMAGE
                    print(f"Player {player_id} hit! HP: {self.game_state['players'][player_id]['hp']}")
                    
                    if self.game_state["players"][player_id]["hp"] <= 0:
                        self.game_state["players"][player_id]["hp"] = 0
                        self.game_state["players"][player_id]["alive"] = False
                        print(f"Player {player_id} died!")
                        
                        if bullet.owner_id in self.game_state["players"]:
                            self.game_state["players"][bullet.owner_id]["kills"] += 1
                            print(f"Player {bullet.owner_id} got a kill!")
                    
                    bullets_to_remove.append(bullet_id)
                    break
        
        for bullet_id in bullets_to_remove:
            self.game_state["bullets"].pop(bullet_id, None)
    
    def _broadcast_game_state(self):
        """Send game state to all connected clients"""
        if not self.clients:
            return
        
        message = json.dumps(self.game_state) + "\n"
        
        for client in self.clients[:]:
            try:
                client.sendall(message.encode())
            except:
                self.clients.remove(client)
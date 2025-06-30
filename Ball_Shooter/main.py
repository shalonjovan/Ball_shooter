import pygame
import threading
import time
import random
from config import *
from game.entities import Player, Camera
from game.renderer import GameRenderer
from game.ui import GameUI
from network.client import GameClient
from network.server import GameServer

class BallShooter:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Ball Shooter")
        self.clock = pygame.time.Clock()
        
        self.font = pygame.font.SysFont(None, FONT_SIZE)
        self.large_font = pygame.font.SysFont(None, LARGE_FONT_SIZE)
        self.renderer = GameRenderer(self.screen, self.font, self.large_font)
        self.ui = GameUI(self.screen, self.font, self.large_font, self.clock)
        self.camera = Camera()
        
        self.my_player = None
        self.players = {}
        self.bullets = {}
        self.new_bullets = []
        self.used_colors = set()
        self.running = True
        self.connected = True
        
        self.client = None
        self.server = None
        self.is_host = False
    
    def setup_networking(self):
        """Setup network connection based on user choice"""
        menu_choice = self.ui.main_menu()
        if menu_choice is None:
            return False
        
        if menu_choice == "host":
            return self._host_game()
        else:
            return self._join_game()
    
    def _host_game(self):
        """Setup hosting"""
        self.is_host = True
        self.server = GameServer()
        if not self.server.start():
            return False
        
        self.client = GameClient()
        time.sleep(0.5) 
        return self.client.connect("localhost")
    
    def _join_game(self):
        """Setup joining"""
        host_ip = self.ui.get_ip_input()
        if host_ip is None:
            return False
        
        self.client = GameClient()
        return self.client.connect(host_ip)
    
    def setup_player(self):
        """Setup player with name and color selection"""
        time.sleep(0.5)
        
        player_name = self.ui.get_name_input()
        if player_name is None:
            return False
        
        selected_color = self.ui.select_color(self.used_colors)
        if selected_color is None:
            return False
        
        self.used_colors.add(selected_color)
        
        self.my_player = Player(
            str(random.randint(1000, 9999)),
            random.randint(50, MAP_WIDTH - 50),
            random.randint(50, MAP_HEIGHT - 50),
            selected_color,
            player_name
        )
        self.players[self.my_player.id] = self.my_player
        
        return True
    
    def handle_network_updates(self, game_state):
        """Handle incoming network updates"""
        if "used_colors" in game_state:
            self.used_colors = set(tuple(c) for c in game_state["used_colors"])
        
        if "players" in game_state:
            current_pids = set(game_state["players"].keys())
            for pid in list(self.players.keys()):
                if pid not in current_pids and pid != self.my_player.id:
                    del self.players[pid]
            
            for pid, pdata in game_state["players"].items():
                if pid == self.my_player.id:
                    # For our own player, accept server's authoritative state for critical values
                    old_x, old_y = self.my_player.x, self.my_player.y
                    
                    self.my_player.hp = pdata["hp"]
                    self.my_player.alive = pdata.get("alive", True)
                    self.my_player.kills = pdata.get("kills", 0)
                    
                    # If we died and respawned on server, accept new position
                    if not self.my_player.alive or (abs(pdata["x"] - old_x) > 100 or abs(pdata["y"] - old_y) > 100):
                        self.my_player.x = pdata["x"]
                        self.my_player.y = pdata["y"]
                    
                    continue
                
                if pid not in self.players:
                    self.players[pid] = Player(
                        pid, pdata["x"], pdata["y"], 
                        pdata["color"], pdata.get("name", "Player")
                    )
                self.players[pid].update_from_dict(pdata)
        
        if "bullets" in game_state:
            from game.entities import Bullet
            self.bullets.clear()
            for bid, bdata in game_state["bullets"].items():
                self.bullets[bid] = Bullet.from_dict(bdata)
    
    def handle_disconnect(self):
        """Handle network disconnection"""
        self.connected = False
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                bullet = self.my_player.shoot()
                if bullet:
                    self.new_bullets.append(bullet.to_dict())
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and not self.my_player.alive:
                    # Send respawn request to server instead of respawning locally
                    if self.client and self.connected:
                        self.client.send_respawn_request(self.my_player.id)
    
    def update_game_state(self):
        """Update local game state"""
        keys = pygame.key.get_pressed()
        
        # Only update movement and aiming if player is alive
        if self.my_player.alive:
            self.my_player.move(keys)
            self.my_player.aim(self.camera)
        
        self.camera.update(self.my_player.x, self.my_player.y)
    
    def render_game(self):
        """Render the game"""
        self.renderer.draw_map(self.camera)
        
        for player in self.players.values():
            if player.connected:
                self.renderer.draw_player(player, self.camera)
        
        for bullet in self.bullets.values():
            self.renderer.draw_bullet(bullet, self.camera)
        
        self.renderer.draw_minimap(self.my_player, self.players)
        self.renderer.draw_leaderboard(self.my_player, self.players)
        
        connected_count = len([p for p in self.players.values() if p.connected])
        self.renderer.draw_ui_info(self.my_player, connected_count)
        
        if not self.my_player.alive:
            self.renderer.draw_respawn_message()
        
        pygame.display.flip()
    
    def send_updates(self):
        """Send updates to server"""
        if self.client and self.connected:
            success = self.client.send_player_update(self.my_player, self.new_bullets)
            if success:
                self.new_bullets.clear()
            else:
                self.connected = False
    
    def run(self):
        """Main game loop"""
        if not self.setup_networking():
            pygame.quit()
            return
        
        if not self.setup_player():
            pygame.quit()
            return
        
        self.client.start_receiving(self.handle_network_updates, self.handle_disconnect)
        
        while self.running:
            if not self.connected:
                if not self.ui.disconnect_screen():
                    self.running = False
                break
            
            self.handle_events()
            self.update_game_state()
            self.render_game()
            self.send_updates()
            
            self.clock.tick(60)
        
        self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        self.connected = False
        if self.client:
            self.client.disconnect()
        if self.server:
            self.server.stop()
        pygame.quit()

def main():
    game = BallShooter()
    game.run()

if __name__ == "__main__":
    main()
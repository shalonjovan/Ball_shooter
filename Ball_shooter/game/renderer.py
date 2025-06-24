import pygame
import math
from config import *

class GameRenderer:
    def __init__(self, screen, font, large_font):
        self.screen = screen
        self.font = font
        self.large_font = large_font
    
    def draw_map(self, camera):
        """Draw the game map with boundaries"""
        self.screen.fill(BLACK)
        
        map_screen_x, map_screen_y = camera.apply(0, 0)
        map_rect = pygame.Rect(map_screen_x, map_screen_y, MAP_WIDTH, MAP_HEIGHT)
        screen_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        
        visible_rect = map_rect.clip(screen_rect)
        if visible_rect.width > 0 and visible_rect.height > 0:
            pygame.draw.rect(self.screen, WHITE, visible_rect)
    
    def draw_player(self, player, camera):
        """Draw a single player"""
        screen_x, screen_y = camera.apply(player.x, player.y)
        
        if not (-PLAYER_RADIUS <= screen_x <= SCREEN_WIDTH + PLAYER_RADIUS and 
                -PLAYER_RADIUS <= screen_y <= SCREEN_HEIGHT + PLAYER_RADIUS):
            return
        
        color = GRAY if not player.alive else player.color
        pygame.draw.circle(self.screen, color, (int(screen_x), int(screen_y)), PLAYER_RADIUS)
        
        if player.alive:
            rad = math.radians(-player.angle)
            bx = screen_x + math.cos(rad) * 40
            by = screen_y + math.sin(rad) * 40
            pygame.draw.line(self.screen, GRAY, (screen_x, screen_y), (bx, by), 6)
            
            self._draw_health_bar(screen_x, screen_y, player.hp)
    
    def _draw_health_bar(self, x, y, hp):
        """Draw health bar above player"""
        bar_w, bar_h = 50, 6
        bar_x = x - bar_w // 2
        bar_y = y - PLAYER_RADIUS - 15
        
        pygame.draw.rect(self.screen, RED, (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(self.screen, GREEN, (bar_x, bar_y, bar_w * hp / 100, bar_h))
    
    def draw_bullet(self, bullet, camera):
        """Draw a single bullet"""
        screen_x, screen_y = camera.apply(bullet.x, bullet.y)
        
        if (-BULLET_RADIUS <= screen_x <= SCREEN_WIDTH + BULLET_RADIUS and 
            -BULLET_RADIUS <= screen_y <= SCREEN_HEIGHT + BULLET_RADIUS):
            pygame.draw.circle(self.screen, bullet.color, 
                             (int(screen_x), int(screen_y)), BULLET_RADIUS)
    
    def draw_minimap(self, my_player, players):
        """Draw minimap in top-right corner"""
        minimap_x = SCREEN_WIDTH - MINIMAP_SIZE - 10
        minimap_y = 10
        
        pygame.draw.rect(self.screen, DARK_GRAY, 
                        (minimap_x, minimap_y, MINIMAP_SIZE, MINIMAP_SIZE))
        pygame.draw.rect(self.screen, WHITE, 
                        (minimap_x + 2, minimap_y + 2, MINIMAP_SIZE - 4, MINIMAP_SIZE - 4))
        
        scale_x = (MINIMAP_SIZE - 4) / MAP_WIDTH
        scale_y = (MINIMAP_SIZE - 4) / MAP_HEIGHT
        
        for player in players.values():
            if player.alive and player.connected:
                px = minimap_x + 2 + int(player.x * scale_x)
                py = minimap_y + 2 + int(player.y * scale_y)
                color = player.color if player.id != my_player.id else YELLOW
                pygame.draw.circle(self.screen, color, (px, py), 3)
    
    def draw_leaderboard(self, my_player, players):
        """Draw leaderboard in bottom-left corner"""
        board_x = 10
        board_y = SCREEN_HEIGHT - 200
        
        sorted_players = sorted([p for p in players.values() if p.connected], 
                              key=lambda p: p.kills, reverse=True)
        
        if not sorted_players:
            return
        
        board_height = min(len(sorted_players) * 25 + 30, 200)
        pygame.draw.rect(self.screen, (*DARK_GRAY, 128), 
                        (board_x, board_y, LEADERBOARD_WIDTH, board_height))
        
        title_text = self.font.render("Leaderboard", True, WHITE)
        self.screen.blit(title_text, (board_x + 5, board_y + 5))
        
        for i, player in enumerate(sorted_players[:7]):
            y_pos = board_y + 30 + i * 25
            color = YELLOW if player.id == my_player.id else WHITE
            text = self.font.render(f"{player.name}: {player.kills} kills", True, color)
            self.screen.blit(text, (board_x + 5, y_pos))
    
    def draw_ui_info(self, my_player, player_count):
        """Draw game UI information"""
        text = self.font.render(f"Players: {player_count}", True, BLACK)
        self.screen.blit(text, (10, 10))
        
        text = self.font.render(f"Position: ({int(my_player.x)}, {int(my_player.y)})", 
                               True, BLACK)
        self.screen.blit(text, (10, 40))
        
        text = self.font.render(f"Your Kills: {my_player.kills}", True, BLACK)
        self.screen.blit(text, (10, 70))
    
    def draw_respawn_message(self):
        """Draw respawn message when player is dead"""
        text = self.large_font.render("Press R to respawn", True, YELLOW)
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        self.screen.blit(text, text_rect)
import pygame
import time
from config import *

class GameUI:
    def __init__(self, screen, font, large_font, clock):
        self.screen = screen
        self.font = font
        self.large_font = large_font
        self.clock = clock
    
    def main_menu(self):
        """Main menu for host/join selection"""
        menu_running = True
        choice = None
        
        button_width = 200
        button_height = 60
        button_x = SCREEN_WIDTH // 2 - button_width // 2
        host_button = pygame.Rect(button_x, 300, button_width, button_height)
        join_button = pygame.Rect(button_x, 400, button_width, button_height)
        
        while menu_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if host_button.collidepoint(event.pos):
                        choice = "host"
                        menu_running = False
                    elif join_button.collidepoint(event.pos):
                        choice = "join"
                        menu_running = False
            
            self._draw_menu_background()
            
            title_text = self.large_font.render("Tank Game", True, WHITE)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 150))
            self.screen.blit(title_text, title_rect)
            
            self._draw_button(host_button, "Host Game")
            self._draw_button(join_button, "Join Game")
            
            pygame.display.flip()
            self.clock.tick(60)
        
        return choice
    
    def get_ip_input(self):
        """Get IP address input from user"""
        input_text = ""
        input_active = True
        
        while input_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and input_text.strip():
                        return input_text.strip()
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        return None
                    elif event.unicode.isdigit() or event.unicode == '.':
                        input_text += event.unicode
            
            self._draw_input_screen("Enter Host IP Address", input_text,
                                  "Press Enter to connect, ESC to cancel")
            
            pygame.display.flip()
            self.clock.tick(60)
        
        return None
    
    def get_name_input(self):
        """Get player name input from user"""
        input_text = ""
        input_active = True
        
        while input_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and input_text.strip():
                        return input_text.strip()
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        return None
                    elif (event.unicode.isalnum() or event.unicode == ' ') and len(input_text) < 15:
                        input_text += event.unicode
            
            self._draw_input_screen("Enter Your Name", input_text,
                                  "Press Enter to continue, ESC to cancel")
            
            pygame.display.flip()
            self.clock.tick(60)
        
        return None
    
    def select_color(self, used_colors):
        """Color selection screen"""
        selected_color = None
        color_rects = self._create_color_grid()
        selecting = True
        
        while selecting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    for rect, color in color_rects:
                        if rect.collidepoint(mouse_pos):
                            if color in used_colors:
                                self._show_error_message("Color already taken! Choose another.")
                            else:
                                selected_color = color
                                selecting = False
                            break
            
            self._draw_color_selection(color_rects, used_colors)
            pygame.display.flip()
            self.clock.tick(60)
        
        return selected_color
    
    def disconnect_screen(self):
        """Show disconnect screen"""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return False
            
            self.screen.fill((30, 30, 30))
            
            text = self.large_font.render("Connection Lost!", True, RED)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(text, text_rect)
            
            inst_text = self.font.render("Press ESC to exit", True, WHITE)
            inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            self.screen.blit(inst_text, inst_rect)
            
            pygame.display.flip()
            self.clock.tick(60)
    
    def _draw_menu_background(self):
        """Draw menu background"""
        self.screen.fill((30, 30, 30))
    
    def _draw_button(self, rect, text):
        """Draw a UI button"""
        pygame.draw.rect(self.screen, GRAY, rect)
        pygame.draw.rect(self.screen, WHITE, rect, 3)
        
        text_surface = self.font.render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
    
    def _draw_input_screen(self, title, input_text, instruction):
        """Draw input screen with title, input box, and instruction"""
        self.screen.fill((30, 30, 30))
        
        title_surface = self.large_font.render(title, True, WHITE)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, 200))
        self.screen.blit(title_surface, title_rect)
        
        input_box = pygame.Rect(SCREEN_WIDTH//2 - 150, 300, 300, 40)
        pygame.draw.rect(self.screen, WHITE, input_box)
        pygame.draw.rect(self.screen, BLACK, input_box, 2)
        
        text_surface = self.font.render(input_text, True, BLACK)
        self.screen.blit(text_surface, (input_box.x + 5, input_box.y + 10))
        
        inst_surface = self.font.render(instruction, True, LIGHT_GRAY)
        inst_rect = inst_surface.get_rect(center=(SCREEN_WIDTH//2, 380))
        self.screen.blit(inst_surface, inst_rect)
    
    def _create_color_grid(self):
        """Create color selection grid"""
        color_rects = []
        cols, rows = 4, 3
        color_size = 80
        start_x = (SCREEN_WIDTH - cols * (color_size + 10)) // 2
        start_y = (SCREEN_HEIGHT - rows * (color_size + 10)) // 2
        
        for i, color in enumerate(PLAYER_COLORS):
            row = i // cols
            col = i % cols
            x = start_x + col * (color_size + 10)
            y = start_y + row * (color_size + 10)
            color_rects.append((pygame.Rect(x, y, color_size, color_size), color))
        
        return color_rects
    
    def _draw_color_selection(self, color_rects, used_colors):
        """Draw color selection screen"""
        self.screen.fill((30, 30, 30))
        
        title_text = self.large_font.render("Choose Your Color", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(title_text, title_rect)
        
        for rect, color in color_rects:
            if color in used_colors:
                pygame.draw.rect(self.screen, GRAY, rect)
                pygame.draw.line(self.screen, RED, rect.topleft, rect.bottomright, 5)
                pygame.draw.line(self.screen, RED, rect.topright, rect.bottomleft, 5)
            else:
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, WHITE, rect, 3)
    
    def _show_error_message(self, message):
        """Show error message briefly"""
        self.screen.fill((30, 30, 30))
        error_text = self.large_font.render(message, True, (255, 100, 100))
        error_rect = error_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        self.screen.blit(error_text, error_rect)
        pygame.display.flip()
        time.sleep(1)
import pygame
import math
import random
import time
from config import *

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
    
    def update(self, target_x, target_y):
        """Center camera on target"""
        self.x = target_x - SCREEN_WIDTH // 2
        self.y = target_y - SCREEN_HEIGHT // 2
        
        self.x = max(0, min(MAP_WIDTH - SCREEN_WIDTH, self.x))
        self.y = max(0, min(MAP_HEIGHT - SCREEN_HEIGHT, self.y))
    
    def apply(self, x, y):
        """Convert world coordinates to screen coordinates"""
        return x - self.x, y - self.y

class GameObject:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Bullet(GameObject):
    def __init__(self, x, y, vx, vy, owner_id, color):
        super().__init__(x, y)
        self.vx = vx
        self.vy = vy
        self.owner_id = owner_id
        self.color = color
        self.id = f"{owner_id}_{random.randint(10000, 99999)}"
    
    def update(self):
        """Update bullet position"""
        self.x += self.vx
        self.y += self.vy
    
    def out_of_bounds(self):
        """Check if bullet is out of map bounds"""
        return not (0 <= self.x <= MAP_WIDTH and 0 <= self.y <= MAP_HEIGHT)
    
    def distance_to(self, player):
        """Calculate distance to player"""
        return math.sqrt((self.x - player.x)**2 + (self.y - player.y)**2)
    
    def to_dict(self):
        """Convert to dictionary for network transmission"""
        return {
            "x": self.x, "y": self.y, "vx": self.vx, "vy": self.vy,
            "owner_id": self.owner_id, "id": self.id, "color": self.color
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create bullet from dictionary"""
        bullet = cls(data["x"], data["y"], data["vx"], data["vy"], 
                    data["owner_id"], data["color"])
        bullet.id = data["id"]
        return bullet

class Player(GameObject):
    def __init__(self, pid, x, y, color, name="Player"):
        super().__init__(x, y)
        self.id = pid
        self.angle = 0
        self.hp = 100
        self.color = color
        self.name = name
        self.last_shot = 0
        self.alive = True
        self.kills = 0
        self.connected = True
    
    def move(self, keys):
        """Move player based on key input"""
        if not self.alive:
            return
        
        new_x, new_y = self.x, self.y
        
        if keys[pygame.K_w]:
            new_y -= PLAYER_SPEED
        if keys[pygame.K_s]:
            new_y += PLAYER_SPEED
        if keys[pygame.K_a]:
            new_x -= PLAYER_SPEED
        if keys[pygame.K_d]:
            new_x += PLAYER_SPEED
        
        self.x = max(PLAYER_RADIUS, min(MAP_WIDTH - PLAYER_RADIUS, new_x))
        self.y = max(PLAYER_RADIUS, min(MAP_HEIGHT - PLAYER_RADIUS, new_y))
    
    def aim(self, camera):
        """Aim at mouse position"""
        if not self.alive:
            return
        
        mx, my = pygame.mouse.get_pos()
        world_mx = mx + camera.x
        world_my = my + camera.y
        self.angle = math.degrees(math.atan2(-(world_my - self.y), world_mx - self.x))
    
    def shoot(self):
        """Create a bullet if cooldown allows"""
        if not self.alive or time.time() - self.last_shot < SHOOT_COOLDOWN:
            return None
        
        self.last_shot = time.time()
        rad = math.radians(-self.angle)
        
        spawn_distance = 40
        bx = self.x + math.cos(rad) * spawn_distance
        by = self.y + math.sin(rad) * spawn_distance
        
        return Bullet(bx, by, 
                     math.cos(rad) * BULLET_SPEED,
                     math.sin(rad) * BULLET_SPEED,
                     self.id, self.color)
    
    def take_damage(self, damage):
        """Apply damage to player"""
        self.hp = max(0, self.hp - damage)
        self.alive = self.hp > 0
    
    def respawn(self):
        """Respawn player at random location"""
        self.hp = 100
        self.alive = True
        self.x = random.randint(PLAYER_RADIUS * 2, MAP_WIDTH - PLAYER_RADIUS * 2)
        self.y = random.randint(PLAYER_RADIUS * 2, MAP_HEIGHT - PLAYER_RADIUS * 2)
    
    def to_dict(self):
        """Convert to dictionary for network transmission"""
        return {
            "x": self.x, "y": self.y, "angle": self.angle, "hp": self.hp,
            "color": self.color, "alive": self.alive, "kills": self.kills,
            "connected": self.connected, "name": self.name
        }
    
    def update_from_dict(self, data):
        """Update player from dictionary"""
        self.x = data["x"]
        self.y = data["y"]
        self.angle = data["angle"]
        self.hp = data["hp"]
        self.color = data["color"]
        self.alive = data.get("alive", True)
        self.kills = data.get("kills", 0)
        self.connected = data.get("connected", True)
        self.name = data.get("name", "Player")
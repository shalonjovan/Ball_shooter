import json
import socket

def send_data(sock, data):
    """Send JSON data over socket"""
    try:
        message = json.dumps(data) + "\n"
        sock.sendall(message.encode())
        return True
    except:
        return False

def receive_data(sock):
    """Receive and parse JSON data from socket"""
    try:
        data = sock.recv(4096).decode()
        if not data:
            return []
        
        messages = []
        for msg_str in data.split('\n'):
            if msg_str.strip():
                try:
                    messages.append(json.loads(msg_str))
                except json.JSONDecodeError:
                    continue
        
        return messages
    except:
        return []

def clamp(value, min_val, max_val):
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))

def distance(x1, y1, x2, y2):
    """Calculate distance between two points"""
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

def is_collision(obj1_x, obj1_y, obj1_radius, obj2_x, obj2_y, obj2_radius):
    """Check if two circular objects collide"""
    return distance(obj1_x, obj1_y, obj2_x, obj2_y) <= (obj1_radius + obj2_radius)

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def validate_ip(ip_string):
    """Validate IP address format"""
    try:
        parts = ip_string.split('.')
        if len(parts) != 4:
            return False
        
        for part in parts:
            if not part.isdigit():
                return False
            num = int(part)
            if num < 0 or num > 255:
                return False
        
        return True
    except:
        return False
"""
Client Permissions Module
Quản lý phân quyền cho các chức năng của client dựa trên role từ database
"""

class ClientPermissions:
    """
    Class quản lý phân quyền cho client
    
    Các role:
    - admin: Quyền cao nhất, không bị giám sát, có thể điều khiển mọi thứ
    - user: Người dùng bình thường, bị giám sát nội dung
    - viewer: Chỉ được xem, không được điều khiển, bị giám sát nghiêm ngặt
    """
    
    # Định nghĩa các permission cho từng role
    ROLE_PERMISSIONS = {
        'admin': {
            'can_share_screen': True,           # Có thể chia sẻ màn hình
            'can_receive_remote_input': True,   # Có thể nhận điều khiển từ xa
            'can_transfer_file': True,          # Có thể truyền file
            'is_monitored': False,              # Không bị giám sát nội dung
            'can_see_cursor': True,             # Hiển thị con trỏ
            'monitoring_level': 'none',         # Mức độ giám sát: none, low, medium, high
        },
        'user': {
            'can_share_screen': True,
            'can_receive_remote_input': True,
            'can_transfer_file': True,
            'is_monitored': True,               # Bị giám sát nội dung
            'can_see_cursor': True,
            'monitoring_level': 'medium',       # Giám sát mức trung bình
        },
        'viewer': {
            'can_share_screen': True,           # Vẫn chia sẻ màn hình (bị xem)
            'can_receive_remote_input': False,  # KHÔNG nhận điều khiển từ xa
            'can_transfer_file': False,         # KHÔNG truyền file
            'is_monitored': True,               # Bị giám sát nghiêm ngặt
            'can_see_cursor': False,            # Không hiển thị con trỏ
            'monitoring_level': 'high',         # Giám sát mức cao
        }
    }
    
    def __init__(self, role='user'):
        """
        Khởi tạo với role từ database
        
        Args:
            role (str): Role của user ('admin', 'user', 'viewer')
        """
        self.role = role.lower() if role else 'user'
        if self.role not in self.ROLE_PERMISSIONS:
            self.role = 'user'  # Default to user if invalid role
        
        self.permissions = self.ROLE_PERMISSIONS[self.role]
    
    def can_share_screen(self):
        """Kiểm tra quyền chia sẻ màn hình"""
        return self.permissions.get('can_share_screen', False)
    
    def can_receive_remote_input(self):
        """Kiểm tra quyền nhận điều khiển từ xa (keyboard, mouse)"""
        return self.permissions.get('can_receive_remote_input', False)
    
    def can_transfer_file(self):
        """Kiểm tra quyền truyền file"""
        return self.permissions.get('can_transfer_file', False)
    
    def is_monitored(self):
        """Kiểm tra có bị giám sát nội dung không"""
        return self.permissions.get('is_monitored', True)
    
    def can_see_cursor(self):
        """Kiểm tra có hiển thị con trỏ chuột không"""
        return self.permissions.get('can_see_cursor', True)
    
    def get_monitoring_level(self):
        """Lấy mức độ giám sát: none, low, medium, high"""
        return self.permissions.get('monitoring_level', 'medium')
    
    def get_role(self):
        """Lấy role hiện tại"""
        return self.role
    
    def get_all_permissions(self):
        """Lấy tất cả permissions"""
        return self.permissions.copy()
    
    def __str__(self):
        """String representation"""
        return f"ClientPermissions(role='{self.role}', permissions={self.permissions})"


# Hàm tiện ích để kiểm tra quyền nhanh
def check_permission(role, permission_name):
    """
    Kiểm tra nhanh một quyền cụ thể
    
    Args:
        role (str): Role của user
        permission_name (str): Tên permission cần kiểm tra
    
    Returns:
        bool: True nếu có quyền, False nếu không
    """
    perms = ClientPermissions(role)
    return perms.permissions.get(permission_name, False)


# Hàm lấy danh sách tất cả permissions theo role
def get_role_permissions(role):
    """
    Lấy tất cả permissions của một role
    
    Args:
        role (str): Role cần lấy permissions
    
    Returns:
        dict: Dictionary chứa tất cả permissions
    """
    if role.lower() in ClientPermissions.ROLE_PERMISSIONS:
        return ClientPermissions.ROLE_PERMISSIONS[role.lower()].copy()
    return ClientPermissions.ROLE_PERMISSIONS['user'].copy()


if __name__ == "__main__":
    # Test các role
    print("=== TEST PHÂN QUYỀN ===\n")
    
    for role in ['admin', 'user', 'viewer']:
        print(f"Role: {role.upper()}")
        perms = ClientPermissions(role)
        print(f"  - Can share screen: {perms.can_share_screen()}")
        print(f"  - Can receive remote input: {perms.can_receive_remote_input()}")
        print(f"  - Can transfer file: {perms.can_transfer_file()}")
        print(f"  - Is monitored: {perms.is_monitored()}")
        print(f"  - Can see cursor: {perms.can_see_cursor()}")
        print(f"  - Monitoring level: {perms.get_monitoring_level()}")
        print()

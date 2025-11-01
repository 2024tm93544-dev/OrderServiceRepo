from enum import Enum

class ShippingStatus(Enum):
    PENDING = "Pending"       
    SHIPPED = "Shipped"        
    DELIVERED = "Delivered"    
    FAILED = "Failed"  
    UNKNOWN = "Unknown"       
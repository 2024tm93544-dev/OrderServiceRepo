from enum import Enum
# Payment statuses
class PaymentStatus(Enum):
    PENDING = 'PENDING'
    PAID = 'PAID'
    REFUNDED = 'REFUNDED'
    FAILED = 'FAILED'

class PaymentMethod(Enum):
    CARD = "Card"
    UPI = "UPI"
    COD = "Cash on Delivery"
    NETBANKING = "Net Banking"
    WALLET = "Wallet"
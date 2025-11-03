from enum import Enum
# Order lifecycle statuses
class OrderStatus(Enum):
    PENDING = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    CANCELLED = 'CANCELLED'
    DELIVERED = 'DELIVERED'

class Direction(Enum):
    ASC = 'Ascending'
    DESC = 'Descending'

class SortBy(Enum):
    DATE = 'Date'
    CREATED_AT = 'Total'
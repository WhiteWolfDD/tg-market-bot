from enum import Enum

class AdvertisementStatus(str, Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

class UserRole(str, Enum):
    USER = 'user'
    ADMIN = 'admin'
    MODERATOR = 'moderator'

class InteractionType(str, Enum):
    VIEWED = 'viewed'
    FAVORITED = 'favorited'
    SHARED = 'shared'

class LogsEnums(str, Enum):
    LOGS_PER_PAGE = 9
    LOGS_PER_ROW = 3
    LOG_FILE_PATH = "storage/logs/"
    DAYS_TO_KEEP_LOGS = 90
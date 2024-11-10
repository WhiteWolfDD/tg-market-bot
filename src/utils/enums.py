class AdvertisementStatus:
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

class UserRole:
    USER = 'user'
    ADMIN = 'admin'
    MODERATOR = 'moderator'

class LogsConfig:
    LOGS_PER_PAGE = 9
    LOGS_PER_ROW = 3
    LOG_FILE_PATH = "storage/logs/"
    DAYS_TO_KEEP_LOGS = 90
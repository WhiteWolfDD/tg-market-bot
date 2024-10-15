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

SUPPORTED_LANGUAGES = {
    "English": "en",
    "Русский": "ru",
    "Eesti": "et"
}
from enum import Enum

class EmailType(str, Enum):
    VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    WELCOME = "welcome"
    NOTIFICATION = "notification"
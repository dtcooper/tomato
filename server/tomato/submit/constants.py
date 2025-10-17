SUBMIT_LOGIN_CAPTCHA_MIN_LENGTH = 5
SUBMIT_LOGIN_CAPTCHA_MAX_LENGTH = 7

SUBMIT_URL_PREFIX = "submissions"  # Can't be "submit" since that clashes with Django admin's URLs
SUBMIT_TOKEN_MAX_AGE = 15 * 60  # 15 minutes

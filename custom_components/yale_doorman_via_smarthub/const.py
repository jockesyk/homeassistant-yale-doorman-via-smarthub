NAME = "Yale Doorman via Smart Hub"
DOMAIN = "yale_doorman_via_smarthub"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.3"
ISSUE_URL = "https://github.com/jockesyk/homeassistant-yale-doorman-via-smarthub/issues"
MANUFACTURER = "Yale"
MODEL = "Doorman"
HUBNAME = "Yale Smart Hub"

BINARY_SENSOR_DEVICE_CLASS = "door"

LOCK = "lock"
BINARY_SENSOR = "binary_sensor"
PLATFORMS = [LOCK, BINARY_SENSOR]

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_PINCODE = "pincode"
CONF_ENABLE_BINARY_SENSOR = "enable_binary_sensor"

BITWISE_CLOSED = 16
BITWISE_LOCKED = 1

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

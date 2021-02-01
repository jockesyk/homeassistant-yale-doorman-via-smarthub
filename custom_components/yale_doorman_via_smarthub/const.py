NAME = "Yale Doorman via Smart Hub"
DOMAIN = "yale_doorman_via_smarthub"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"
ATTRIBUTION = ""
ISSUE_URL = "https://github.com/jockesyk/homeassistant-yale-doorman-via-smarthub/issues"
MANUFACTURER = "Yale"
MODEL = "Doorman"
HUBNAME = "Yale Smart Hub"

# Icons
ICON = "mdi:door"

# Device class
BINARY_SENSOR_DEVICE_CLASS = "door"

# Platforms
LOCK = "lock"
BINARY_SENSOR = "binary_sensor"
PLATFORMS = [LOCK]
#PLATFORMS = [LOCK, BINARY_SENSOR] # Use this if you also want a binary sensor indicating if the door is open or closed

# Configuration and options
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_PINCODE = "pincode"

# Defaults
DEFAULT_NAME = DOMAIN

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

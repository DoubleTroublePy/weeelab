from dotenv import load_dotenv
from utils import getuser
import os

load_dotenv(os.path.join(os.path.dirname(os.path.realpath(__file__)), '.env'))

COLOR_RED = "\033[1;31m"
COLOR_NATIVE = "\033[m"

VERSION = "3.2"
PROGRAM_NAME = __file__.split('/')[-1]
HOST_USER = getuser()
DEBUG_MODE = False  # Don't set it here, use -d when running
MAX_WORK_DONE = 2000

LDAP_SERVER = os.getenv("LDAP_SERVER")
LDAP_BIND_DN = os.getenv("LDAP_BIND_DN")
LDAP_PASSWORD = os.getenv("LDAP_PASSWORD")
LDAP_TREE = os.getenv("LDAP_TREE")
LOG_PATH = os.getenv("LOG_PATH")
LOG_FILENAME = LOG_PATH + "/log.txt"
FIRST_IN = os.getenv("FIRST_IN_SCRIPT_PATH")
LAST_OUT = os.getenv("LAST_OUT_SCRIPT_PATH")

FIRST_IN_HAPPENED = False
LAST_OUT_HAPPENED = False
SIR_HAPPENED = False

# BACKUP_PATH = "/home/" + HOST_USER + "/ownCloud/" + PROGRAM_NAME.capitalize() + "/"



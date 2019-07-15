import configparser
config = configparser.ConfigParser()
config.read("config.txt")

GITHUB_ID = config.get("configuration", "github_id")
GITHUB_PASS = config.get("configuration", "github_password")
GITHUB_API_TOKEN = config.get("configuration", "github_api_token")

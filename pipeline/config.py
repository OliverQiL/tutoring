import os
from dotenv import load_dotenv

# load environment variables from .env file
load_dotenv()

# get variables from environment
def get_env_variable(var_name):
    """
    Get the environment variable or raise an exception.
    """
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"{var_name} is not set in the environment variables.")
    return value

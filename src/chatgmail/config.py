import os
import dotenv
import llm

dotenv.load_dotenv()


# def get_llm_sys_prompt_from_file() -> str:
#     _file = os.getenv('LLM_SYSTEM_PROMPT', '.prompt')
#     if not os.path.exists(_file):
#         raise FileExistsError(f'LLM_SYSTEM_PROMPT file not exist')
#
#     with open(_file, 'r') as fh:
#         _prompt = fh.read()
#     return _prompt


def get_llm_model() -> llm.models:
    model = llm.get_model(os.getenv('LLM_MODEL_NAME', '4o-mini'))
    model_key = os.getenv('LLM_MODEL_API_KEY')
    if model_key:
        model.key = model_key
    return model


def get_gmail_msg_transfer_folder() -> str:
    return os.getenv('GMAIL_MSG_TRANSFER_FOLDER', '.markdown')


def get_gmail_msg_saved_folder() -> str:
    return os.getenv('GMAIL_MSG_SAVED_FOLDER', '.gmail')


def get_gcp_credentials_file() -> str:
    """GCP project OAuth client desktop app credentials file."""
    return os.getenv('GCP_CREDENTIALS_FILE', 'credentials.json')


logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
        "time_simple": {
            'format': '%(asctime)s, %(message)s'
        },
        "api_response": {
            'format': '%(message)s'
        },
        'standard': {
            # 'format': '[%(levelname)s] %(name)s: %(message)s'
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "DEBUG",
            "stream": "ext://sys.stdout"
        },
        "default": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "filename": "chatgmail.log",
            "maxBytes": 5 * 1024 * 1024,  # 5 MB
            "backupCount": 5,
            "level": "DEBUG"
        },
    },
    "root": {
        "handlers": ["console"],
    },
    "loggers": {
        "chatgmail.cli": {
            "handlers": ["console", "default"],
            "level": "INFO",
            "propagate": False
        },
        "chatgmail": {
            "handlers": ["console", "default"],
            "level": "INFO",
            "propagate": False
        },
        "py_hr_agentic": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False
        },
        "tests": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False
        }
    }
}

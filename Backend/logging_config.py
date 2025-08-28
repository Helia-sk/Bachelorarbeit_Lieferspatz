import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
            "pathname": record.pathname,
            "lineno": record.lineno,
        }
        return json.dumps(log_record)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler("user_actions.log"),
        logging.StreamHandler()
    ]
)

# Set JSON formatter
for handler in logging.getLogger().handlers:
    handler.setFormatter(JSONFormatter())

import logging
import sys
from datetime import datetime
import json

class RSSLogger:
    def __init__(self, feed_name):
        self.feed_name = feed_name
        self.logger = logging.getLogger(feed_name)
        self.logger.setLevel(logging.INFO)
        
        # Create console handler with formatting
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Create file handler for detailed logs
        file_handler = logging.FileHandler(f'{feed_name}_detailed.log')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)

    def log_scrape_start(self):
        self.logger.info(f"Starting scrape for {self.feed_name} at {datetime.now().isoformat()}")

    def log_scrape_success(self, latest_post_title, latest_post_date):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "feed": self.feed_name,
            "status": "success",
            "latest_post": {
                "title": latest_post_title,
                "date": latest_post_date
            }
        }
        self.logger.info(json.dumps(log_entry))
        return log_entry

    def log_scrape_error(self, error_message):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "feed": self.feed_name,
            "status": "error",
            "error": error_message
        }
        self.logger.error(json.dumps(log_entry))
        return log_entry 
"""
Telegram notification implementation
"""
from typing import List
import telegram
from .base import BaseNotifier
from src.scrapers.base import JobPosting

class TelegramNotifier(BaseNotifier):
    """Telegram notification system"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram notifier
        
        Args:
            bot_token: Telegram bot API token
            chat_id: Telegram chat ID to send messages to
        """
        super().__init__()
        self.bot = telegram.Bot(token=bot_token)
        self.chat_id = chat_id
        
    def send_notification(self, jobs: List[JobPosting]) -> bool:
        """Send Telegram notification"""
        try:
            message = self.format_message(jobs)
            
            # Split message if it's too long
            max_length = 4096
            if len(message) > max_length:
                chunks = [message[i:i+max_length] for i in range(0, len(message), max_length)]
                for chunk in chunks:
                    self.bot.send_message(
                        chat_id=self.chat_id,
                        text=chunk,
                        parse_mode=telegram.ParseMode.MARKDOWN
                    )
            else:
                self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode=telegram.ParseMode.MARKDOWN
                )
                
            self.logger.info(f"Successfully sent Telegram notification for {len(jobs)} jobs")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Telegram notification: {str(e)}")
            return False

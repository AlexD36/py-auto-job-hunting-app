"""
Telegram notification implementation with enhanced error handling and type safety
"""
from typing import List, Optional
import time
from functools import wraps
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError, NetworkError, TimedOut
from .base import BaseNotifier
from src.scrapers.base import JobPosting

def retry_on_telegram_error(max_retries: int = 3, delay: int = 2):
    """
    Decorator to retry operations on Telegram API errors
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except (NetworkError, TimedOut) as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        self.logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed. "
                            f"Retrying in {delay} seconds... Error: {str(e)}"
                        )
                        time.sleep(delay)
                    continue
                except TelegramError as e:
                    # Don't retry on non-transient errors
                    self.logger.error(f"Non-retryable Telegram error: {str(e)}")
                    raise
                    
            raise last_error
            
        return wrapper
    return decorator

class TelegramNotifierError(Exception):
    """Custom exception for TelegramNotifier specific errors"""
    pass

class TelegramNotifier(BaseNotifier):
    """
    Telegram notification system with enhanced error handling and retry logic
    
    Attributes:
        bot: Telegram Bot instance
        chat_id: Telegram chat ID for message destination
        max_message_length: Maximum allowed message length for Telegram
        initialized: Flag indicating if the bot was successfully initialized
    """
    
    MAX_MESSAGE_LENGTH: int = 4096
    TEST_MESSAGE: str = "🤖 Bot successfully initialized and connected!"
    
    async def __init__(self, bot_token: str, chat_id: str, auto_validate: bool = True) -> None:
        """
        Initialize Telegram notifier with validation
        
        Args:
            bot_token: Telegram bot API token
            chat_id: Telegram chat ID to send messages to
            auto_validate: Whether to validate connection on initialization
            
        Raises:
            ValueError: If bot_token or chat_id is empty
            TelegramNotifierError: If bot initialization or validation fails
        """
        super().__init__()
        
        self.logger.info("Initializing Telegram notifier...")
        
        if not bot_token or not isinstance(bot_token, str):
            raise ValueError("Bot token must be a non-empty string")
        if not chat_id or not isinstance(chat_id, str):
            raise ValueError("Chat ID must be a non-empty string")
            
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        self.initialized = False
        
        # Perform initial validation if requested
        if auto_validate:
            await self.validate_connection()
            
    async def validate_connection(self) -> bool:
        """
        Validate bot connection and chat ID by sending a test message
        
        Returns:
            bool: True if validation successful
            
        Raises:
            TelegramNotifierError: If validation fails
        """
        try:
            self.logger.info("Validating Telegram bot connection...")
            
            # Verify bot token by getting bot info
            bot_info = await self.bot.get_me()
            self.logger.info(f"Connected as bot: {bot_info.username}")
            
            # Send test message to verify chat ID
            sent_message = await self.bot.send_message(
                chat_id=self.chat_id,
                text=self.TEST_MESSAGE,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Clean up test message
            await self.bot.delete_message(
                chat_id=self.chat_id,
                message_id=sent_message.message_id
            )
            
            self.initialized = True
            self.logger.info("Telegram bot validation successful")
            return True
            
        except TelegramError as e:
            self.logger.error(f"Telegram API error during validation: {str(e)}")
            raise TelegramNotifierError(f"Validation failed: {str(e)}")
            
    @retry_on_telegram_error(max_retries=3, delay=2)
    def _send_message_chunk(self, chunk: str) -> None:
        """
        Send a single message chunk to Telegram with retry logic
        
        Args:
            chunk: Message text to send
            
        Raises:
            TelegramNotifierError: If message sending fails after retries
        """
        if not self.initialized:
            self.logger.warning("Bot not initialized. Attempting to validate connection...")
            self.validate_connection()
            
        try:
            self.bot.send_message(
                chat_id=self.chat_id,
                text=chunk,
                parse_mode=ParseMode.MARKDOWN
            )
            self.logger.debug(f"Successfully sent message chunk of length {len(chunk)}")
            
        except TelegramError as e:
            raise TelegramNotifierError(f"Failed to send message: {str(e)}")
            
    @retry_on_telegram_error(max_retries=3, delay=2)
    def send_notification(self, jobs: List[JobPosting]) -> bool:
        """
        Send Telegram notification for job postings with retry logic
        
        Args:
            jobs: List of job postings to send notifications for
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        if not jobs:
            self.logger.warning("No jobs provided for notification")
            return False
            
        try:
            message = self.format_message(jobs)
            chunks = self._split_message(message)
            
            self.logger.info(
                f"Sending notification for {len(jobs)} jobs in {len(chunks)} chunks"
            )
            
            for i, chunk in enumerate(chunks, 1):
                if len(chunks) > 1:
                    chunk = f"(Part {i}/{len(chunks)})\n\n{chunk}"
                    
                self._send_message_chunk(chunk)
                
            self.logger.info(
                f"Successfully sent Telegram notification in {len(chunks)} parts"
            )
            return True
            
        except TelegramNotifierError as e:
            self.logger.error(f"Telegram notification error: {str(e)}")
            return False
        except ValueError as e:
            self.logger.error(f"Validation error: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return False

    def _split_message(self, message: str, chunk_size: Optional[int] = None) -> List[str]:
        """
        Split message into chunks while preserving Markdown formatting and message integrity
        
        Args:
            message: Original message text to split
            chunk_size: Optional custom chunk size (defaults to MAX_MESSAGE_LENGTH)
            
        Returns:
            List[str]: List of message chunks ready for sending
            
        Raises:
            ValueError: If chunk_size is invalid or message is empty
        """
        if not message:
            raise ValueError("Cannot split empty message")
            
        max_length = chunk_size or self.MAX_MESSAGE_LENGTH
        
        if max_length <= 0:
            raise ValueError("Chunk size must be positive")
            
        if len(message) <= max_length:
            return [message]
            
        chunks: List[str] = []
        current_pos = 0
        
        while current_pos < len(message):
            # Find the best splitting point
            chunk_end = self._find_safe_split_point(
                message, 
                current_pos, 
                max_length
            )
            
            # Extract the chunk
            chunk = message[current_pos:chunk_end]
            
            # Ensure chunk has balanced Markdown
            chunk = self._balance_markdown(chunk)
            
            chunks.append(chunk)
            current_pos = chunk_end
            
        return chunks

    def _find_safe_split_point(self, message: str, start: int, max_length: int) -> int:
        """
        Find a safe point to split the message that doesn't break words or Markdown
        
        Args:
            message: Full message text
            start: Starting position for this chunk
            max_length: Maximum length of chunk
            
        Returns:
            int: Index where it's safe to split the message
        """
        # Calculate the maximum possible end point
        end = min(start + max_length, len(message))
        
        # If we can fit the rest of the message, return it
        if end == len(message):
            return end
            
        # Try to find a natural break point
        break_chars = ['\n\n', '\n', ' ']
        
        for char in break_chars:
            last_break = message[start:end].rfind(char)
            if last_break != -1:
                return start + last_break + len(char)
                
        # If no natural break point, force split at max_length
        return end

    def _balance_markdown(self, chunk: str) -> str:
        """
        Ensure Markdown formatting is properly balanced within a chunk
        
        Args:
            chunk: Message chunk to balance
            
        Returns:
            str: Chunk with balanced Markdown formatting
        """
        # Count unclosed formatting
        asterisk_count = chunk.count('*') % 2
        backtick_count = chunk.count('`') % 2
        
        # Add closing markers if needed
        if asterisk_count:
            chunk += '*'
        if backtick_count:
            chunk += '`'
            
        # Handle unclosed links
        open_brackets = chunk.count('[') - chunk.count(']')
        open_parens = chunk.count('(') - chunk.count(')')
        
        if open_brackets > 0:
            chunk += ']' * open_brackets
        if open_parens > 0:
            chunk += ')' * open_parens
            
        return chunk

    def format_message(self, jobs: List[JobPosting]) -> str:
        """
        Format job postings into a Markdown-formatted message for Telegram
        
        Args:
            jobs: List of job postings to format
            
        Returns:
            str: Markdown-formatted message
            
        Raises:
            ValueError: If job data is invalid or missing required fields
        """
        if not jobs:
            raise ValueError("Cannot format empty jobs list")
            
        # Header for the notification
        header = "*🔍 New Job Postings Found!*\n\n"
        
        # Format each job posting
        job_sections: List[str] = []
        
        for job in jobs:
            try:
                # Escape special Markdown characters in text fields
                title = self._escape_markdown(job.title)
                company = self._escape_markdown(job.company)
                location = self._escape_markdown(job.location) if job.location else "Remote/Unspecified"
                salary = self._escape_markdown(job.salary) if job.salary else "Not specified"
                
                # Build job section with proper Markdown formatting
                job_section = [
                    f"*{title}*",
                    f" Company: {company}",
                    f"📍 Location: {location}",
                    f"💰 Salary: {salary}"
                ]
                
                # Add job link if available
                if job.url:
                    job_section.append(f"🔗 [View Job]({job.url})")
                # Add job description preview if available
                if job.description:
                    # Truncate description to prevent overly long messages
                    max_desc_length = 150
                    description = self._escape_markdown(job.description)
                    if len(description) > max_desc_length:
                        description = f"{description[:max_desc_length]}..."
                    job_section.append(f"📝 {description}")
                    
                # Add posting date if available
                if job.posted_date:
                    formatted_date = job.posted_date.strftime("%Y-%m-%d")
                    job_section.append(f"📅 Posted: {formatted_date}")
                    
                # Combine job section with double newlines
                job_sections.append("\n".join(job_section))
                
            except AttributeError as e:
                self.logger.warning(f"Skipping malformed job posting: {str(e)}")
                continue
                
        # Combine all sections with separators
        separator = "\n\n" + "-" * 30 + "\n\n"
        formatted_message = header + separator.join(job_sections)
        
        # Validate message length
        if len(formatted_message) > self.MAX_MESSAGE_LENGTH:
            self.logger.warning("Message exceeds maximum length and will be split")
            
        return formatted_message

    def _escape_markdown(self, text: Optional[str]) -> str:
        """
        Escape special Markdown characters in text to prevent formatting issues
        
        Args:
            text: Text to escape
            
        Returns:
            str: Escaped text safe for Markdown formatting
            
        Note:
            Escapes the following characters: _ * [ ] ( ) ~ ` > # + - = | { } . !
        """
        if not text:
            return ""
            
        # Characters that need escaping in Markdown
        markdown_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', 
                         '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        escaped_text = text
        for char in markdown_chars:
            escaped_text = escaped_text.replace(char, f"\\{char}")
            
        return escaped_text

    def _validate_markdown(self, text: str) -> bool:
        """
        Validate that the text contains valid Markdown syntax
        
        Args:
            text: Text to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Basic validation rules for Markdown
        try:
            # Check for matching asterisks
            if text.count('*') % 2 != 0:
                return False
                
            # Check for matching square brackets and parentheses
            if text.count('[') != text.count(']'):
                return False
            if text.count('(') != text.count(')'):
                return False
                
            # Check for valid URLs in markdown links
            import re
            link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
            links = re.findall(link_pattern, text)
            for _, url in links:
                if not url.startswith(('http://', 'https://')):
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Markdown validation error: {str(e)}")
            return False

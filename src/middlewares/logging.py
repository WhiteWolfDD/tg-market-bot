import os
from datetime import datetime, timedelta

from aiogram import BaseMiddleware

from src.utils.const import LogsConfig


def clean_old_logs():
    """Remove log entries older than DAYS_TO_KEEP_LOGS."""
    if not os.path.exists(LogsConfig.LOG_FILE_PATH.value + "access.log"):
        return

    cutoff_date = datetime.now() - timedelta(days=float(LogsConfig.DAYS_TO_KEEP_LOGS.value))
    with open(LogsConfig.LOG_FILE_PATH.value + "access.log", "r", encoding='utf-8') as file:
        lines = file.readlines()

    with open(LogsConfig.LOG_FILE_PATH.value + "access.log", "w", encoding='utf-8') as file:
        for line in lines:
            try:
                # Parse the date in each log entry
                log_date_str = line.split("]")[0][1:]  # Get the date part
                log_date = datetime.strptime(log_date_str, "%Y-%m-%d %H:%M:%S")

                # Write the line back if it's within the retention period
                if log_date >= cutoff_date:
                    file.write(line)
            except (ValueError, IndexError):
                # If there's an error parsing the date, keep the log line as-is
                file.write(line)


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware for logging each request (access level) and cleaning up old logs.
    """

    def __init__(self):
        clean_old_logs()

    async def __call__(self, handler, event, data):
        """
        Log each event and clean up logs older than 90 days.
        """
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{date}] {event}"

        with open(LogsConfig.LOG_FILE_PATH.value + "access.log", "a", encoding='utf-8') as file:
            file.write(msg + "\n")

        return await handler(event, data)

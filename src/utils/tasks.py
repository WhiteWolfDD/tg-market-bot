from src.utils.log import setup_logging

logger = setup_logging()

async def database_test_connection() -> bool:
    """
    Test the connection to the database.
    :return: True if the connection is successful, otherwise False.
    """
    from src.database import test_connection

    try:
        await test_connection()
        return True
    except Exception as e:
        print(e)
        return False

async def update_statistics():
    """
    Update statistics.
    """
    from src.services.statistic import StatisticService

    logger.info("Starting statistics update...")

    try:
        await StatisticService.update_all_statistics()
        logger.info("Statistics updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update statistics: {e}")


async def check_media_files_expiration():
    """
    Check media files expiration.
    """
    from src.services.advertisement import AdvertisementService

    logger.info("Checking for expired media files...")

    try:
        await AdvertisementService.delete_expired_media_file()
        logger.info("Expired media files deleted successfully.")
    except Exception as e:
        logger.error(f"Failed to delete expired media files: {e}")
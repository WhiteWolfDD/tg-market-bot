from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    import logging
    import sys
    import asyncio

    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    from src.app import Application

    app = Application()
    # app.start()
    asyncio.run(app.start())
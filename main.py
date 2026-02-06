import asyncio
from aiogram import Bot, Dispatcher
from config import config
from utils.logger import logger

async def main():
    try:
        config.check_deps()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.warning("Please setup your .env file according to setup_instructions.md")
        return

    logger.info("Starting Semantist Bot...")
    
    # Initialize Bot and Dispatcher
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    
    # Register routers
    from bot.handlers import register_routes
    register_routes(dp)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot execution error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")

from bot.handlers.processing import router as processing_router

def register_routes(dp):
    dp.include_router(processing_router)

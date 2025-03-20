import logging

import uvicorn

if __name__ == "__main__":
    logging.info("Starting server...")
    uvicorn.run(
        "app.main:get_app",
        host="0.0.0.0",  # noqa
        port=8000,
        reload=True,
        factory=True,
    )

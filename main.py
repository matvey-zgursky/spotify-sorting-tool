import logging

from dotenv import load_dotenv

from app import App
from errors import SpotifyAppError
from logging_config import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    """Запустить менеджер любимых треков Spotify."""
    try:
        load_dotenv()
        configure_logging()
        app = App.create()
        app.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\nProgram interrupted. Exiting...")
        raise SystemExit(130)
    except SpotifyAppError as error:
        logger.error("Application error: %s", error)
        print(error)
        raise SystemExit(1)
    except Exception as error:
        logger.exception("Unexpected program failure")
        print(f"Program failed: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

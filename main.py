from dotenv import load_dotenv

from app import App
from api.errors import SpotifyAppError


def main() -> None:
    """Запустить менеджер любимых треков Spotify."""
    try:
        load_dotenv()
        app = App.create()
        app.run()
    except SpotifyAppError as error:
        print(error)
        raise SystemExit(1)
    except Exception as error:
        print(f"Program failed: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

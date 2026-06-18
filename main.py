from dotenv import load_dotenv

from app import App


def main() -> None:
    """Запустить менеджер любимых треков Spotify."""
    try:
        load_dotenv()
        app = App.create()
        app.run()
    except Exception as error:
        print(f"Program failed: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

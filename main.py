from dotenv import load_dotenv

from auth import Authenticator


def main() -> None:
    """Run the Spotify favorites manager."""

    try:
        load_dotenv()
        authenticator = Authenticator()
        user = authenticator.authorize_user()
        display_name = user.get("display_name") or user.get("id")
        print(f"Authorized in Spotify as: {display_name}")
    except Exception as error:
        print(f"Program failed: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

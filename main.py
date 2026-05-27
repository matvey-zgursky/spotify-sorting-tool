from dotenv import load_dotenv

from auth import Authenticator
from media_library import ADDED_YEAR, LikedTracks


def main() -> None:
    """Run the Spotify favorites manager."""
    try:
        load_dotenv()
        authenticator = Authenticator()
        spotify = authenticator.create_client()
        user = spotify.current_user()
        display_name = user.get("display_name") or user.get("id")
        print(f"Authorized in Spotify as: {display_name}")

        liked_tracks = LikedTracks(spotify)
        track_uris = liked_tracks.get_uris_by_added_year()
        if not track_uris:
            print(f"No liked tracks found for {ADDED_YEAR}.")
            return

        print(f"Liked track URIs added in {ADDED_YEAR}:")
        for index, track_uri in enumerate(track_uris, start=1):
            print(f"{index}. {track_uri}")
    except Exception as error:
        print(f"Program failed: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

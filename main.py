from dotenv import load_dotenv

from auth import Authenticator
from media_library import ADDED_YEAR, LikedTracks
from playlist import PlaylistManager, TargetPlaylistSelector
from user_interface import UserInterface


def main() -> None:
    """Запустить менеджер любимых треков Spotify."""
    try:
        load_dotenv()
        authenticator = Authenticator()
        spotify = authenticator.create_client()
        user = spotify.current_user()
        ui = UserInterface()
        ui.show_authorized_user(user)

        playlist_manager = PlaylistManager(spotify, user["id"])
        playlist_selector = TargetPlaylistSelector(playlist_manager, ui)
        target_playlist = playlist_selector.select()
        if target_playlist is None:
            ui.show_no_target_playlist_selected()
            return

        ui.show_selected_playlist(target_playlist)

        # liked_tracks = LikedTracks(spotify)
        # track_uris = liked_tracks.get_uris_by_added_year()
        # if not track_uris:
        #     print(f"No liked tracks found for {ADDED_YEAR}.")
        #     return

        # print(f"Liked track URIs added in {ADDED_YEAR}:")
        # for index, track_uri in enumerate(track_uris, start=1):
        #     print(f"{index}. {track_uri}")
    except Exception as error:
        print(f"Program failed: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

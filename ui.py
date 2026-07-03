from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from actions import UserAction
from api.types import SpotifyPlaylist, SpotifyUser

if TYPE_CHECKING:
    from liked_tracks import RemoveTracksResult
    from playlist import AddTracksResult

MIN_SPOTIFY_YEAR = 2008
UNTITLED_PLAYLIST_NAME = "[untitled playlist]"


class UserInterface:
    """Отвечает за взаимодействие с пользователем в консоли."""

    def show_authorized_user(self, user: SpotifyUser) -> None:
        """Показать текущего авторизованного пользователя."""
        display_name = user["display_name"] or user["id"]
        print(f"Authorized in Spotify as: {display_name}")

    def ask_user_action(self) -> UserAction:
        """Попросить пользователя выбрать действие."""
        actions = {
            "1": UserAction.TRANSFER_LIKED_TRACKS,
            "2": UserAction.DELETE_LIKED_TRACKS,
        }

        print("Choose action:")
        print("1. Transfer liked tracks to playlist")
        print("2. Delete liked tracks")

        while True:
            choice = input("Enter action number: ").strip()
            action = actions.get(choice)
            if action is not None:
                return action

            print("Please enter a valid action number.")

    def ask_playlist_name_or_url(self) -> str:
        """Запросить название или URL плейлиста."""
        while True:
            value = input("Enter playlist name or URL: ").strip()
            if value:
                return value

            print("Playlist name or URL cannot be empty.")

    def ask_added_year(self) -> int:
        """Запросить год добавления любимых треков."""
        while True:
            value = input("Enter added year: ").strip()
            if not value:
                print("Year cannot be empty.")
            elif not value.isdigit():
                print("Year must contain only digits.")
            elif len(value) != 4:
                print("Year must contain exactly 4 digits.")
            elif int(value) <= 0:
                print("Year must be greater than 0.")
            elif int(value) < MIN_SPOTIFY_YEAR:
                print(f"Year cannot be earlier than {MIN_SPOTIFY_YEAR}.")
            elif int(value) > date.today().year:
                print("Year cannot be in the future.")
            else:
                return int(value)

    def ask_enter_another_playlist(self) -> bool:
        """Спросить, хочет ли пользователь ввести другой плейлист."""
        return self.ask_yes_no("Do you want to enter another playlist name or URL?")

    def ask_create_playlist(self, name: str | None = None) -> bool:
        """Спросить, хочет ли пользователь создать новый плейлист."""
        if name is None:
            return self.ask_yes_no("Do you want to create a new playlist?")

        return self.ask_yes_no(f"Do you want to create a new playlist named '{name}'?")

    def ask_new_playlist_name(self) -> str:
        """Запросить название нового плейлиста."""
        while True:
            name = input("Enter new playlist name: ").strip()
            if name:
                return name

            print("Playlist name cannot be empty.")

    def ask_yes_no(self, question: str) -> bool:
        """Запросить ответ yes/no."""
        while True:
            answer = input(f"{question} [y/n]: ").strip().lower()
            if answer in ("y", "yes"):
                return True
            if answer in ("n", "no"):
                return False

            print("Please answer y or n.")

    def choose_playlist(self, playlists: list[SpotifyPlaylist]) -> SpotifyPlaylist:
        """Попросить пользователя выбрать плейлист из списка."""
        print("Found several editable playlists with this name:")
        for index, playlist in enumerate(playlists, start=1):
            print(f"{index}. {self._format_playlist(playlist)}")

        while True:
            choice = input("Choose playlist number: ").strip()
            if choice.isdigit():
                playlist_index = int(choice) - 1
                if 0 <= playlist_index < len(playlists):
                    return playlists[playlist_index]

            print("Please enter a valid playlist number.")

    def show_playlist_not_found(self) -> None:
        """Сообщить, что плейлист не найден."""
        print("Playlist was not found in your library.")

    def show_no_permission(self) -> None:
        """Сообщить, что пользователь не может добавлять треки."""
        print("You do not have permission to add tracks to this playlist.")

    def show_selected_playlist(self, playlist: SpotifyPlaylist) -> None:
        """Показать выбранный плейлист."""
        print(f"Selected playlist: {self._format_playlist(playlist)}")

    def show_no_target_playlist_selected(self) -> None:
        """Сообщить, что пользователь не выбрал целевой плейлист."""
        print("No target playlist selected.")

    def show_selected_tracks_count(self, tracks_count: int, year: int) -> None:
        """Показать количество выбранных любимых треков."""
        print(f"Found {tracks_count} liked tracks added in {year}.")

    def show_no_liked_tracks_found(self, year: int) -> None:
        """Сообщить, что любимые треки за год не найдены."""
        print(f"No liked tracks found for {year}.")

    def show_liked_tracks_search_started(self, year: int) -> None:
        """Сообщить, что поиск любимых треков начался."""
        print(f"Searching liked tracks added in {year}...")

    def ask_confirm_tracks_transfer(self) -> bool:
        """Спросить, подтверждает ли пользователь перенос треков."""
        return self.ask_yes_no("Do you want to transfer these tracks?")

    def ask_confirm_tracks_delete(self) -> bool:
        """Спросить, подтверждает ли пользователь удаление треков."""
        return self.ask_yes_no("Do you want to delete these tracks?")

    def ask_delete_transferred_tracks(self) -> bool:
        """Спросить, нужно ли удалить перенесенные треки из любимых."""
        return self.ask_yes_no(
            "Do you want to delete transferred tracks from liked tracks?",
        )

    def show_tracks_transfer_cancelled(self) -> None:
        """Сообщить, что пользователь отменил перенос треков."""
        print("Tracks transfer cancelled.")

    def show_tracks_delete_cancelled(self) -> None:
        """Сообщить, что пользователь отменил удаление треков."""
        print("Tracks delete cancelled.")

    def show_tracks_transfer_started(self) -> None:
        """Сообщить, что перенос треков начался."""
        print("Adding tracks to playlist...")

    def show_tracks_delete_started(self) -> None:
        """Сообщить, что удаление треков началось."""
        print("Deleting tracks from liked tracks...")

    def show_tracks_added(
        self,
        result: AddTracksResult,
        playlist: SpotifyPlaylist,
    ) -> None:
        """Показать результат добавления треков в плейлист."""
        formatted_playlist = self._format_playlist(playlist)
        print(
            f"Added {result.added_count} tracks to playlist: {formatted_playlist}. "
            f"Skipped {result.skipped_count} duplicates.",
        )

    def show_tracks_deleted(self, result: RemoveTracksResult) -> None:
        """Показать результат удаления треков из любимых."""
        print(f"Deleted {result.removed_count} liked tracks.")

    def show_tracks_partially_added(
        self,
        result: AddTracksResult,
        playlist: SpotifyPlaylist,
    ) -> None:
        """Показать частичный результат добавления треков перед ошибкой."""
        formatted_playlist = self._format_playlist(playlist)
        print(
            f"Added {result.added_count} tracks to playlist before the error: "
            f"{formatted_playlist}. Skipped {result.skipped_count} duplicates.",
        )

    def show_tracks_partially_deleted(self, result: RemoveTracksResult) -> None:
        """Показать частичный результат удаления треков перед ошибкой."""
        print(
            f"Deleted {result.removed_count} liked tracks before the error.",
        )

    def _format_playlist(self, playlist: SpotifyPlaylist) -> str:
        """Вернуть строку с названием и URL плейлиста."""
        playlist_name = playlist["name"] or UNTITLED_PLAYLIST_NAME
        return f"{playlist_name} ({self._get_playlist_url(playlist)})"

    def _get_playlist_url(self, playlist: SpotifyPlaylist) -> str:
        """Вернуть URL плейлиста Spotify или запасное значение, при отсутствии."""
        return playlist["spotify_url"] or "unknown URL"

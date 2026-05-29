class UserInterface:
    """Отвечает за взаимодействие с пользователем в консоли."""

    def show_authorized_user(self, user: dict) -> None:
        """Показать текущего авторизованного пользователя."""
        display_name = user.get("display_name") or user.get("id")
        print(f"Authorized in Spotify as: {display_name}")

    def ask_playlist_name_or_url(self) -> str:
        """Запросить название или URL плейлиста."""
        while True:
            value = input("Enter playlist name or URL: ").strip()
            if value:
                return value

            print("Playlist name or URL cannot be empty.")

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

    def choose_playlist(self, playlists: list[dict]) -> dict:
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

    def show_selected_playlist(self, playlist: dict) -> None:
        """Показать выбранный плейлист."""
        print(f"Selected playlist: {self._format_playlist(playlist)}")

    def show_no_target_playlist_selected(self) -> None:
        """Сообщить, что пользователь не выбрал целевой плейлист."""
        print("No target playlist selected.")

    def _format_playlist(self, playlist: dict) -> str:
        """Вернуть строку с названием и URL плейлиста."""
        return f"{playlist.get('name')} ({self._get_playlist_url(playlist)})"

    def _get_playlist_url(self, playlist: dict) -> str:
        """Вернуть URL плейлиста Spotify или запасное значение, при отсутствии."""
        external_urls = playlist.get("external_urls") or {}
        spotify_url = external_urls.get("spotify")
        if spotify_url:
            return spotify_url

        return "unknown URL"

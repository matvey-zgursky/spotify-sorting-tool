def print_liked_tracks(spotify, limit: int = 5) -> None:
    """Print the first liked tracks from the user's Spotify library."""
    saved_tracks = spotify.current_user_saved_tracks(limit=limit)
    items = saved_tracks.get("items", [])

    if not items:
        print("No liked tracks found.")
        return

    print(f"First {len(items)} liked tracks:")
    for index, item in enumerate(items, start=1):
        track = item["track"]
        track_name = track["name"]
        artist_names = ", ".join(artist["name"] for artist in track["artists"])
        added_date = item["added_at"][:10]
        print(f"{index}. {artist_names} - {track_name} (added: {added_date})")

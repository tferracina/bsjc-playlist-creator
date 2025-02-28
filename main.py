from playlist_updater import SpotifyPlaylistUpdater

updater = SpotifyPlaylistUpdater()

# To create a new playlist and automatically update the config:
new_playlist_uri = updater.create_new_playlist("BSJC DUMP 2024-25 SEM1 test")

# To update the newly created playlist:
updater.update_playlist("091624_chat.txt")

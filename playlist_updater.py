import re
import time
import os
import configparser
import spotipy
from spotipy.oauth2 import SpotifyOAuth


class SpotifyPlaylistUpdater:
    """Playlist updater class for Spotify playlists."""
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = self.load_config()
        self.sp = self.get_spotify_client()

    def load_config(self):
        config = configparser.ConfigParser()
        if not os.path.exists(self.config_file):
            print("Config file not found. Please create a config.ini file.")
            exit(1)
        config.read(self.config_file)
        return config

    def save_config(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def get_spotify_client(self):
        return spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.config['SPOTIFY']['SPOTIPY_CLIENT_ID'],
            client_secret=self.config['SPOTIFY']['SPOTIPY_CLIENT_SECRET'],
            redirect_uri=self.config['SPOTIFY']['SPOTIPY_REDIRECT_URI'],
            scope='playlist-modify-public playlist-modify-private',
            username=self.config['SPOTIFY']['USERNAME']
        ))

    def extract_spotify_links(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return re.findall(r'https://open\.spotify\.com/track/([a-zA-Z0-9]+)', text)

    def get_playlist_track_ids(self, playlist_id):
        track_ids = []
        try:
            results = self.sp.playlist_tracks(playlist_id)
            while results and 'items' in results:
                track_ids.extend([item['track']['id'] for item in results['items'] if item['track']])
                results = self.sp.next(results) if results.get('next') else None
            if not track_ids:
                print(f"Warning: No tracks found in playlist {playlist_id}")
            return track_ids
        except spotipy.SpotifyException as e:
            print(f"Error retrieving tracks for playlist {playlist_id}: {e}")
            return []

    def compare_track_lists(self, old_list, new_list):
        return list(set(new_list) - set(old_list))

    def add_tracks_to_playlist(self, playlist_uri, spotify_song_links):
        added_tracks = []
        for i in range(0, len(spotify_song_links), 100):
            batch = spotify_song_links[i:i+100]
            try:
                self.sp.playlist_add_items(playlist_uri, items=batch)
                added_tracks.extend(batch)
                print(f"Added {len(batch)} tracks to the playlist")
                time.sleep(1)
            except spotipy.SpotifyException as e:
                print(f"Error adding tracks: {e}")
        return len(added_tracks)

    def make_current_list(self, playlist_ids):
        current_list = []
        for playlist_id in playlist_ids:
            playlist_tracks = self.get_playlist_track_ids(playlist_id)
            if playlist_tracks:
                current_list.extend(playlist_tracks)
            else:
                print(f"Warning: Skipping playlist {playlist_id} due to retrieval error")
        return list(set(current_list))

    def update_playlist(self, file_path):
        comparison_playlists = self.config['PLAYLISTS']['COMPARISON_PLAYLISTS'].split(',')
        target_playlist = self.config['PLAYLISTS']['TARGET_PLAYLIST']

        current_list = self.make_current_list(comparison_playlists)
        new_list = self.extract_spotify_links(file_path)
        new_tracks = self.compare_track_lists(current_list, new_list)

        added_count = self.add_tracks_to_playlist(target_playlist, new_tracks)
        print(f"Total number of songs added to the playlist: {added_count}")

    def create_new_playlist(self, name, update_config=True):
        playlist = self.sp.user_playlist_create(self.config['SPOTIFY']['USERNAME'], name, public=True)
        playlist_uri = playlist['uri']
        playlist_id = playlist['id']
        print(f"Created new playlist: {name} with URI: {playlist_uri}")
        if update_config:
            self.update_config_with_new_playlist(playlist_id)
        return playlist_uri

    def update_config_with_new_playlist(self, playlist_id):
        current_target = self.config['PLAYLISTS']['TARGET_PLAYLIST']
        if current_target != 'target_playlist_id':
            # Move the current target to comparison playlists
            current_comparison = self.config['PLAYLISTS']['COMPARISON_PLAYLISTS']
            if current_comparison == 'playlist_id1,playlist_id2':
                self.config['PLAYLISTS']['COMPARISON_PLAYLISTS'] = current_target
            else:
                self.config['PLAYLISTS']['COMPARISON_PLAYLISTS'] += f",{current_target}"        
        # Set the new playlist as the target
        self.config['PLAYLISTS']['TARGET_PLAYLIST'] = playlist_id
        self.save_config()
        print(f"Updated config file. New playlist {playlist_id} is now the target playlist.")


if __name__ == "__main__":
    updater = SpotifyPlaylistUpdater()

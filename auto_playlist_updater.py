from playlist_updater import SpotifyPlaylistUpdater
import time
import os 
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from requests.exceptions import ReadTimeout, ConnectionError


#set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('playlist_updates.log'),
        logging.StreamHandler()
    ]
)


class Watcher(FileSystemEventHandler):
    def __init__(self, watch_directory):
        self.updater = SpotifyPlaylistUpdater()
        self.watch_directory = watch_directory
        self.processed_files = set()

    def on_created(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith('_chat.txt'):
            return
        
        file_path = event.src_path
        if file_path in self.processed_files:
            return
            
        try:
            time.sleep(2)

            logging.info(f"New chat file detected {file_path}")
            self.updater.update_playlist(file_path)
            self.processed_files.add(file_path)
            logging.info(f"Successfully processed {file_path}")

        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")

def run_watcher(directory):
    event_handler = Watcher(directory)
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=False)
    observer.start()

    logging.info(f"Watching directory: {directory}")

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Stopping watcher")

    observer.join()


if __name__ == "__main__":
    run_watcher("chat")
            
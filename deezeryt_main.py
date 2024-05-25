import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QCheckBox, QLabel, QLineEdit, QPushButton, QScrollArea, QMessageBox
from PySide6.QtGui import QFont
import pandas as pd
import deezer
import re
import urllib.request
import urllib.parse
import subprocess 
import os
import librosa
from pytube import YouTube
from moviepy.editor import VideoFileClip
import glob
from pydub import AudioSegment
import soundfile as sf


class TrackSelectionApp(QMainWindow):
    def __init__(self): 
        super().__init__()

        self.dataframe = pd.DataFrame()
        self.selected_tracks = set()

        self.setWindowTitle("DeezerYoutubeConv")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # headline
        self.selection_layout = QHBoxLayout()
        self.headline_label = QLabel("No Playlist Connected")
        font = QFont()
        font.setPointSize(16)  # Set the font size
        font.setWeight(QFont.Bold)  # Set the font weight
        self.headline_label.setFont(font)
        self.layout.addWidget(self.headline_label)

        # entering playlist id
        self.playlist_layout = QHBoxLayout()
        self.id_label = QLabel("Enter Playlist ID:")
        self.playlist_layout.addWidget(self.id_label)
        self.id_input = QLineEdit()
        self.playlist_layout.addWidget(self.id_input)
        self.confirm_button = QPushButton("Confirm ID")
        self.confirm_button.clicked.connect(self.update_dataframe)
        self.playlist_layout.addWidget(self.confirm_button)
        self.layout.addLayout(self.playlist_layout)

        # selection of tracks
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.stateChanged.connect(self.select_all_tracks)
        self.selection_layout.addWidget(self.select_all_checkbox)
        self.latest_tracks_label = QLabel("Latest tracks >>")
        self.selection_layout.addWidget(self.latest_tracks_label)
        self.latest_tracks_input = QLineEdit()
        self.selection_layout.addWidget(self.latest_tracks_input)
        self.latest_tracks_button = QPushButton("Select")
        self.latest_tracks_button.clicked.connect(self.select_latest_tracks)
        self.selection_layout.addWidget(self.latest_tracks_button)
        self.layout.addLayout(self.selection_layout)

        # track list
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout.addWidget(self.scroll_area)

        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.download_selected_tracks)
        self.layout.addWidget(self.download_button)

        self.client = deezer.Client()


    def add_tracks_to_list(self):
        max_idx = len(self.dataframe)
        for index, row in self.dataframe.iterrows():
            track_checkbox = QCheckBox(f'({abs(index-max_idx)}) {row["title"]} - {row["artist"]["name"]}')
            track_checkbox.setChecked(row['title'] in self.selected_tracks)
            track_checkbox.stateChanged.connect(lambda state, track=row['title']: self.track_selection_changed(track, state))
            self.scroll_layout.addWidget(track_checkbox)

    def clear_track_list(self):
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

    def select_all_tracks(self, state):
        for i in range(self.scroll_layout.count()):
            checkbox = self.scroll_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(state == 2)

    def select_latest_tracks(self):
        num_latest_tracks = self.latest_tracks_input.text()
        if num_latest_tracks.isdigit():
            num_latest_tracks = int(num_latest_tracks)
            if num_latest_tracks > 0:
                # Clear the current selection
                self.clear_track_selection()
                # Select the latest tracks
                for i in range(min(num_latest_tracks, len(self.dataframe))):
                    track_checkbox = self.scroll_layout.itemAt(i).widget()
                    if isinstance(track_checkbox, QCheckBox):
                        track_checkbox.setChecked(True)
        else:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for selecting latest tracks.")

    def clear_track_selection(self):
        for i in range(self.scroll_layout.count()):
            checkbox = self.scroll_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(False)

    def track_selection_changed(self, track, state):
        if state == 2:
            self.selected_tracks.add(track)
        else:
            self.selected_tracks.discard(track)

    def update_dataframe(self):
        new_id = self.id_input.text()
        if new_id.isdigit():
            # Update dataframe with new ID
            # For demonstration purposes, let's print the updated dataframe
            playlist = self.client.get_playlist(playlist_id=new_id)
            playlist_dict = playlist.as_dict()
            tracks_frame = pd.DataFrame(playlist_dict["tracks"])
            tracks_frame = tracks_frame.sort_values("time_add", ascending=False)
            playlist_name = playlist_dict["title"]
            self.headline_label.setText(playlist_name)
            print(f"Updated to Playlist: {playlist_name}")
            self.dataframe = tracks_frame
            print(self.dataframe)
            self.clear_track_list()
            self.add_tracks_to_list()
        else:
            QMessageBox.warning(self, "Invalid ID", "Please enter a valid numerical ID.")

# Example usage:
# convert_mp4_to_wav('/path/to/your/folder')

    def download_selected_tracks(self):
        selected_dataframe = self.dataframe[self.dataframe['title'].isin(self.selected_tracks)]
        # For demonstration purposes, let's print the selected dataframe
        print("Selected Tracks:")
        # 12342264551
        temp_folder = os.path.dirname(__file__)
        already_existing_files = glob.glob(os.path.join(temp_folder, '*.wav'))
        
        print(f"Download started - id {id}")
        for index, track in selected_dataframe.iterrows():
            print(track)
            print("---")
            print(track["title"], "\t", track["artist"]["name"])

            title = track["title"]
            artist = track["artist"]["name"]

            input = urllib.parse.urlencode({'search_query': title + ' by ' + artist})
            #html = requests.get("https://www.youtube.com/results?search_query=" + s_k)
            html = urllib.request.urlopen("http://www.youtube.com/results?" + input)
            print("http://www.youtube.com/results?" + input)
            video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
            first_res_html = f"http://www.youtube.com/watch?v={video_ids[0]}"

            youtubeObject = YouTube(first_res_html)
            youtubeObject = youtubeObject.streams.get_highest_resolution()
            youtubeObject.download(temp_folder)
            print(youtubeObject.title)

        mp4_files = glob.glob(os.path.join(temp_folder, '*.mp4'))
        print(mp4_files)
        for mp4_file in mp4_files:
            wav_file = mp4_file.replace('.mp4', '.wav')
            video = VideoFileClip(mp4_file)
            audio = video.audio
            temp_mp3_path = mp4_file.replace('.mp4', '.mp3')
            audio.write_audiofile(temp_mp3_path)
            sound = AudioSegment.from_mp3(temp_mp3_path)
            sound.export(wav_file, format='wav')
            audio.close()
            video.close()
            
            os.remove(temp_mp3_path)
            os.remove(mp4_file)
            
        print(f"Converted {len(mp4_files)} .mp4 files to .wav format and deleted the originals.")


if __name__ == "__main__":
    df = pd.DataFrame()

    app = QApplication(sys.argv)
    window = TrackSelectionApp()
    window.show()
    sys.exit(app.exec())

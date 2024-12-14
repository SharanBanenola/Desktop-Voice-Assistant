#ui.py code

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QStackedLayout, QWidget
import numpy as np
import sounddevice as sd

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Disable maximizing, but allow minimizing and closing
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.browser = QWebEngineView()
        self.browser.setHtml("""
        <!DOCTYPE html>
        <html>
          <head>
            <title>Siri Waveform with SiriWaveJS</title>
            <style>
              body {
                background-color: #000000;  /* Dark background */
                margin: 0;
                padding: 0;
              }
            </style>
          </head>
          <body>
            <div style="position: relative; width: 100%; height: 100vh;">
                <div id="user-command" style="position: absolute; color: white; font-size: 36px; text-align: center; top: 360px; width: 100%;"></div>
                <div id="siri-container" style="position: absolute; top: 0; width: 100%; height: 100vh;"></div>
            </div>

            <script src="https://unpkg.com/siriwave/dist/siriwave.umd.min.js"></script>
            <script>
              // Initialize SiriWave with dark mode settings
              var siriWave;
              function initializeSiriWave() {
                  siriWave = new SiriWave({
                      container: document.getElementById('siri-container'),
                      width: window.innerWidth,
                      height: window.innerHeight,
                      style: 'ios9',
                      cover: true,
                      speed: 0.03,
                      amplitude: 1,
                      frequency: 1,
                      color: "#ffffff"  // White color waves
                  });
                  siriWave.start();
              }

              // Make it globally accessible
              window.setAmplitude = function(amp) {
                  if (!siriWave) {
                      initializeSiriWave();
                  }
                  siriWave.setAmplitude(amp);
              };

              // Initialize SiriWave on page load
              window.onload = initializeSiriWave;
              window.setUserCommand = function(command) {
                document.getElementById('user-command').innerText = command;
            };

              // Resize SiriWave when window is resized
              window.onresize = function() {
                  if (siriWave) {
                      siriWave.set('width', window.innerWidth);
                      siriWave.set('height', window.innerHeight);
                  }
              };
            </script>
          </body>
        </html>
        """)

        self.browser.loadFinished.connect(self.on_load_finished)

        self.setCentralWidget(self.browser)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.showMaximized()

    # Initialize a QLabel to display text
        self.label = QLabel()

        # Create a stacked layout and add both browser and label
        self.layout = QStackedLayout()
        self.layout.addWidget(self.browser)
        self.layout.addWidget(self.label)

        # Set the layout
        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)
    
    def set_user_command(self, command):
        escaped_command = command.replace("\n", "\\n").replace('"', '\\"')
        self.browser.page().runJavaScript(f'window.setUserCommand("{escaped_command}")')


    def update_method(self, text):
        existing_text = self.label.text()
        new_text = existing_text + "\n" + text
        self.label.setText(new_text)


    def resizeEvent(self, event):
        self.browser.page().runJavaScript('window.dispatchEvent(new Event("resize"));')
        super(MainWindow, self).resizeEvent(event)

    def on_load_finished(self):
        # Initialize sounddevice and numpy
        self.stream = sd.InputStream(callback=self.audio_callback)
        self.stream.start()

        # Initialize QTimer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_amplitude)
        self.timer.start(50)  # Update every 50 ms

    def audio_callback(self, indata, frames, time, status):
        
        self.audio_amplitude = np.abs(indata).mean()

    def update_amplitude(self):
        
        scaled_amplitude = np.sqrt(self.audio_amplitude) * 10
        self.browser.page().runJavaScript(f'window.setAmplitude({scaled_amplitude})')

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    app.exec_()
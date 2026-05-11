import sys
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QGridLayout, QHBoxLayout, QLineEdit, QMainWindow, QMenu, QPlainTextEdit, QWidget, QPushButton, QLabel, QVBoxLayout, QCheckBox
from PySide6.QtCore import Qt, QProcess
import platform
os = platform.system()
import subprocess
import cv2
import socket
from qtpy import QtCore, QtWidgets
from qtpyTerminal import qtpyTerminal
import psutil
from cv2_enumerate_cameras import enumerate_cameras

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebcamtoRTSP")
        self.setMinimumSize(900, 600)
        layout = QGridLayout()
        #camera and network settings label
        label1 = QLabel("Camera and Network Settings")
        label1.setStyleSheet("font-weight: bold;")
        layout.addWidget(label1, 0, 0, 1, 6)
        #check operating system
        if os == "Windows":
            print("Running on Windows")
            #add label for system os and version
            label2 = QLabel(f"System OS: {os} {platform.release()}")
            layout.addWidget(label2, 0, 6, 1, 6)
            #enumerate cameras using cv2_enumerate_cameras
            cameras = enumerate_cameras()
            #add cameras to a combo box showing camera name
            winlabel1 = QLabel("Select Camera:")
            layout.addWidget(winlabel1, 1, 0, 1, 1)
            camera_list = []
            for camera in cameras:
                if f"{camera.name}" not in camera_list:
                    camera_list.append(f"{camera.name}")
            combo = QComboBox()
            combo.addItem("")
            combo.addItems(camera_list)
            layout.addWidget(combo, 1, 1, 1, 7)
            #add framerate dropdown with common framerates
            winlabel2 = QLabel("Select Framerate:")
            layout.addWidget(winlabel2, 1, 8, 1, 1)
            framerate_combo = QComboBox()
            framerate_combo.addItem("")
            framerate_combo.addItems(["15", "24", "25", "30", "44", "60", "120"])
            layout.addWidget(framerate_combo, 1, 9, 1, 1)
            #add resolution dropdown with common resolutions
            winlabel3 = QLabel("Select Resolution:")
            layout.addWidget(winlabel3, 1, 10, 1, 1)
            resolution_combo = QComboBox()
            resolution_combo.addItem("")
            resolution_combo.addItems(["640x480", "1280x720", "1920x1080", "3840x2160"])
            layout.addWidget(resolution_combo, 1, 11, 1, 1)
            #use selected camera to show a video feed using opencv
            def show_video():
                selected_camera = combo.currentText()
                print(f"Selected Camera: {selected_camera}")
                #check if a camera is selected
                if selected_camera == "":
                    dlg = QDialog(self)
                    dlg.setWindowTitle("Info")
                    dlg.setMinimumSize(400, 200)
                    layoutd = QVBoxLayout()
                    label = QLabel("Please select a camera before showing the video feed.")
                    layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                    dlg.setLayout(layoutd)
                    dlg.exec()
                    return
                #use camera name to find the camera matching camera object
                for camera in cameras:
                    print(f"Camera: {camera.name}")
                matching_camera = next((camera for camera in cameras if camera.name == selected_camera), None)
                if matching_camera is None:
                    dlg = QDialog(self)
                    dlg.setWindowTitle("Info")
                    dlg.setMinimumSize(400, 200)
                    layoutd = QVBoxLayout()
                    label = QLabel("Selected camera not found.")
                    layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                    dlg.setLayout(layoutd)
                    dlg.exec()
                    return
                cap = cv2.VideoCapture(matching_camera.index)
                if not cap.isOpened():
                    cap.release()
                    return
                show_video_button.setEnabled(False)
                try:
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        cv2.imshow("Selected Camera Video Feed", frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                        if cv2.getWindowProperty("Selected Camera Video Feed", cv2.WND_PROP_VISIBLE) < 1:
                            break
                finally:
                    cap.release()
                    cv2.destroyAllWindows()
                    show_video_button.setEnabled(True)
            show_video_button = QPushButton("Preview Selected Camera")
            #show_video_button.setStyleSheet("font-weight: bold; background-color: blue; color: white;")
            show_video_button.clicked.connect(show_video)
            layout.addWidget(show_video_button, 2, 11)

            #create horizontal line separator
            line = QtWidgets.QFrame()
            line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
            line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
            layout.addWidget(line, 5, 0, 1, 11)

            #add two checkboxes to select either localhost ip or the local network ip
            def get_local_ip():
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    s.close()
                    return local_ip
                except Exception as e:
                    print(f"Error getting local IP: {e}")
                    return "127.0.0.1"
            local_ip = get_local_ip()
            localhost_ip = "127.0.0.1"
            winlabel4 = QLabel("Select IP Address:")
            layout.addWidget(winlabel4, 6, 0, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)
            #add checkbox to toggle between local ip and public ip
            local_ip_checkbox = QCheckBox(f"Local Network IP ({local_ip})")
            public_ip_checkbox = QCheckBox(f"Localhost IP ({localhost_ip})")

            def on_local_ip_change(state):
                if local_ip_checkbox.isChecked():
                    public_ip_checkbox.blockSignals(True)
                    public_ip_checkbox.setChecked(False)
                    public_ip_checkbox.blockSignals(False)

            def on_public_ip_change(state):
                if public_ip_checkbox.isChecked():
                    local_ip_checkbox.blockSignals(True)
                    local_ip_checkbox.setChecked(False)
                    local_ip_checkbox.blockSignals(False)

            local_ip_checkbox.stateChanged.connect(on_local_ip_change)
            public_ip_checkbox.stateChanged.connect(on_public_ip_change)
            layout.addWidget(local_ip_checkbox, 6, 1, 1, 1)
            layout.addWidget(public_ip_checkbox, 6, 2, 1, 1)

            #add horizontal line separator
            line2 = QtWidgets.QFrame()
            line2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
            line2.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
            layout.addWidget(line2, 8, 0, 1, 11)

            #show selected camera and selected ip in a label
            winlabel5 = QLabel("Selected Settings:")
            layout.addWidget(winlabel5, 9, 0, 1, 11, alignment=Qt.AlignmentFlag.AlignLeft)
            wlabel6 = QLabel("Camera: ")
            layout.addWidget(wlabel6, 10, 0, 1, 3)
            wlabel7 = QLabel("IP: ")
            layout.addWidget(wlabel7, 10, 3, 1, 3)
            wlabel8 = QLabel("FPS: ")
            layout.addWidget(wlabel8, 10, 6, 1, 3)
            wlabel9 = QLabel("Resolution: ")
            layout.addWidget(wlabel9, 10, 9, 1, 3)

            def update_selected_settings():
                selected_camera = combo.currentText()
                selected_ip = ""
                if local_ip_checkbox.isChecked():
                    selected_ip = local_ip
                elif public_ip_checkbox.isChecked():
                    selected_ip = localhost_ip
                wlabel6.setText(f"Camera: {selected_camera}")
                wlabel7.setText(f"IP: {selected_ip}")
                wlabel8.setText(f"FPS: {framerate_combo.currentText()}")
                wlabel9.setText(f"Resolution: {resolution_combo.currentText()}")

            combo.currentIndexChanged.connect(update_selected_settings)
            local_ip_checkbox.stateChanged.connect(update_selected_settings)
            public_ip_checkbox.stateChanged.connect(update_selected_settings)
            framerate_combo.currentIndexChanged.connect(update_selected_settings)
            resolution_combo.currentIndexChanged.connect(update_selected_settings)
            update_selected_settings()

            #start streaming button
            start_streaming_button = QPushButton("Confirm & Start RTSP Stream")
            start_streaming_button.setStyleSheet("font-weight: bold; background-color: green; color: white;")
            layout.addWidget(start_streaming_button, 11, 0, 1, 6)
            start_streaming_button.clicked.connect(lambda: start_mediamtx())
            #quit webcamtortsp button
            quit_button = QPushButton("Stop RTSP Streams")
            quit_button.setStyleSheet("font-weight: bold; background-color: red; color: white;")
            layout.addWidget(quit_button, 11, 6, 1, 6)

            def is_mediamtx_running():
                return any('mediamtx' in proc.info['name'] for proc in psutil.process_iter(['name']))
            
            def update_stream_buttons_state(mediamtx_running):
                start_streaming_button.setEnabled(not mediamtx_running)
                #quit_button.setEnabled(mediamtx_running)

            update_stream_buttons_state(is_mediamtx_running())

            #add two terminals to show mediamtx server output and ffmpeg output
            label12 = QLabel("MediaMTX Server Output:")
            layout.addWidget(label12, 12, 0, 1, 6)
            #testbtn = QPushButton("Test")
            #layout.addWidget(testbtn, 13, 0, 1, 6)

            def check_mediamtx_process():
                if is_mediamtx_running():
                    #show dialog box with message "MediaMTX is running. Do you want to stop it?" and options "Yes" and "No"
                    dlg = QDialog(self)
                    dlg.setWindowTitle("MediaMTX is running")
                    dlg.setMinimumSize(400, 200)
                    layoutd = QVBoxLayout()
                    label = QLabel("MediaMTX. Confirm is running?")
                    layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                    button_layout = QHBoxLayout()
                    yes_button = QPushButton("Yes")
                    no_button = QPushButton("No")
                    button_layout.addWidget(yes_button)
                    button_layout.addWidget(no_button)
                    layoutd.addLayout(button_layout)
                    dlg.setLayout(layoutd)
                    def handle_yes_clicked():
                        stop_mediamtx()
                        dlg.close()
                    def handle_no_clicked():
                        start_ffmpeg()
                        dlg.close()
                    yes_button.clicked.connect(handle_no_clicked)
                    no_button.clicked.connect(handle_yes_clicked)
                    dlg.exec()
                else:
                    #check again after 500 milliseconds
                    QtCore.QTimer.singleShot(500, check_mediamtx_process)

            #test function for test button
            def start_mediamtx():
                #check if camera, ip, framerate, and resolution are selected before starting the stream
                selected_camera = combo.currentText()
                selected_ip = ""
                if local_ip_checkbox.isChecked():
                    selected_ip = local_ip
                elif public_ip_checkbox.isChecked():
                    selected_ip = localhost_ip
                selected_frame_rate = framerate_combo.currentText()
                selected_resolution = resolution_combo.currentText()
                if selected_camera == "" or selected_ip == "" or selected_frame_rate == "" or selected_resolution == "":
                    dlg = QDialog(self)
                    dlg.setWindowTitle("Info")
                    dlg.setMinimumSize(400, 200)
                    layoutd = QVBoxLayout()
                    label = QLabel("Please select a camera, IP address, frame rate, and resolution before starting the RTSP stream.")
                    layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                    dlg.setLayout(layoutd)
                    dlg.exec()
                    return

                print("Starting Mediamtx process")
                pmessage("Starting Mediamtx process")
                self.p = QProcess()
                def process_finished():
                    print("Mediamtx process finished")
                    pmessage("Mediamtx process finished")
                    self.p = None
                self.p.readyReadStandardOutput.connect(handle_stdout)
                self.p.readyReadStandardError.connect(handle_stderr)
                self.p.stateChanged.connect(handle_state)
                self.p.finished.connect(process_finished)
                #self.p.start("ping", ["google.com"])
                self.p.start("./mediamtx/mediamtx.exe", ["./mediamtx/mediamtx.yml"])
                #wait for 500 milliseconds to allow mediamtx to start before starting ffmpeg
                QtCore.QTimer.singleShot(500, check_mediamtx_process)

            #testbtn.clicked.connect(start_mediamtx)
            edittext = QPlainTextEdit()
            edittext.setReadOnly(True)
            layout.addWidget(edittext, 14, 0, 1, 6)

            def pmessage(msg):
                edittext.appendPlainText(msg)

            def handle_stderr():
                if self.p:
                    error_output = self.p.readAllStandardError().data().decode()
                    pmessage(f"Error: {error_output}")
            
            def handle_stdout():
                if self.p:
                    standard_output = self.p.readAllStandardOutput().data().decode()
                    pmessage(standard_output)

            def handle_state(state):
                states = {
                    QProcess.NotRunning: "Not Running",
                    QProcess.Starting: "Starting",
                    QProcess.Running: "Running"
                }
                pmessage(f"Process state changed: {states.get(state, 'Unknown State')}")

            label13 = QLabel("FFmpeg Output:")
            layout.addWidget(label13, 12, 6, 1, 6)

            def start_ffmpeg():
                selected_camera = combo.currentText()
                if selected_camera:
                    device_path = selected_camera.split("(")[-1].strip(")")
                else:
                    device_path = ""
                selected_ip = ""
                if local_ip_checkbox.isChecked():
                    selected_ip = local_ip
                elif public_ip_checkbox.isChecked():                    
                    selected_ip = localhost_ip
                    
                selected_frame_rate = framerate_combo.currentText()
                selected_resolution = resolution_combo.currentText()


                print(f"Selected Camera: {device_path}")
                print(f"Selected IP: {selected_ip}")
                print(f"Selected Frame Rate: {selected_frame_rate}")
                print(f"Selected Resolution: {selected_resolution}")

                if selected_camera == "" or selected_ip == "" or selected_frame_rate == "" or selected_resolution == "":
                    dlg = QDialog(self)
                    dlg.setWindowTitle("Info")
                    dlg.setMinimumSize(400, 200)
                    layoutd = QVBoxLayout()
                    label = QLabel("Please select a camera, frame rate, and resolution before starting the RTSP stream.")
                    layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                    dlg.setLayout(layoutd)
                    dlg.exec()
                    return
                elif selected_camera and selected_ip and selected_frame_rate and selected_resolution:
                    #ffmpeg_command = f"ffmpeg -f dshow -video_size {selected_resolution} -i video=\"{selected_camera}\" -c:v libx264 -preset ultrafast -tune zerolatency -fflags nobuffer -pix_fmt yuv420p -rtsp_transport udp -analyzeduration 0 -probesize 32 -flags low_delay  -f rtsp rtsp://{selected_ip}:8554/webcam"
                    self.ffmpegp = QProcess()
                    pmessageffmpeg("Starting FFmpeg process")
                    def ffmpeg_finished():
                        print("FFmpeg process finished")
                        pmessageffmpeg("FFmpeg process finished")
                        self.ffmpegp = None
                    self.ffmpegp.readyReadStandardOutput.connect(handle_ffmpeg_stdout)
                    self.ffmpegp.readyReadStandardError.connect(handle_ffmpeg_stderr)
                    self.ffmpegp.stateChanged.connect(handle_ffmpeg_state)
                    self.ffmpegp.finished.connect(ffmpeg_finished)
                    self.ffmpegp.start("ffmpeg", ["-f", "dshow", "-video_size", selected_resolution, "-i", f"video={selected_camera}", "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency", "-fflags", "nobuffer", "-pix_fmt", "yuv420p", "-rtsp_transport", "udp", "-analyzeduration", "0", "-probesize", "32", "-flags", "low_delay", "-f", "rtsp", f"rtsp://{selected_ip}:8554/webcam"])

            edittextffmpeg = QPlainTextEdit()
            edittextffmpeg.setReadOnly(True)
            layout.addWidget(edittextffmpeg, 14, 6, 1, 6)

            def pmessageffmpeg(msg):
                edittextffmpeg.appendPlainText(msg)

            def handle_ffmpeg_stderr():
                if self.ffmpegp:
                    error_output = self.ffmpegp.readAllStandardError().data().decode()
                    pmessageffmpeg(f"FFmpeg Error: {error_output}")

            def handle_ffmpeg_stdout():
                if self.ffmpegp:
                    standard_output = self.ffmpegp.readAllStandardOutput().data().decode()
                    pmessageffmpeg(f"FFmpeg Output: {standard_output}")

            def handle_ffmpeg_state(state):
                states = {
                    QProcess.NotRunning: "Not Running",
                    QProcess.Starting: "Starting",
                    QProcess.Running: "Running"
                }
                pmessageffmpeg(f"FFmpeg process state changed: {states.get(state, 'Unknown State')}")







            #stop mediamtx by finding the process and killing it
            def stop_mediamtx():
                stopped = False
                if os == "Linux":
                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'] == "mediamtx":
                            proc.kill()
                            stopped = True
                    #console.stop()
                    #console.close()
                elif os == "Windows":
                    subprocess.call("taskkill /f /im mediamtx.exe", shell=True)
                    stopped = True
                elif os == "Darwin":
                    subprocess.call("pkill mediamtx", shell=True)
                    stopped = True

                if stopped or not is_mediamtx_running():
                    update_stream_buttons_state(False)

            #stop ffmpeg by finding the process and killing it
            def stop_ffmpeg():
                if os == "Linux":
                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'] == "ffmpeg":
                            proc.terminate()
                elif os == "Windows":
                    subprocess.call("taskkill /f /im ffmpeg.exe", shell=True)
                elif os == "Darwin":
                    subprocess.call("pkill ffmpeg", shell=True)

            #stop both mediamtx and ffmpeg when the main window is closed
            def handle_close_event():
                print("Closing application, stopping FFmpeg and MediaMTX processes...")
                stop_ffmpeg()
                stop_mediamtx()
                
            quit_button.clicked.connect(lambda: handle_close_event())










        elif os == "Linux":
            print("Running on Linux")
            #add label for system os and version
            label2 = QLabel(f"System OS: {os} {platform.release()}")
            layout.addWidget(label2, 0, 6, 1, 6)
        #query available cameras using v4l2-ctl command and add them to a combo box showing camera name and device path
            cameras = subprocess.check_output("v4l2-ctl --list-devices", shell=True).decode().split("\n\n")
            camera_list = []
            for camera in cameras:
                lines = camera.split("\n")
                if len(lines) > 1:
                    name = lines[0].strip()
                    device = lines[1].strip()
                    camera_list.append(f"{name} ({device})")
            label3 = QLabel("Select Camera:")
            layout.addWidget(label3, 1, 0, 1, 1)
            combo = QComboBox()
            combo.addItem("")
            combo.addItems(camera_list)
            layout.addWidget(combo, 1, 1, 1, 7)
            #add framerate dropdown with common framerates
            label4 = QLabel("Select Framerate:")
            layout.addWidget(label4, 1, 8, 1, 1)
            framerate_combo = QComboBox()
            framerate_combo.addItem("")
            framerate_combo.addItems(["15", "24", "25", "30", "44", "60", "120"])
            layout.addWidget(framerate_combo, 1, 9, 1, 1)
            #add resolution dropdown with common resolutions
            label5 = QLabel("Select Resolution:")
            layout.addWidget(label5, 1, 10, 1, 1)
            resolution_combo = QComboBox()
            resolution_combo.addItem("")
            resolution_combo.addItems(["640x480", "1280x720", "1920x1080", "3840x2160"])
            layout.addWidget(resolution_combo, 1, 11, 1, 1)
            #use selected camera to show a video feed using opencv
            def show_video():
                selected_camera = combo.currentText()
                #check if a camera is selected
                if selected_camera == "":
                    dlg = QDialog(self)
                    dlg.setWindowTitle("Info")
                    dlg.setMinimumSize(400, 200)
                    layoutd = QVBoxLayout()
                    label = QLabel("Please select a camera before showing the video feed.")
                    layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                    dlg.setLayout(layoutd)
                    dlg.exec()
                    return
                if selected_camera:
                    device_path = selected_camera.split("(")[-1].strip(")")
                    cap = cv2.VideoCapture(device_path)
                    if not cap.isOpened():
                        cap.release()
                        return
                    try:
                        while True:
                            ret, frame = cap.read()
                            if not ret:
                                break
                            cv2.imshow("Selected Camera Video Feed", frame)
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                break
                            if cv2.getWindowProperty("Selected Camera Video Feed", cv2.WND_PROP_VISIBLE) < 1:
                                break
                        cap.release()
                        cv2.destroyAllWindows()
                    finally:
                        cap.release()
                        cv2.destroyAllWindows()
            show_video_button = QPushButton("Preview Selected Camera")
            show_video_button.setStyleSheet("font-weight: bold; background-color: blue; color: white;")
            show_video_button.clicked.connect(show_video)
            layout.addWidget(show_video_button, 2, 11)

            #create horizontal line separator
            line = QtWidgets.QFrame()
            line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
            line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
            layout.addWidget(line, 5, 0, 1, 11)

            #add two checkboxes to select either localhost ip or the local network ip
            def get_local_ip():
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    ip = s.getsockname()[0]
                    s.close()
                    return ip
                except:
                    return "127.0.0.1"
                
            local_ip = get_local_ip()
            localhost_ip = "127.0.0.1"
            label6 = QLabel("Select IP Address:")
            layout.addWidget(label6, 6, 0, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)
            #add checkbox to toggle between local ip and public ip
            local_ip_checkbox = QCheckBox(f"Local Network IP ({local_ip})")
            public_ip_checkbox = QCheckBox(f"Localhost IP ({localhost_ip})")
            
            def on_local_ip_change(state):
                if local_ip_checkbox.isChecked():
                    public_ip_checkbox.blockSignals(True)
                    public_ip_checkbox.setChecked(False)
                    public_ip_checkbox.blockSignals(False)
            
            def on_public_ip_change(state):
                if public_ip_checkbox.isChecked():
                    local_ip_checkbox.blockSignals(True)
                    local_ip_checkbox.setChecked(False)
                    local_ip_checkbox.blockSignals(False)
            
            local_ip_checkbox.stateChanged.connect(on_local_ip_change)
            layout.addWidget(local_ip_checkbox, 6, 1, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
            public_ip_checkbox.stateChanged.connect(on_public_ip_change)
            layout.addWidget(public_ip_checkbox, 6, 2, 1, 11, alignment=Qt.AlignmentFlag.AlignLeft)

            #add horizontal line separator
            line2 = QtWidgets.QFrame()
            line2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
            line2.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
            layout.addWidget(line2, 8, 0, 1, 11)
            
            #show selected camera and selected ip in a label
            label7 = QLabel("Selected Settings:")
            layout.addWidget(label7, 9, 0, 1, 11, alignment=Qt.AlignmentFlag.AlignLeft)
            label8 = QLabel("Camera: ")
            layout.addWidget(label8, 10, 0, 1, 3)
            label9 = QLabel("IP: ")
            layout.addWidget(label9, 10, 3, 1, 3)
            label10 = QLabel("FPS: ")
            layout.addWidget(label10, 10, 6, 1, 3)
            label11 = QLabel("Resolution: ")
            layout.addWidget(label11, 10, 9, 1, 3)

            def update_selected_settings():
                selected_camera = combo.currentText()
                selected_ip = ""
                if local_ip_checkbox.isChecked():
                    selected_ip = local_ip
                elif public_ip_checkbox.isChecked():
                    selected_ip = localhost_ip
                label8.setText(f"Camera: {selected_camera}")
                label9.setText(f"IP: {selected_ip}")
                label10.setText(f"FPS: {framerate_combo.currentText()}")
                label11.setText(f"Resolution: {resolution_combo.currentText()}")
            
            combo.currentIndexChanged.connect(update_selected_settings)
            local_ip_checkbox.stateChanged.connect(update_selected_settings)
            public_ip_checkbox.stateChanged.connect(update_selected_settings)
            framerate_combo.currentIndexChanged.connect(update_selected_settings)
            resolution_combo.currentIndexChanged.connect(update_selected_settings)
            update_selected_settings()

            #start streaming button
            start_streaming_button = QPushButton("Confirm & Start RTSP Stream")
            start_streaming_button.setStyleSheet("font-weight: bold; background-color: green; color: white;")
            layout.addWidget(start_streaming_button, 11, 0, 1, 6)
            #quit webcamtortsp button
            quit_button = QPushButton("Stop RTSP Streams")
            quit_button.setStyleSheet("font-weight: bold; background-color: red; color: white;")
            layout.addWidget(quit_button, 11, 6, 1, 6)

            def is_mediamtx_running():
                return any('mediamtx' in proc.info['name'] for proc in psutil.process_iter(['name']))

            def update_stream_buttons_state(mediamtx_running):
                start_streaming_button.setEnabled(not mediamtx_running)
                quit_button.setEnabled(mediamtx_running)

            update_stream_buttons_state(is_mediamtx_running())

            #add two terminals to show mediamtx server output and ffmpeg output
            label12 = QLabel("MediaMTX Server Output:")
            layout.addWidget(label12, 12, 0, 1, 6)
            console = qtpyTerminal()
            def start_mediamtx():
                #check if camera, ip, framerate, and resolution are selected before starting the stream
                selected_camera = combo.currentText()
                selected_ip = ""
                if local_ip_checkbox.isChecked():
                    selected_ip = local_ip
                elif public_ip_checkbox.isChecked():
                    selected_ip = localhost_ip
                selected_frame_rate = framerate_combo.currentText()
                selected_resolution = resolution_combo.currentText()
                if selected_camera == "" or selected_ip == "" or selected_frame_rate == "" or selected_resolution == "":
                    dlg = QDialog(self)
                    dlg.setWindowTitle("Info")
                    dlg.setMinimumSize(400, 200)
                    layoutd = QVBoxLayout()
                    label = QLabel("Please select a camera, IP address, frame rate, and resolution before starting the RTSP stream.")
                    layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                    dlg.setLayout(layoutd)
                    dlg.exec()
                    return
                elif selected_camera and selected_ip and selected_frame_rate and selected_resolution:
                    console.set_cmd("mediamtx")
                    console.start()
                    update_stream_buttons_state(True)
                    #wait for 500 milliseconds to allow mediamtx to start before starting ffmpeg
                    QtCore.QTimer.singleShot(500, check_mediamtx_process)
                    
                
            start_streaming_button.clicked.connect(lambda: start_mediamtx())
            layout.addWidget(console, 14, 0, 1, 6)

            label13 = QLabel("FFmpeg Output:")
            layout.addWidget(label13, 12, 6, 1, 6)
            ffmpeg_console = qtpyTerminal()
            layout.addWidget(ffmpeg_console, 14, 6, 1, 6)
            def start_ffmpeg():
                selected_camera = combo.currentText()
                if selected_camera:
                    device_path = selected_camera.split("(")[-1].strip(")")
                else:
                    device_path = ""
                selected_ip = ""
                if local_ip_checkbox.isChecked():
                    selected_ip = local_ip
                elif public_ip_checkbox.isChecked():                    
                    selected_ip = localhost_ip
                    
                selected_frame_rate = framerate_combo.currentText()
                selected_resolution = resolution_combo.currentText()


                print(f"Selected Camera: {device_path}")
                print(f"Selected IP: {selected_ip}")
                print(f"Selected Frame Rate: {selected_frame_rate}")
                print(f"Selected Resolution: {selected_resolution}")

                if selected_camera == "" or selected_ip == "" or selected_frame_rate == "" or selected_resolution == "":
                    dlg = QDialog(self)
                    dlg.setWindowTitle("Info")
                    dlg.setMinimumSize(400, 200)
                    layoutd = QVBoxLayout()
                    label = QLabel("Please select a camera, frame rate, and resolution before starting the RTSP stream.")
                    layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                    dlg.setLayout(layoutd)
                    dlg.exec()
                    return
                elif selected_camera and selected_ip and selected_frame_rate and selected_resolution:
                    ffmpeg_command = f"ffmpeg -f v4l2 -video_size {selected_resolution} -i {device_path} -c:v libx264 -preset ultrafast -tune zerolatency -fflags nobuffer -pix_fmt yuv420p -rtsp_transport udp -analyzeduration 0 -probesize 32 -flags low_delay  -f rtsp rtsp://{selected_ip}:8554/webcam"
                    ffmpeg_console.set_cmd(ffmpeg_command)
                    print("Starting FFmpeg with the following command:")
                    ffmpeg_console.start()

            def check_mediamtx_process():
                if is_mediamtx_running():
                    #show dialog box with message "MediaMTX is running. Do you want to stop it?" and options "Yes" and "No"
                    dlg = QDialog(self)
                    dlg.setWindowTitle("MediaMTX is running")
                    dlg.setMinimumSize(400, 200)
                    layoutd = QVBoxLayout()
                    label = QLabel("MediaMTX. Confirm is running?")
                    layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                    button_layout = QHBoxLayout()
                    yes_button = QPushButton("Yes")
                    no_button = QPushButton("No")
                    button_layout.addWidget(yes_button)
                    button_layout.addWidget(no_button)
                    layoutd.addLayout(button_layout)
                    dlg.setLayout(layoutd)

                    def handle_yes_clicked():
                        stop_mediamtx()
                        dlg.close()

                    def handle_no_clicked():
                        start_ffmpeg()
                        dlg.close()

                    yes_button.clicked.connect(handle_no_clicked)
                    no_button.clicked.connect(handle_yes_clicked)
                    dlg.exec()
                else:
                    #check again after 500 milliseconds
                    QtCore.QTimer.singleShot(500, check_mediamtx_process)
        

            #stop mediamtx by finding the process and killing it
            def stop_mediamtx():
                stopped = False
                if os == "Linux":
                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'] == "mediamtx":
                            proc.kill()
                            stopped = True
                    #console.stop()
                    #console.close()
                elif os == "Windows":
                    subprocess.call("taskkill /f /im mediamtx.exe", shell=True)
                    stopped = True
                elif os == "Darwin":
                    subprocess.call("pkill mediamtx", shell=True)
                    stopped = True

                if stopped or not is_mediamtx_running():
                    update_stream_buttons_state(False)

            #stop ffmpeg by finding the process and killing it
            def stop_ffmpeg():
                if os == "Linux":
                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'] == "ffmpeg":
                            proc.terminate()
                elif os == "Windows":
                    subprocess.call("taskkill /f /im ffmpeg.exe", shell=True)
                elif os == "Darwin":
                    subprocess.call("pkill ffmpeg", shell=True)
            

            #stop both mediamtx and ffmpeg when the main window is closed
            def handle_close_event():
                stop_ffmpeg()
                stop_mediamtx()

            quit_button.clicked.connect(lambda: handle_close_event())


        elif os == "Darwin":
            print("Running on macOS")
        else:
            print("Unknown operating system")


        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)



app = QApplication(sys.argv) #creates an instance of the application, which is necessary to run any PySide6 application.
window = MainWindow()
window.show()

app.exec() #starts the event loop, which keeps the application running until the user closes it.
import json
import sys
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QGridLayout, QHBoxLayout, QLineEdit, QMainWindow, QMenu, QPlainTextEdit, QScrollArea, QTableView, QWidget, QPushButton, QLabel, QVBoxLayout, QCheckBox
from PySide6.QtCore import Qt, QProcess
import platform
ostype = platform.system()
import subprocess
import cv2
import socket
from qtpy import QtCore, QtWidgets
from qtpyTerminal import qtpyTerminal
import psutil
from cv2_enumerate_cameras import enumerate_cameras
import os

#table model
class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        if role == Qt.BackgroundRole:
            if index.row() == 0:
                from PySide6.QtGui import QColor
                return QColor("lightgray")
            elif index.row() > 0 and index.column() in [1, 2]:
                from PySide6.QtGui import QColor
                return QColor("lightblue")
        if role == Qt.FontRole:
            from PySide6.QtGui import QFont
            font = QFont()
            if index.row() == 0:
                font.setBold(True)
            return font


    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wxrtsp")
        self.setMinimumSize(900, 600)
        layout = QGridLayout()
        #camera and network settings label
        label1 = QLabel("Camera and Network Settings")
        label1.setStyleSheet("font-weight: bold;")
        layout.addWidget(label1, 0, 0, 1, 6)
        #check operating system
        if ostype == "Windows":
            #===========================================================
            #START OF WINDOWS-SPECIFIC CODE
            #===========================================================
            print("Running on Windows")
            #add label for system os and version
            label2 = QLabel(f"System OS: {ostype} {platform.release()}")
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
            layout.addWidget(show_video_button, 6, 0, 1, 2)
            #use selected camera, framerate, and the resolution to append to a list of settings to be used in the ffmpeg command when starting multiple streams
            addcamera_button = QPushButton("Add Camera to Stream List")
            addcamera_button.setStyleSheet("font-weight: bold; background-color: orange; color: white;")
            layout.addWidget(addcamera_button, 6, 2, 1, 1)

            stream_settings = []
            def add_camera_to_stream_list():
                selected_camera = combo.currentText()
                selected_frame_rate = framerate_combo.currentText()
                selected_resolution = resolution_combo.currentText()
                selected_ip = ""
                if local_ip_checkbox.isChecked():
                    selected_ip = local_ip
                elif public_ip_checkbox.isChecked():
                    selected_ip = localhost_ip
                if selected_camera == "" or selected_frame_rate == "" or selected_resolution == "" or selected_ip == "":
                    dlg = QDialog(self)
                    dlg.setWindowTitle("Info")
                    dlg.setMinimumSize(400, 200)
                    layoutd = QVBoxLayout()
                    label = QLabel("Please select a camera, frame rate, resolution, and IP address before adding to the stream list.")
                    layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                    dlg.setLayout(layoutd)
                    dlg.exec()
                    return
                new_setting = {
                    "camera": selected_camera,
                    "frame_rate": selected_frame_rate,
                    "resolution": selected_resolution,
                    "ip": selected_ip
                }
                if new_setting["camera"] not in [s["camera"] for s in stream_settings]:
                    stream_settings.append(new_setting)
                else:
                    return
                print(f"Added to stream list: Camera: {selected_camera}, Frame Rate: {selected_frame_rate}, Resolution: {selected_resolution}, IP: {selected_ip}")
                toggle_edittextffmpeg()
            addcamera_button.clicked.connect(add_camera_to_stream_list)

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
            layout.addWidget(winlabel4, 5, 0, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)
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
            layout.addWidget(local_ip_checkbox, 5, 1, 1, 1)
            layout.addWidget(public_ip_checkbox, 5, 4, 1, 1)

            #add horizontal line separator
            line2 = QtWidgets.QFrame()
            line2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
            line2.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
            layout.addWidget(line2, 8, 0, 1, 12)

            #show selected camera and selected ip in a label
            winlabel5 = QLabel("Selected Settings:")
            layout.addWidget(winlabel5, 9, 0, 1, 12, alignment=Qt.AlignmentFlag.AlignLeft)
            wlabel6 = QLabel("Camera: ")
            wlabel6.setStyleSheet("font-weight: bold; background-color: lightgray;")
            layout.addWidget(wlabel6, 10, 0, 1, 3)
            wlabel7 = QLabel("IP: ")
            wlabel7.setStyleSheet("background-color: lightgray;")
            layout.addWidget(wlabel7, 10, 3, 1, 3)
            wlabel8 = QLabel("FPS: ")
            wlabel8.setStyleSheet("background-color: lightgray;")
            layout.addWidget(wlabel8, 10, 6, 1, 3)
            wlabel9 = QLabel("Resolution: ")
            wlabel9.setStyleSheet("background-color: lightgray;")
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

            #draw a horizontal line separator
            line3 = QtWidgets.QFrame()
            line3.setFrameShape(QtWidgets.QFrame.Shape.HLine)
            line3.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
            line3.setVisible(len(stream_settings) > 0)
            layout.addWidget(line3, 11, 0, 1, 12)

            #show camera info added to the stream_settings array in scrollable area with a label showing the camera name, frame rate, and resolution for each item in the stream settings list
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_area.setWidget(scroll_content)
            scroll_area.setVisible(len(stream_settings) > 0)
            layout.addWidget(scroll_area, 12, 0, 1, 12)

            stream_settings_table = QTableView()
            #layout.addWidget(stream_settings_table, 
            # 12, 0, 1, 11)

            def update_stream_list():
                scroll_area.setVisible(len(stream_settings) > 0)
                for i in reversed(range(scroll_layout.count())):
                    scroll_layout.itemAt(i).widget().setParent(None)
                tempcamera_data = []
                selected_ip = ""
                if local_ip_checkbox.isChecked():
                    selected_ip = local_ip
                elif public_ip_checkbox.isChecked():
                    selected_ip = localhost_ip

                for idx, stream in enumerate(stream_settings, 1):
                    #label = QLabel(f"{idx}. Camera: {stream['camera']}, Frame Rate: {stream['frame_rate']}, Resolution: {stream['resolution']}")
                    #scroll_area.setStyleSheet("background-color: lightgray;")
                    #scroll_layout.addWidget(label)
                    #data = [[f"Camera: {stream['camera']}"], [f"Frame Rate: {stream['frame_rate']}"], [f"Resolution: {stream['resolution']}"]]

                    tempcamera_data.append([
                        f"Camera: {stream['camera']} Frame Rate: ({stream['frame_rate']} FPS, Resolution: {stream['resolution']})",
                        f"rtsp://{selected_ip}:8554/{stream['camera'].strip().replace(' ', '_')}",
                        f"http://{selected_ip}:8889/{stream['camera'].strip().replace(' ', '_')}"
                    ])

                data = [
                  ["Camera Config", "RTSP URL [Click to Copy]", "Browser URL [Click to Copy]"],
                ] + tempcamera_data
                model = TableModel(data)
                stream_settings_table.setModel(model)
                stream_settings_table.setStyleSheet("QTableView { background-color: lightgray;} QHeaderView::section { background-color: gray; color: white; font-weight: bold; }")
                stream_settings_table.horizontalHeader().setStretchLastSection(False)
                stream_settings_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)  # ResizeMode.Stretch
                stream_settings_table.mousePressEvent = lambda event: on_stream_settings_table_clicked(event, stream_settings_table, tempcamera_data)
                stream_settings_table.setCursor(Qt.CursorShape.PointingHandCursor)


                def on_stream_settings_table_clicked(event, table, data):
                    index = table.indexAt(event.pos())
                    if index.isValid():
                        row = index.row()
                        column = index.column()
                        if column in [1, 2] and row != 0:
                            url = data[row - 1][column]
                            clipboard = QApplication.clipboard()
                            clipboard.setText(url)

                scroll_layout.addWidget(stream_settings_table)

            addcamera_button.clicked.connect(lambda: [add_camera_to_stream_list(), update_stream_list()])

            #start streaming button
            start_streaming_button = QPushButton("Confirm & Start RTSP Stream")
            start_streaming_button.setStyleSheet("font-weight: bold; background-color: green; color: white;")
            layout.addWidget(start_streaming_button, 13, 0, 1, 6)
            start_streaming_button.clicked.connect(lambda: start_mediamtx())
            #quit webcamtortsp button
            quit_button = QPushButton("Stop RTSP Streams")
            quit_button.setStyleSheet("font-weight: bold; background-color: red; color: white;")
            layout.addWidget(quit_button, 13, 6, 1, 6)

            def is_mediamtx_running():
                return any('mediamtx' in proc.info['name'] for proc in psutil.process_iter(['name']))
            
            def update_stream_buttons_state(mediamtx_running):
                start_streaming_button.setEnabled(not mediamtx_running)

            update_stream_buttons_state(is_mediamtx_running())

            #add two terminals to show mediamtx server output and ffmpeg output
            label12 = QLabel("MediaMTX Server Output:")
            layout.addWidget(label12, 14, 0, 1, 6)

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
                        if len(stream_settings) > 0:
                            #start multiple ffmpeg processes for each stream in the stream settings list
                            print("Starting FFmpeg processes for each stream in the stream settings list")
                            start_multiple_ffmpeg_processes()
                        elif len(stream_settings) == 0:
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
                self.p.start("mediamtx.exe", ["mediamtx.yml"])
                #wait for 500 milliseconds to allow mediamtx to start before starting ffmpeg
                QtCore.QTimer.singleShot(500, check_mediamtx_process)

            #testbtn.clicked.connect(start_mediamtx)
            edittext = QPlainTextEdit()
            edittext.setReadOnly(True)
            edittext.setCenterOnScroll(True)
            #edittext.verticalScrollBar().setValue(edittext.verticalScrollBar().maximum())
            layout.addWidget(edittext, 15, 0, 1, 6)

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
            layout.addWidget(label13, 14, 6, 1, 6)

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
                    self.ffmpegp.start("ffmpeg", ["-f", "dshow", "-video_size", selected_resolution, "-framerate", selected_frame_rate, "-i", f"video={selected_camera}", "-c:v", "libx264", "-b:v", "2M", "-preset", "ultrafast", "-tune", "zerolatency", "-fflags", "nobuffer", "-rtsp_transport", "udp", "-analyzeduration", "0", "-probesize", "32", "-flags", "low_delay", "-f", "rtsp", f"rtsp://{selected_ip}:8554/{selected_camera.replace(' ', '_')}"])

            edittextffmpeg = QPlainTextEdit()
            edittextffmpeg.setReadOnly(True)
            #edittextffmpeg.setCenterOnScroll(True)
            edittextffmpeg.verticalScrollBar().setValue(edittextffmpeg.verticalScrollBar().maximum())
            layout.addWidget(edittextffmpeg, 15, 6, 1, 6)

            #show four QplainTextEdit widget inside a QBoxLayout to show the output of the ffmpeg command for each stream added to the stream settings list. The output should show the ffmpeg command being run for each stream and any errors or output from the command. The QPlainTextEdit widgets should only be visible when there are streams in the stream settings list.
            ffmpegbox = QVBoxLayout()
            ffmpegbox_container = QWidget()
            ffmpegbox_container.setLayout(ffmpegbox)
            ffmpegscrollarea = QScrollArea()
            ffmpegscrollarea.setWidget(ffmpegbox_container)
            ffmpegscrollarea.setWidgetResizable(True)
            
            def toggle_edittextffmpeg():
                print("Toggling FFmpeg output visibility")
                edittextffmpeg.setVisible(len(stream_settings) == 0)
                layout.addWidget(ffmpegscrollarea, 15, 6, 1, 6)

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
            
            def start_multiple_ffmpeg_processes():
                print("Starting multiple FFmpeg processes for each stream in the stream settings list")
                for stream in stream_settings:
                    print(f"Starting FFmpeg for Camera: {stream['camera']}, Frame Rate: {stream['frame_rate']}, Resolution: {stream['resolution']}")
                    labelx = QLabel(f"Camera: {stream['camera']}, Frame Rate: {stream['frame_rate']}, Resolution: {stream['resolution']}")
                    labelx.setStyleSheet("font-weight: bold; font-size: 11px;")
                    ffmpegbox.addWidget(labelx)
                    edittext = QPlainTextEdit()
                    edittext.setReadOnly(True)
                    #edittext.setCenterOnScroll(True)
                    edittext.verticalScrollBar().setValue(edittext.verticalScrollBar().maximum())
                    ffmpegbox.addWidget(edittext)
                    selected_ip = ""
                    if local_ip_checkbox.isChecked():
                        selected_ip = local_ip
                    elif public_ip_checkbox.isChecked():
                        selected_ip = localhost_ip
                    p = QProcess()
                    def make_ffmpeg_finished_callback(camera, edittext):
                        def ffmpeg_finished():
                            print(f"FFmpeg process for camera {camera} finished")
                            pmessageffmpeg(f"FFmpeg process for camera {camera} finished")
                        return ffmpeg_finished
                    p.readyReadStandardOutput.connect(lambda p=p, edittext=edittext: handle_multiple_ffmpeg_stdout(p, edittext))
                    p.readyReadStandardError.connect(lambda p=p, edittext=edittext: handle_multiple_ffmpeg_stderr(p, edittext))
                    p.stateChanged.connect(lambda state, p=p, edittext=edittext: handle_multiple_ffmpeg_state(state, p, edittext))
                    p.finished.connect(make_ffmpeg_finished_callback(stream['camera'], edittext))
                    
                    p.start("ffmpeg", ["-f", "dshow", "-video_size", stream['resolution'], "-framerate", stream['frame_rate'], "-i", f"video={stream['camera']}", "-c:v", "libx264", "-b:v", "2M", "-preset", "ultrafast", "-tune", "zerolatency", "-fflags", "nobuffer", "-rtsp_transport", "udp", "-analyzeduration", "0", "-probesize", "32", "-flags", "low_delay", "-f", "rtsp", f"rtsp://{selected_ip}:8554/{stream['camera'].replace(' ', '_')}"])

            def handle_multiple_ffmpeg_stderr(p, edittext):
                error_output = p.readAllStandardError().data().decode()
                pmessageffmpeg(f"FFmpeg Error: {error_output}")
                edittext.appendPlainText(f"FFmpeg Error: {error_output}")

            def handle_multiple_ffmpeg_stdout(p, edittext):
                standard_output = p.readAllStandardOutput().data().decode()
                pmessageffmpeg(f"FFmpeg Output: {standard_output}")
                edittext.appendPlainText(f"FFmpeg Output: {standard_output}")

            def handle_multiple_ffmpeg_state(state, p, edittext):
                states = {
                    QProcess.NotRunning: "Not Running",
                    QProcess.Starting: "Starting",
                    QProcess.Running: "Running"
                }
                pmessageffmpeg(f"FFmpeg process state changed: {states.get(state, 'Unknown State')}")
                edittext.appendPlainText(f"FFmpeg process state changed: {states.get(state, 'Unknown State')}")


            #stop mediamtx by finding the process and killing it
            def stop_mediamtx():
                stopped = False
                if ostype == "Linux":
                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'] == "mediamtx":
                            proc.kill()
                            stopped = True
                    #console.stop()
                    #console.close()
                elif ostype == "Windows":
                    subprocess.call("taskkill /f /im mediamtx.exe", shell=True)
                    stopped = True
                elif ostype == "Darwin":
                    subprocess.call("pkill mediamtx", shell=True)
                    stopped = True

                if stopped or not is_mediamtx_running():
                    update_stream_buttons_state(False)

            #stop ffmpeg by finding the process and killing it
            def stop_ffmpeg():
                if ostype == "Linux":
                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'] == "ffmpeg":
                            proc.terminate()
                elif ostype == "Windows":
                    subprocess.call("taskkill /f /im ffmpeg.exe", shell=True)
                elif ostype == "Darwin":
                    subprocess.call("pkill ffmpeg", shell=True)

            #stop both mediamtx and ffmpeg when the main window is closed
            def handle_close_event():
                print("Closing application, stopping FFmpeg and MediaMTX processes...")
                stop_ffmpeg()
                stop_mediamtx()
                
            quit_button.clicked.connect(lambda: handle_close_event())

            #show rtsp link in a label at the bottom of the window
            selected_camera = combo.currentText() if combo.currentText() else "webcam"
            rtsp_label = QLabel(f"RTSP Stream URL: rtsp://<IP_ADDRESS>:8554/{selected_camera.strip().replace(' ', '_')}")
            rtsp_urls = []
            
            def copy_to_clipboard(url):
                clipboard = QApplication.clipboard()
                clipboard.setText(url)
            
            def update_rtsp_label():
                selected_ip = ""
                if local_ip_checkbox.isChecked():
                    selected_ip = local_ip
                elif public_ip_checkbox.isChecked():
                    selected_ip = localhost_ip
                selected_camera = combo.currentText()

                rtsp_urls.clear()
                if stream_settings and selected_ip:
                    urls = []
                    for camera in stream_settings:
                        if local_ip_checkbox.isChecked():
                            url = f"rtsp://{local_ip}:8554/{camera['camera'].strip().replace(' ', '_')}"
                        elif public_ip_checkbox.isChecked():
                            url = f"rtsp://{localhost_ip}:8554/{camera['camera'].strip().replace(' ', '_')}"
                        urls.append(url)
                        rtsp_urls.append(url)
                    rtsp_label.setText(f"RTSP Stream URLs: {', '.join(urls)} [Click to copy]")
                elif selected_ip and local_ip_checkbox.isChecked():
                    url = f"rtsp://{local_ip}:8554/{selected_camera.strip().replace(' ', '_')}"
                    rtsp_urls.append(url)
                    rtsp_label.setText(f"RTSP Stream URL: {url} [Click to copy]")
                elif selected_ip and public_ip_checkbox.isChecked():
                    url = f"rtsp://{localhost_ip}:8554/{selected_camera.strip().replace(' ', '_')}"
                    rtsp_urls.append(url)
                    rtsp_label.setText(f"RTSP Stream URL: {url} [Click to copy]")
                else:
                    rtsp_label.setText(f"RTSP Stream URL: rtsp://<IP_ADDRESS>:8554/{selected_camera.strip().replace(' ', '_')}")
            
            def on_rtsp_label_clicked():
                if rtsp_urls:
                    for url in rtsp_urls:
                        copy_to_clipboard(url)
            
            rtsp_label.setCursor(Qt.CursorShape.PointingHandCursor)
            rtsp_label.mousePressEvent = lambda event: on_rtsp_label_clicked()
            local_ip_checkbox.stateChanged.connect(update_rtsp_label)
            public_ip_checkbox.stateChanged.connect(update_rtsp_label)
            rtsp_label.setVisible(False)
            layout.addWidget(rtsp_label, 16, 0, 1, 11, alignment=Qt.AlignmentFlag.AlignLeft)

            #show webrtc link in a label at the bottom of the window
            webrtc_label = QLabel(f"Browser Stream URL: http://<IP_ADDRESS>:8889/{selected_camera.strip().replace(' ', '_')}")
            webrtc_urls = []

            def copy_webrtc_to_clipboard(url):
                clipboard = QApplication.clipboard()
                clipboard.setText(url)

            def update_webrtc_label():
                selected_ip = ""
                if local_ip_checkbox.isChecked():
                    selected_ip = local_ip
                elif public_ip_checkbox.isChecked():
                    selected_ip = localhost_ip
                selected_camera = combo.currentText()

                webrtc_urls.clear()
                if stream_settings and selected_ip:
                    urls = []
                    for camera in stream_settings:
                        if local_ip_checkbox.isChecked():
                            url = f"http://{local_ip}:8889/{camera['camera'].strip().replace(' ', '_')}"
                        elif public_ip_checkbox.isChecked():
                            url = f"http://{localhost_ip}:8889/{camera['camera'].strip().replace(' ', '_')}"
                        urls.append(url)
                        webrtc_urls.append(url)
                    webrtc_label.setText(f"Browser Stream URLs: {', '.join(urls)} [Click to copy]")
                elif selected_ip and local_ip_checkbox.isChecked():
                    url = f"http://{local_ip}:8889/{selected_camera.strip().replace(' ', '_')}"
                    webrtc_urls.append(url)
                    webrtc_label.setText(f"Browser Stream URL: {url} [Click to copy]")
                elif selected_ip and public_ip_checkbox.isChecked():
                    url = f"http://{localhost_ip}:8889/{selected_camera.strip().replace(' ', '_')}"
                    webrtc_urls.append(url)
                    webrtc_label.setText(f"Browser Stream URL: {url} [Click to copy]")
                else:
                    webrtc_label.setText(f"Browser Stream URL: http://<IP_ADDRESS>:8889/{selected_camera.strip().replace(' ', '_')}")
            def on_webrtc_label_clicked():
                if webrtc_urls:
                    for url in webrtc_urls:
                        copy_webrtc_to_clipboard(url)
            webrtc_label.setCursor(Qt.CursorShape.PointingHandCursor)
            webrtc_label.mousePressEvent = lambda event: on_webrtc_label_clicked()
            local_ip_checkbox.stateChanged.connect(update_webrtc_label)
            public_ip_checkbox.stateChanged.connect(update_webrtc_label)
            webrtc_label.setVisible(False)
            layout.addWidget(webrtc_label, 17, 0, 1, 11, alignment=Qt.AlignmentFlag.AlignLeft)

            #add reset button to clear the stream settings list and reset all selections
            reset_button = QPushButton("Reset Settings")
            reset_button.setStyleSheet("font-weight: bold; background-color: orange; color: white;")
            layout.addWidget(reset_button, 18, 0, 1, 1)

            def reset_settings():
                combo.setCurrentIndex(0)
                framerate_combo.setCurrentIndex(0)
                resolution_combo.setCurrentIndex(0)
                local_ip_checkbox.setChecked(False)
                public_ip_checkbox.setChecked(False)
                stream_settings.clear()
                update_stream_list()
                #toggle_edittextffmpeg()
                #clear mediamtx and ffmpeg output text boxes
                edittext.clear()
                edittextffmpeg.clear()
                update_rtsp_label()
                update_webrtc_label()
                #reset ffmpegbox by removing all widgets from the layout
                for i in reversed(range(ffmpegbox.count())):
                    ffmpegbox.itemAt(i).widget().setParent(None)
                
                edittextffmpeg.setVisible(True)
                ffmpegbox.addWidget(edittextffmpeg)

            reset_button.clicked.connect(reset_settings)

            #save settings button to save the current stream settings to a json file
            save_settings_button = QPushButton("Save Settings")
            save_settings_button.setStyleSheet("font-weight: bold; background-color: purple; color: white;")
            layout.addWidget(save_settings_button, 18, 1, 1, 1)
            def save_settings():
                settings = {
                    "stream_settings": stream_settings,
                    "selected_ip": local_ip if local_ip_checkbox.isChecked() else localhost_ip if public_ip_checkbox.isChecked() else "",
                    "selected_frame_rate": framerate_combo.currentText(),
                    "selected_resolution": resolution_combo.currentText()
                }

                with open("stream_settings.json", "w") as f:
                    json.dump(settings, f)
                dlg = QDialog(self)
                dlg.setWindowTitle("Settings Saved")
                dlg.setMinimumSize(400, 200)
                layoutd = QVBoxLayout()
                label = QLabel("Stream settings have been saved to stream_settings.json")
                layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                dlg.setLayout(layoutd)
                dlg.exec()


            save_settings_button.clicked.connect(save_settings)

            #on application start, check if stream_settings.json file exists and if it does, load the settings and populate the stream settings list and update the UI accordingly
            def load_settings():
                if os.path.exists("stream_settings.json"):
                    with open("stream_settings.json", "r") as f:
                        settings = json.load(f)
                    loaded_stream_settings = settings.get("stream_settings", [])
                    stream_settings.extend(loaded_stream_settings)
                    print(f"Loaded stream settings: {stream_settings}")
                    selected_camera = stream_settings[0]['camera'] if stream_settings else ""
                    selected_ip = settings.get("selected_ip", "")
                    selected_frame_rate = settings.get("selected_frame_rate", "")
                    selected_resolution = settings.get("selected_resolution", "")

                    if selected_camera in [combo.itemText(i) for i in range(combo.count())]:
                        combo.setCurrentText(selected_camera)

                    if selected_ip == local_ip:
                        local_ip_checkbox.setChecked(True)
                    elif selected_ip == localhost_ip:
                        public_ip_checkbox.setChecked(True)

                    if selected_frame_rate in [framerate_combo.itemText(i) for i in range(framerate_combo.count())]:
                        framerate_combo.setCurrentText(selected_frame_rate)

                    if selected_resolution in [resolution_combo.itemText(i) for i in range(resolution_combo.count())]:
                        resolution_combo.setCurrentText(selected_resolution)

                    update_stream_list()
                    #toggle_edittextffmpeg()
                    update_selected_settings()
                    update_rtsp_label()
                    update_webrtc_label()


            load_settings()


            #===========================================================
            #END OF WINDOWS-SPECIFIC CODE, START OF LINUX-SPECIFIC CODE
            #===========================================================

        elif ostype == "Linux":
            #============================================================
            #START OF LINUX-SPECIFIC CODE
            #============================================================
            print("Running on Linux")
            #add label for system os and version
            label2 = QLabel(f"System OS: {ostype} {platform.release()}")
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

            #===========================================================
            #END OF LINUX-SPECIFIC CODE, START OF MACOS-SPECIFIC CODE
            #===========================================================


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
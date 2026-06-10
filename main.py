import json
import sys
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QGridLayout, QHBoxLayout, QLineEdit, QMainWindow, QPlainTextEdit, QProgressBar, QScrollArea, QTableView, QTextEdit, QWidget, QPushButton, QLabel, QVBoxLayout, QCheckBox
from PySide6.QtCore import QSize, QTimer, Qt, QProcess, QUrl
from PySide6.QtGui import QMovie
from PySide6 import QtGui
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
from pathlib import Path
from PySide6 import QtNetwork
import keyring

#login screen
class LoginDialog(QDialog):
    SERVICE_NAME = "wrtspx_app"
    USERNAME_KEY = "wrtspx_username"
    PASSWORD_KEY = "wrtspx_password"
    TOKEN_KEY = "wrtspx_token"
    
    def __init__(self):
        super().__init__()
        app_icon = QtGui.QIcon("applicationx.png")
        self.setWindowIcon(app_icon)
        self.setWindowTitle("Login")
        self.setMinimumSize(300, 200)
        self.token = None
        layout = QVBoxLayout()
        self.username_input = QLineEdit()
        self.username_input.setMaxLength(50)
        self.username_input.setStyleSheet("font-size: 16px; padding: 5px;")
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setMaxLength(50)
        self.password_input.setStyleSheet("font-size: 16px; padding: 5px;")
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)
        
        self.remember_checkbox = QCheckBox("Remember me")
        layout.addWidget(self.remember_checkbox)
        
        login_button = QPushButton("Login")
        login_button.clicked.connect(lambda: self.accept() if self.handle_login() else None)
        layout.addWidget(login_button)
        self.setLayout(layout)
        self.load_saved_credentials()
        
        # Auto-login if credentials are loaded
        if self.has_saved_session():
            print("Attempting auto-login with saved credentials...")
            QTimer.singleShot(200, lambda: self.accept() if self.handle_login() else None)
        

    def load_saved_credentials(self):
        """Load saved credentials from keyring if available"""
        try:
            username = keyring.get_password(self.SERVICE_NAME, self.USERNAME_KEY)
            password = keyring.get_password(self.SERVICE_NAME, self.PASSWORD_KEY)
            if username and password:
                print("Loaded saved credentials from keyring")
                self.username_input.setText(username)
                self.password_input.setText(password)
                self.remember_checkbox.setChecked(True)
        except Exception as e:
            print(f"Error loading saved credentials: {e}")

    def save_credentials(self):
        """Save credentials to keyring if remember checkbox is checked"""
        print("Saving credentials...")
        if self.remember_checkbox.isChecked():
            try:
                keyring.set_password(self.SERVICE_NAME, self.USERNAME_KEY, self.username_input.text())
                keyring.set_password(self.SERVICE_NAME, self.PASSWORD_KEY, self.password_input.text())
                if self.token:
                    keyring.set_password(self.SERVICE_NAME, self.TOKEN_KEY, self.token)
            except Exception as e:
                print(f"Error saving credentials: {e}")
        else:
            self.clear_saved_credentials()

    def clear_saved_credentials(self):
        """Clear saved credentials from keyring"""
        try:
            keyring.delete_password(self.SERVICE_NAME, self.USERNAME_KEY)
            keyring.delete_password(self.SERVICE_NAME, self.PASSWORD_KEY)
            keyring.delete_password(self.SERVICE_NAME, self.TOKEN_KEY)
        except Exception:
            pass

    @staticmethod
    def has_saved_session():
        """Check if a valid session is saved"""
        try:
            username = keyring.get_password(LoginDialog.SERVICE_NAME, LoginDialog.USERNAME_KEY)
            password = keyring.get_password(LoginDialog.SERVICE_NAME, LoginDialog.PASSWORD_KEY)
            token = keyring.get_password(LoginDialog.SERVICE_NAME, LoginDialog.TOKEN_KEY)
            return username and password and token
        except Exception:
            return False

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        #use username and password to post to api endpoint to check if the username and password are correct and return true or false based on the response
        urlx = QUrl("https://staging-users-api.onlinemanagement.info/api/v1.1/users/login")
        request = QtNetwork.QNetworkRequest(urlx)
        #send post request with username and password as json data
        data = json.dumps({"userName": username, "password": password}).encode('utf-8')
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        manager = QtNetwork.QNetworkAccessManager()
        loop = QtCore.QEventLoop()
        manager.finished.connect(loop.quit)
        manager.post(request, data)
        loop.exec()
        reply = manager.post(request, data)
        loop.exec()
        if reply.error() == QtNetwork.QNetworkReply.NoError:
            response_data = reply.readAll().data().decode()
            #check if the response contains a token and return true if it does, otherwise return false
            if "token" in response_data:
                try:
                    response_json = json.loads(response_data)
                    self.token = response_json.get("data", {}).get("token")
                except Exception as e:
                    print(f"Error parsing response: {e}")
                self.save_credentials()
                return True
            else:
                dlg = QDialog(self)
                dlg.setWindowTitle("Login Failed")
                dlg.setMinimumSize(400, 200)
                layoutd = QVBoxLayout()
                label = QLabel("Login failed. Please check your username and password and try again.")
                layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                dlg.setLayout(layoutd)
                dlg.exec()
                return False
        else:
            dlg = QDialog(self)
            dlg.setWindowTitle("Login Failed")
            dlg.setMinimumSize(400, 200)
            layoutd = QVBoxLayout()
            label = QLabel("An error occurred while trying to log in. Please check your network connection and try again.")
            layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
            dlg.setLayout(layoutd)
            dlg.exec()
            return False
        
    #logout function to clear saved credentials and return to login screen
    def handle_logout(self):
        self.clear_saved_credentials()
        self.token = None
        self.username_input.clear()
        self.password_input.clear()
        self.remember_checkbox.setChecked(False)
        dlg = QDialog(self)
        dlg.setWindowTitle("Logged Out")
        dlg.setMinimumSize(400, 200)
        layoutd = QVBoxLayout()
        label = QLabel("You have been logged out.")
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dlg.accept)
        layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
        layoutd.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)
        dlg.setLayout(layoutd)
        dlg.exec()
        #close the main window and show the login dialog again
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, MainWindow):
                widget.close()
        login_dialog = LoginDialog()
        login_dialog.show()

#table model
class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, header, parent=None, *args):
        super(TableModel, self).__init__()
        self._data = data
        self._header = header
        cols = len(data[0]) if data else 0
        self._backgrounds = [[None] * cols for _ in range(len(data))]  # Initialize background colors for each cell

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        if role == Qt.FontRole:
            from PySide6.QtGui import QFont
            font = QFont()
            if index.row() >= 0:
                font.setBold(True)
            return font
        if role == Qt.BackgroundRole:
            return self._backgrounds[index.row()][index.column()]
        
    def setData(self, index, value, /, role = ...):
        if role == Qt.BackgroundRole:
            self._backgrounds[index.row()][index.column()] = value
            self.dataChanged.emit(index, index, [role])
            return True


    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])
    
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._header[section]
        return super().headerData(section, orientation, role)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wxrtsp")
        self.setMinimumSize(900, 700)
        layout = QGridLayout()
        #camera and network settings label
        label1 = QLabel("Camera and Network Settings")
        label1.setStyleSheet("font-weight: bold;")
        layout.addWidget(label1, 0, 0, 1, 4)
        gif_path = Path("gifx.gif")
        app_icon = QtGui.QIcon("applicationx.png")
        self.setWindowIcon(app_icon)


        #check operating system
        if ostype == "Windows":
            #===========================================================
            #START OF WINDOWS-SPECIFIC CODE
            #===========================================================
            print("Running on Windows")

            #add label for system os and version
            label2 = QLabel(f"System OS: {ostype} {platform.release()}")
            layout.addWidget(label2, 0, 3, 1, 4)

            #add label to show Autogate name
            autogate_main_name = 'N/A'
            global_autogateid = 'undefined'
            autogate_label = QLabel(f"Autogate Name: {autogate_main_name}")
            autogate_label.setStyleSheet("font-weight: bold;")
            layout.addWidget(autogate_label, 0, 6, 1, 4)

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
                    dlg.setMinimumSize(400, 100)
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
                    "ip": selected_ip,
                    "custom_name": selected_camera.strip().replace(' ', '_')
                }
                if new_setting["camera"] not in [s["camera"] for s in stream_settings]:
                    print("Everything is OK")
                    #add a input text field to input a custom name for the stream to be used in the rtsp url instead of the camera name  in a dialog box when adding a camera to the stream list. The custom name should be optional and if not provided, the camera name should be used in the rtsp url
                    customNamedlg = QDialog(self)
                    customNamedlg.setWindowTitle("Custom Stream Name")
                    customNamedlg.setMinimumSize(400, 150)
                    layoutd = QVBoxLayout()
                    label = QLabel("Enter a custom name for the stream URL:")
                    layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                    line_edit = QLineEdit()
                    layoutd.addWidget(line_edit, alignment=Qt.AlignmentFlag.AlignCenter)

                    #add a button to confirm adding the camera to the stream list in the dialog box and only add the camera to the stream list when the button is clicked
                    button = QPushButton("Add to Stream List")
                    layoutd.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)

                    #post selected camera configuration to the server
                    def post_camera_configurations():
                        print("Posting camera configurations to the server...")
                        #camera configuration data to be posted to the server
                        camera_value = "{\n\"CameraType\": \"USB\",\n\"CameraName\": \"" + new_setting["camera"] + "\",\n\"FrameRate\": " + new_setting["frame_rate"] + ",\n\"Resolution\": \"" + new_setting["resolution"] + "\"\n, \"RTSP\": \"rtsp://" + new_setting["ip"] + ":8554/" + new_setting["custom_name"].strip().replace(' ', '_') + "\"\n, \"Selected_IP\": \"" + new_setting["ip"] + "\"\n, \"CustomName\": \"" + new_setting["custom_name"].strip().replace(' ', '_') + "\"\n}"
                        camera_config = json.dumps({
                            "autoGateId": global_autogateid,
                            "type": "Device",
                            "infoSource": "Intercom",
                            "name": "rtspcamera",
                            "value": camera_value
                        }).encode('utf-8')

                        #show gifx.gif while posting the camera configuration to the server
                        gif_label = QLabel()
                        movie = QMovie("gifx.gif")
                        movie.setScaledSize(QSize(20, 20))
                        gif_label.setMovie(movie)
                        movie.start()
                        layoutd.addWidget(gif_label, alignment=Qt.AlignmentFlag.AlignCenter)

                        #check if the camera configuration exist on the autoGateInfo/all/{autoGateId} endpoint and if it does, show a dialog box with the message "Camera configuration already exists" and an "OK" button to close the dialog
                        #fetch autogateinfo from the server using the autoGateId
                        getAutogateInfoURL = QUrl(f"https://staging-users-api.onlinemanagement.info/api/v1.1/autoGateInfo/all/{global_autogateid}?name=rtspcamera")
                        getAutogateInfoRequest = QtNetwork.QNetworkRequest(getAutogateInfoURL)
                        token = keyring.get_password(LoginDialog.SERVICE_NAME, LoginDialog.TOKEN_KEY)
                        if token:
                            getAutogateInfoRequest.setRawHeader(b"Authorization", f"Bearer {token}".encode('utf-8'))
                        getAutogateInfoManager = QtNetwork.QNetworkAccessManager()
                        getAutogateInfoReply = getAutogateInfoManager.get(getAutogateInfoRequest)
                        loop = QtCore.QEventLoop()
                        getAutogateInfoManager.finished.connect(loop.quit)
                        loop.exec()
                        if getAutogateInfoReply.error() == QtNetwork.QNetworkReply.NoError:
                            response_data = getAutogateInfoReply.readAll().data().decode()
                            try:
                                response_json = json.loads(response_data)
                                finderFlag = False
                                for cameraconfig in response_json:
                                    print(f"Checking existing camera configuration: {cameraconfig}")
                                    print(f"Camera configuration value: {cameraconfig.get('value', '')}")
                                    #CameraName
                                    print(f"CameraName in value: {json.loads(cameraconfig.get('value', '{}')).get('CameraName', '')}")
                                    #RTSP
                                    print(f"RTSP in value: {json.loads(cameraconfig.get('value', '{}')).get('RTSP', '')}")
                                    if json.loads(cameraconfig.get('value', '{}')).get('CameraName', '') == new_setting["camera"] and json.loads(cameraconfig.get('value', '{}')).get('RTSP', '') == f"rtsp://{new_setting['ip']}:8554/{new_setting['custom_name'].strip().replace(' ', '_')}":
                                        finderFlag = True
                                        break
                                if finderFlag:
                                    dlg = QDialog(self)
                                    dlg.setWindowTitle("Info")
                                    dlg.setMinimumSize(400, 150)
                                    layoutx = QVBoxLayout()
                                    label = QLabel("Camera configuration already exists.")
                                    layoutx.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                                    ok_button = QPushButton("OK")
                                    ok_button.clicked.connect(dlg.accept)
                                    layoutx.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)
                                    dlg.setLayout(layoutx)
                                    movie.stop()
                                    dlg.exec()
                                    customNamedlg.close()
                                    return
                                #if the camera configuration does not exist, post the camera configuration to the server
                                if finderFlag == False:
                                    print("Camera configuration does not exist. Posting to the server...")
                                    #post request to the server with the camera configuration data
                                    url = QUrl("https://staging-users-api.onlinemanagement.info/api/v1.1/autoGateInfo")
                                    request = QtNetwork.QNetworkRequest(url)
                                    token = keyring.get_password(LoginDialog.SERVICE_NAME, LoginDialog.TOKEN_KEY)
                                    if token:
                                        request.setRawHeader(b"Authorization", f"Bearer {token}".encode('utf-8'))
                                    request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
                                    manager = QtNetwork.QNetworkAccessManager()
                                    loop = QtCore.QEventLoop()
                                    manager.finished.connect(loop.quit)
                                    reply = manager.post(request, camera_config)
                                    loop.exec()

                                    if reply.error() == QtNetwork.QNetworkReply.NoError:
                                        response_data = reply.readAll().data().decode()
                                        print("Camera configuration posted successfully. Server response:", response_data)
                                        customNamedlg.close()
                                        #show dialog box with message "Camera configuration posted successfully" and an "OK" button to close the dialog
                                        success_dlg = QDialog(self)
                                        success_dlg.setWindowTitle("Success")
                                        success_dlg.setMinimumSize(400, 150)
                                        success_layout = QVBoxLayout()
                                        success_label = QLabel("Camera configuration posted successfully.")
                                        success_layout.addWidget(success_label, alignment=Qt.AlignmentFlag.AlignCenter)
                                        ok_button = QPushButton("OK")
                                        ok_button.clicked.connect(success_dlg.accept)
                                        success_layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)
                                        success_dlg.setLayout(success_layout)
                                        movie.stop()
                                        success_dlg.exec()
                                    else:
                                        print("Error posting camera configuration. Server response:", reply.errorString())
                                        #show dialog box with message "Error posting camera configuration" and an "OK" button to close the dialog
                                        error_dlg = QDialog(self)
                                        error_dlg.setWindowTitle("Error")
                                        error_dlg.setMinimumSize(400, 150)
                                        error_layout = QVBoxLayout()
                                        error_label = QLabel("Error posting camera configuration. Please try again.")
                                        error_layout.addWidget(error_label, alignment=Qt.AlignmentFlag.AlignCenter)
                                        ok_button = QPushButton("OK")
                                        ok_button.clicked.connect(error_dlg.accept)
                                        error_layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)
                                        error_dlg.setLayout(error_layout)
                                        movie.stop()
                                        error_dlg.exec()

                            except Exception as e:
                                print(f"Error parsing response: {e}")

                    def confirm_add():
                        custom_name = line_edit.text().strip()
                        if custom_name:
                            new_setting["custom_name"] = custom_name
                        elif not custom_name:
                            new_setting["custom_name"] = selected_camera

                        stream_settings.append(new_setting)
                        post_camera_configurations()

                    button.clicked.connect(confirm_add)
                    customNamedlg.setLayout(layoutd)
                    customNamedlg.exec()


                    #stream_settings.append(new_setting)
                else:
                    return
                print(f"Added to stream list: Camera: {selected_camera}, Frame Rate: {selected_frame_rate}, Resolution: {selected_resolution}, IP: {selected_ip}")
                toggle_edittextffmpeg()
            #addcamera_button.clicked.connect(add_camera_to_stream_list)

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

            def toggle_live_status(row, status):
                current_model = stream_settings_table.model()
                if current_model:
                    index = current_model.index(row, 0)
                    widget = stream_settings_table.indexWidget(index)
                    if widget:
                        live_label = widget.findChild(QLabel)
                        if live_label:
                            live_label.setVisible(status)

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

                for i, stream in enumerate(stream_settings, 1):
                    tempcamera_data.append([
                        f"Camera: {stream['camera']} Frame Rate: ({stream['frame_rate']} FPS, Resolution: {stream['resolution']})",
                        f"rtsp://{selected_ip}:8554/{stream['custom_name'].strip().replace(' ', '_')}",
                        f"http://{selected_ip}:8889/{stream['custom_name'].strip().replace(' ', '_')}"
                    ])

                tableheader = ["Camera Config", "RTSP URL [Click to Copy]", "Browser URL [Click to Copy]"]
                data = tempcamera_data
                model = TableModel(data, tableheader)
                len(stream_settings) > 0 and stream_settings_table.setModel(model)
                stream_settings_table.setStyleSheet("QTableView {background-color: lightgray;} QHeaderView::section { background-color: gray; color: white; font-weight: bold; }")
                stream_settings_table.horizontalHeader().setStretchLastSection(False)
                stream_settings_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)  # ResizeMode.Stretch
                stream_settings_table.setCursor(Qt.CursorShape.PointingHandCursor)

                def add_edit_button(row):
                    widget = QWidget()
                    layout = QHBoxLayout(widget)
                    layout.setContentsMargins(5, 2, 5, 2)
                    edit_button = QPushButton("Edit")
                    edit_button.setIcon(QtGui.QIcon("pencil.png"))
                    edit_button.setStyleSheet("padding: 2px; font-weight: bold; background-color: purple; color: white;")
                    layout.addWidget(edit_button)
                    layout.setAlignment(Qt.AlignmentFlag.AlignRight)
                    stream_settings_table.setIndexWidget(model.index(row, 1), widget)
                    edit_button.clicked.connect(lambda _, r=row: edit_stream_settings(r))

                    #button 2
                    widget2 = QWidget()
                    layout2 = QHBoxLayout(widget2)
                    layout2.setContentsMargins(5, 2, 5, 2)
                    edit_button2 = QPushButton("Edit")
                    edit_button2.setIcon(QtGui.QIcon("pencil.png"))
                    edit_button2.setStyleSheet("padding: 2px; font-weight: bold; background-color: purple; color: white;")
                    layout2.addWidget(edit_button2)
                    layout2.setAlignment(Qt.AlignmentFlag.AlignRight)
                    stream_settings_table.setIndexWidget(model.index(row, 2), widget2)
                    edit_button2.clicked.connect(lambda _, r=row: edit_stream_settings(r))

                #edit buttons
                for i in range(len(stream_settings)):
                    stream_settings_table.setRowHeight(i, 30)
                    add_edit_button(i)

                #mediamtx is running check
                def mediamtx_process():
                    for proc in psutil.process_iter(['name']):
                        if proc.info['name'] and 'mediamtx' in proc.info['name'].lower():
                            return True
                    return False

                #play button func
                def play_button_handler(row):
                    print("Play button clicked")
                    keyring.set_password(LoginDialog.SERVICE_NAME, "confirm_start_mediamtx_status", "False")
                    print(row)
                    #start_ffmpeg()
                    #check if mediamtx is running
                    if mediamtx_process():
                        print("Mediamtx is running")
                        #start another ffmpeg process for the stream settings in the row that the play button is clicked and use the camera configuration in the stream settings to start the ffmpeg process
                        start_ffmpeg(row)
                    else:
                        print("Mediamtx is not running. Please start Mediamtx to stream the video.")
                        start_mediamtx()
                        start_ffmpeg(row)


                #stop button func
                def stop_button_handler(row):
                    print("Stop button clicked")
                    print(row)
                    #check ffmpeg for streams started with the camera configuration in the stream settings
                    for proc in psutil.process_iter(['name', 'cmdline']):
                        if proc.info['name'] and 'ffmpeg' in proc.info['name'].lower():
                            cmdline = ' '.join(proc.info['cmdline']).lower()
                            stream = stream_settings[row]
                            camera_name = stream['camera'].lower()
                            ip_address = stream['selected_ip'].lower()
                            custom_name = stream['custom_name'].strip().replace(' ', '_').lower()
                            if camera_name in cmdline and ip_address in cmdline and custom_name in cmdline:
                                print(f"Terminating ffmpeg process with PID {proc.pid} for stream: {stream}")
                                proc.terminate()
                                
                

                #toggle visibility of the live.gif label when play button is clicked and stop button is clicked
                def toggle_live_status(row, status):
                    index = model.index(row, 0)
                    widget = stream_settings_table.indexWidget(index)
                    if widget:
                        live_label = widget.findChild(QLabel)
                        if live_label:
                            live_label.setVisible(status)

                            

                #delete buttons
                for i in range(len(stream_settings)):
                    widget = QWidget()
                    layout = QHBoxLayout(widget)
                    layout.setContentsMargins(5, 2, 5, 2)

                    #play video
                    play_button = QPushButton("Play")
                    play_button.setIcon(QtGui.QIcon("play.png"))
                    play_button.setStyleSheet("padding: 2px; font-weight: bold; background-color: #1d73bc; color: white;")
                    layout.addWidget(play_button)
                    play_button.clicked.connect(lambda _, r=i: play_button_handler(r))


                    #stop video
                    stop_button = QPushButton("Stop")
                    stop_button.setIcon(QtGui.QIcon("pause.png"))
                    stop_button.setStyleSheet("padding: 2px; font-weight: bold; background-color: #1d73bc; color: white;")
                    layout.addWidget(stop_button)
                    stop_button.clicked.connect(lambda _, r=i: stop_button_handler(r))

                    #delete camera configuration
                    delete_button = QPushButton("Delete")
                    delete_button.setIcon(QtGui.QIcon("delete.png"))
                    delete_button.setStyleSheet("padding: 2px; font-weight: bold; background-color:red ; color: white;")
                    layout.addWidget(delete_button)

                    #live status indicator live.gif
                    live_label = QLabel()
                    live_movie = QMovie("live.gif")
                    live_movie.setScaledSize(QSize(100, 80))
                    live_label.setMovie(live_movie)
                    live_movie.start()
                    layout.addWidget(live_label)
                    live_label.setVisible(False)

                    layout.setAlignment(Qt.AlignmentFlag.AlignRight)
                    stream_settings_table.setIndexWidget(model.index(i, 0), widget)
                    delete_button.clicked.connect(lambda _, r=i: delete_stream_settings(r))

                def edit_stream_settings(row):
                    print(f"Editing stream settings for row {row}")
                    stream = stream_settings[row]
                    dlg = QDialog(self)
                    dlg.setWindowTitle("Edit Stream Settings")
                    dlg.setMinimumSize(400, 200)
                    dlg.setMaximumSize(400, 200)
                    layoutd = QVBoxLayout()
                    label = QLabel("Edit the stream URL name:")
                    layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                    custom_name_line_edit = QLineEdit(stream['custom_name'])
                    layoutd.addWidget(QLabel("Custom Stream Name (optional):"))
                    layoutd.addWidget(custom_name_line_edit)

                    gif_label_visible = False

                    def save_changes():
                        stream['custom_name'] = custom_name_line_edit.text().strip()
                        update_stream_list()
                        gif_label_visible = True
                        gif_label.setVisible(gif_label_visible)
                        save_button.setEnabled(False)
                        #update the camera configuration on the server with the new custom name
                        new_camera_value ="{\n\"CameraType\": \"USB\",\n\"CameraName\": \"" + stream["camera"] + "\", \n\"FrameRate\": " + stream["frame_rate"] + ",\n\"Resolution\": \"" + stream["resolution"] + "\"\n, \"RTSP\": \"rtsp://" + stream["selected_ip"] + ":8554/" + stream["custom_name"].strip().replace(' ', '_') + "\"\n, \"Selected_IP\": \"" + stream["selected_ip"] + "\"\n, \"CustomName\": \"" + stream["custom_name"].strip().replace(' ', '_') + "\"\n}"
                        temp_camera_config = json.dumps({
                            "value": new_camera_value
                        }).encode('utf-8')

                        url = QUrl(f"https://staging-users-api.onlinemanagement.info/api/v1.1/autoGateInfo/{stream['autogateinfoid']}")
                        request = QtNetwork.QNetworkRequest(url)
                        token = keyring.get_password(LoginDialog.SERVICE_NAME, LoginDialog.TOKEN_KEY)
                        if token:
                            request.setRawHeader(b"Authorization", f"Bearer {token}".encode('utf-8'))
                        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
                        manager = QtNetwork.QNetworkAccessManager()
                        loop = QtCore.QEventLoop()
                        manager.finished.connect(loop.quit)
                        reply = manager.post(request, temp_camera_config)
                        loop.exec()

                        if reply.error() == QtNetwork.QNetworkReply.NoError:
                            response_data = reply.readAll().data().decode()
                            gif_label_visible = False
                            gif_label.setVisible(gif_label_visible)
                            save_button.setEnabled(True)
                            dlg.close()
                            #show dialog box with message "Camera configuration updated successfully" and an "OK" button to close the dialog
                            success_dlg = QDialog(self)
                            success_dlg.setWindowTitle("Success")
                            success_dlg.setMinimumSize(400, 150)
                            success_layout = QVBoxLayout()
                            success_label = QLabel("Camera configuration updated successfully.")
                            success_layout.addWidget(success_label, alignment=Qt.AlignmentFlag.AlignCenter)
                            ok_button = QPushButton("OK")
                            ok_button.clicked.connect(success_dlg.accept)
                            success_layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)
                            success_dlg.setLayout(success_layout)
                            success_dlg.exec()

                        else:
                            error_message = reply.errorString()
                            print("Failed to update camera configuration. Error:", error_message)
                            gif_label_visible = False
                            gif_label.setVisible(gif_label_visible)
                            save_button.setEnabled(True)
                            dlg.close()
                            #show dialog box with message "Failed to update camera configuration" and an "OK" button to close the dialog
                            error_dlg = QDialog(self)
                            error_dlg.setWindowTitle("Error")
                            error_dlg.setMinimumSize(400, 150)
                            error_layout = QVBoxLayout()
                            error_label = QLabel("Failed to update camera configuration.")
                            error_layout.addWidget(error_label, alignment=Qt.AlignmentFlag.AlignCenter)
                            ok_button = QPushButton("OK")
                            ok_button.clicked.connect(error_dlg.accept)
                            error_layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)
                            error_dlg.setLayout(error_layout)
                            error_dlg.exec()

                    save_button = QPushButton("Save Changes")
                    save_button.setStyleSheet("font-weight: bold; background-color: green; color: white;")
                    save_button.clicked.connect(save_changes)
                    layoutd.addWidget(save_button, alignment=Qt.AlignmentFlag.AlignCenter)
                    #add gifx.gif to the dialog and show it while saving changes to the server
                    gif_label = QLabel()
                    movie = QMovie("gifx.gif")
                    gif_label.setMovie(movie)
                    movie.start()
                    movie.setScaledSize(QSize(20, 20))
                    layoutd.addWidget(gif_label, alignment=Qt.AlignmentFlag.AlignCenter)
                    gif_label.setVisible(gif_label_visible)
                    dlg.setLayout(layoutd)
                    dlg.exec()

                def delete_stream_settings(row):
                    print(f"Deleting stream settings for row {row}")
                    #show a confirmation dialog box before deleting the stream settings with the message "Are you sure you want to delete this stream configuration?" and options "Yes" and "No"
                    dlg = QDialog(self)
                    dlg.setWindowTitle("Confirm Delete")
                    dlg.setMinimumSize(400, 150)
                    dlg.setMaximumSize(400, 150)
                    layoutd = QVBoxLayout()
                    label = QLabel("Are you sure you want to delete this stream configuration?")
                    layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                    button_layout = QHBoxLayout()
                    yes_button = QPushButton("Yes")
                    no_button = QPushButton("No")
                    button_layout.addWidget(yes_button)
                    button_layout.addWidget(no_button)
                    layoutd.addLayout(button_layout)
                    dlg.setLayout(layoutd)
                    #add gifx.gif to the dialog and show it while deleting the camera configuration from the server
                    gif_label = QLabel()
                    movie = QMovie("gifx.gif")
                    gif_label.setMovie(movie)
                    movie.start()
                    movie.setScaledSize(QSize(20, 20))
                    layoutd.addWidget(gif_label, alignment=Qt.AlignmentFlag.AlignCenter)
                    gif_label.setVisible(False)


                    def handle_yes():
                        #delete the camera configuration from the server
                        stream = stream_settings[row]
                        gif_label.setVisible(True)
                        url = QUrl(f"https://staging-users-api.onlinemanagement.info/api/v1.1/autoGateInfo/{stream['autogateinfoid']}")
                        request = QtNetwork.QNetworkRequest(url)
                        token = keyring.get_password(LoginDialog.SERVICE_NAME, LoginDialog.TOKEN_KEY)
                        if token:
                            request.setRawHeader(b"Authorization", f"Bearer {token}".encode('utf-8'))
                        manager = QtNetwork.QNetworkAccessManager()
                        loop = QtCore.QEventLoop()
                        manager.finished.connect(loop.quit)
                        reply = manager.deleteResource(request)
                        loop.exec()

                        if reply.error() == QtNetwork.QNetworkReply.NoError:
                            print("Camera configuration deleted successfully.")
                            gif_label.setVisible(False)
                            dlg.close()
                            #show dialog box with message "Camera configuration deleted successfully" and an "OK" button to close the dialog
                            success_dlg = QDialog(self)
                            success_dlg.setWindowTitle("Success")
                            success_dlg.setMinimumSize(400, 150)
                            success_layout = QVBoxLayout()
                            success_label = QLabel("Camera configuration deleted successfully.")
                            success_layout.addWidget(success_label, alignment=Qt.AlignmentFlag.AlignCenter)
                            ok_button = QPushButton("OK")
                            ok_button.clicked.connect(success_dlg.accept)
                            success_layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)
                            success_dlg.setLayout(success_layout)
                            success_dlg.exec()
                            stream_settings.pop(row)
                            update_stream_list()
                        else:
                            error_message = reply.errorString()
                            print("Failed to delete camera configuration. Error:", error_message)
                            gif_label.setVisible(False)
                            dlg.close()
                            #show dialog box with message "Failed to delete camera configuration" and an "OK" button to close the dialog
                            error_dlg = QDialog(self)
                            error_dlg.setWindowTitle("Error")
                            error_dlg.setMinimumSize(400, 150)
                            error_layout = QVBoxLayout()
                            error_label = QLabel("Failed to delete camera configuration.")
                            error_layout.addWidget(error_label, alignment=Qt.AlignmentFlag.AlignCenter)
                            ok_button = QPushButton("OK")
                            ok_button.clicked.connect(error_dlg.accept)
                            error_layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)
                            error_dlg.setLayout(error_layout)
                            error_dlg.exec()

                    button_layout.itemAt(0).widget().clicked.connect(handle_yes)
                    button_layout.itemAt(1).widget().clicked.connect(dlg.close)
                    dlg.exec()
                    


                def on_stream_settings_table_clicked(index):
                    if index.isValid():
                        row = index.row()
                        column = index.column()
                        if column in [1, 2]:
                            url = tempcamera_data[row][column]
                            clipboard = QApplication.clipboard()
                            clipboard.setText(url)
                            #change background color of the cell to green for 1 second to indicate the url has been copied
                            model.setData(model.index(row, column), QtGui.QColor("lightblue"), role=Qt.BackgroundRole)
                            QTimer.singleShot(1000, lambda: model.setData(model.index(row, column), QtGui.QColor("lightgray"), role=Qt.BackgroundRole))

                stream_settings_table.clicked.connect(on_stream_settings_table_clicked)

                scroll_layout.addWidget(stream_settings_table)

            addcamera_button.clicked.connect(lambda: [add_camera_to_stream_list(), update_stream_list()])

            #start streaming button
            start_streaming_button = QPushButton("Confirm & Start RTSP Stream")
            start_streaming_button.setStyleSheet("font-weight: bold; background-color: green; color: white;")
            layout.addWidget(start_streaming_button, 13, 0, 1, 6)
            print("Initial Start Streaming Button Status: ", keyring.get_password(LoginDialog.SERVICE_NAME, "confirm_start_mediamtx_status"))
            def confirm_start_button_status():
                keyring.set_password(LoginDialog.SERVICE_NAME, "confirm_start_mediamtx_status", "True")


            start_streaming_button.clicked.connect(lambda: start_mediamtx())
            start_streaming_button.clicked.connect(lambda: confirm_start_button_status())
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
                    dlg.setMinimumSize(400, 100)
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
                if keyring.get_password(LoginDialog.SERVICE_NAME, "automate_status") == "False":
                    if keyring.get_password(LoginDialog.SERVICE_NAME, "confirm_start_mediamtx_status") == "True":
                        QtCore.QTimer.singleShot(500, check_mediamtx_process)

            edittext = QPlainTextEdit()
            edittext.setReadOnly(True)
            edittext.setCenterOnScroll(True)
            edittext.setStyleSheet("background-color: black; color: white; font-family: Consolas, monospace;")
            edittext.verticalScrollBar().setValue(edittext.verticalScrollBar().maximum())
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

            edittextffmpeg = QPlainTextEdit()
            edittextffmpeg.setReadOnly(True)
            #edittextffmpeg.setCenterOnScroll(True)
            edittextffmpeg.setStyleSheet("background-color: black; color: white; font-family: Consolas, monospace;")
            edittextffmpeg.verticalScrollBar().setValue(edittextffmpeg.verticalScrollBar().maximum())
            layout.addWidget(edittextffmpeg, 15, 6, 1, 6)

            #show four QplainTextEdit widget inside a QBoxLayout to show the output of the ffmpeg command for each stream added to the stream settings list. The output should show the ffmpeg command being run for each stream and any errors or output from the command. The QPlainTextEdit widgets should only be visible when there are streams in the stream settings list.
            ffmpegbox = QVBoxLayout()
            ffmpegbox_container = QWidget()
            ffmpegbox_container.setLayout(ffmpegbox)
            #ffmpegbox_container.setStyleSheet("background-color: lightgray; border: 1px solid black;")
            ffmpegscrollarea = QScrollArea()
            ffmpegscrollarea.setWidget(ffmpegbox_container)
            ffmpegscrollarea.setWidgetResizable(True)

            def start_ffmpeg(row):
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
                custom_name = stream_settings[-1]["custom_name"] if stream_settings else selected_camera.strip().replace(' ', '_')

                print("Custom Name for Stream: ", custom_name)
                print(f"Selected Camera: {device_path}")
                print(f"Selected IP: {selected_ip}")
                print(f"Selected Frame Rate: {selected_frame_rate}")
                print(f"Selected Resolution: {selected_resolution}")
                #print(stream_settings)

                if selected_camera == "" or selected_ip == "" or selected_frame_rate == "" or selected_resolution == "":
                    dlg = QDialog(self)
                    dlg.setWindowTitle("Info")
                    dlg.setMinimumSize(400, 100)
                    layoutd = QVBoxLayout()
                    label = QLabel("Please select a camera, frame rate, and resolution before starting the RTSP stream.")
                    layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                    dlg.setLayout(layoutd)
                    dlg.exec()
                    return
                elif selected_camera and selected_ip and selected_frame_rate and selected_resolution:
                    print("Starting FFmpeg process")
                    print(stream_settings[row])
                    print(keyring.get_password(LoginDialog.SERVICE_NAME, "confirm_start_mediamtx_status"))
                    if(keyring.get_password(LoginDialog.SERVICE_NAME, "confirm_start_mediamtx_status") != "True"):
                        print("Start individual FFmpeg process without starting MediaMTX since the confirm start mediamtx status is not True")
                        ffmpegbox.addWidget(edittextffmpeg)
                        edittextffmpeg.setVisible(True)

                        ffmpegp = QProcess()
                        pmessageffmpeg("Starting FFmpeg process")
                        def make_ffmpeg_finished_callback(row):
                             def ffmpeg_finished():
                                print(f"FFmpeg process for row {row} finished")
                                pmessageffmpeg(f"FFmpeg process for row {row} finished")
                             return ffmpeg_finished
                        ffmpeg_finished = make_ffmpeg_finished_callback(row)
                        ffmpegp.readyReadStandardOutput.connect(lambda: handle_ffmpeg_stdout(ffmpegp))
                        ffmpegp.readyReadStandardError.connect(lambda: handle_ffmpeg_stderr(ffmpegp))
                        ffmpegp.stateChanged.connect(lambda state: handle_ffmpeg_state(state, row))
                        ffmpegp.finished.connect(ffmpeg_finished)
                        ffmpegp.start("ffmpeg", ["-f", "dshow", "-video_size", stream_settings[row]["resolution"], "-framerate", stream_settings[row]["frame_rate"], "-i", f"video={stream_settings[row]['camera']}", "-c:v", "libx264", "-b:v", "2M", "-preset", "ultrafast", "-tune", "zerolatency", "-fflags", "nobuffer", "-rtsp_transport", "udp", "-analyzeduration", "0", "-probesize", "32", "-flags", "low_delay", "-f", "rtsp", f"rtsp://{stream_settings[row]['selected_ip']}:8554/{stream_settings[row]['custom_name'].replace(' ', '_')}"])

                    else:
                        print("Start FFmpeg process and MediaMTX since the confirm start mediamtx status is True")

                        #add edittextffmpeg to ffmpegbox layout and make it visible
                        ffmpegbox.addWidget(edittextffmpeg)
                        edittextffmpeg.setVisible(True)

                        ffmpegp = QProcess()
                        pmessageffmpeg("Starting FFmpeg process")
                        def make_ffmpeg_finished_callback(row):
                             def ffmpeg_finished():
                                print(f"FFmpeg process for row {row} finished")
                                pmessageffmpeg(f"FFmpeg process for row {row} finished")
                             return ffmpeg_finished
                        ffmpeg_finished = make_ffmpeg_finished_callback(row)
                        ffmpegp.readyReadStandardOutput.connect(lambda: handle_ffmpeg_stdout(ffmpegp))
                        ffmpegp.readyReadStandardError.connect(lambda: handle_ffmpeg_stderr(ffmpegp))
                        ffmpegp.stateChanged.connect(lambda state: handle_ffmpeg_state(state, row))
                        ffmpegp.finished.connect(ffmpeg_finished)
                        ffmpegp.start("ffmpeg", ["-f", "dshow", "-video_size", selected_resolution, "-framerate", selected_frame_rate, "-i", f"video={selected_camera}", "-c:v", "libx264", "-b:v", "2M", "-preset", "ultrafast", "-tune", "zerolatency", "-fflags", "nobuffer", "-rtsp_transport", "udp", "-analyzeduration", "0", "-probesize", "32", "-flags", "low_delay", "-f", "rtsp", f"rtsp://{selected_ip}:8554/{custom_name.replace(' ', '_')}"])
            
            def toggle_edittextffmpeg():
                print("Toggling FFmpeg output visibility")
                print(len(stream_settings))
                #edittextffmpeg.setVisible(len(stream_settings) > 0)
                #edittextffmpeg.setVisible(False)
                layout.addWidget(ffmpegscrollarea, 15, 6, 1, 6)

            def pmessageffmpeg(msg):
                edittextffmpeg.appendPlainText(msg)

            def handle_ffmpeg_stderr(ffmpegp):
                if ffmpegp:
                    error_output = ffmpegp.readAllStandardError().data().decode()
                    pmessageffmpeg(f"FFmpeg Error: {error_output}")

            def handle_ffmpeg_stdout(ffmpegp):
                if ffmpegp:
                    standard_output = ffmpegp.readAllStandardOutput().data().decode()
                    pmessageffmpeg(f"FFmpeg Output: {standard_output}")

            def handle_ffmpeg_state(state, row):
                states = {
                    QProcess.NotRunning: "Not Running",
                    QProcess.Starting: "Starting",
                    QProcess.Running: "Running"
                }

                pmessageffmpeg(f"FFmpeg process state changed: {states.get(state, 'Unknown State')}")

                if state == QProcess.Running:
                    if(keyring.get_password(LoginDialog.SERVICE_NAME, "confirm_start_mediamtx_status") != "True"):
                        toggle_live_status(row, True)
                    else:
                        toggle_live_status(0, True)
                else:
                    if(keyring.get_password(LoginDialog.SERVICE_NAME, "confirm_start_mediamtx_status") != "True"):
                        toggle_live_status(row, False)
                    else:
                        toggle_live_status(0, False)
            
            def start_multiple_ffmpeg_processes():
                print("Starting multiple FFmpeg processes for each stream in the stream settings list")
                for stream in stream_settings:
                    #print(f"Starting FFmpeg for Camera: {stream['camera']}, Frame Rate: {stream['frame_rate']}, Resolution: {stream['resolution']}")
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
                    
                    
                    p.start("ffmpeg", ["-f", "dshow", "-video_size", stream['resolution'], "-framerate", stream['frame_rate'], "-i", f"video={stream['camera']}", "-c:v", "libx264", "-b:v", "2M", "-preset", "ultrafast", "-tune", "zerolatency", "-fflags", "nobuffer", "-rtsp_transport", "udp", "-analyzeduration", "0", "-probesize", "32", "-flags", "low_delay", "-f", "rtsp", f"rtsp://{selected_ip}:8554/{stream['custom_name'].replace(' ', '_')}"])

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
                #if status is running, call toggle_live_status for the corresponding camera to show the live.gif label
                if state == QProcess.Running:
                    #find the camera name from the edittext widget above the current edittext widget and toggle the live status for that camera
                    index = ffmpegbox.indexOf(edittext)
                    if index != -1:
                        camera_label = ffmpegbox.itemAt(index - 1).widget()
                        camera_name = camera_label.text().split(",")[0].replace("Camera: ", "").strip()
                        print("Camera name for toggling live status: ", camera_name)
                        for stream in stream_settings:
                            if stream['camera'] == camera_name:
                                print("Toggling live status for camera: ", camera_name)
                                toggle_live_status(stream_settings.index(stream), True)
                #if status is not running, call toggle_live_status for the corresponding camera to hide the live.gif label
                if state != QProcess.Running:
                    index = ffmpegbox.indexOf(edittext)
                    if index != -1:
                        camera_label = ffmpegbox.itemAt(index - 1).widget()
                        camera_name = camera_label.text().split(",")[0].replace("Camera: ", "").strip()
                        print("Camera name for toggling live status: ", camera_name)
                        for stream in stream_settings:
                            if stream['camera'] == camera_name:
                                print("Toggling live status for camera: ", camera_name)
                                toggle_live_status(stream_settings.index(stream), False)





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
                print("Resetting settings and clearing stream settings list")
                combo.setCurrentIndex(0)
                framerate_combo.setCurrentIndex(0)
                resolution_combo.setCurrentIndex(0)
                local_ip_checkbox.setChecked(False)
                public_ip_checkbox.setChecked(False)
                toggle_edittextffmpeg()
                #clear mediamtx and ffmpeg output text boxes
                edittext.clear()
                edittextffmpeg.clear()
                update_rtsp_label()
                update_webrtc_label()
                #reset stream settings list
                stream_settings.clear()
                update_stream_list()
                
                #reset ffmpegbox by removing all widgets from the layout
                for i in reversed(range(ffmpegbox.count())):
                    ffmpegbox.itemAt(i).widget().setParent(None)
                
                edittextffmpeg.setVisible(True)
                ffmpegbox.addWidget(edittextffmpeg)

                #fetch stream_settings file and reset settings to the values in the file if it exist
                if settings_file.exists():
                    settings = {
                        "stream_settings": stream_settings,
                        "selected_ip": "",
                        "selected_frame_rate": "",
                        "selected_resolution": ""
                    }
                    with open(settings_file, "w") as f:
                        json.dump(settings, f)


            reset_button.clicked.connect(reset_settings)

            #create a path to C:\Users\<Username>\AppData\Roaming\wrtspx and save the stream_settings.json file there. If the directory does not exist, create it.
            appdata_path = Path(os.getenv("APPDATA")) / "wrtspx"
            appdata_path.mkdir(parents=True, exist_ok=True)
            settings_file = appdata_path / "stream_settings.json"

            #save settings button to save the current stream settings to a json file
            save_settings_button = QPushButton("Save Settings")
            save_settings_button.setStyleSheet("font-weight: bold; background-color: purple; color: white;")
            save_settings_button.setVisible(False)
            layout.addWidget(save_settings_button, 18, 1, 1, 1)
            def save_settings():
                settings = {
                    "stream_settings": stream_settings,
                    "selected_ip": local_ip if local_ip_checkbox.isChecked() else localhost_ip if public_ip_checkbox.isChecked() else "",
                    "selected_frame_rate": framerate_combo.currentText(),
                    "selected_resolution": resolution_combo.currentText()
                }

                with open(settings_file, "w") as f:
                    json.dump(settings, f)
                dlg = QDialog(self)
                dlg.setWindowTitle("Settings Saved")
                dlg.setMinimumSize(400, 70)
                layoutd = QVBoxLayout()
                label = QLabel("Stream settings have been saved to stream_settings.json")
                layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                dlg.setLayout(layoutd)
                dlg.exec()


            save_settings_button.clicked.connect(save_settings)

            #on application start, check if stream_settings.json file exists and if it does, load the settings and populate the stream settings list and update the UI accordingly
            def load_settings():
                if settings_file.exists():
                    with open(settings_file, "r") as f:
                        settings = json.load(f)
                    loaded_stream_settings = settings.get("stream_settings", [])
                    stream_settings.extend(loaded_stream_settings)
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
                    update_selected_settings()
                    update_rtsp_label()
                    update_webrtc_label()
                    edittextffmpeg.setVisible(len(stream_settings) == 0)
                    layout.addWidget(ffmpegscrollarea, 15, 6, 1, 6)

                #load autogate configuration from autogate_config.json file in the appdata directory if it exists and update the autogate label in the main window
                if appdata_path.exists():
                    autogate_config_file = appdata_path / "autogate_config.json"
                    if autogate_config_file.exists():
                        with open(autogate_config_file, "r") as f:
                            autogate_config = json.load(f)
                        autogate_name = autogate_config.get("gateName", "N/A")
                        autogate_id = autogate_config.get("id", "N/A")
                        nonlocal autogate_main_name
                        autogate_main_name = autogate_name
                        autogate_label.setText(f"Autogate Name: {autogate_main_name}")
                        #update global_autogateid variable with the autogate id from the config file
                        nonlocal global_autogateid
                        global_autogateid = autogate_id

                #fetch autogateinfo by the autogate id from the autogate configuration file if it exists and print the response in the console
                if global_autogateid:
                        try:
                            urlx = QUrl(f"https://staging-users-api.onlinemanagement.info/api/v1.1/autoGateInfo/all/{global_autogateid}?name=rtspcamera")
                            request = QtNetwork.QNetworkRequest(urlx)
                            token = keyring.get_password(LoginDialog.SERVICE_NAME, LoginDialog.TOKEN_KEY)
                            if token:
                                request.setRawHeader(b"Authorization", f"Bearer {token}".encode())
                            manager = QtNetwork.QNetworkAccessManager(self)
                            reply = manager.get(request)
                            def handle_reply():
                                if reply.error() == QtNetwork.QNetworkReply.NoError:
                                    response = reply.readAll().data().decode()
                                    try:
                                        response_json = json.loads(response)
                                        wait_load_data = False
                                        for cameraconfig in response_json:
                                            #print("AutoGate Info Response: ", cameraconfig)
                                            #print("id", cameraconfig.get('id', 'N/A'))
                                            #x = {'id': '338C3F17-C5BD-40A2-B93C-012CF0B51F4C', 'autoGateId': '56EA9E50-2AA9-43B2-8773-E74889CD4C6E', 'type': 'Device', 'infoSource': 'Intercom', 'info': None, 'name': 'rtspcamera', 'value': '{\n"CameraType": "USB",\n"CameraName": "GENERAL WEBCAM",\n"FrameRate": 30,\n"Resolution": "1280x720"\n, "RTSP": "rtsp://127.0.0.1:8554/intercom"\n}', 'extra': None, 'file': None, 'deviceShortCode': None}
                                            #CameraName
                                            cameraconfigname = json.loads(cameraconfig.get('value', '{}')).get('CameraName', 'N/A')
                                            #print(f"CamerName in value : {cameraconfigname}")

                                            selected_camera = cameraconfigname
                                            selected_ip = json.loads(cameraconfig.get('value', '{}')).get('Selected_IP', '')
                                            selected_frame_rate = str(json.loads(cameraconfig.get('value', '{}')).get('FrameRate', ''))
                                            #selected_frame_rate = '30'
                                            selected_resolution = json.loads(cameraconfig.get('value', '{}')).get('Resolution', '')

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

                                            #use response to populate the stream settings list with a dictionary that has the keys "camera", "frame_rate", "resolution", and "custom_name" where the values are taken from the response
                                            stream_settings.append({
                                                "camera": selected_camera,
                                                "frame_rate": selected_frame_rate,
                                                "resolution": selected_resolution,
                                                "custom_name": json.loads(cameraconfig.get('value', '{}')).get('CustomName', ''),
                                                "selected_ip": selected_ip,
                                                "autogateinfoid": cameraconfig.get('id', '')
                                            })
                                            #print("Stream settings list after loading from autogate info: ", stream_settings)
                                            update_stream_list()
                                            update_selected_settings()
                                            update_rtsp_label()
                                            update_webrtc_label()
                                            #edittextffmpeg.setVisible(len(stream_settings) == 0)
                                            wait_load_data = True
                                            toggle_edittextffmpeg()

                                        if wait_load_data == True:
                                            #print("DONE loading AutoGate info response: ", response_json)
                                            #autostart mediamtx and ffmpeg if there are stream settings loaded from the autogate info
                                            if stream_settings and keyring.get_password(LoginDialog.SERVICE_NAME, "automate_status") == "True":
                                                start_mediamtx()
                                                start_multiple_ffmpeg_processes()


                                    except json.JSONDecodeError:
                                        print("AutoGate Info Response: ", response)
                                    

                                else:
                                    error_message = reply.errorString()
                                    print("Error fetching AutoGate info: ", error_message)
    
                            reply.finished.connect(handle_reply)
    
                        except Exception as e:
                            print("Exception occurred while fetching AutoGate info: ", str(e))

            load_settings()

            #add a logout button that clears the saved credentials and returns to the login screen
            logout_button = QPushButton("Logout")
            logout_button.setStyleSheet("font-weight: bold; background-color: red; color: white;")
            layout.addWidget(logout_button, 18, 2, 1, 1)
            def logout():
                print("Logging out and clearing saved credentials...")
                #call handle_logout function on the LoginDialog class
                login_dialog = LoginDialog()
                login_dialog.handle_logout()

            logout_button.clicked.connect(logout)

            #configure autogate
            autogate_button = QPushButton("Configure AutoGate")
            autogate_button.setStyleSheet("font-weight: bold; background-color: teal; color: white;")
            layout.addWidget(autogate_button, 18, 3, 1, 1)

            def configure_autogate():
                dlg = QDialog(self)
                dlg.setWindowTitle("AutoGate Configuration")
                dlg.setMinimumSize(400, 200)
                layoutd = QVBoxLayout()
                label = QLabel("Enter IntercomShortCode to fetch Autogate configuration from the server")
                layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                shortcode_line_edit = QLineEdit()
                layoutd.addWidget(shortcode_line_edit, alignment=Qt.AlignmentFlag.AlignCenter)
                fetch_button = QPushButton("Fetch Configuration")
                layoutd.addWidget(fetch_button, alignment=Qt.AlignmentFlag.AlignCenter)

                #define function to handle fetching autogate configuration using the entered intercom shortcode
                def handle_autogate_configuration():
                    print("Handling AutoGate configuration...")
                    print("Entered Intercom Shortcode: ", shortcode_line_edit.text())
                    #use the entered shortcode to fetch autogate configuration from the server using a GET request to the endpoint 'https://staging-users-api.onlinemanagement.info/api/v1.1/autoGate?intercomShortCode={shortcode}' 
                    try:
                        urlx = QUrl(f"https://staging-users-api.onlinemanagement.info/api/v1.1/autoGate?intercomShortCode={shortcode_line_edit.text()}")
                        request = QtNetwork.QNetworkRequest(urlx)
                        token = keyring.get_password(LoginDialog.SERVICE_NAME, LoginDialog.TOKEN_KEY)
                        if token:
                            request.setRawHeader(b"Authorization", f"Bearer {token}".encode())
                        manager = QtNetwork.QNetworkAccessManager(self)
                        reply = manager.get(request)
                        def handle_reply():
                            if reply.error() == QtNetwork.QNetworkReply.NoError:
                                response = reply.readAll().data().decode()
                                #close dlg
                                dlg.close()
                                dlg_response = QDialog(self)
                                dlg_response.setWindowTitle("AutoGate Configuration Response")
                                dlg_response.setMinimumSize(400, 200)
                                layout_response = QVBoxLayout()
                                label_response = QLabel(f"AutoGate Configuration Response")
                                #show autogate name and the autogateid from response in a message box
                                try:
                                    response_json = json.loads(response)
                                    autogate_name = response_json.get("data", {})
                                    autogate_namex = autogate_name[0].get("gateName", "N/A")
                                    autogate_id = autogate_name[0].get("id", "N/A")
                                    label_response.setText(f"AutoGate Name: {autogate_namex}\nAutoGate ID: {autogate_id}")
                                    #add save button autogate name and id to a json file in the appdata directory
                                    save_button = QPushButton("Save AutoGate Configuration")
                                    layout_response.addWidget(save_button, alignment=Qt.AlignmentFlag.AlignCenter)
                                    def save_autogate_configuration():
                                        autogate_config = {
                                            "gateName": autogate_namex,
                                            "id": autogate_id
                                        }
                                        autogate_config_file = appdata_path / "autogate_config.json"
                                        with open(autogate_config_file, "w") as f:
                                            json.dump(autogate_config, f)
                                        dlg_saved = QDialog(self)
                                        dlg_saved.setWindowTitle("Saved")
                                        dlg_saved.setMinimumSize(400, 100)
                                        layout_saved = QVBoxLayout()
                                        label_saved = QLabel("AutoGate configuration saved successfully.")
                                        layout_saved.addWidget(label_saved, alignment=Qt.AlignmentFlag.AlignCenter)
                                        dlg_saved.setLayout(layout_saved)
                                        dlg_saved.exec()
                                        #update autogate_main_name variable and autogate label in the main window
                                        nonlocal autogate_main_name
                                        autogate_main_name = autogate_namex
                                        autogate_label.setText(f"Autogate Name: {autogate_main_name}")

                                    save_button.clicked.connect(save_autogate_configuration)
                                        
                                except json.JSONDecodeError:
                                    label_response.setText(f"AutoGate Configuration Response:\n{response}")
                                label_response.setWordWrap(True)
                                layout_response.addWidget(label_response, alignment=Qt.AlignmentFlag.AlignCenter)
                                dlg_response.setLayout(layout_response)
                                dlg_response.exec()
                            else:
                                error_message = reply.errorString()
                                print("Error fetching AutoGate configuration: ", error_message)
                                dlg_error = QDialog(self)
                                dlg_error.setWindowTitle("Error")
                                dlg_error.setMinimumSize(400, 100)
                                layout_error = QVBoxLayout()
                                label_error = QLabel(f"Error fetching AutoGate configuration:\n{error_message}")
                                label_error.setWordWrap(True)
                                layout_error.addWidget(label_error, alignment=Qt.AlignmentFlag.AlignCenter)
                                dlg_error.setLayout(layout_error)
                                dlg_error.exec()
                        reply.finished.connect(handle_reply)

                    except Exception as e:
                        print("Exception occurred while fetching AutoGate configuration: ", str(e))
                        dlg_exception = QDialog(self)
                        dlg_exception.setWindowTitle("Exception")
                        dlg_exception.setMinimumSize(400, 100)
                        layout_exception = QVBoxLayout()
                        label_exception = QLabel(f"Exception occurred while fetching AutoGate configuration:\n{str(e)}")
                        label_exception.setWordWrap(True)
                        layout_exception.addWidget(label_exception, alignment=Qt.AlignmentFlag.AlignCenter)
                        dlg_exception.setLayout(layout_exception)
                        dlg_exception.exec()

                fetch_button.clicked.connect(lambda: handle_autogate_configuration())

                #show dialog
                dlg.setLayout(layoutd)
                dlg.exec()
            autogate_button.clicked.connect(configure_autogate)

            #add a configure automate button
            automate_button = QPushButton("Configure Automate")
            automate_button.setStyleSheet("font-weight: bold; background-color: navy; color: white;")
            layout.addWidget(automate_button, 18, 4, 1, 1)
            def configure_automate():
                dlg = QDialog(self)
                dlg.setWindowTitle("Automate Configuration")
                dlg.setMinimumSize(400, 150)
                layoutd = QVBoxLayout()
                label = QLabel("This is where you can configure Automate integration. This feature is coming soon!")
                layoutd.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
                #add button to save True for automated status and a reset button to reset it to False. Save the automated status to keyring with the key "automate_status" and the service name as defined in the LoginDialog class
                button_layout = QHBoxLayout()
                save_button = QPushButton("Set Automate Status to True")
                reset_button = QPushButton("Reset Automate Status to False")
                button_layout.addWidget(save_button)
                button_layout.addWidget(reset_button)
                layoutd.addLayout(button_layout)
                def set_automate_status_true():
                    keyring.set_password(LoginDialog.SERVICE_NAME, "automate_status", "True")
                    automate_status_label.setText("Automate Status: True")
                    dlg.close()
                def reset_automate_status_false():
                    keyring.set_password(LoginDialog.SERVICE_NAME, "automate_status", "False")
                    automate_status_label.setText("Automate Status: False")
                    dlg.close()
                save_button.clicked.connect(set_automate_status_true)
                reset_button.clicked.connect(reset_automate_status_false)

                dlg.setLayout(layoutd)
                dlg.exec()

            automate_button.clicked.connect(configure_automate)

            #add qlabel to show automated status
            try:
                automate_status = keyring.get_password(LoginDialog.SERVICE_NAME, "automate_status")
                status_text = f"<b>Automate Status: {automate_status}</b>" if automate_status else "<b>Automate Status: Not Configured</b>"
            except Exception:
                status_text = "<b>Automate Status: Not Configured</b>"
            automate_status_label = QLabel(status_text)
            layout.addWidget(automate_status_label, 18, 5, 1, 1)

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
                    dlg.setMinimumSize(400, 100)
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
                    dlg.setMinimumSize(400, 100)
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
                    dlg.setMinimumSize(400, 100)
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
                    dlg.setMinimumSize(400, 100)
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
                #update keyring confirm automate status to False when the application is closed
                keyring.set_password(LoginDialog.SERVICE_NAME, "confirm_start_mediamtx_status", "False")

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

login = LoginDialog()
if login.exec() == QDialog.DialogCode.Accepted:
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) #starts the event loop, which keeps the application running until the user closes it.

app.exec() #starts the event loop, which keeps the application running until the user closes it.
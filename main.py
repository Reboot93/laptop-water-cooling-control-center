import json, sys, random, time, _thread, os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from main_windows import Ui_Form
from paho.mqtt import client as mqtt_client

# ======/ 信号定义 /=====================
usr_dir = os.environ['LOCALAPPDATA']
config_dir = os.path.join(str(usr_dir), 'mqtt_iot_center')
file_name = 'config.json'
file = os.path.join(config_dir, file_name)

jsonLoad_flag = 0

control_data = [45, 0, 55, 60, 62, 100, 'broker.emqx.io', '1883']

Topic_now_wendu = 'show_wendu'  # ===/ 当前温度频道（接收） /=========
Topic_SetPwm = 'set_pwm'  # ===/ 温度曲线频道（发送） /=========
Topic_status = 'power_now'  # ===/ 运行状态频道（接收） /=========
Topic_SetPower = 'set_power'  # ===/ 外机开关频道（发送） /=========

# ==/ 界面控件刷新控制 /===============
status_flag = 'Mqtt连接中'
mqtt_flag = 0
now_wendu = 233
updata_flag = 0  # ==/ 控件刷新信号 ( 1/0 触发/pass )/==

# =====(温度一/pwm 1/温度二/pwm 2/温度三/pwm 3/服务器地址/端口)=====

broker = control_data[6]
port = control_data[7]

print(control_data)


# ======/ UI界面信号设置 /================

class MainWindow(QWidget, Ui_Form):
    # 定义点击信号
    chooseSignal = pyqtSignal(str)

    def __init__(self, parent=None):
        global control_data
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        #==/ Icon设置 /===
        self.setWindowIcon(QIcon('icon/256x256.ico'))
        # ==/ 设置文件读取及应用 /===========
        self.spinBox_pwm_wendu1.setValue(control_data[0])
        self.spinBox_pwm_wendu2.setValue(control_data[2])
        self.spinBox_pwm_wendu3.setValue(control_data[4])
        self.spinBox_pwm_1.setValue(control_data[1])
        self.spinBox_pwm_2.setValue(control_data[3])
        self.spinBox_pwm_3.setValue(control_data[5])
        self.mqtt_service.setText(control_data[6])
        self.mqtt_port.setText(control_data[7])
        # ==/ 按键信号设置 /================
        self.bt_on.clicked.connect(lambda: self.bt_on_clicked())
        self.bt_off.clicked.connect(lambda: self.bt_off_clicked())
        # ==/ MQTT信息设置信号 /============
        self.pushButton.clicked.connect(lambda: self.updata_mqtt())
        # ==/ Mqtt触发的界面更新，由函数 self.flash() 实现 /========
        _thread.start_new_thread(lambda: self.flash(), ())

        # ==/ 温度与PWM设置信号 /===========
        self.pwm_save.clicked.connect(lambda: self.updata_pwm_control())

        # ======/ 从‘%HOMEPATH%/AppData/Local/mqtt_iot/config.json’恢复配置 /==========
        self.json_load()

    def json_load(self):
        global jsonLoad_flag, control_data, updata_flag
        try:
            with open(file) as f:
                control_data = json.load(f)
                jsonLoad_flag = 1
                updata_flag = 1
                print('已从json恢复配置')
        except:
            print('未找到文件')
            if os.path.isdir(config_dir):
                self.json_save()
            else:
                os.mkdir(config_dir)
                self.json_save()

    # ==/ 开关按钮互斥 /====================
    def bt_on_clicked(self):
        if self.bt_off.isChecked() == True:
            self.bt_off.toggle()
        if mqtt_flag == 0:
            if do_connect() == True:
                publish(Topic_SetPower, 'on')
            else:
                QMessageBox.critical(self, 'MQTT连接',
                                     'MQTT连接失败，当前设置为：\n服务器地址：' + control_data[6] + '\n端口：' + control_data[
                                         7] + '\n请检查MQTT设置或检查服务器状态')
        else:
            publish(Topic_SetPower, 'on')

    def bt_off_clicked(self):
        if self.bt_on.isChecked() == True:
            self.bt_on.toggle()
        if mqtt_flag == 0:
            if do_connect() == True:
                publish(Topic_SetPower, 'off')
            else:
                QMessageBox.critical(self, 'MQTT连接',
                                     'MQTT连接失败，当前设置为：\n服务器地址：' + control_data[6] + '\n端口：' + control_data[
                                         7] + '\n请检查MQTT设置或检查服务器状态')
        else:
            publish(Topic_SetPower, 'off')

    # ==/ 保存MQTT服务器设置 /===============
    def updata_mqtt(self):
        global broker, port, mqtt_flag
        broker = self.mqtt_service.text()
        port = self.mqtt_port.text()
        control_data[6] = broker
        control_data[7] = port
        self.json_save()
        if do_connect() == True:
            QMessageBox.about(self, 'MQTT连接', '已重新连接至MQTT服务器')
        else:
            QMessageBox.critical(self, 'MQTT连接', 'MQTT连接失败，当前设置为：\n服务器地址：' + control_data[6] + '\n端口：' + control_data[
                7] + '\n请检查MQTT设置或检查服务器状态')
        print(broker)
        print(port)
        print(control_data)

    def updata_pwm_control(self):
        global control_data
        control_data[0] = self.spinBox_pwm_wendu1.value()
        control_data[2] = self.spinBox_pwm_wendu2.value()
        control_data[4] = self.spinBox_pwm_wendu3.value()
        control_data[1] = self.spinBox_pwm_1.value()
        control_data[3] = self.spinBox_pwm_2.value()
        control_data[5] = self.spinBox_pwm_3.value()
        self.json_save()
        if mqtt_flag == 0:
            if do_connect() == True:
                publish(Topic_SetPwm, json.dumps(control_data[0:6]))
            else:
                QMessageBox.critical(self, 'MQTT连接',
                                     'MQTT连接失败，当前设置为：\n服务器地址：' + control_data[6] + '\n端口：' + control_data[
                                         7] + '\n请检查MQTT设置或检查服务器状态')
        else:
            publish(Topic_SetPwm, json.dumps(control_data[0:6]))

    def json_save(self):
        global control_data
        print(config_dir)
        try:
            with open(file, 'w+') as f:
                json.dump(control_data, f)
                f.close()
                if jsonLoad_flag == 0:
                    self.json_load()
        except IOError:
            print('Io error')
            self.IO_window()

    def IO_window(self):
        QMessageBox.information(self, '保存设置到本地失败', '请创建配置文件（无内容）：\n' + config_dir, QMessageBox.Yes | QMessageBox.No)

    def flash(self):  # ==/ 控件刷新函数 /====
        global updata_flag
        i = 0
        while True:
            time.sleep(0.2)
            while updata_flag == 1:
                updata_flag = 0
                i = i + 1
                # ===/ 更新控件 /=================================
                self.label_show_zhuangtai.setText(status_flag)
                self.show_wendu.display(now_wendu)
                self.mqtt_service.setText(control_data[6])
                self.mqtt_port.setText(control_data[7])
                # ==============================================


# ======/ MQTT /===========================================================================================

def Mqtt_connect():
    global client

    def connect():
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(client_id)
        client.on_connect = on_connect
        client.connect(control_data[6], int(control_data[7]))
        return client

    # ======================================================
    client_id = f'python-mqtt-{random.randint(0, 1000)}'
    client = connect()
    subscribe(client)
    client.loop_start()


def subscribe(client):
    def on_message(client, userdata, msg):
        global status_flag, now_wendu, updata_flag
        updata_flag = 1
        if msg.topic == 'power_now':
            Msg = msg.payload.decode()
            print(Msg)
            if Msg == 'on':
                status_flag = ' 运行中'
                print('1')
            elif Msg == 'off':
                status_flag = '  休眠'
                print('2')
            else:
                pass
            QApplication.processEvents()
        if msg.topic == 'show_wendu':
            now_wendu = msg.payload.decode()
            QApplication.processEvents()
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    client.subscribe(Topic_status)
    client.subscribe(Topic_now_wendu)
    client.on_message = on_message


def publish(topic, msg):
    global client
    result = client.publish(topic, msg)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")


def do_connect():
    global mqtt_flag
    try:
        Mqtt_connect()
        mqtt_flag = 1
        print('Mqtt连接成功')
        a = True
        return a
    except:
        mqtt_flag = 0
        print('无法连接指mqtt服务器，请检查配置或服务器。')
        a = False
        return a


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ma = MainWindow()
    do_connect()
    ma.show()
    sys.exit(app.exec_())

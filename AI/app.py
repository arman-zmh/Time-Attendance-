import json
import uuid
import  jsons
from flask import Flask, request, jsonify
from  flask import render_template 
# from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import base64

from config.readConf import readConf
from flask_sock import Sock
from Helpers.log_conf import Logger 

from flask_sqlalchemy import SQLAlchemy
from extensions import db
from database import db,app
from job.SendOrderJob import  SendOrderJob
from app import db

sock = Sock(app)
readConf_=readConf()
url=readConf_.GetDBParam()
print(url)

db = SQLAlchemy() 
app.config['SQLALCHEMY_DATABASE_URI'] = url


db.init_app(app)

import atexit
send_order_job = SendOrderJob()
@app.before_request
def start_thread_once():
    if not send_order_job.is_running():
        print("start----------")
        send_order_job.start_thread()

atexit.register(send_order_job.stop_thread)

@app.route('/')
def index():  
    print(os.environ["FLASK_ENV"])
    APP_PATH =  request.base_url[:-1]
    print(APP_PATH)
    return render_template("index.html", APP_PATH=APP_PATH)

@app.route('/logRecords')
def logRecords(): 
    device_sn = request.args.get('deviceSn')
    print(os.environ["FLASK_ENV"])
    APP_PATH =  request.base_url[:-10]
    print(APP_PATH)
    return render_template("logRecords.html", APP_PATH=APP_PATH,deviceSn=device_sn)


@app.route('/a')
def index2():
    data = {'key1': 'value1', 'key2': 'value2'}

    
    return jsonify(data)

from Models.Device import Device, insert_device, get_all_devices, get_device_by_id, get_device_by_serial_num, update_device
from Models.Person import Person, insert_person, select_person_by_id, delete_person_by_id, update_person_by_id,select_all
from Models.MachineCommand import MachineCommand, insert_machine_command, select_machine_command_by_id
from Models.EnrollInfo import EnrollInfo, insert_enroll_info, get_all_enroll_info,selectByBackupnum,update_enroll_info2
from Models.AccessDay import AccessDay,insert_access_day,get_all_access_days,get_access_day_by_id
from Models.AccessWeek import AccessWeek, insert_access_week, get_all_access_weeks, get_access_week_by_id
from Models.LockGroup import LockGroup
from Models.UserLock import UserLock
from Models.Records import Record, insert_record,select_all_records,insert_record2
from Models.Msg import Msg

from Services.PersonService import PersonService,PersonServiceImpl
from Services.EnrollInfoService import EnrollInfoService
from Services.AccessWeekService import AccessWeekService
from Services.LockService import LockGroupService
from Services.UserLockService import UserLockService


person_=Person()
enrollinfo=EnrollInfo()
enrollinfoserive=EnrollInfoService( enroll_info=enrollinfo,person=person_)

personService = PersonServiceImpl(person=person_, enroll_info=enrollinfoserive, machine_command=MachineCommand())



@app.route('/device', methods=['POST'])
def create_device():

    data = request.get_json() 
    serial_num = data.get('serial_num')
    status = data.get('status')
    insert_device(serial_num, status)
    return jsonify({"message": "Device created successfully."}), 201
@app.route('/device', methods=['GET'])
def get_all_device():
    print("get all device")
    update_status_by_primary_key(62, 1)
    device_list = get_all_devices()
    device_list = [device.to_dict() for device in device_list] 
    return jsons.dump(Msg.success().add("device", device_list))



@app.route('/enrollInfo', methods=['GET'])
def get_all_enrollinfo():
    enroll_infoes = get_all_enroll_info()
    enroll_infoes = [enroll_info.to_dict() for enroll_info in enroll_infoes]
    return jsons.dump(Msg.success().add("enrollInfo", enroll_infoes))



@app.route('/sendWs', methods=['GET'])
def send_ws():
    device_sn = request.args.get('deviceSn')
    print(("device_sn:"+device_sn))
    message = "{\"cmd\":\"getuserlist\",\"stn\":true}"

    device_list = Device.query.all()
    for device in device_list:
        machine_command = MachineCommand(
            name="getuserlist",
            status=0,
            send_status=0,
            err_count=0,
            serial=device.serial_num,
            gmt_crate=datetime.now(),
            gmt_modified=datetime.now(),
            content=message
        )
        print(machine_command)
        db.session.add(machine_command)
    db.session.commit()

    return jsons.dump(Msg.success())





@app.route('/addPerson', methods=['POST'])
def add_person():
    person_temp = request.form
    pic = request.files['pic']
    # path = "C:/dynamicface/picture/"
    path=readConf().GetUploadParam()
    photo_name = ""
    new_name = ""
    if pic:
        if pic.filename:
            photo_name = secure_filename(pic.filename)
            new_name = str(uuid.uuid4()) + photo_name[photo_name.rfind('.'):]
            photo_file = os.path.join(path, new_name)
            pic.save(photo_file)

    person = {
        'id': person_temp.get('userId'),
        'name': person_temp.get('name'),
        'roll_id': person_temp.get('privilege')
    }
    existing_person = select_person_by_id(person_temp.get('userId'))

    if not existing_person:
        insert_person(**person)

    if person_temp.get('password'):
        enroll_info_temp2 = {
            'backupnum': 10,
            'enroll_id': person_temp.get('userId'),
            'signatures': person_temp.get('password')
        }
        insert_enroll_info(**enroll_info_temp2)

    if person_temp.get('cardNum'):
        enroll_info_temp3 = {
            'backupnum': 11,
            'enroll_id': person_temp.get('userId'),
            'signatures': person_temp.get('cardNum')
        }
        insert_enroll_info(**enroll_info_temp3)

    if new_name:
        with open(os.path.join(path, new_name), "rb") as image_file:
            base64_str = base64.b64encode(image_file.read()).decode()

        enroll_info_temp = {
            'backupnum': 50,
            'enroll_id': person_temp.get('userId'),
            'imagepath': new_name,
            'signatures': base64_str
        }
        insert_enroll_info(**enroll_info_temp)
    else:
        enroll_info_temp = {
            'backupnum': 50,
            'enroll_id': person_temp.get('userId'),
            'imagepath': "",
            'signatures': ""
        }
        insert_enroll_info(**enroll_info_temp)
    return jsons.dump(Msg.success())


@app.route('/getUserInfo', methods=['GET'])
def get_user_info():
    print("Get user info")
    device_sn = request.args.get('deviceSn')
    persons = Person.query.all()
    enrolls_prepared = []
    for person in persons:
        enroll_infos = EnrollInfo.query.filter_by(enroll_id=person.id).all()
        for enroll_info in enroll_infos:
            if enroll_info.enroll_id and enroll_info.backupnum:
                enrolls_prepared.append(enroll_info)
    print("Collecting user data: ", enrolls_prepared)
    PersonServiceImpl.get_signature2(enrolls_prepared, device_sn)

    return jsons.dump(Msg.success())


@app.route('/sendGetUserInfo', methods=['GET'])
def send_get_user_info():
    enroll_id = request.args.get('enrollId', type=int)
    backupnum = request.args.get('backupNum', type=int)
    device_sn = request.args.get('deviceSn')

    device_list = Device.query.all()
    print("Device info: ", device_list)

    message = {"cmd": "getuserinfo", "enrollid": enroll_id, "backupnum": backupnum}

    MachineCommand.add_get_one_user_command(enroll_id, backupnum, device_sn)

    return jsons.dump(Msg.success())


@app.route('/setPersonToDevice', methods=['GET']) 
def send_set_user_info():
    device_sn = request.args.get('deviceSn')

    personService.setUserToDevice2(device_sn)

    return jsons.dump(Msg.success())


@app.route('/setUsernameToDevice', methods=['GET']) 
def set_username_to_device():
    device_sn = request.args.get('deviceSn')

    personService.set_username_to_device(device_sn)

    return jsons.dump(Msg.success())


@app.route('/getDeviceInfo', methods=['GET']) 
def get_device_info():
    device_sn = request.args.get('deviceSn')

    message ='{"cmd":"getdevinfo"}'
    machine_command = MachineCommand(content=message, name="getdevinfo", status=0, send_status=0, err_count=0, serial = device_sn)
    machine_command.insert_machine_command(machine_command)
    return jsons.dump(Msg.success())


@app.route('/setOneUser', methods=['GET']) 
def set_one_user_to():
    enroll_id = request.args.get('enrollId', type=int)
    backupnum = request.args.get('backupNum', type=int)
    device_sn = request.args.get('deviceSn')

    # print("Set one user to device: ", enroll_id, backupnum, device_sn)
    person = select_person_by_id(enroll_id)
    enroll_info = selectByBackupnum(enroll_id, backupnum)
    # print("Enroll info: ", enroll_info)
    # print("Enroll info: ", enroll_info.signatures)
    if enroll_info is not None:
        personService.set_user_to_device(enroll_id, person.name, backupnum, person.roll_id, enroll_info.signatures,device_sn)
        return jsons.dump(Msg.success())
    elif backupnum == -1:
        personService.set_user_to_device(enroll_id, person.name, backupnum, 0, "", device_sn)
        return jsons.dump(Msg.success())
    else:
        return jsons.dump(Msg.fail())


@app.route('/deletePersonFromDevice', methods=['GET'])
def delete_device_user_info():
    enroll_id = request.args.get('enrollId', type=int)
    device_sn = request.args.get('deviceSn')

    print("Deleting user devicesn: ", device_sn)
    personService.delete_user_info_from_device(enroll_id, device_sn)

    return jsons.dump(Msg.success())


@app.route('/initSystem', methods=['GET']) 
def init_system():
    device_sn = request.args.get('deviceSn')

    print("Initialization request")
   
    message = '{"cmd": "enabledevice"}'
    message2 = '{"cmd": "settime", "cloudtime": "2020-12-23 13:49:30"}'
    s4 = '{"cmd": "settime", "cloudtime": "2016-03-25 13:49:30"}'
    s2 = '{"cmd": "setdevinfo", "deviceid": 1, "language": 0, "volume": 0, "screensaver": 0, "verifymode": 0, "sleep": 0,"userfpnum": 3, "loghint": 1000, "reverifytime": 0}'
    s5 = '{"cmd": "enableuser", "enrollid": 1, "enflag": 0}'
    s6 = '{"cmd": "getusername", "enrollid": 1}'
    message = '{"cmd": "initsys"}'

    machine_command = MachineCommand(content=message, name="initsys", status=0, send_status=0, err_count=0, serial=device_sn)

    machine_command.insert_machine_command(machine_command)

    return jsons.dump(Msg.success())


@app.route('/getAllLog', methods=['GET'])
def getAllLog():
    device_sn = request.args.get('deviceSn')

    message = '{"cmd":"getalllog","stn":true}'
    # messageTemp = '{"cmd":"getalllog","stn":true,"from":"2020-12-03","to":"2020-12-30"}'

    machine_command = MachineCommand()
    machine_command.content = message
    machine_command.name = "getalllog"
    machine_command.status = 0
    machine_command.send_status = 0
    machine_command.err_count = 0
    machine_command.serial = device_sn
    machine_command.gmt_crate = datetime.now()
    machine_command.gmt_modified = datetime.now()

    machine_command.insert_machine_command(machine_command)
    return jsons.dump(Msg.success())

@app.route('/getNewLog', methods=['GET'])
def get_new_log():
    device_sn = request.args.get('deviceSn')
    message = '{"cmd": "getnewlog", "stn": true}'
    machine_command = MachineCommand(content=message, name="getnewlog", status=0, send_status=0, err_count=0,serial=device_sn)
    machine_command.insert_machine_command(machine_command)
    return jsons.dump(Msg.success())

from  Services.AccessDayService import  AccessDayService
@app.route('/setAccessDay', methods=['POST'])
def set_access_day():
    access_day = request.form.to_dict()
    print(access_day)
    if get_access_day_by_id(access_day['id']) is not None:
        return jsons.dump(Msg.fail())
    access_day_instance = AccessDay(**access_day)
    db.session.add(access_day_instance)
 
    accessDayService=AccessDayService()
    accessDayService.set_access_day()
    return jsons.dump(Msg.success())


@app.route('/setAccessWeek', methods=['POST'])
def set_access_week():
    access_week = request.form.to_dict()  
    if get_access_week_by_id(access_week['id']) is not None:
        return jsons.dump(Msg.fail())
    access_week_instance = AccessWeek(**access_week)
    db.session.add(access_week_instance)
    accessWeekService = AccessWeekService()
    accessWeekService.set_access_week()
    return jsons.dump(Msg.success())

from flask import send_from_directory 
@app.route('/img/<filename>', methods=['GET'])
def upload_file(filename):
    path = readConf().GetUploadParam()
    return send_from_directory(path, filename)

@app.route('/setLocckGroup', methods=['POST'])
def set_lock_group():
    lock_group =  request.form.to_dict()
    lockGroupService = LockGroupService()
    lockGroupService.set_lock_group(lock_group)
    return jsons.dump(Msg.success())




@app.route('/setUserLock', methods=['POST']) 
def set_user_lock():
    user_lock =  request.form.to_dict()
    userLockService = UserLockService()
    userLockService.set_user_lock(user_lock, user_lock['starttime'], user_lock['endtime'])
    return jsons.dump(Msg.success())

from Models.Page import PageInfo
@app.route('/emps', methods=['GET'])
def get_all_person_from_db():
    pn = request.args.get('pn', default=1, type=int)
    person_list = select_all()
    enroll_list = get_all_enroll_info()  #EnrollInfo.select_all()
    emps = []
    for person in person_list:
        for enroll_info in enroll_list:
            if person.id == enroll_info.enroll_id and enroll_info.backupnum == 50:
                emps.append({
                    'enrollId': person.id,
                    'admin': person.roll_id,
                    'name': person.name,
                    'imagePath': enroll_info.imagepath
                })
    page=PageInfo(emps,5)
    # return jsons.dump(success=True, pageInfo={'emps': emps, 'pn': pn})  # you'll need to implement your own paging
    return jsons.dump(Msg.success().add("pageInfo", page))
#Msg.success().add("device", device_list)

@app.route('/records', methods=['GET'])
def get_all_log_from_db():
    pn = request.args.get('pn', default=1, type=int)
    records = select_all_records()

    records = [record.to_dict() for record in records]
    print(records)
    pageInfo=PageInfo(records,5)
    # print(pageInfo)
    return jsons.dump(Msg.success().add("pageInfo", pageInfo))

@app.route('/accessDays', methods=['GET'])
def get_access_day_from_db():
    access_days = get_all_access_days()
    access_days = [access_day.to_dict() for access_day in access_days]  # Convert each Device to a dictionary
    # print(access_days)
    return jsons.dump(Msg.success().add("accessdays", access_days))



@app.route('/uploadUserToDevice', methods=['POST']) 
def upload_user_to_device():
    enroll_id = request.args.get('enrollId', type=int)
    person = Person.selectByPrimaryKey(enroll_id)
    
    return jsons.dump(Msg.success())




@app.route('/openDoor', methods=['GET'])
def open_door():
    door_num = request.args.get('doorNum', type=int)
    device_sn = request.args.get('deviceSn')
    message = json.dumps({'cmd': 'opendoor', 'doornum': door_num})
    machine_command = MachineCommand(content=message, name="opendoor", status=0, send_status=0, err_count=0,serial=device_sn)
    machine_command.insert_machine_command(machine_command)
    return jsons.dump(Msg.success())


@app.route('/getDevLock', methods=['GET'])
def get_dev_lock():
    device_sn = request.args.get('deviceSn')
    message =json.dumps({"cmd": "getdevlock"})
    machine_command = MachineCommand(content=message, name="getdevlock", status=0, send_status=0, err_count=0,serial=device_sn)
    machine_command.insert_machine_command(machine_command)
    return jsons.dump(Msg.success())


@app.route('/getUserLock', methods=['GET'])
def get_user_lock():
    enroll_id = request.args.get('enrollId', type=int)
    device_sn = request.args.get('deviceSn')
    message = json.dumps({"cmd": "getuserlock", "enrollid": enroll_id})
    machine_command = MachineCommand(content=message, name="getuserlock", status=0, send_status=0, err_count=0, serial=device_sn)
    machine_command.insert_machine_command(machine_command)
    return jsons.dump(Msg.success())


@app.route('/cleanAdmin', methods=['GET'])
def clean_admin():
    device_sn = request.args.get('deviceSn')
    message =json.dumps({"cmd": "cleanadmin"})
    machine_command = MachineCommand(content=message, name="cleanadmin", status=0, send_status=0, err_count=0, serial=device_sn)
    machine_command.insert_machine_command(machine_command)
    return jsons.dump(Msg.success())




@sock.route('/')
def websock(sock):
    while True:
        data = sock.receive()
        #if not data is None:
        print('收到消息/pub/chat:', data)
        # sock.send(data[::-1])
        #sock.send(data)

@sock.route('/pub/chat')
def handler(sock):
    try:
        while True:
            message = sock.receive()
            # print("sock:"+message)
            # for message in data:
            # dt=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            # reply = f"Data received as \"{message}\".  time: {dt}"
            # print(reply)
            try:
                
                try:
                    jsonMsg = json.loads(message)
                except:
                    import traceback
                    traceback.print_exc()

                try:
                    cmd = jsonMsg["cmd"]
                except :
                    cmd=""
                    # import traceback
                    # traceback.print_exc()
                try :
                    ret = jsonMsg["ret"]
                except :
                    # import traceback
                    # traceback.print_exc()
                    ret=""
                print("cmd--:" + cmd)
                print("ret--:" + ret)
                if len(cmd) != 0 :  # client active send data
                    print("cmd--:" + cmd)

                    if cmd == "reg":
                        try:

                            get_device_info_websocket(jsonMsg,sock)
                        except Exception as err:
                            print(err)
                            import traceback
                            traceback.print_exc()
                            # sock.send(json.dumps({"ret": "reg", "result": False, "reason": 1}))
                            sock.send("{\"ret\":\"reg\",\"result\":false,\"reason\":1}")
                    elif cmd == "sendlog":
                        try:
                            # print("sendlog:" + str(jsonMsg))
                            get_attendance(jsonMsg, sock)
                        except Exception as err:
                            print(err)
                            import traceback
                            traceback.print_exc()
                            #sock.send(json.dumps({"ret": "sendlog", "result": False, "reason": 1}))
                            sock.send("{\"ret\":\"sendlog\",\"result\":false,\"reason\":1}")
                    elif cmd == "senduser":
                        try:
                            get_enroll_info(jsonMsg, sock)
                        except Exception as err:
                            print(err)
                            import traceback
                            traceback.print_exc()
                            # sock.send(json.dumps({"ret": "senduser", "result": False, "reason": 1}))
                            sock.send("{\"ret\":\"senduser\",\"result\":false,\"reason\":1}")
                    else:
                        print("cmd未知:" + cmd)
                elif len(ret) != 0 :  # server send cmd and rec data
                    print("ret--:" + ret)
                    if ret == "getuserlist":
                        print("getuserlist:" + str(jsonMsg))
                        get_user_list(jsonMsg, sock)
                    elif ret == "getuserinfo":
                        print("getuserinfo:" + str(jsonMsg))
                        get_user_info_websocket(jsonMsg, sock)
                        sn = jsonMsg["sn"]
                        deviceStatus=DeviceStatus()
                        deviceStatus.device_sn = sn
                        deviceStatus.websocket = sock
                        deviceStatus.status = 1
                        update_device_websocket(sn, deviceStatus)

                    elif ret == "setuserinfo":
                        print("setuserinfo" + str(jsonMsg))
                        sn = jsonMsg["sn"]
                        deviceStatus = DeviceStatus()
                        deviceStatus.device_sn = sn
                        deviceStatus.websocket = sock
                        deviceStatus.status = 1
                        update_device_websocket(sn, deviceStatus)
                        update_command_status_websocket(sn,"setuserinfo")
                    elif ret == "getalllog":
                        print("sgetalllog"+ str(jsonMsg))
                        try:
                            get_all_log(jsonMsg, sock)
                        except Exception as err:
                            import traceback
                            traceback.print_exc()
                            print(err)
                    elif ret == "getnewlog":

                        print("getnewlog" + str(jsonMsg))
                        try:
                            get_new_log(jsonMsg, sock)
                        except Exception as err:
                            import traceback
                            traceback.print_exc()
                            print(err)
                    elif ret == "deleteuser":
                        print("deleteuser" + str(jsonMsg))
                        sn = jsonMsg["sn"]
                        deviceStatus = DeviceStatus()
                        deviceStatus.device_sn = sn
                        deviceStatus.websocket = sock
                        deviceStatus.status = 1
                        update_device_websocket(sn, deviceStatus)
                        update_command_status_websocket(sn, "deleteuser")
                    elif ret == "initsys":
                        print("initsys" + str(jsonMsg))
                        sn = jsonMsg["sn"]
                        deviceStatus = DeviceStatus()
                        deviceStatus.device_sn = sn
                        deviceStatus.websocket = sock
                        deviceStatus.status = 1
                        update_device_websocket(sn, deviceStatus)
                        update_command_status_websocket(sn, "initsys")
                    elif ret == "setdevlock":
                        print("setdevlock" + str(jsonMsg))
                        sn = jsonMsg["sn"]
                        deviceStatus = DeviceStatus()
                        deviceStatus.device_sn = sn
                        deviceStatus.websocket = sock
                        deviceStatus.status = 1
                        update_device_websocket(sn, deviceStatus)
                        update_command_status_websocket(sn, "setdevlock")
                    elif ret == "setuserlock":
                        print("setuserlock" + str(jsonMsg))
                        sn = jsonMsg["sn"]
                        deviceStatus = DeviceStatus()
                        deviceStatus.device_sn = sn
                        deviceStatus.websocket = sock
                        deviceStatus.status = 1
                        update_device_websocket(sn, deviceStatus)
                        update_command_status_websocket(sn, "setuserlock")

                    elif ret == "getdevinfo":
                        print("getdevinfo" + str(jsonMsg))
                        sn = jsonMsg["sn"]
                        deviceStatus = DeviceStatus()
                        deviceStatus.device_sn = sn
                        deviceStatus.websocket = sock
                        deviceStatus.status = 1
                        update_device_websocket(sn, deviceStatus)
                        update_command_status_websocket(sn, "getdevinfo")
                    elif ret == "setusername":
                        print("setusername" + str(jsonMsg))
                        sn = jsonMsg["sn"]
                        deviceStatus = DeviceStatus()
                        deviceStatus.device_sn = sn
                        deviceStatus.websocket = sock
                        deviceStatus.status = 1
                        update_device_websocket(sn, deviceStatus)
                        update_command_status_websocket(sn, "setusername")

                    elif ret == "reboot":
                        print("reboot:" + str(jsonMsg))
                        sn = jsonMsg["sn"]
                        deviceStatus = DeviceStatus()
                        deviceStatus.device_sn = sn
                        deviceStatus.websocket = sock
                        deviceStatus.status = 1
                        update_device_websocket(sn, deviceStatus)
                        update_command_status_websocket(sn, "reboot")

                    elif ret == "getdevlock":
                        print("getdevlock:" + str(jsonMsg))
                        sn = jsonMsg["sn"]
                        deviceStatus = DeviceStatus()
                        deviceStatus.device_sn = sn
                        deviceStatus.websocket = sock
                        deviceStatus.status = 1
                        update_device_websocket(sn, deviceStatus)
                        update_command_status_websocket(sn, "getdevlock")

                    elif ret == "getuserlock":
                        print("getuserlock:" + str(jsonMsg))
                        sn = jsonMsg["sn"]
                        deviceStatus = DeviceStatus()
                        deviceStatus.device_sn = sn
                        deviceStatus.websocket = sock
                        deviceStatus.status = 1
                        update_device_websocket(sn, deviceStatus)
                        update_command_status_websocket(sn, "getuserlock")

                    else:
                        print("not get:" + ret)
                        sn = jsonMsg["sn"]
                        deviceStatus = DeviceStatus()
                        deviceStatus.device_sn = sn
                        deviceStatus.websocket = sock
                        deviceStatus.status = 1
                        update_device_websocket(sn, deviceStatus)
                        update_command_status_websocket(sn, ret)

            except Exception as ex:
                print("error:" + str(ex))
                import traceback
                traceback.print_exc()

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(e)

    finally:
        pass

from Models.DeviceStatus import DeviceStatus
from web_socket.WebSocketPool import WebSocketPool
def update_device_websocket(sn, device_status):

    if WebSocketPool.get_device_status(sn) is not None:
        WebSocketPool.add_device_and_status(sn, device_status)
    else:
        WebSocketPool.add_device_and_status(sn, device_status)

def update_command_status_websocket(serial, command_type):
    print("serial:"+str(serial) +" command_type:"+ command_type)
    machine_command = find_pending_command(1, serial)
    print("update_command_status_websocket")
    print(machine_command)
    if len(machine_command) > 0 and machine_command[0].name == command_type:
       update_command_status(1, 0, datetime.now(), machine_command[0].id)

from Models.Device import Device,get_device_by_serial_num,insert_device,update_status_by_primary_key

time_stamp =0
time_stamp2=0
def get_device_info_websocket(json_node, sock_):
    sn = json_node.get('sn')

    device_status = {}
    if sn:

        d1 = get_device_by_serial_num(sn)

        # print(d1.serial_num)
        if d1 is None:
            i = insert_device(sn, 1)
            print(i)
        else:
            update_status_by_primary_key(d1.id, 1)

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = json.dumps({'ret': 'reg', 'result': True, 'cloudtime': current_time})
        # emit('message', message, room=args1)
        sock_.send(message)
        device_status = {'websocket': sock_, 'status': 1, 'device_sn': sn}
        update_device_websocket(sn, device_status)
        # print(cls.get_device_status(sn))
        # j_obj = {'SN': sn, 'currentTime': datetime.now().timestamp()}
        # RestTemplateUtil.post_device_info(j_obj)  # Implement this method in your way
    else:
        message = json.dumps({'ret': 'reg', 'result': False, 'reason': 1})
        # emit('message', message, room=args1)
        sock_.send(message)
        device_status = {'websocket': sock_, 'status': 1, 'device_sn': sn}
        update_device_websocket(sn, device_status)
    global time_stamp
    global time_stamp2
    time_stamp = datetime.now().timestamp()
    time_stamp2 = time_stamp
   


import uuid

# from collections import defaultdict
from Models.Records import Record,insert_record,select_all_records,select_record_by_id,update_record_by_id

def get_attendance(json_node, conn):
    sn = json_node["sn"]
    count = json_node["count"]
    log_index = json_node.get("logindex", -1)
    record_all = []
    device_status = DeviceStatus()
    flag = False
    if count > 0:
        for record in json_node["record"]:
            obj = {} 
            enroll_id = record["enrollid"]
            time_str = record["time"]
            mode = record["mode"]
            in_out = record["inout"]
            event = record["event"]
            temperature = 0
            if record.get("temp"):
                temperature = round(record["temp"] / 10, 1)
                obj["temperature"] = str(temperature)
            records = {
                'device_serial_num': sn,
                'enroll_id': enroll_id,
                'event': event,
                'intOut': in_out,
                'mode': mode,
                'records_time': time_str,
                'temperature': temperature
            }
            if enroll_id == 99999999:
                obj["resultStatus"] = 0
            else:
                obj["resultStatus"] = 1
            obj["IdentifyType"] = "0"
            obj["SN"] = sn
            try:
                if record["image"]:
                    pic_name = str(uuid.uuid4())
                    obj["face_base64"] = record["image"]
                    flag = base64_to_image(record["image"], pic_name)
                  
                    records["image"] = pic_name + ".jpg"
            except:
                pass
            print("records====1")
            print(records)
            record_all.append(records)
            obj["time"] = time_str
            obj["userid"] = str(enroll_id)
           
        if log_index >= 0:
            conn.send(json.dumps({"ret":"sendlog","result":True,"count":count,"logindex":log_index,"cloudtime":str(datetime.now())}))
        elif log_index < 0:
            conn.send(json.dumps({"ret":"sendlog","result":True,"cloudtime":str(datetime.now())}))
        device_status.websocket = conn
        device_status.status = 1
        device_status.device_sn = sn
        update_device_websocket(sn, device_status)
    elif count == 0:
        conn.send(json.dumps({"ret":"sendlog","result":False,"reason":1}))
        device_status.websocket = conn
        device_status.status = 1
        device_status.device_sn = sn
        update_device_websocket(sn, device_status)
    print(record_all)
    for record in record_all:
        insert_record2(**record) 
    global timestamp2
    timestamp2 = datetime.now()

def base64_to_image(base64_string, pic_name):
    try:
        image_data = base64.b64decode(base64_string)
        with open(os.path.join(readConf_.GetUploadParam(), pic_name + '.jpg'), 'wb') as f:
            f.write(image_data)
        return True
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


import json




def get_enroll_info(json_node, conn):

    # enroll_id = json_node["enrollid"]
    sn = json_node["sn"]
    signatures1 = json_node["record"]
    flag = False
    device_status = DeviceStatus()

    if signatures1 is None:
        conn.send(json.dumps({"ret": "senduser", "result": False, "reason": 1}))
        device_status.websocket = conn
        device_status.status = 1
        device_status.device_sn = sn
        update_device_websocket(sn, device_status)
    else:
        backupnum = json_node["backupnum"]
        enroll_id = json_node["enrollid"]
        name = json_node["name"]
        roll_id = json_node["admin"]
        signatures = json_node["record"]
        person= {
            'id': enroll_id,
            'name': name,
            'roll_id': roll_id
        }

        #person_service.select_by_primary_key(enroll_id)

        if select_person_by_id(enroll_id) is None:
            insert_person(**person)

        enroll_info ={
            'enroll_id': enroll_id,
            'backupnum': backupnum,
            'signatures': signatures
        }

        if backupnum == 50:
            pic_name = str(uuid.uuid4())
            flag = base64_to_image(json_node["record"], pic_name)
            enroll_info["imagepath"] = pic_name + ".jpg"

        if selectByBackupnum(enroll_id, backupnum) is None:
            insert_enroll_info(**enroll_info)
        else:
            update_enroll_info2(enroll_id,enroll_info["imagepath"],enroll_info["signatures"]) 

        conn.send(json.dumps(
            {"ret": "senduser", "result": True, "cloudtime": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}))
        device_status.websocket = conn
        device_status.status = 1
        device_status.device_sn = sn
        update_device_websocket(sn, device_status)

    global timestamp2
    timestamp2 = datetime.now()


from  Models.UserTemp import UserTemp
def get_user_list(json_node, conn):
    user_temps = []

    result = json_node["result"]
    sn = json_node["sn"]
    device_status = DeviceStatus()

    if result:
        count = json_node["count"]
        records = json_node["record"]
        print("get_user_list:count "+str(count))
        if count > 0:
            for record in records:
                enroll_id = record["enrollid"]
                admin = record["admin"]
                backupnum = record["backupnum"]
                user_temp = UserTemp(enrollId = enroll_id, backupnum=backupnum, admin=admin)
                user_temps.append(user_temp)

            # conn.send(json.dumps({"cmd": "getuserlist", "stn": False}))
            conn.send("{\"cmd\":\"getuserlist\",\"stn\":false}")
            print("get_user_list count > 0 send")
            print(conn)
            device_status.websocket = conn
            device_status.status = 1
            device_status.device_sn = sn
            update_device_websocket(sn, device_status)

    for user_temp in user_temps:
        if select_person_by_id(user_temp.enrollId) is None:
            # person_temp = Person(id=user_temp.enrollId, name="", roll_id=user_temp.admin)
            person_temp={
                'id': user_temp.enrollId,
                'name': "",
                'roll_id': user_temp.admin
            }
            insert_person(**person_temp)

    for user_temp in user_temps:
        if selectByBackupnum(user_temp.enrollId, user_temp.backupnum) is None:
            # enroll_info = EnrollInfo(enroll_id=user_temp.enrollId, backupnum=user_temp.backupnum)
            enroll_info={
                'enroll_id': user_temp.enrollId,
                'backupnum': user_temp.backupnum,
                'imagepath':  "",
                'signatures': ""
            }
            insert_enroll_info(**enroll_info)

    update_command_status_websocket(sn, "getuserlist")
    print("update_command_status_websocket")
from Models.MachineCommand import MachineCommand,find_pending_command,update_command_status
# def update_command_status_(serial, command_type):
#     machine_command = find_pending_command(1, serial)
#     if len(machine_command) > 0 and machine_command[0].name == command_type:
#         update_command_status(1, 0, datetime.datetime.now(), machine_command[0].id)

from Models.Person import insert_person2,update_by_primary_key
def get_user_info_websocket(json_node, conn):
    result = json_node["result"]
    sn = json_node["sn"]
    flag = False

    if result:
        backupnum = json_node["backupnum"]
        signatures1 = json_node["record"]
        enroll_id = json_node["enrollid"]
        name = json_node["name"]
        admin = json_node["admin"]
        signatures = json_node["record"]

        person = Person(id=enroll_id, name=name, roll_id=admin)
        enroll_info = selectByBackupnum(enroll_id, backupnum)

        if backupnum == 50:
            pic_name = str(uuid.uuid4())
            flag = base64_to_image(json_node["record"], pic_name)
            enroll_info.imagepath = pic_name + ".jpg"

        if select_person_by_id(enroll_id) is None:

            insert_person2(person)
        elif select_person_by_id(enroll_id) is not None:
            update_by_primary_key(person)

        if enroll_info is None:
            enroll_info={
                'enroll_id': 0,
                'backupnum': None,
                'signatures': None,
                'imagepath': None,
            }
            insert_enroll_info(**enroll_info)
        elif enroll_info is not None:
            from Models.EnrollInfo import update_by_primary_key_with_blobs
            enroll_info.signatures = signatures
            update_by_primary_key_with_blobs(enroll_info)

    update_command_status_websocket(sn, "getuserinfo")


def get_all_log(json_node, conn):
    result = json_node["result"]
    record_all = []
    sn = json_node["sn"]
    records = json_node["record"]
    device_status = DeviceStatus()
    flag = False

    if result:
        count = json_node["count"]
        if count > 0:
            for record in records:
                enroll_id = record["enrollid"]
                time_str = record["time"]
                mode = record["mode"]
                in_out = record["inout"]
                event = record["event"]
                temperature = 0.0
                if record.get("temp") is not None:
                    temperature = record["temp"]
                    temperature = temperature / 100
                    temperature = round(temperature, 1)

                rec = Record(enroll_id=enroll_id, event=event, intOut=in_out, mode=mode, records_time=time_str,
                              device_serial_num=sn, temperature=temperature)
                record_all.append(rec)

            conn.send(json.dumps({"cmd": "getalllog", "stn": False}))
            device_status.websocket = conn
            device_status.status = 1
            device_status.device_sn = sn
            update_device_websocket(sn, device_status)

    for record in record_all:
        insert_record(record)

    update_command_status_websocket(sn, "getalllog")


def get_all_log(json_node, conn):
    result = json_node["result"]
    record_all = []
    sn = json_node["sn"]
    records = json_node["record"]
    device_status = DeviceStatus()
    flag = False

    if result:
        count = json_node["count"]
        if count > 0:
            for record in records:
                enroll_id = record["enrollid"]
                time_str = record["time"]
                mode = record["mode"]
                in_out = record["inout"]
                event = record["event"]
                temperature = 0.0
                if record.get("temp") is not None:
                    temperature = record["temp"]
                    temperature = temperature / 100
                    temperature = round(temperature, 1)

                rec = Record(enroll_id=enroll_id, event=event, intOut=in_out, mode=mode, records_time=time_str,
                              device_serial_num=sn, temperature=temperature)
                record_all.append(rec)

            conn.send(json.dumps({"cmd": "getalllog", "stn": False}))
            device_status.websocket = conn
            device_status.status = 1
            device_status.device_sn = sn
            update_device_websocket(sn, device_status)

    for record in record_all:
        insert_record(record)

    update_command_status_websocket(sn, "getalllog")



def get_new_log(json_node, conn):
    result = json_node["result"]
    record_all = []
    sn = json_node["sn"]
    records = json_node["record"]
    device_status = DeviceStatus()
    flag = False

    if result:
        count = json_node["count"]
        if count > 0:
            for record in records:
                enroll_id = record["enrollid"]
                time_str = record["time"]
                mode = record["mode"]
                in_out = record["inout"]
                event = record["event"]
                temperature = 0.0
                if record.get("temp") is not None:
                    temperature = record["temp"]
                    temperature = temperature / 100
                    temperature = round(temperature, 1)

                rec = Record(enroll_id=enroll_id, event=event, intOut=in_out, mode=mode, records_time=time_str,
                              device_serial_num=sn, temperature=temperature)
                record_all.append(rec)

            conn.send(json.dumps({"cmd": "getnewlog", "stn": False}))
            device_status.websocket = conn
            device_status.status = 1
            device_status.device_sn = sn
            update_device_websocket(sn, device_status)

    for record in record_all:
        insert_record(record)(record)

        update_command_status_websocket(sn, "getnewlog")



# import threading
# import time
# from Models.MachineCommand import MachineCommand,find_pending_command,update_command_status,update_machine_command
# from Models.Device import Device,get_device_by_serial_num
# class SendOrderJob(threading.Thread):
#     def __init__(self):
#         threading.Thread.__init__(self)
#         self.stop_event = threading.Event()
#         # self.machine_command_mapper = machine_command_mapper
#         # self.device_mapper = device_mapper
#         self.wd_list = {}  # WebSocketPool.wsDevice
#
#     def run(self):
#         while not self.stop_event.is_set():
#             print("SendOrderJob start running-----" +datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
#             for key, device_status in self.wd_list.items():
#                 try:
#                     in_sending = find_pending_command(0, key)
#                     if in_sending:
#                         pending_command = find_pending_command(1, key)
#                         if not pending_command:
#                             device_status.get('websocket').send(in_sending[0].get('content'))
#                             update_command_status(0, 1, time.time(),in_sending[0].get('id'))
#                         elif len(pending_command) == 1:
#                             if time.time() - pending_command[0].get('run_time') > 20:
#                                 if pending_command[0].get('err_count') < 3:
#                                     machine_command = pending_command[0]
#                                     machine_command['err_count'] += 1
#                                     machine_command['run_time'] = time.time()
#                                     update_machine_command(**machine_command)
#                                     device = get_device_by_serial_num(pending_command[0].get('serial'))
#                                     if device.get('status') != 0:
#                                         device_status.get('websocket').send(pending_command[0].get('content'))
#                                 else:
#                                     machine_command = pending_command[0]
#                                     machine_command['err_count'] += 1
#                                     update_machine_command(**machine_command)
#                 except Exception as e:
#                     pass
#             time.sleep(0.1)  # Avoid high CPU usage
#
#     def stop(self):
#         self.stop_event.set()
#
#     def start_thread(self):
#         self.start()
#
#     def stop_thread(self):
#         self.stop()



# python.exe -m flask run --port=7700
# python.exe -m flask run  --host=0.0.0.0 --port=7788
#python.exe -m flask run  --host=192.168.0.118 --port=7788

if __name__ == '__main__':
    print("start")

    try:
        app.run(debug=True)
    finally:
        pass
        # Stop the thread when the app is shut down ctrl + c


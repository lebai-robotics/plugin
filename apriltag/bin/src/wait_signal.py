# encoding: utf-8
import threading
import apriltag
import json
import time
import math
import lebai_sdk

lebai = lebai_sdk.connect("127.0.0.1", True)

def i16_to_u16(i):
    if i < 0:
        return i + 65536
    else:
        return i
def u16_to_i16(u):
    if u <= 32767:
        return u
    else:
        return u - 65536
def pose2reg(pose):
    x = i16_to_u16(int(pose["x"] * 1000))
    y = i16_to_u16(int(pose["y"] * 1000))
    z = i16_to_u16(int(pose["z"] * 1000))
    rz = i16_to_u16(int(pose["rz"]/(2*math.pi)*65536))
    ry = i16_to_u16(int(pose["ry"]/(2*math.pi)*65536))
    rx = i16_to_u16(int(pose["rx"]/(2*math.pi)*65536))
    return [x, y, z, rz, ry, rx]
def reg2pose(reg):
    x = u16_to_i16(reg[0]) / 1000
    y = u16_to_i16(reg[1]) / 1000
    z = u16_to_i16(reg[2]) / 1000
    rz = u16_to_i16(reg[3])/65536*(2*math.pi)
    ry = u16_to_i16(reg[4])/65536*(2*math.pi)
    rx = u16_to_i16(reg[5])/65536*(2*math.pi)
    return {"x":x, "y":y, "z":z, "rz":rz, "ry":ry, "rx":rx}

def main():
    modbus_address = (lebai.get_item("plugin_apriltag_modbus_address"))['value']
    if not modbus_address:
        modbus_address = ""
    modbus_id = (lebai.get_item("plugin_apriltag_modbus_id"))['value']
    if not modbus_id:
        modbus_id = "7"
    modbus_id = int(modbus_id)
    if modbus_address != "":
        from pymodbus.framer.rtu_framer import ModbusRtuFramer
        from pymodbus.server import StartTcpServer, StartSerialServer
        from pymodbus.datastore import (
            ModbusSequentialDataBlock,
            ModbusSlaveContext,
            ModbusServerContext,
        )

        # 定义co线圈寄存器，存储起始地址为0，长度为20
        co_block = ModbusSequentialDataBlock(0, [False] * 20)
        # 定义di离散输入寄存器，存储起始地址为0，长度为20
        di_block = ModbusSequentialDataBlock(0, [False] * 20)
        # 定义ir输入寄存器，存储起始地址为0，长度为10
        ir_block = ModbusSequentialDataBlock(0, [0] * 10)
        # 定义hr保持寄存器，存储起始地址为0，长度为10
        hr_block = ModbusSequentialDataBlock(0, [0] * 400)
        # 创建从机，从机的di离散量、co线圈、hr保持寄存器、ir输入寄存器等由上面定义并传入
        slaves = {modbus_id: ModbusSlaveContext(di=di_block, co=co_block, hr=hr_block, ir=ir_block, zero_mode=True)}
        # 创建单从机上下文，交由服务器调度
        context = ModbusServerContext(slaves=slaves, single=False)

        thread_modbus = threading.Thread(target=StartSerialServer, kwargs={"context":context, "framer":ModbusRtuFramer, "port":modbus_address, "baudrate":115200})
        thread_modbus.start()

    apriltag_signal = (lebai.get_item("plugin_apriltag_signal"))['value']
    if not apriltag_signal:
        apriltag_signal = "13"
    apriltag_signal = int(apriltag_signal)
    while True:
        time.sleep(0.1)
        apriltag_id = lebai.get_signal(apriltag_signal)
        if apriltag_id > 0:
            apriltag_data = apriltag.main()
            lebai.set_item("plugin_apriltag_tags", json.dumps(apriltag_data))

            lebai.set_signal(apriltag_signal, -1)
        if modbus_address != "" and hr_block.getValues(300)[0] == 1:
            hr_block.setValues(301, 0)
            flange_pose = reg2pose(hr_block.getValues(302, 6))
            apriltag_data = apriltag.find_tags_pose(flange_pose)
            for tag_id, tag in apriltag_data.items():
                tag_num = hr_block.getValues(301)[0] + 1
                hr_block.setValues(301, tag_num)
                if tag_num > 9:
                    break
                hr_block.setValues(301+10*tag_num, int(tag_id))
                hr_block.setValues(302+10*tag_num, pose2reg(tag))
            hr_block.setValues(300, 0)


if __name__ == '__main__':
    main()

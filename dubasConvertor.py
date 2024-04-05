import socket
import struct
from datetime import datetime
import mysql.connector
import time
import binascii

while True:
    # Define the server's IP address and port
    server_ip = "10.9.220.43"  # Replace with your server's IP address
    server_port = 443  # Replace with your server's Modbus port number

    # Define the Modbus unit ID (slave address)
    unit_id = 2  # Replace with your specific unit ID

    # Modbus function code for reading holding registers
    read_holding_registers = 3  # Function code 3 for reading holding registers

    # Register address to read (e.g., address 0)
    register_address = 0

    hex_data = "418000000006020300000014"
    request_packet = bytes.fromhex(hex_data)

    # Number of registers to read
    num_registers_to_read = 20

    # Create a TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    can_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    unprocesseddb = mysql.connector.connect(
            host="121.242.232.211",
            user="emsroot",
            password="22@teneT",
            database='EMS',
            port=3306
        )

    ltocur = unprocesseddb.cursor()

    try:
        # Connect to the Modbus TCP server
        try:
            client_socket.connect((server_ip, server_port))
            # print(client_socket)
        except Exception as ex:
            print(ex)
            time.sleep(10)
            continue

        # print(client_socket)

        # Send the request to the server
        client_socket.send(request_packet)

        # Modbus TCP frame for reading holding registers
        modbus_frame = bytearray([
            unit_id,            # Unit ID (Slave address) 
                                # Function code for reading holding registers
            (register_address >> 8) & 0xFF,  # High byte of register address
            register_address & 0xFF,  # Low byte of register address
            (num_registers_to_read >> 8) & 0xFF,  # High byte of number of registers
            num_registers_to_read & 0xFF,  # Low byte of number of registers
        ])
        

        # Send the Modbus frame to the server
        client_socket.send(modbus_frame)

        # Receive the response from the server
        response = client_socket.recv(1024)  # Adjust the buffer size as needed

        # print(response)
        resp = ''.join([f'{byte:02x}' for byte in response])

        print(resp)
        # resp = str(response)
        clean_li = resp[22:]

        # print(clean_li)

        chunk_size = 4

        res_hex_data = [clean_li[i:i + chunk_size] for i in range(0, len(clean_li), chunk_size)]

        # print(res_hex_data)
        int_lis = []
        # print(len(hex_data[0:-2]))
        # print(hex_data[0:-2])
        print(res_hex_data)       
        for i in res_hex_data:
            if int(i,16) > 60000:
                # print(i,int(i,16)-65535)
                int_lis.append(int(i,16)-65535)
            else:
                # print(i,int(i,16))
                int_lis.append(int(i,16))
        
        # for i in range(1,len(int_lis)):
        #     if i == 8 or i == 9:
        #         print(int_lis[i]/10)
        #     else:
        #         print(int_lis[i])
        
        now = datetime.now()

        # print(int_lis)
        
        try:
            inputVoltageRY = int_lis[0]
        except:
            inputVoltageRY = None
        
        try:
            inputVoltageYB = int_lis[1]
        except:
            inputVoltageYB = None

        try:
            inputVoltageBR = int_lis[2]
        except:
            inputVoltageBR = None
        
        try:
            inputCurrentR = int_lis[3]
        except:
            inputCurrentR = None

        try:
            inputCurrentY = int_lis[4]
        except:
            inputCurrentY = None

        try:
            inputCurrentB = int_lis[5]
        except:
            inputCurrentB = None

        try:
            reservedVoltage = int_lis[6]
        except:
            reservedVoltage = None

        try:
            outputVoltage = int_lis[7]/10
        except:
            outputVoltage = None
        
        try:
            outputCurrent = int_lis[8]/10
        except:
            outputCurrent = None
        
        try:
            reservedCurrent = int_lis[9]
        except:
            reservedCurrent = None
        
        try:
            statusFault = bin(int_lis[10])[2:]
            statusFault = statusFault.rjust(16,'0')
        except:
            statusFault = None

        try:
            currentSet = int_lis[11]
        except:
            currentSet = None
        
        try:
            voltageSet = int_lis[12]
        except:
            voltageSet = None

        try:
            sql = "insert into dubasConverterData(inputVoltageRY,inputVoltageYB,inputVoltageBR,inputCurrentR,inputCurrentY,inputCurrentB,reservedVoltage,outputVoltage,outputCurrent,reservedCurrent,currentSet,voltageSet,recordTimestamp) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            val = (inputVoltageRY,inputVoltageYB,inputVoltageBR,inputCurrentR,inputCurrentY,inputCurrentB,reservedVoltage,outputVoltage,outputCurrent,reservedCurrent,currentSet,voltageSet,now)
            ltocur.execute(sql,val)
            unprocesseddb.commit()
            print(val)
            print("Converter data inserted")
        except Exception as ex:
            print(ex)
            continue
        
        print(statusFault)
        
        try:
            mainsHealth = int(statusFault[15])
        except:
            mainsHealth = None
        
        try:
            dcdcON = int(statusFault[14])
        except:
            dcdcON = None

        try:
            dcdcTrip = int(statusFault[13])
        except:
            dcdcTrip = None

        try:
            inputUnderVoltage = int(statusFault[12])
        except:
            inputUnderVoltage = None

        try:
            inputOverVoltage = int(statusFault[11])
        except:
            inputOverVoltage = None

        try:
            outputUnderVoltage = int(statusFault[10])
        except:
            outputUnderVoltage = None

        try:
            outputOverVoltage = int(statusFault[9])
        except:
            outputOverVoltage = None

        try:
            ShortCircuit = int(statusFault[8])
        except:
            ShortCircuit = None

        try:
            OverTemperature = int(statusFault[7])
        except:
            OverTemperature = None

        try:
            batteryLowVoltage = int(statusFault[6])
        except:
            batteryLowVoltage = None
        
        try:
            reserved1 = int(statusFault[5])
        except:
            reserved1 = None

        try:
            localSelection = int(statusFault[4])
        except:
            localSelection = None

        try:
            remoteSelection = int(statusFault[3])
        except:
            remoteSelection = None
        
        try:
            chargeMode = int(statusFault[2])
        except:
            chargeMode = None

        try:
            dischargeMode = int(statusFault[1])
        except:
            dischargeMode = None

        try:
            reserved2 = int(statusFault[0])
        except:
            reserved2 = None
        
        try:
            sql = "insert into dubasConverterStatus(mainsHealth,dcdcON,dcdcTrip,inputUnderVoltage,inputOverVoltage,outputUnderVoltage,outputOverVoltage,ShortCircuit,OverTemperature,batteryLowVoltage,reserved1,localSelection,remoteSelection,chargeMode,dischargeMode,reserved2,recordTimestamp) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            val = (mainsHealth,dcdcON,dcdcTrip,inputUnderVoltage,inputOverVoltage,outputUnderVoltage,outputOverVoltage,ShortCircuit,OverTemperature,batteryLowVoltage,reserved1,localSelection,remoteSelection,chargeMode,dischargeMode,reserved2,now)
            ltocur.execute(sql,val)
            unprocesseddb.commit()
            print(val)
            print("Converter Status inserted")
        except Exception as ex:
            print(ex)
            continue

    finally:
        # Close the socket
        client_socket.close()

    time.sleep(60)
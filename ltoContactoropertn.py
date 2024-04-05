import socket
import time
from datetime import datetime
import logging

hexON = "11870000000902100011000102001B"
bytON= bytes.fromhex(hexON)

resetConv = "1187000000090210000F0001020017"
resetON = bytes.fromhex(resetConv)

hexOFF = "11870000000902100011000102001C"
bytOFF = bytes.fromhex(hexOFF)

preOFF = bytes.fromhex("851803FF1202FFFFFFFF000000")
preON = bytes.fromhex("851803FF1201FFFFFFFF000000")

mainOFF = bytes.fromhex("851803FF12FF01FFFFFF000000")

logging.basicConfig(
    filename='ltoContactor.log',  # Specify the log file name
    level=logging.DEBUG,     # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def batData():
    bat_server_ip = "10.9.220.42"  # Replace with your server's IP address
    bat_server_port = 15153 

    bat_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        bat_client_socket.connect((bat_server_ip, bat_server_port))
    except Exception as ex:
        print(ex,'to battery')
        logger.info((ex,'to battery'))
        return "exception"

    bat_response = bat_client_socket.recv(10240) 

    bat_hex_string = ' '.join(f"{byte:02X}" for byte in bat_response)

    # print(bat_hex_string)
        
    initial_li = bat_hex_string.split('88 18')

    def ltoBattery(clean_li):
        global batteryVolt
        global mainConsSts
        global preConSts
        global batterySts
        global batteryCurent
        try:
            batteryVolt = clean_li[1] + clean_li[0]
            batteryVolt = int(batteryVolt,16)/10
        except:
            batteryVolt = None

        try:
            mainConsSts = clean_li[4][1]
            preConSts = clean_li[4][0]
                # print("main sts",mainConsSts)
                # print("prests",preConSts)
        except:
            mainConsSts = None
            preConSts = None
        
        try:
            batteryCurent = clean_li[3] + clean_li[2]
            batteryCurent = int(batteryCurent,16) / 100
        except:
            batteryCurent = None
        
        try:
            batterySts = clean_li[5][1]
                # print(batteryCurent)
                # CHG -> 3 , DCHG -> 2 ,
                # print("sts",batterySts)
            if batterySts == '2':
                batterySts = 'IDLE'
            elif batterySts == '3':
                batterySts = 'CHG'
            elif batterySts == '4':
                    # print(batteryCurent)
                if batteryCurent > 3:
                    batterySts = 'DCHG'
                else:
                    batterySts = 'IDLE'
            elif batterySts == '5':
                batterySts = 'FAULT'
            
        except:
            batterySts = None
                    

    def convertLTO(cleaned_li):
        if cleaned_li[0] == "03":
            now = datetime.now()
            ltoBattery(cleaned_li[3:])
    
    def clean_resp(raw_li):
        li = []
        order_li = raw_li.split(" ")
        for i in order_li:
            if len(i) > 1:
                li.append(i)
            if len(li) > 1:
                # print(li)
                convertLTO(li)

    for i in initial_li:
        # print(i)
        clean_resp(i)

    # print(batteryVolt,mainConsSts,preConSts,batterySts)

    return batteryVolt,mainConsSts,preConSts,batterySts,batteryCurent

def Convertor_data():
    conv_server_ip = "10.9.220.43"  # Replace with your server's IP address
    conv_server_port = 443 
        
    conv_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        conv_client_socket.connect((conv_server_ip, conv_server_port))
    except Exception as ex:
        print(ex,'to convertor')
        return "exception"

    hex_data = "418000000006020300000014"
    request_packet = bytes.fromhex(hex_data)

    conv_client_socket.send(request_packet)
    conv_response = conv_client_socket.recv(1024)

    conv_resp = ''.join([f'{byte:02x}' for byte in conv_response])

            # resp = str(response)
    clean_li = conv_resp[22:]

    chunk_size = 4

    conv_hex_data = [clean_li[i:i + chunk_size] for i in range(0, len(clean_li), chunk_size)]

    # print(conv_hex_data)

    conv_int_lis = []

    for i in conv_hex_data:
        if int(i,16) > 60000:
                    # print(i,int(i,16)-65535)
            conv_int_lis.append(int(i,16)-65535)
        else:
                    # print(i,int(i,16))
            conv_int_lis.append(int(i,16))

    try:
        currentSet = conv_int_lis[11]
    except:
        currentSet = None

    try:
        voltageSet = conv_int_lis[12]
    except:
        voltageSet = None
    
    try:
        bytSet = conv_int_lis[16]
    except:
        bytSet = None
    
    try:
        outputVoltage = conv_int_lis[7]/10
    except:
        outputVoltage = None
    
    try:
        outputCurrent = conv_int_lis[8]/10
    except:
        outputCurrent = None
    
    try:
        statusFault = bin(conv_int_lis[10])[2:]
        statusFault = statusFault.rjust(16,'0')
    except:
        statusFault = None
            
    return voltageSet,currentSet,bytSet,outputVoltage,outputCurrent,statusFault


while True:
    curnttime = datetime.now()

    logger.info(curnttime)
    bat_server_ip = "10.9.220.42"  # Replace with your server's IP address
    bat_server_port = 15153 

    bat_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        bat_client_socket.connect((bat_server_ip, bat_server_port))
    except Exception as ex:
        print(ex,'to battery')
        continue

    conv_server_ip = "10.9.220.43"  # Replace with your server's IP address
    conv_server_port = 443 
        
    conv_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        conv_client_socket.connect((conv_server_ip, conv_server_port))
    except Exception as ex:
        print(ex,'to convertor')
        continue

    battData = batData()
    convData = Convertor_data()

    convVoltage = convData[0]
    batVoltage = battData[0]
    mainConsSts = battData[1]
    preConSts = battData[2]
    batSts = battData[3]
    statusFault = convData[5]
    convByteON = int(convData[2])

    if statusFault != None: 
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
    else:
        continue

    print("InUnderVolt",inputUnderVoltage)
    print("InOverVolt",inputOverVoltage)
    print("OutUnderVolt",outputUnderVoltage)
    print("OutOverVolt",outputOverVoltage)
    print("Convertor",convByteON)
    logger.info(("InUnderVolt",inputUnderVoltage))
    logger.info(("InOverVolt",inputOverVoltage))
    logger.info(("OutUnderVolt",outputUnderVoltage))
    logger.info(("OutOverVolt",outputOverVoltage))

    if inputOverVoltage == 1 or inputUnderVoltage == 1 or outputOverVoltage == 1 or outputUnderVoltage == 1:
        # print("inunder :",inputUnderVoltage,"inover :",inputOverVoltage,"outunder :",outputUnderVoltage,"outUnder :",outputOverVoltage)
        logger.info(("inunder :",inputUnderVoltage,"inover :",inputOverVoltage,"outunder :",outputUnderVoltage,"outUnder :",outputOverVoltage))
        conv_client_socket.send(resetON)
        print("Convertor Fault")
        print("Convertor Reset Sent")
        logger.info("Convertor Fault")
        logger.info("Convertor Reset Sent")

    elif convVoltage != None and batVoltage != None:

        if convVoltage != None and convVoltage != 'exception':
            convVoltage = int(convVoltage)
            conv_hex = hex(convVoltage)[2:]
            if len(conv_hex) == 3:
                conv_hex = '0'+conv_hex.upper()
        else:
            continue   

        
        if batVoltage != None and batVoltage != 'exception':
            batVoltage = int(batVoltage)
            bat_hex = hex(batVoltage)[2:]
            if len(bat_hex) == 3:
                bat_hex = '0'+bat_hex.upper()
        else:
            continue  

        convCurrent = int(Convertor_data()[1])

        print("Conv Current",convCurrent)
        print("Main",mainConsSts)
        print("pre",preConSts)   
        print("Battery sts",batSts) 
        print("Convertor voltage",convVoltage,conv_hex)
        print("Battery Voltage",batVoltage,bat_hex)
        logger.info(("Conv Current",convCurrent))
        logger.info(("Main",mainConsSts))
        logger.info(("pre",preConSts))
        logger.info(("Convertor voltage",convVoltage,conv_hex))
        logger.info(("Battery Voltage",batVoltage,bat_hex))
        logger.info(("Battery sts",batSts))

        #--------------------------------------------------------Charge ON------------------------------------------------------------

        def setLowerCurrent(crate):
            print("setting current")
            logger.info("setting current")
            cur_mode = bytes.fromhex("1D5A000000090210000C0001020000")
            conv_client_socket.send(cur_mode)
            conv_client_socket.send(bytON)
            time.sleep(2)
            convData = Convertor_data()
            convByteON = int(convData[2])
            convOutVolt = int(convData[3])
            print(convByteON,convOutVolt)
            try:
                if convByteON == 27:
                    print("Lower current set on Convertor success and Conv out voltage > 300")
                    logger.info("Lower current set on Convertor success and Conv out voltage > 300")
                    SetPreON(crate)
                else:
                    setLowerCurrent(crate)
            except Exception as ex:
                print(ex)
                setLowerCurrent(crate)


        def SendConvVoltage(bat_hex,crate):
            setConvVolt = "029A000000090210000D000102"+bat_hex
            setConvVolt = bytes.fromhex(setConvVolt)   
            conv_client_socket.send(setConvVolt)
            time.sleep(2)
            print(setConvVolt)
            print("Convert voltage sent")
            logger.info("Convert voltage sent")
            convVoltage = int(Convertor_data()[0])
            batVoltage = batData()[0]
            try:
                if convVoltage == batVoltage:
                    print("Battery and Conv volt equal success")
                    logger.info("Battery and Conv volt equal success")
                    setLowerCurrent(crate)
                else:
                    SendConvVoltage(bat_hex,crate)
            except Exception as ex:
                print(ex)
                logger.info(ex)
                SendConvVoltage(bat_hex,crate)

        def CheckPreON(crate):
            preConSts = batData()[2]
            convOutVolt = Convertor_data()[3]
            try:
                if preConSts == '1' and convOutVolt > 300:
                    print("Pre ON Success")
                    logger.info("Pre ON Success")
                    setCHVolt(crate)
                else:
                    SetPreON(crate)
            except Exception as ex:
                print(ex)
                SetPreON(crate)

        def SetPreON(crate):
            bat_client_socket.send(preON)
            time.sleep(2)
            print("Pre ON sent")
            logger.info("Pre ON sent")
            time.sleep(2)
            preConSts = batData()[2]
            print('pre',preConSts)
            logger.info(('pre',preConSts))
            CheckPreON(crate)

        def setCHVolt(crate):
            volt_limit = "01A4"
            setConvVolt = "029A000000090210000D000102"+volt_limit
            setConvVolt = bytes.fromhex(setConvVolt)  
            conv_client_socket.send(setConvVolt)
            time.sleep(2)
            print("Max voltage sent")
            logger.info("Max voltage sent")
            CheckCHVolatge(crate)
        
        def setCHCurrent(crate):
            chg_mode = bytes.fromhex(crate)
            conv_client_socket.send(chg_mode)
            time.sleep(2)
            convCurrent = int(Convertor_data()[1])
            try:
                if convCurrent == 40:
                    print("Current set on Convertor Set Success")
                    print("Charge started")
                    logger.info("Current set on Convertor Set Success")
                    logger.info("Charge started")
                    time.sleep(50)
                else:
                    setCHCurrent(crate)
            except Exception as ex:
                print(ex)
                setCHCurrent(crate)


        def CheckCHVolatge(crate):
            convVoltage = int(Convertor_data()[0])
            try:
                if convVoltage == 420:
                    print("Voltage max set on Conv success")
                    logger.info("Voltage max set on Conv success")
                    setCHCurrent(crate)
                else:
                    print("Convertor voltage and current not set")
                    logger.info("Convertor voltage and current not set")
                    setCHVolt(crate)
            except Exception as ex:
                print(ex)
                setCHVolt(crate)


        def ChargeON(crate):
            SendConvVoltage(bat_hex,crate)
        
        #--------------------------------------------------------Discharge ON------------------------------------------------------------
        
        def setDCCurrent(crate):
            dchg_mode = bytes.fromhex(crate)
            conv_client_socket.send(dchg_mode)
            time.sleep(2)
            convCurrent = int(Convertor_data()[1])
            print(convCurrent)
            try:
                if (convCurrent-1) >= -40:
                    print("Current set on Convertor Set Success")
                    print("Disharge started")
                    logger.info("Current set on Convertor Set Success")
                    logger.info("Disharge started")
                    time.sleep(50)
                else:
                    setDCCurrent(crate)
            except Exception as ex:
                print(ex)
                setDCCurrent(crate)
        
        # def CheckDCVolatge():
        #     convVoltage = int(Convertor_data()[0])
        #     if convVoltage == 420:
        #         print("Voltage max set on Conv success")
        #         setDCCurrent()
        #     else:
        #         print("Convertor voltage and current not set")
        #         setDCVolt()
        
        # def setDCVolt():
        #     volt_limit = "01A4"
        #     setConvVolt = "029A000000090210000D000102"+volt_limit
        #     setConvVolt = bytes.fromhex(setConvVolt)  
        #     conv_client_socket.send(setConvVolt)
        #     time.sleep(2)
        #     print("Max voltage sent")
        #     CheckDCVolatge()
        
        def CheckPreONDC(crate):
            preConSts = batData()[2]
            convOutVolt = Convertor_data()[3]
            try:
                if preConSts == '1' and convOutVolt > 300:
                    print("Pre ON Success")
                    logger.info("Pre ON Success")
                    setDCCurrent(crate)
                else:
                    SetPreONDC(crate)
            except Exception as ex:
                print(ex)
                logger.info(ex)
                SetPreONDC(crate)
        
        def SetPreONDC(crate):
            bat_client_socket.send(preON)
            time.sleep(2)
            print("Pre ON sent")
            logger.info("Pre ON sent")
            time.sleep(2)
            preConSts = batData()[2]
            print('pre',preConSts)
            logger.info(('pre',preConSts))
            CheckPreONDC(crate)
        
        def setLowerCurrentDC(crate):
            print("setting current")
            logger.info("setting current")
            cur_mode = bytes.fromhex("1D5A000000090210000C0001020000")
            conv_client_socket.send(cur_mode)
            conv_client_socket.send(bytON)
            time.sleep(3)
            convData = Convertor_data()
            convByteON = int(convData[2])
            convOutVolt = int(convData[3])
            print(convByteON,convOutVolt)
            logger.info((convByteON,convOutVolt))
            try:
                if convByteON == 27:
                    print("Lower current set on Convertor success and Conv out voltage > 300")
                    logger.info("Lower current set on Convertor success and Conv out voltage > 300")
                    SetPreONDC(crate)
                else:
                    setLowerCurrentDC(crate)
            except Exception as ex:
                print(ex)
                logger.info(ex)
                setLowerCurrentDC(crate)
        
        def SendConvVoltageDC(bat_hex,crate):
            setConvVolt = "029A000000090210000D000102"+bat_hex
            setConvVolt = bytes.fromhex(setConvVolt)   
            conv_client_socket.send(setConvVolt)
            time.sleep(2)
            print(setConvVolt)
            print("Convert voltage sent")
            logger.info(setConvVolt)
            logger.info("Convert voltage sent")
            convVoltage = int(Convertor_data()[0])
            batVoltage = batData()[0]
            try:
                if convVoltage == batVoltage:
                    print("Battery and Conv volt equal success")
                    logger.info("Battery and Conv volt equal success")
                    setLowerCurrentDC(crate)
                else:
                    SendConvVoltageDC(bat_hex,crate)
            except Exception as ex:
                print(ex)
                SendConvVoltageDC(bat_hex,crate)

        def DischargeON(crate):
            SendConvVoltageDC(bat_hex,crate)

        #--------------------------------------------------------Charge OFF------------------------------------------------------------

        def setMainOFF():
            print("Main OFF called")
            logger.info("Main OFF called")
            bat_client_socket.send(mainOFF)
            BatData = batData()
            mainConsSts = BatData[1]
            batCur = BatData[4]
            print(mainConsSts,batCur)
            try:
                if mainConsSts == '2':
                    print("Charge OFF Completed")
                    logger.info("Charge OFF Completed")
                    PreOFFchfOg()
                else:
                    print("Main not OFF")
                    logger.info("Main not OFF")
                    setMainOFF()
            except Exception as ex:
                print(ex)
                setMainOFF()

        
        def SetOFFCur():
            print("current and voltage sending to conv")
            cur_mode = bytes.fromhex("1D5A000000090210000C0001020000")
            conv_client_socket.send(cur_mode)
            setConvVolt = "029A000000090210000D000102"+bat_hex
            setConvVolt = bytes.fromhex(setConvVolt)   
            conv_client_socket.send(setConvVolt)
            time.sleep(2) 
            convData = Convertor_data()
            convVoltage = int(convData[0])
            convCurrent = convData[1]
            convOutCur = convData[4]
            batVoltage = batData()[0]
            print(convVoltage,batVoltage,convCurrent)
            # abs(convVoltage - batVoltage) <= 2
            try:
                if abs(convVoltage - batVoltage) <= 10 and convCurrent == 0 and convOutCur < 2: #and convOutVolt > 300
                    print("Conv and Bat voltage equal and conv current 0 success")
                    logger.info(("Conv and Bat voltage equal and conv current 0 success"))
                    setMainOFF()
                else:
                    print("Conv and Bat voltage not set")
                    logger.info(("Conv and Bat voltage not set"))
                    SetOFFCur()
            except Exception as ex:
                print(ex)
                SetOFFCur()

        def PreOFFchfOg():
            bat_client_socket.send(preOFF)
            preConSts = batData()[2]
            try:
                if preConSts == '2':
                    print("Pre OFF Success")
                    logger.info(("Pre OFF Success."))
                    time.sleep(2)
                    checkBatSts()
                else:
                    PreOFFchfOg()
            except Exception as ex:
                print(ex)
                PreOFFchfOg()
        
        def checkBatSts():
            conv_client_socket.send(bytOFF)
            print("Byte OFF sent")
            logger.info(("Byte OFF sent"))
            time.sleep(3)
            convByteON = int(Convertor_data()[2])
            try:
                if convByteON == 28:
                    print("Charge OFF completed")
                    logger.info(("Charge OFF completed"))
                    time.sleep(50)
                else:
                    checkBatSts()
            except Exception as ex:
                print(ex)
                checkBatSts()
        
        def ChargeOFF():
            SetOFFCur()

            # batterySts = batData()[3]
            # if batterySts == 'IDLE':
            #     print("Battery Went IDLE success")
            #     preOFF()
            # else:
            #     print("Battery not Idle")
            #     checkBatSts()
        # -------------------------------------------------DischargeOFF---------------------------------------------------------
            
        def PreOFFDCof():
            bat_client_socket.send(preOFF)
            preConSts = batData()[2]
            print("Pre OFF sent")
            logger.info(("Pre OFF sent"))
            time.sleep(2) 
            try:
                if preConSts == '2':
                    print("Pre OFF Success.")
                    logger.info("Pre OFF Success.")
                    time.sleep(3)
                    checkBatStsDC()
                else:
                    PreOFFDCof()
            except Exception as ex:
                print(ex)
                PreOFFDCof()

        def setMainOFFDC():
            print("Main OFF called")
            logger.info("Main OFF called")
            bat_client_socket.send(mainOFF)
            time.sleep(2) 
            BatData = batData()
            mainConsSts = BatData[1]
            batCur = BatData[4]
            print(mainConsSts,batCur)
            try:
                if mainConsSts == '2':
                    print("Discharge OFF Completed")
                    logger.info("Discharge OFF Completed")
                    time.sleep(3)
                    PreOFFDCof()
                else:
                    print("Main not OFF")
                    print("Main",mainConsSts)
                    logger.info("Main not OFF")
                    logger.info(("Main",mainConsSts))
                    time.sleep(2)
                    setMainOFFDC()
            except Exception as ex:
                print(ex)
                setMainOFFDC()
        
        def SetOFFCurDC():
            print("current and voltage sending to conv")
            logger.info(("current and voltage sending to conv"))
            cur_mode = bytes.fromhex("1D5A000000090210000C0001020000")
            conv_client_socket.send(cur_mode)
            # setConvVolt = "029A000000090210000D000102"+bat_hex
            # setConvVolt = bytes.fromhex(setConvVolt)   
            # conv_client_socket.send(setConvVolt) 
            time.sleep(2) 
            convCurrent = Convertor_data()[1]
            convOutVolt = Convertor_data()[3]
            convOutCur = Convertor_data()[4]
            print(convCurrent)
            # abs(convVoltage - batVoltage) <= 2
            try:
                if convCurrent == 0 and convOutVolt > 300 and convOutCur < 2:
                    print("Conv and Bat voltage equal and conv current 0 success")
                    logger.info("Conv and Bat voltage equal and conv current 0 success")
                    setMainOFFDC()
                else:
                    print("Conv and Bat voltage not set")
                    logger.info("Conv and Bat voltage not set")
                    SetOFFCurDC()
            except Exception as ex:
                print(ex)
                SetOFFCurDC()
        
        
        def checkBatStsDC():
            conv_client_socket.send(bytOFF)
            print("Byte OFF sent")
            logger.info(("Byte OFF sent"))
            time.sleep(2)
            convByteON = int(Convertor_data()[2])
            try:
                if convByteON == 28:
                    print("Discharge OFF completed")
                    time.sleep(50)
                    logger.info("Discharge OFF completed")
                else:
                    checkBatStsDC()
            except Exception as ex:
                print(ex)
                checkBatStsDC()
            
        def DischargeOFF():
            SetOFFCurDC()

    #----------------------------------------------------------------------------------------------------------------------------
        
        curtime = datetime.now()
        cur = str(curtime)[11:16]

        print(cur)


        if cur == "12":
            print("Charge on called")
            logger.info("Charge off called")
            crate = "1D5A000000090210000C0001020028"  #"1D5A000000090210000C0001020028"
            ChargeON(crate)

        if cur == "":
            conv_client_socket.send(bytOFF)
            print("Byte OFF sent")
            # time.sleep(60)
            # bat_client_socket.send(preOFF)
            # bat_client_socket.send(mainOFF)
            # print("Main OFF sent")

        
        if cur == "":
            print("Charge off called")
            ChargeOFF()
        
        if cur == "":
            print("Discharge on called")
            crate = "1D5A000000090210000C000102FFD8"
            DischargeON(crate)
            logger.info("Discharge on called")

        if cur == "":
            print("Discharge off called")
            DischargeOFF()

        
        if 1==1:
            
            conv_client_socket.send(bytOFF)
            print("Byte OFF sent")
        #     # print("Discharge off called")
        #     # DischargeOFF()
        #     bat_client_socket.send(preON)
        #     time.sleep(2)
        #     print("Pre ON sent")
        #     time.sleep(59)
        
        # if int(batteryVolt) <= 350:
        #     batsts = batData()[3]
        #     if batsts == 'DCHG':
        #         print("Discharge off called")
        #         DischargeOFF()
        
        # if int(batteryVolt) >= 418:
        #     batsts = batData()[3]
        #     if batsts == 'CHG':
        #         print("Charge off called")
        #         ChargeOFF()

    else:
        continue

    time.sleep(3)
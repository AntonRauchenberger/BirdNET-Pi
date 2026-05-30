import serial
import time
import threading

SERIAL_PORT = '/dev/ttyS0'
BAUD_RATE = 9600

# Official u_blox UBX commands for power management
UBX_DEEP_SLEEP = b'\xb5\x62\x06\x04\x04\x00\x00\x00\x08\x00\x16\x74'
UBX_STANDBY_ON = b'\xb5\x62\x06\x11\x02\x00\x08\x01\x22\x92'
UBX_STANDBY_OFF = b'\xb5\x62\x06\x11\x02\x00\x08\x00\x21\x91'

# Global flag to temporarily pause printing of NMEA data
print_nmea = True

def lese_seriell(ser):
    """Background thread that continuously prints incoming lines"""
    global print_nmea
    while True:
        try:
            if ser.is_open:
                raw_line = ser.readline()
                if raw_line and print_nmea:
                    line = raw_line.decode('utf-8', errors='ignore').strip()
                    # Only show GPRMC lines to keep the terminal clean
                    if line.startswith('$GPRMC'):
                        print(f"\r[NEO-6M]: {line}")
                        print("Enter command (sleep/wake/standby_on/standby_off/exit): ", end="", flush=True)
            time.sleep(0.1)
        except:
            break

def main():
    global print_nmea
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        ser.flushInput()
    except Exception as e:
        print(f"Error opening port: {e}")
        return

    # Start the read thread in the background
    thread = threading.Thread(target=lese_seriell, args=(ser,), daemon=True)
    thread.start()

    time.sleep(1)

    while True:
        # Query user input
        cmd = input().strip().lower()

        if cmd == "sleep":
            print_nmea = True  # Ensure NMEA lines are printed until the sleep command is sent
            print("\n--> Sending command: DEEP SLEEP ...")
            ser.write(UBX_DEEP_SLEEP)
            ser.flush()
            print("Note: NMEA data lines ($GPRMC) should STOP immediately!\n")

        elif cmd == "wake":
            print("\n--> Starting u-blox wake-up sequence...")
            
            # 1. Hardware trigger: Generate edge change on RX line
            # We send 3 dummy bytes in a row to ensure the chip wakes up
            ser.write(b'\xFF\xFF\xFF')
            ser.flush()
            
            # 2. Give the processor some time to stabilize the baud rate
            print("Waiting 0.8 seconds for receiver boot and baud rate sync...")
            time.sleep(0.8)
            
            # 3. Official u-blox UBX-CFG-RXM command for CONTINUOUS MODE (full operation)
            # This string sets the receiver permanently back to maximum performance.
            UBX_FORCE_CONTINUOUS = b'\xb5\x62\x06\x11\x02\x00\x08\x00\x21\x91'
            
            print("Sending CFG-RXM (force continuous mode)...")
            ser.write(UBX_FORCE_CONTINUOUS)
            ser.flush()
            print("Note: NMEA data lines should NOW be coming in continuously every second.\n")

        elif cmd == "standby_on":
            print("\n--> Sending command: STANDBY / POWER SAVE MODE ON...")
            ser.write(UBX_STANDBY_ON)
            ser.flush()
            print("Note: The module is entering cyclic power save mode.\n")

        elif cmd == "standby_off":
            print("\n--> Sending command: STANDBY / POWER SAVE MODE OFF...")
            ser.write(UBX_STANDBY_OFF)
            ser.flush()
            print("Note: The module is back to continuous high-performance mode.\n")

        elif cmd == "exit":
            break
        
        time.sleep(0.5)

    ser.close()
    print("Test ended.")

if __name__ == "__main__":
    main()
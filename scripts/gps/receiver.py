"""
Handles the interaction with the Neo 6M GPS module.
"""

import datetime
import time
import serial

try:
    from ..utils.helpers import save_single_setting
except ImportError:
    from utils.helpers import save_single_setting

SERIAL_PORT = '/dev/ttyS0' 
BAUD_RATE = 9600
GPS_READ_ATTEMPTS = 15
GPS_WAKE_BOOT_DELAY = 0.8
GPS_SIGNAL_SETTLE_DELAY = 20
GPS_UPDATE_ATTEMPTS = 20
GPS_RETRY_DELAY = 30

# Official u_blox UBX command
UBX_DEEP_SLEEP = b'\xb5\x62\x06\x04\x04\x00\x00\x00\x08\x00\x16\x74'

# Official u-blox UBX-CFG-RXM command for continuous mode (sets the receiver permanently back to maximum performance)
UBX_FORCE_CONTINUOUS = b'\xb5\x62\x06\x11\x02\x00\x08\x00\x21\x91'


class GPSReceiver:

    @staticmethod
    def _nmea_to_decimal(nmea_val, direction):
        """Converts NMEA coordinate format to decimal degrees"""
        try:
            if not nmea_val or not direction: 
                return None
            if direction in ['N', 'S']:
                degrees = float(nmea_val[:2])
                minutes = float(nmea_val[2:])
            else: # E or W
                degrees = float(nmea_val[:3])
                minutes = float(nmea_val[3:])
            
            decimal = degrees + (minutes / 60.0)
            if direction in ['S', 'W']:
                decimal = -decimal
            return f"{decimal:.4f}"
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_gps_data():
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                ser.reset_input_buffer()
                
                has_no_fix_sentence = False
                for _ in range(GPS_READ_ATTEMPTS):
                    raw_line = ser.readline()
                    if not raw_line:
                        time.sleep(0.1)
                        continue
                        
                    line = raw_line.decode('utf-8', errors='ignore').strip()

                    if line.startswith('$GPRMC'):
                        print(f"Received NMEA sentence from GPS: {line}")
                        parts = line.split(',')
                        
                        if len(parts) > 6:
                            status = parts[2]  # 'A' = Active, 'V' = Invalid
                            
                            if status == 'A':
                                raw_lat = parts[3]
                                lat_dir = parts[4]
                                raw_lon = parts[5]
                                lon_dir = parts[6]
                                
                                lat = GPSReceiver._nmea_to_decimal(raw_lat, lat_dir)
                                lon = GPSReceiver._nmea_to_decimal(raw_lon, lon_dir)
                                
                                if lat and lon:
                                    print(f"GPS fix acquired: Latitude={lat}, Longitude={lon}")
                                    return {"latitude": lat, "longitude": lon, "status": "success"}
                            elif status == 'V':
                                # Keep track if we only see 'V' sentences, which means the GPS is active but has no fix yet
                                has_no_fix_sentence = True
                                
                if has_no_fix_sentence:
                    print("GPS is active but has no fix yet.")
                    return {"latitude": None, "longitude": None, "status": "no_fix"}
                    
                return {"latitude": None, "longitude": None, "status": "waiting"}

        except Exception as e:
            print(f"Error reading gps data: {e}")
            return {"latitude": None, "longitude": None, "status": "error"}
        
    @staticmethod
    def handle_gps_work(gps_active):
        if not gps_active:
            return

        GPSReceiver.deactivate_sleep_mode()

        try:
            # Wait a few seconds to ensure the GPS module has time to wake up and acquire satellite signals
            time.sleep(GPS_SIGNAL_SETTLE_DELAY)

            for attempt in range(GPS_UPDATE_ATTEMPTS):
                gps_data = GPSReceiver.get_gps_data()

                if gps_data.get("status") == "success":
                    save_single_setting("LATITUDE", gps_data["latitude"])
                    save_single_setting("LONGITUDE", gps_data["longitude"])
                    save_single_setting("LAST_GPS_UPDATE", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print("GPS successfully updated")
                    return

                if gps_data.get("status") in ["no_fix", "waiting"] and attempt < GPS_UPDATE_ATTEMPTS - 1:
                    time.sleep(GPS_RETRY_DELAY)
        finally:
            GPSReceiver.activate_sleep_mode()


    @staticmethod
    def activate_sleep_mode():
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                ser.write(UBX_DEEP_SLEEP)
                ser.flush()
                
        except Exception as e:
            print(f"Error activating GPS sleep mode: {e}")

    @staticmethod
    def deactivate_sleep_mode():
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                # Send 3 dummy bytes to trigger wake-up via edge change on RX line
                ser.write(b'\xFF\xFF\xFF')
                ser.flush()

                # Wait for the receiver to boot and stabilize baud rate
                time.sleep(GPS_WAKE_BOOT_DELAY)

                # Set receiver permanently back to maximum performance
                ser.write(UBX_FORCE_CONTINUOUS)
                ser.flush()

        except Exception as e:
            print(f"Error deactivating GPS sleep mode: {e}")
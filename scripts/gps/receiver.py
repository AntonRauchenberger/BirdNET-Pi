import serial

from ..utils.helpers import save_single_setting

SERIAL_PORT = '/dev/ttyACM0' 
BAUD_RATE = 115200

class GPSReceiver:

    @staticmethod
    def get_gps_data():
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                raw_line = ser.readline()
                if raw_line:
                    line = raw_line.decode('utf-8', errors='ignore').strip()

                    if "+CGNSSINFO:" in line:
                        raw_data = line.replace("+CGNSSINFO:", "").strip()
                        parts = raw_data.split(',')

                        if len(parts) > 4 and parts[1] == '1':
                            lat = parts[3]  # 49.013400
                            lon = parts[4]  # 12.101600
                            if lat and lon:
                                return {"latitude": lat, "longitude": lon, "status": "success"}
                            else:
                                return {"latitude": "0.0", "longitude": "0.0", "status": "waiting"}
                        else:
                            return {"latitude": None, "longitude": None, "status": "no_fix"}
        except Exception as e:
            print(f"Error reading gps data: {e}")
            return {"latitude": None, "longitude": None, "status": "error"}
        
    @staticmethod
    def handle_gps_work(gps_active):
        if not gps_active:
            return

        gps_data = GPSReceiver.get_gps_data()
        if gps_data.get("status") == "success":
            import datetime
            save_single_setting("latitude", gps_data["latitude"])
            save_single_setting("longitude", gps_data["longitude"])
            save_single_setting("last_gps_update", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
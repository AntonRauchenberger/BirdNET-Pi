import serial

from ..utils.helpers import save_single_setting

SERIAL_PORT = '/dev/ttyS0' 
BAUD_RATE = 9600

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
            return f"{decimal:.6f}"
        except:
            return None

    @staticmethod
    def get_gps_data():
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                # We read up to 10 lines to ensure we catch the $GPRMC sentence
                for _ in range(10):
                    raw_line = ser.readline()
                    if not raw_line:
                        continue
                        
                    line = raw_line.decode('utf-8', errors='ignore').strip()

                    # NEO-6M specific NMEA sentence for primary navigation data
                    if line.startswith('$GPRMC'):
                        parts = line.split(',')
                        
                        # Safety check
                        if len(parts) > 6:
                            status = parts[2]  # 'A' = Active/Fix, 'V' = Invalid/No Fix
                            
                            if status == 'A':
                                raw_lat = parts[3]   # e.g., 4901.3400
                                lat_dir = parts[4]   # N
                                raw_lon = parts[5]   # e.g., 01210.1600
                                lon_dir = parts[6]   # E
                                
                                lat = GPSReceiver._nmea_to_decimal(raw_lat, lat_dir)
                                lon = GPSReceiver._nmea_to_decimal(raw_lon, lon_dir)
                                
                                if lat and lon:
                                    return {"latitude": lat, "longitude": lon, "status": "success"}
                            else:
                                # Status is 'V' -> Sensor is running but hasn't found satellites yet
                                return {"latitude": None, "longitude": None, "status": "no_fix"}
                                
                # If no $GPRMC sentence was found after 10 lines
                return {"latitude": None, "longitude": None, "status": "waiting"}

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
#!/usr/bin/env python3
"""
Comprehensive pyrometer debugging script
"""

from Pyrometer import Pyrometer
import time

def debug_pyrometer():
    print("=== Pyrometer Debugging ===")
    
    try:
        # Initialize pyrometer
        print("1. Initializing pyrometer...")
        pyrometer = Pyrometer('/dev/cu.usbserial-B00378DF')
        print("✓ Pyrometer connected successfully")
        
        print("\n2. Getting device parameters...")
        try:
            params = pyrometer.get_parameters()
            if params:
                print("✓ Device parameters retrieved")
            else:
                print("⚠ Could not get device parameters")
        except Exception as e:
            print(f"✗ Error getting parameters: {e}")
        
        print("\n3. Setting emissivity...")
        try:
            result = pyrometer.set_emissivity(0.95)
            print(f"✓ Emissivity set: {result}")
            time.sleep(0.5)
        except Exception as e:
            print(f"✗ Error setting emissivity: {e}")
        
        print("\n4. Testing temperature measurements...")
        for attempt in range(5):
            print(f"\nAttempt {attempt + 1}:")
            try:
                # Try default measurement (no channel specified)
                print("  Testing default measurement...")
                temp = pyrometer.measure_temperature()
                if temp is not None:
                    print(f"  ✓ Temperature: {temp}°C")
                else:
                    print("  ⚠ Temperature reading returned None")
                
                # Try channel-specific measurement
                print("  Testing channel 1 measurement...")
                temp1 = pyrometer.measure_temperature(channel=1)
                if temp1 is not None:
                    print(f"  ✓ Channel 1 Temperature: {temp1}°C")
                else:
                    print("  ⚠ Channel 1 temperature reading returned None")
                    
                print("  Testing channel 2 measurement...")
                temp2 = pyrometer.measure_temperature(channel=2)
                if temp2 is not None:
                    print(f"  ✓ Channel 2 Temperature: {temp2}°C")
                else:
                    print("  ⚠ Channel 2 temperature reading returned None")
                    
            except Exception as e:
                print(f"  ✗ Error during measurement: {e}")
            
            time.sleep(1)
        
        print("\n5. Testing device internal temperature...")
        try:
            internal_temp = pyrometer.check_device_temperature()
            if internal_temp is not None:
                print(f"✓ Device internal temperature: {internal_temp}°C")
            else:
                print("⚠ Could not read device internal temperature")
        except Exception as e:
            print(f"✗ Error reading internal temperature: {e}")
            
        print("\n6. Raw communication test...")
        try:
            # Send a simple command and see what we get back
            pyrometer.ser.write('00ms\r'.encode('ascii'))
            time.sleep(0.5)
            raw_response = pyrometer.ser.readline()
            print(f"Raw response to '00ms\\r': {raw_response}")
            decoded = raw_response.decode('ascii', errors='replace').strip()
            print(f"Decoded response: '{decoded}' (length: {len(decoded)})")
            
            if decoded == "":
                print("⚠ Empty response - device may not be responding to commands")
            elif decoded == "88880":
                print("⚠ Device reports temperature outside measurement range")
            elif decoded == "77770":
                print("⚠ Device reports thermostat not ready")
            else:
                try:
                    temp_value = float(decoded) / 10
                    print(f"✓ Parsed temperature: {temp_value}°C")
                except ValueError:
                    print(f"⚠ Could not parse response as temperature: '{decoded}'")
                    
        except Exception as e:
            print(f"✗ Error in raw communication test: {e}")
        
    except Exception as e:
        print(f"✗ Failed to initialize pyrometer: {e}")

if __name__ == "__main__":
    debug_pyrometer()
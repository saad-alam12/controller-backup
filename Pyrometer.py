import serial
import time

class Pyrometer:
    def __init__(self, port):
        self.ser=serial.Serial(port=port, baudrate=19200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, timeout=1)
        if self.ser.is_open:
            print("Serial port is open.")
            
            # Clear any existing data in buffers
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            time.sleep(0.1)
            
            # Get device serial number
            self.ser.write('99sn\r'.encode('ascii'))
            time.sleep(0.3)
            serial_response = self.ser.readline().decode().strip()
            print("Device Serial Number: ", serial_response)
            
            # Clear buffer before next command
            self.ser.reset_input_buffer()
            time.sleep(0.1)
            
            # Get device address
            self.ser.write('99ga\r'.encode('ascii'))
            time.sleep(0.3)
            address_response = self.ser.readline().decode().strip()
            print('Address: ', address_response)
            
            # Clear buffers after initialization
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            time.sleep(0.2)
        else:
            print("Serial port is not open.")

    def set_emissivity(self, emissivity, channel=None):
        if channel is None:
            command = f"00ea{emissivity}"
            self.ser.write((command+'\r').encode('ascii'))
            return f"Emissivity set to {emissivity} for channel 1 and 2."
        else:   
            command = f"00en{channel}{emissivity}"
            self.ser.write((command+'\r').encode('ascii'))
            return f"Emissivity set to {emissivity} for channel {channel}."

    def measure_temperature(self, channel=None):
        if channel is None:
            self.ser.write('00ms\r'.encode('ascii'))
            time.sleep(0.5)
            value = self.ser.readline().decode('ascii', errors='replace').strip()
            
            if value == "88880":
                print("Temperature is outside the measurement range.")
                return None
            elif value == "77770":
                print("Thermostat is not ready.")
                return None
            else:
                try:
                    # Convert the 5-digit decimal number
                    temp = float(value) / 10
                    print(f"Measured temperature: {temp}°C for channel 1 and 2.")
                    return temp
                except ValueError:
                    print(f"Invalid temperature reading: {value}")
                    return None
        else:
            command = f"00kt{channel}\r"
            self.ser.write(command.encode('ascii'))
            time.sleep(0.3)
            value = self.ser.readline().decode('ascii', errors='replace').strip()
            
            if value == "88880":
                print(f"Temperature for channel {channel} is outside the measurement range.")
                return None
            elif value == "77770":
                print(f"Thermostat for channel {channel} is not ready.")
                return None
            else:
                try:
                    # Convert the 5-digit decimal number
                    temp = float(value) / 10
                    print(f"Measured temperature for channel {channel}: {temp}°C")
                    return temp
                except ValueError:
                    print(f"Invalid temperature reading for channel {channel}: {value}")
                    return None

    def check_device_temperature(self):
        self.ser.write('00ti\r'.encode('ascii'))
        time.sleep(0.3)
        value = self.ser.readline().decode('ascii', errors='replace').strip()
        try:
            temp = float(value) / 10
            print(f"Device internal temperature: {temp}°C")
            return temp
        except ValueError:
            print(f"Invalid temperature reading: {value}")
            return None
        
    def get_parameters(self, parameter=None):
        self.ser.write('00pa\r'.encode('ascii'))
        time.sleep(0.3)
        value = self.ser.readline().decode('ascii', errors='replace').strip()
        
        if len(value) < 11:
            print(f"Invalid parameter response: {value}")
            return None
        
        parameters = {
            'emissivity': value[0:2],
            'response_time': value[2],
            'max_value_memory': value[3],
            'analog_output_sensitivity': value[4],
            'internal_temperature': value[5:7],
            'device_address': value[7:9],
            'baudrate': value[9],
            'unused': value[10],
            'emissivity_ratio': value[11:15] if len(value) >= 15 else "N/A"
        }
        
        # Convert values to appropriate types
        parsed_values = {
            'emissivity': int(parameters['emissivity']) / 100,  # Convert to percentage
            'response_time': parameters['response_time'],
            'max_value_memory': parameters['max_value_memory'],
            'internal_temperature': int(parameters['internal_temperature']),
            'device_address': parameters['device_address'],
            'baudrate': parameters['baudrate'],
            'emissivity_ratio': parameters['emissivity_ratio']
        }
        
        # Updated response time values according to manual
        response_times = {
            '0': 'Device time constant',
            '1': '0.01s',
            '2': '0.05s',
            '3': '0.25s',
            '4': '1.00s',
            '5': '3.00s',
            '6': '10.00s'
        }
        
        # Updated max value memory clearing time according to manual
        max_value_times = {
            '0': 'Off',
            '1': '0.01s',
            '2': '0.05s',
            '3': '0.25s',
            '4': '1.00s',
            '5': '5.00s',
            '6': '25.00s',
            '7': 'External clearing',
            '8': 'Automatic'
        }
        
        baudrates = {
            '0': 9600, '1': 19200, '2': 38400, 
            '3': 57600, '4': 115200
        }
        
        # Convert string values to actual values
        if 'baudrate' in parsed_values:
            parsed_values['baudrate'] = baudrates.get(parsed_values['baudrate'], 0)
        
        # Format for user-friendly output
        formatted = {
            'emissivity': f"Emissivity: {parsed_values['emissivity']}",
            'response_time': f"Response time (t90): {response_times.get(parameters['response_time'], 'Unknown')}",
            'max_value_memory': f"Max value memory clearing time (tCL): {max_value_times.get(parameters['max_value_memory'], 'Unknown')}",
            'internal_temperature': f"Internal temperature: {parsed_values['internal_temperature']}°C",
            'device_address': f"Device address: {parsed_values['device_address']}",
            'baudrate': f"Baudrate: {parsed_values['baudrate']} baud",
            'emissivity_ratio': f"Emissivity ratio: {parsed_values['emissivity_ratio']}"
        }
        
        # Return specific parameter or all parameters
        if parameter and parameter in parsed_values:
            print(formatted[parameter])  # Print user-friendly message
            return parsed_values[parameter]  # Return actual value
        else:
            result = "Device Parameters:\n"
            for key, value in formatted.items():
                if key != 'analog_output_sensitivity':  # Skip analog output 
                    result += f"- {value}\n"
            print(result)
            return parsed_values  # Return all values as a dictionary
        



        






    

       


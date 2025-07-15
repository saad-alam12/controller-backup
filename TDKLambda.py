import serial
import time

class TDKLambda:
    def __init__(self, port, address=6, baudrate=9600, timeout=1):
    
        self.port = port
        self.address = address
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

        try:
            self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
            if self.ser.is_open:
                print(f"Serial port {self.port} is open.")
                
                # Address the device 
                addr_command = f"ADR {self.address}\r"
                self.ser.write(addr_command.encode())
                response = self.ser.readline().decode().strip()
                
                if response == "OK":
                    print(f"Device at address {self.address} acknowledged.")
                    
                    # Get Device ID
                    self.ser.write("IDN?\r".encode()) 
                    time.sleep(0.5) 
                    device_id = self.ser.readline().decode().strip()
                    print(f"Device ID: {device_id}")
                else:
                    print(f"Error: Device at address {self.address} did not acknowledge. Response: {response}")
                    self.ser.close()
                    self.ser = None
            else:
                print(f"Error: Serial port {self.port} is not open.")
                self.ser = None
        except serial.SerialException as e:
            print(f"Error opening serial port {self.port}: {e}")
            self.ser = None

    def _send_command(self, command_str, query=False):
        """Helper function to send a command and handle response."""
        if not self.ser or not self.ser.is_open:
            print("Error: Serial port is not connected.")
            return None

        self.ser.write(command_str.encode())
        time.sleep(0.3) # Short delay for command processing
        
        response_lines = []
        if query:
            # For queries, the first line is the data
            line = self.ser.readline().decode().strip()
            response_lines.append(line)
        else:
            # For set commands, expect "OK"
            line = self.ser.readline().decode().strip()
            if line == "OK":
                response_lines.append(line)
            else:
                # Attempt to read more if not "OK" for potential error messages
                response_lines.append(line)
                time.sleep(0.1)
                while self.ser.in_waiting > 0:
                    additional_line = self.ser.readline().decode().strip()
                    if additional_line:
                        response_lines.append(additional_line)
                    else:
                        break
        
        full_response = " | ".join(response_lines)
        # print(f"Sent: '{command_str.strip()}', Received: '{full_response}'") # For debugging
        return full_response


    def set_voltage(self, voltage):
    
        command = f"PV {voltage:.3f}\r" 
        response = self._send_command(command)
        if response == "OK":
            return f"Voltage set to {voltage}V."
        else:
            return f"Error setting voltage: {response if response else 'No response'}"

    def set_current(self, current):
    
        command = f"PC {current:.3f}\r" # [cite: 945]
        response = self._send_command(command)
        if response == "OK":
            return f"Current set to {current}A."
        else:
            return f"Error setting current: {response if response else 'No response'}"

    def get_set_voltage(self):

        command = "PV?\r" 
        response = self._send_command(command, query=True)
        if response:
            try:
                value = float(response)
                
                return value
            except ValueError:
                print(f"Error parsing set voltage: {response}")
                return None
        return None

    def get_set_current(self):
   
        command = "PC?\r" 
        response = self._send_command(command, query=True)
        if response:
            try:
                value = float(response)
                return value
            except ValueError:
                print(f"Error parsing set current: {response}")
                return None
        return None
        
    # methods for getting set values (returning string)
    def voltage_set(self):
        value = self.get_set_voltage()
        if value is not None:
            return f"Voltage is set to {value}V"
        return "Error reading set voltage."
            
    def current_set(self):
        value = self.get_set_current()
        if value is not None:
            return f"Current is set to {value}A"
        return "Error reading set current."


    def output_on(self):
     
        command = "OUT 1\r" 
        response = self._send_command(command)
        if response == "OK":
            return "Output turned on."
        else:
            return f"Error turning output on: {response if response else 'No response'}"

    def output_off(self):

        command = "OUT 0\r" 
        response = self._send_command(command)
        if response == "OK":
            return "Output turned off."
        else:
            return f"Error turning output off: {response if response else 'No response'}"

    def measure_voltage(self):
   
        command = "MV?\r" 
        response = self._send_command(command, query=True)
        if response:
            try:
                value = float(response)
                print(f"Measured voltage: {value}V")
                return value
            except ValueError:
                print(f"Error parsing measured voltage: {response}")
                return None
        return None

    def measure_current(self):

        command = "MC?\r" 
        response = self._send_command(command, query=True)
        if response:
            try:
                value = float(response)
                print(f"Measured current: {value}A")
                return value
            except ValueError:
                print(f"Error parsing measured current: {response}")
                return None
        return None

    def close(self):
        """Closes the serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"Serial port {self.port} closed.")
        self.ser = None

if __name__ == '__main__':

    COM_PORT = '/dev/ttyUSB1'  # Default port for testing
    ADDRESS = 6 

    # Check if a placeholder port is being used
    if COM_PORT == '':
        print("Please update 'COM_PORT' in the example usage section of the script.")
        exit()
    else:
        psu = TDKLambda(port=COM_PORT, address=ADDRESS)

        if psu.ser and psu.ser.is_open:
            print("\n--- Testing Commands ---")
            
            try:
                # Set Voltage and Current
                print(psu.set_voltage(5.0))  # Sets voltage to 5.0V
                time.sleep(0.5)
                print(psu.set_current(0.1))  # Sets current to 0.1A
                time.sleep(0.5)

            # Check programmed values
            # Using Korad-style string output methods
            print(psu.voltage_set())     
            time.sleep(0.5)
            print(psu.current_set())     
            time.sleep(0.5)

            # Alternatively, get float values directly
            # set_volt = psu.get_set_voltage()
            # if set_volt is not None:
            #     print(f"Programmed voltage (float): {set_volt}V")
            # set_curr = psu.get_set_current()
            # if set_curr is not None:
            #     print(f"Programmed current (float): {set_curr}A")

            # Turn Output ON
            print(psu.output_on())
            time.sleep(1) # Wait for output to stabilize

            # Measure Voltage and Current
            meas_v = psu.measure_voltage()
            # if meas_v is not None:
            # print(f"Measured voltage confirm: {meas_v}V") # Already printed in method
            time.sleep(0.5)
            meas_c = psu.measure_current()
            # if meas_c is not None:
            # print(f"Measured current confirm: {meas_c}A") # Already printed in method
            time.sleep(0.5)

            # Turn Output OFF
            print(psu.output_off())

                # Close the connection
                psu.close()
            except Exception as e:
                print(f"Error during testing: {e}")
            psu.output_off()
            psu.close()
        else:
            print("Could not connect to the power supply.")
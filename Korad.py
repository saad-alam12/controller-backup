import serial 
import time

class Korad:
    def __init__(self, port):
        self.ser=serial.Serial(port=port, baudrate=9600, timeout=1)
        if self.ser.is_open:
            print("Serial port is open.")
            self.ser.write('*IDN?\r\n'.encode())
            time.sleep(0.3)
            print("Device ID: ", self.ser.readline().decode())
        else:
            print("Serial port is not open.") 
        
        # sets the voltage and current

    def set_voltage(self, voltage, channel=1):
        command = f"VSET{channel}:{voltage}"
        self.ser.write((command+'\r\n').encode())
        time.sleep(0.5)
        return f"Voltage set to {voltage}V on channel {channel}."
            
    def set_current(self, current, channel=1):
        command= f"ISET{channel}:{current}\r\n"
        self.ser.write(command.encode())
        time.sleep(0.5)
        return f"Current set to {current}A on channel {channel}."

        # checks the set voltage and current

    def voltage_set(self, channel=1):
            self.ser.write(f"VSET{channel}?\r\n".encode())
            value = float(self.ser.readline().decode())
            return f"Voltage is set to {value}V on channel {channel}"
            
    def current_set(self, channel=1):
            self.ser.write(f"ISET{channel}?\r\n".encode())
            value = float(self.ser.readline().decode())
            return f"Current is set to {value}A on channel {channel}"

    def output_on(self):
            self.ser.write(f'OUTP1\r\n'.encode())
            return f"Output turned on."
            
    def output_off(self):
            self.ser.write(f'OUTP0\r\n'.encode())
            return "Output turned off"


    def measure_voltage(self, channel=1):
            self.ser.write(f'VOUT{channel}?\r\n'.encode())
            time.sleep(1)
            value = float(self.ser.readline().decode())
            print(f"Measured voltage: {value}V on channel {channel}")
            return value
            
    def measure_current(self, channel=1):
            self.ser.write(f'IOUT{channel}?\r\n'.encode())
            time.sleep(1)
            value = float(self.ser.readline().decode())
            print(f"Measured current: {value}A on channel {channel}")
            return value 




      
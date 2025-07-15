#!/usr/bin/env python3
"""
Interactive command-line test script for TDK Lambda PSU
Allows manual testing of all PSU functions from the command line
"""

import sys
import time
from TDKLambda import TDKLambda

def print_menu():
    """Display the main menu options"""
    print("\n" + "="*50)
    print("TDK Lambda PSU Test Console")
    print("="*50)
    print("1. Set voltage")
    print("2. Set current") 
    print("3. Get set voltage")
    print("4. Get set current")
    print("5. Turn output ON")
    print("6. Turn output OFF")
    print("7. Measure voltage")
    print("8. Measure current")
    print("9. Get device status")
    print("10. Run quick test sequence")
    print("0. Exit")
    print("-"*50)

def get_float_input(prompt, min_val=None, max_val=None):
    """Get float input with validation"""
    while True:
        try:
            value = float(input(prompt))
            if min_val is not None and value < min_val:
                print(f"Value must be >= {min_val}")
                continue
            if max_val is not None and value > max_val:
                print(f"Value must be <= {max_val}")
                continue
            return value
        except ValueError:
            print("Please enter a valid number")

def run_quick_test(psu):
    """Run a quick test sequence"""
    print("\n--- Running Quick Test Sequence ---")
    
    # Set safe values
    print("Setting voltage to 1kV...")
    result = psu.set_voltage(1000)
    print(result)
    time.sleep(0.5)
    
    print("Setting current to 0.1A")
    result = psu.set_current(0.1)
    print(result)
    time.sleep(0.5)
    
    # Check set values
    print("Reading set values...")
    print(psu.voltage_set())
    print(psu.current_set())
    time.sleep(0.5)
    
    # Turn on briefly
    print("Turning output ON...")
    print(psu.output_on())
    time.sleep(2)
    
    # Measure
    print("Measuring actual values...")
    psu.measure_voltage()
    psu.measure_current()
    time.sleep(0.5)
    
    # Turn off
    print("Turning output OFF...")
    print(psu.output_off())
    
    print("--- Quick Test Complete ---")

def main():
    """Main interactive loop"""
    # Get serial port from user
    print("TDK Lambda PSU Test Script")
    print("Default port: /dev/ttyUSB1")
    port = input("Enter serial port (or press Enter for default): ").strip()
    if not port:
        port = "/dev/ttyUSB1"
    
    # Get device address
    print("Default address: 6")
    addr_input = input("Enter device address (or press Enter for default): ").strip()
    if addr_input:
        try:
            address = int(addr_input)
        except ValueError:
            print("Invalid address, using default (6)")
            address = 6
    else:
        address = 6
    
    # Initialize PSU
    print(f"\nConnecting to PSU on {port} at address {address}...")
    try:
        psu = TDKLambda(port=port, address=address)
        
        if not psu.ser or not psu.ser.is_open:
            print("Failed to connect to PSU. Exiting.")
            return
            
    except Exception as e:
        print(f"Error connecting to PSU: {e}")
        return
    
    print("Connected successfully!")
    
    # Main loop
    try:
        while True:
            print_menu()
            choice = input("Enter choice (0-10): ").strip()
            
            if choice == "0":
                break
                
            elif choice == "1":
                voltage = get_float_input("Enter voltage (V): ", 0, 80)
                result = psu.set_voltage(voltage)
                print(f"Result: {result}")
                
            elif choice == "2":
                current = get_float_input("Enter current (A): ", 0, 20)
                result = psu.set_current(current)
                print(f"Result: {result}")
                
            elif choice == "3":
                result = psu.voltage_set()
                print(f"Result: {result}")
                
            elif choice == "4":
                result = psu.current_set()
                print(f"Result: {result}")
                
            elif choice == "5":
                result = psu.output_on()
                print(f"Result: {result}")
                
            elif choice == "6":
                result = psu.output_off()
                print(f"Result: {result}")
                
            elif choice == "7":
                voltage = psu.measure_voltage()
                if voltage is not None:
                    print(f"Measured voltage: {voltage}V")
                else:
                    print("Failed to measure voltage")
                    
            elif choice == "8":
                current = psu.measure_current()
                if current is not None:
                    print(f"Measured current: {current}A")
                else:
                    print("Failed to measure current")
                    
            elif choice == "9":
                print("Device Status:")
                print(f"  {psu.voltage_set()}")
                print(f"  {psu.current_set()}")
                
            elif choice == "10":
                confirm = input("Run quick test sequence? (y/n): ").lower()
                if confirm == 'y':
                    run_quick_test(psu)
                    
            else:
                print("Invalid choice. Please try again.")
                
            input("\nPress Enter to continue...")
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        
    finally:
        print("\nTurning off output and closing connection...")
        try:
            psu.output_off()
            psu.close()
        except:
            pass
        print("Done.")

if __name__ == "__main__":
    main()
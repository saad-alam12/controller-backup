import Korad as korad

psu=korad.Korad("/dev/cu.usbmodem00273B64024C1")

try:
  
    print(psu.output_on())

    print(psu.set_voltage(20.0))


    print(psu.set_current(1.0))

  
    print(psu.voltage_set())
    print(psu.current_set())


    print(psu.output_off())

except Exception as e:
    print(f"An error occurred: {e}")

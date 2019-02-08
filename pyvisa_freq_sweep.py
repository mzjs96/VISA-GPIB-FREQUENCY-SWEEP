import visa
import time
import sys
import math
import csv
import numpy

def freq_sweep():
    try:
        # Connect to the instrument
        rm = visa.ResourceManager()

        list_res = rm.list_resources()
        #('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::82::INSTR')
        if list_res is not None:
            inst = rm.open_resource(list_res[0])
        else:
            print('Error: Resources not found, please check connections.')
            sys.exit(1)
        #automatically connects to the default resource (first detected)
    except:
        print('Error connecting to the instrument!')
        sys.exit(1)
    
    #print(inst.query("*IDN?"))
    print("Connected:" + inst)

    #Set the default center frequency
    inst.write(':FREQ:CENT 66 MHz')
    #Set the default step frequency
    inst.write(':FREQ:CENT:STEP 11 MHz')

    #Open the CSV file descriptor
    with open('test1.csv', 'wb') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter = ' ', quotechar = '|')

    time.sleep(3)

    ###parameters to be changed here:
    ################################################

    freq_unit = 'MHz'
    power_unit = 'dBm'
    initial_freq = 66
    step_freq = 11
    steps = 32
    delay = 5

    #Choose whether to average the power when measuring:
    averaging = True

    #Set the Delay Time when calculating power:
    meas_pwr_delay = 10

    ################################################

    curr_freq = initial_freq

    #set the center frequency
    #Format: :FREQ:CENT 66 MHz'
    inst.write(':FREQ:CENT '+ str(initial_freq) + ' ' + freq_unit)

    #set the center frequency step
    #Format: :FREQ:CENT:STEP 11 MHz'
    inst.write(':FREQ:CENT:STEP '+ str(step_freq) + ' ' + freq_unit)

    #set the number of average if averaging is on
    if averaging:
        inst.write('AVER ON')
        inst.write('AVER:COUN 10')
    else:
        inst.write('AVER OFF')

    for i in range(steps):
        curr_freq = 66 + i * step_freq
        #calculate the value of center frequency
        inst.write('CALC:MARK:CENT')
        time.sleep(delay)

        #calcualte the Y-coordinate of the center frequency (measure the peak power)
        inst.write('CALC:MARK:Y?')
        time.sleep(meas_pwr_delay)

        meas_pwr = float(inst.read())
        #Stdout current frequency, number of steps, and measured power
        print("Current Frequency: " + curr_freq + freq_unit + ' , Step: ' + i + ' , Measured Power: ' + meas_pwr + ' ' + power_unit)

        #increment the frequency by step
        inst.write('FREQ:CENT UP')
        time.sleep(delay)

        #write to CSV file:
        csvwriter.writerow(i + 1, curr_freq, meas_pwr)
    return

if __name__ == '__main__':
    freq_sweep()
    print("Success: Frequency sweep ends.")
    sys.exit()


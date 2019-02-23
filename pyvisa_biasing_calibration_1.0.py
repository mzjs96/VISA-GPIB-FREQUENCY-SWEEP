import visa
import datetime
import time
import sys
import math
import csv
import collections
from decimal import *
import os.path

class FreqSweep():
    def __init__(self, freq_start, freq_end, multiplier, version, sa_cent_freq, freq_step):
        getcontext().prec = 15
        self.freq_start = freq_start
        self.freq_step = freq_step
        self.freq_end = freq_end
        self.multiplier = multiplier
        self.version = version
        self.sa_cent_freq = sa_cent_freq

        self.sweep_freq_start = Decimal(freq_start+0.065) / Decimal(multiplier)
        self.sweep_freq_step = Decimal(self.freq_step)/Decimal(multiplier)

        #instances for instruments
        self.vs = None      #Voltage Source
        self.sg = None      #Signal Generator
        self.sa = None      #Spectrum Analyzer
        self.rm = None      #Resource Manager

        self.freq_volt = collections.defaultdict()  #Frequency to Vg mapping that optimizes output power
        self.num_step = int((freq_end - freq_start)/self.freq_step) + 1 #number of steps increment by 5GHz(step frequency) when in the frequency range

        self.is_calibrated = False

    def initialize_instrument(self):
        try:
            # Connect to the instrument
            self.rm = visa.ResourceManager()
            list_res = self.rm.list_resources()
            # example: ('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::82::INSTR')

            print("Resource list:")
            print(list_res)

            #automatically connects to the default resource (needs to be checked and possibly changed every time the connection is set up.
            if len(list_res) == 3:
                self.vs = self.rm.open_resource(list_res[0])      # Voltage Source
                self.sg = self.rm.open_resource(list_res[1])      # E8257D signal generator to be sweeped
                self.sa = self.rm.open_resource(list_res[2])      # Spectrum Analyzer
            else:
                print('Error: Not all resources were found, please check connections!')
                sys.exit(1)
        except:
            print('Error connecting to the instrument!')
            sys.exit(1)

        if not self.vs or not self.sg or not self.sa:
            #Throw warning and exit if any one of the instrument fails to connect
            print('Error occurred when connecting to the instrument!')    
            sys.exit(1)

        print("Initialization Success. All instruments are connected!")

        #set the output port to 2 (Vg port):
        self.vs.write('INST:SEL OUT2')
        #Set the voltage protection for voltage source:

        self.vs.write("VOLT 0")
        self.vs.write("OUTP ON")

        return 

    def biasing_calibration(self):
        ###########################################################################
        #Parameters for the voltage source sweep to be changed HERE:

        initial_voltage = 0.1 #Volts
        volt_steps = 41  #steps to go up
        volt_step = 0.01
        
        #Sweeping through this range of voltage: 50 mV to 500 mV, step: 10mV for each frequency
        ###########################################################################
        
        #Initialize the spectrum analyzer to frequency to be measured:
        self.sa.write(':FREQ:CENT 0.065 GHz')
        #Set the market to the center
        self.sa.write('CALC:MARK:CENT') 

        #set the number of averaging to be measured in the spectrum analyzer
        self.sa.write('AVER ON')
        self.sa.write('AVER:COUN 10')

        #Initialize the Signal Generator
        curr_freq = self.freq_start
        curr_sweep_freq = self.sweep_freq_start

        self.sg.write(':FREQ:FIX ' + str(self.sweep_freq_start) + ' GHz')
        self.sg.write(':FREQ:STEP ' + str(self.sweep_freq_step) + ' GHz')

        #Set the power of the signal:
        #Command ':POW 0DBM'
        #Page 164 in SCPI command reference
        
        volt_pwr = collections.defaultdict()

        time.sleep(2)
        file_name = 'data_2_22_2019_220-300ghz_100-500mv.csv'

        #open the csv file and record the data
        with open(file_name, 'wb') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter = ',', quotechar = '|')
            csvwriter.writerow(['FREQ','V_G','MEAS_PWR'])

            #iterate through the frequency range
            for i in range(self.num_step):
                #special case: if the frequency reaches the higher limit, sweep with the frequency within the range:
                '''
                if i + 1 == self.num_step:
                    #TO BE CHECKED LATER
                    curr_sweep_freq = Decimal(curr_sweep_freq) - Decimal(2 * 0.065/self.multiplier)
                    print(float(curr_sweep_freq))
                    self.sg.write(':FREQ:FIX ' + str(curr_sweep_freq) + ' GHz')
                '''
                #iterate through all the voltages:
                curr_volt = initial_voltage
                volt_pwr.clear()
                for j in range(volt_steps):
                    #Safety Procedure: Check if the voltage is in the safe range
                    if (curr_volt) > 0.65:
                        print("Error: Voltage is too high! Please check voltage step and try again")
                        sys.exit(1)
                    self.vs.write('VOLT ' + str(curr_volt))
                    time.sleep(0.5)
                    self.sa.write('AVER:CLE')
                    time.sleep(25)
                    #measure the power and store accordingly
                    self.sa.write('CALC:MARK:CENT') 
                    time.sleep(0.5)
                    self.sa.write('CALC:MARK:Y?')
                    time.sleep(0.5)
                    meas_pwr = float(self.sa.read())

                    #write biasing data into the file
                    print("{0:.2f}".format(round(curr_volt, 2)), meas_pwr)

                    #write data to CSV:
                    csvwriter.writerow([curr_freq, "{0:.2f}".format(round(curr_volt, 2)), meas_pwr])

                    volt_pwr[curr_volt] = meas_pwr
                    curr_volt += volt_step

                    #increment the voltage by step
                    #curr_volt += volt_step

                #store highest voltage at current frequency into hashmap
                max_volt = max(volt_pwr, key = volt_pwr.get)
                self.freq_volt[curr_freq] = max_volt
                max_pwr = max(volt_pwr.values())
                print('Frequency: ' + str(curr_freq) + ', Maximum power voltage: ' + str(max_volt) + ', Maximum power: ' + str(max_pwr))

                #increment frequency
                self.sg.write(':FREQ UP')
                time.sleep(2)
                self.sa.write('AVER:CLE')
                curr_freq += self.freq_step
                curr_sweep_freq += self.sweep_freq_step

        self.is_calibrated = True
        print('SUCCESS: Mapping of the voltage that produces highest power for each frequency (freq->volt)')
        print(self.freq_volt)

        #reset the voltage source and return
        self.vs.write('VOLT 0')
        
        #record map to local csv file
        self.write_vmap_to_csv(self.freq_volt)
        return  
    
    def write_vmap_to_csv(self, mydict):
        with open('freq_volt_map.csv', 'w') as csv_file:
            writer = csv.writer(csv_file)
            for key, value in mydict.items():
                writer.writerow([key, value])
    
    def read_vmap_from_csv(self):
        try:
            with open('freq_volt_map.csv') as csv_file:
                reader = csv.reader(csv_file)
                mydict = dict(reader)
            return mydict
        except:
            return None

if __name__ == '__main__':
    #Parameters: start frequency, end frequency, mixer multiplier(1/3/18), version(0/1/2), spectrum analyzer center frequency (GHz), Frequency Step
    FS = FreqSweep(220, 300, 18, 0, 0.065, 5)
    FS.initialize_instrument()
    #input("Initialization done. Press Enter to continue...")
    FS.biasing_calibration()
    #input("Calibration done. Press Enter to continue...")
    #FS.frequency_sweep()
    #input("Frequency sweep done. Press Enter to exit...")
    sys.exit(0)
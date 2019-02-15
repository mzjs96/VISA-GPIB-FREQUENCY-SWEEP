import visa
import datetime
import time
import sys
import math
import csv
import collections

class FreqSweep():
    def __init__(self, freq_start, freq_end, multiplier, version, sa_cent_freq):
        self.freq_start = freq_start
        self.freq_end = freq_end
        self.multiplier = multiplier
        self.version = version
        self.sa_cent_freq = sa_cent_freq

        self.sweep_freq_start = float((freq_start+0.065)/multiplier)
        self.sweep_freq_step = float(5.065/3)

        #instances for instruments
        self.vs = None      #Voltage Source
        self.sg = None      #Signal Generator
        self.sa = None      #Spectrum Analyzer
        self.rm = None      #Resource Manager

        self.freq_volt = collections.defaultdict()  #Frequency to Vg mapping that optimizes output power
        self.num_step = int((freq_start - freq_end)/5) #number of steps increment by 5GHz when in the frequency range

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
        return 

    def biasing_calibration(self):
        ###########################################################################
        #Parameters for the voltage source sweep to be changed HERE:

        initial_voltage = 0.05 #Volts
        volt_steps = 25  #steps to go up
        volt_step = 0.01
        
        #Sweeping through this range of voltage: 50 mV to 500 mV, step: 10mV for each frequency
        ###########################################################################
        
        #Initialize the spectrum analyzer to frequency to be measured:
        self.sa.write(':FREQ:CENT 0.065 GHz')
        #Set the market to the center
        self.sa.write('CALC:MARK:CENT') 

        #set the number of averaging to be measured in the spectrum analyzer
        self.sa.write('AVER ON')
        self.sa.write('AVER:COUN 15')

        #Initialize the Signal Generator
        cur_freq = self.freq_start
        freq_step = 5
        cur_sweep_freq = self.sweep_freq_start

        self.sg.write(':FREQ:FIX ' + str(self.sweep_freq_start) + ' GHz')
        self.sg.write(':FREQ:STEP ' + str(self.sweep_freq_step) + ' GHz')
        
        volt_pwr = collections.defaultdict()
        
        #iterate through the frequency range
        for _ in range(self.num_step):
            #iterate through all the voltages
            curr_volt = initial_voltage

            for j in range(volt_steps):
                #Safety Procedure: Check if the voltage is in the safe range
                if (curr_volt + j * 0.01) > 0.5:
                    print("Error: Voltage is too high! Please check voltage step and try again")
                    sys.exit(1)

                self.vs.write('VOLT ' + str(curr_volt + j * 0.01))

                #measure the power and store accordingly
                self.sa.write('CALC:MARK:Y?')
                time.sleep(20)
                meas_pwr = float(self.sa.read())
                volt_pwr[curr_volt] = meas_pwr

                #increment the voltage by step
                curr_volt += volt_step

            #store highest voltage at current frequency into hashmap
            self.freq_volt[cur_freq] = max(volt_pwr, key = volt_pwr.get)

            #increment frequency
            self.sg.write(':FREQ UP')
            cur_freq += freq_step
            cur_sweep_freq += self.sweep_freq_step

        self.is_calibrated = True
        print('Success: Mapping of the voltage that produces highest power for each frequency (freq:volt):')
        print(self.freq_volt)

        #reset the voltage source and return
        self.vs.write('VOLT 0')
        return  

    def frequency_sweep(self):
        #Open the CSV file descriptor
        try:
            with open('test_data.csv', 'wb') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter = ' ', quotechar = '|')
        except:
            print('ERROR: CSV file open failed! Please check file path and name.')
            sys.exit(1)
        
        #Record time and import header
        csvwriter.writerow(datetime.datetime.now())
        csvwriter.writerow('TEST_NUMBER,CURR_FREQ,SWEEP_FREQ,V_G,MEAS_PWR')

        #parameters for frequency sweep to be changed HERE:
        ########################################################

        #Choose whether to average the power when measuring:
        averaging = True

        #Set the Delay Time when calculating power:
        meas_pwr_delay = 20

        ########################################################

        #loading the biasing calibration:
        if not self.is_calibrated:
            self.freq_volt = self.read_from_csv()

        curr_freq = self.freq_start
        curr_sweep_freq = self.sweep_freq_start

        #Configure the Spectrum Analyzer:
        #Initialize the spectrum analyzer to frequency to be measured:
        self.sa.write(':FREQ:CENT 0.065 GHz')
        #Set the market to the center
        self.sa.write('CALC:MARK:CENT') 
        #set the number of average if averaging is on
        if averaging:
            self.sa.write('AVER ON')
            self.sa.write('AVER:COUN 15')
        else:
            self.sa.write('AVER OFF')
        
        #Configure the Signal Generator:
        self.sg.write(':FREQ:FIX ' + str(self.sweep_freq_start) + ' GHz')
        self.sg.write(':FREQ:STEP ' + str(self.sweep_freq_step) + ' GHz')
        time.sleep(2)

        for i in range(self.num_step):
            #edge case for frequency step when it reaches the range limit: (TO DO)
            #if i + 1 == self.num_step:

            #calculate the value of center frequency
            self.sa.write('CALC:MARK:CENT')

            #calcualte the Y-coordinate of the center frequency (measure the peak power)
            self.sa.write('CALC:MARK:Y?')
            time.sleep(meas_pwr_delay)

            meas_pwr = float(self.sa.read())
            #Stdout current frequency, number of steps, and measured power
            print("Current Frequency: " + curr_freq + 'Current Sweep Frequency: ' + curr_sweep_freq + ', Step: ' + i + ' , Measured Power: ' + meas_pwr)

            #increment the frequency by step
            self.sg.write('FREQ UP')
            time.sleep(2)

            #write to CSV file:
            csvwriter.writerow(i + 1, curr_freq, curr_sweep_freq, meas_pwr)
        return
    
    def write_to_csv(self, mydict):
        with open('freq_volt_map.csv', 'w') as csv_file:
            writer = csv.writer(csv_file)
            for key, value in mydict.items():
                writer.writerow([key, value])
    
    def read_from_csv(self):
        with open('dict.csv') as csv_file:
            reader = csv.reader(csv_file)
            mydict = dict(reader)
        return mydict

if __name__ == '__main__':
    #Parameters: start frequency, end frequency, mixer multiplier(1/3/18), version(0/1/2), spectrum analyzer center frequency (GHz)
    FS = FreqSweep(140, 200, 3, 0, 0.065)
    FS.initialize_instrument()
    FS.biasing_calibration()
    FS.frequency_sweep()

    sys.exit(0)
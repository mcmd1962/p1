#!/usr/bin/env python2
# vim: set autoindent filetype=python tabstop=4 shiftwidth=4 softtabstop=4 number textwidth=175 expandtab:
# vim: set fileencoding=utf-8

"""
This script is collecting information as being provided from the P1 port on an electical usage meter and is
based on code as made available by Ge Janssen, see:
   http://gejanssen.com/howto/Slimme-meter-uitlezen/index.html

"""
#===============================================================================
#
#         FILE:  P1reader.py
#
#        USAGE:  ./P1reader.py
#
#  DESCRIPTION:  Reads P1 'Slimme Meter' and stores in RRD file
#                Based on code and information given by Ge Janssen, see:
#                   http://gejanssen.com/howto/Slimme-meter-uitlezen/index.html
#
#       AUTHOR:  Marcel (MCMD), Marcel@....
#      COMPANY:
#      VERSION:  1.0
#      CREATED:  20130320 20:59
# DEPENDENCIES:
#
#      HISTORY:
#                + 20130320/MCMD: Creation of script
#===============================================================================

import time
import datetime
import sys
import re
import os.path
import serial
import ConfigParser
import signal


def do_exit(sig, stack):
    raise SystemExit('Exiting')
    power_meter.flush_data()
    power_meter.print_html()
    power_meter.print_csv()
    power_meter.close_port(ser)

# ##############################################################################
#===  CLASS  ===================================================================
#         NAME:  SlimmeMeter
#      PURPOSE:  Interface to P1 port of 'Slimme Meter'
#     COMMENTS:  none
#     SEE ALSO:  n/a
#===============================================================================


P1MESSAGE_RGX  = re.compile(r'(?P<key>\S+:\S+)\((?P<value>\S+)\)')
REALVALUE_RGX  = re.compile(r'(?P<value>\d+\.\d+)')

class SlimmeMeter():

    """
      This class contains the logic to communicate with the serial port, fetch data,
      store data and generate reports.
    """
    def __init__(self, ser):
        self.measurements = []
        self.lastten = []
        self.csvdata = []
        self.csvverbruik = []
        self.csvfm   =  0  # first moment
        self.ser     = ser
        ser.bytesize = serial.SEVENBITS
        ser.parity   = serial.PARITY_EVEN
        ser.stopbits = serial.STOPBITS_ONE
        ser.xonxoff  =  0
        ser.rtscts   =  0
        ser.timeout  = 20

    def open_port(self, ser, baudrate=9600, port="/dev/ttyUSB0"):
        """
            Opens the serial port using ttyUSB0 (USB <-> Serial)
        """
        #Set COM port config
        ser.baudrate = baudrate
        ser.port     = port

        #Open COM port
        try:
            ser.open()
        except serial.SerialException:
            sys.exit ("Fout bij het openen van %s. Aaaaarch."  % ser.port)

        print "Poort %s geopend" % ser.port


    def print_html(self):
        """
           Print out an html page with last period information.
        """
        lastminute_file = open('/usr/share/nginx/html/p1/lastm.html', 'w')
        lastminute_file.write(''' <html>
      <head>
         <title>Electriciteitsverbruik laatste 10 metingen</title>
         <meta http-equiv="refresh" content="10" />
         <meta http-equiv="pragma" content="no-cache" />
         <meta http-equiv="cache-control" content="no-cache" />
         <meta http-equiv="content-type" content="text/html; charset=iso-8859-1" />
      </head>
      <body>
         <font size="4">
         <big>
      ''')
        lastminute_file.write("<H1>Vermogensverbruik</H1>now: %s <br><br>\n<table>\n" % time.strftime("%Y%m%d", time.localtime()) )

        for epoch_time, power_watt in self.lastten:
            time_fmt = time.strftime("%H:%M:%S", time.localtime(epoch_time))
            power = 1000 * power_watt
            lastminute_file.write("   <tr><td>%s</td> <td><b>%dW</b></td></tr>\n" % (time_fmt, power))

        lastminute_file.write('</big></table><br><br><a href="lastm.html">refresh</a></font></body></html>')
        lastminute_file.close()

    def print_csv(self):
        """
           Print out an csv file with last period information.
        """
        csv_file = open("/home/user/data/p1reading-%s.csv" % time.strftime("%Y%m%d-%H%M%S", time.localtime()), 'w')

        # from self.csvverbruik determine average, min, max and median
        for epoch_time, power_watt, csvverbruiklist in self.csvdata:
            N = 0
            min = 999999
            max = 0
            sum = 0
            for e in csvverbruiklist:
                if e > max:
                    max = e
                if e < min:
                    min = e
                sum += e
                N   += 1
            avg = sum / N

            time_fmt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch_time))
            csv_file.write("%s, %s, %s, %s, %s\n" % (time_fmt, power_watt, min, avg, max ))

        csv_file.close()
        self.csvdata     = []


    def close_port(self, ser):
        """
           Close the serial connection.
        """
        try:
            ser.close()
        except serial.SerialException:
            sys.exit ("Oops %s. Programma closed. Could not close the serial port." % ser.name )

    def read_port_value(self, ser, first_line='ISk5'):
        """
           Read a datagram from the serial port. This looks like the following:

           /ISk52MT382-1003
           1-0:1.8.1(00438.023*kWh)
           1-0:1.8.2(00384.391*kWh)
           1-0:2.8.1(00000.000*kWh)
           1-0:2.8.2(00000.001*kWh)
           0-0:96.14.0(0002)
           1-0:1.7.0(0000.62*kW)
           1-0:2.7.0(0000.00*kW)
           0-0:17.0.0(0999.00*kW)
           0-0:96.3.10(1)
           0-0:96.13.1()
           0-0:96.13.0()
           !

           Used notation: OBIS (IEC 62056-61 Object Identification System)

           http://en.wikipedia.org/wiki/IEC_62056

           B : C.D.E * F
           where:
           + B: energy metering channel 1-6.
                Not indicated for a single self-metering channel when no external channels are defined.
           + C: identifies a physical instrumentation quantity, like the type of a source power and
                its direction. 0 identifes general purpose objects.
           + D: identifies a quantity processing algorithm, like time accumulation, maximum and
                cumulative maximum.
           + E: tariff rate 1...8, or 0 for total readings.
           + F: billing period 0-3, 0 (not indicated) for present billing period, 1 for the first previous
                (last) period, 2 for the second previous billing period, 3 for the third previous billing
                period.

        """

        #Initialize
        p1_line = ''
        epochtime_now = 0
        data = dict()
        timestart = time.time()

        while not (data.has_key('1-0:1.7.0') and data.has_key('1-0:1.8.1') and data.has_key('1-0:1.8.2')):

            #When it takes more than delta seconds to finish this loop, than please report this:
            if time.time() - timestart > 30:
                timestart = time.time()
                print "%s ERROR: not all data values present in time, need 1-0:1.7.0, 1-0:1.8.1 and 1-0:1.8.2, but have:" % time.strftime('%Y-%m-%d %H:%M:%S')
                print "   data=%s" % data

            #Read a line van de seriele poort
            try:
                p1_raw = ser.readline()
            except serial.SerialException:
                sys.exit ("Seriele poort %s kan niet gelezen worden. Aaaaaaaaarch." % ser.name )

            p1_str  = str(p1_raw)
            p1_line = p1_str.strip()
            p1message_match = P1MESSAGE_RGX.match( p1_line )
            if p1message_match:
                key   = p1message_match.group('key')
                value = p1message_match.group('value')
                if '*kW' in value:
                    realvalue_match = REALVALUE_RGX.search(value)
                    if realvalue_match:
                        value = float(realvalue_match.group('value'))

                data[key] = value

            if first_line in p1_line:
                epochtime_now = int(time.time())
                data['epochtime'] = epochtime_now

        self.measurements.append([epochtime_now, data['1-0:1.8.1'], data['1-0:1.8.2'], data['1-0:1.7.0']])

        if len(self.lastten) > 9:
            self.lastten = self.lastten[1:] + [[epochtime_now, data['1-0:1.7.0']]]
        else:
            self.lastten.append([epochtime_now, data['1-0:1.7.0']])

        self.csvverbruik.append(int(1000*data['1-0:1.7.0']))
        if ((epochtime_now % 300) < 10)  or  ((epochtime_now - self.csvfm) > 300):
            total = int(( data['1-0:1.8.1'] + data['1-0:1.8.2']) * 1000)
            self.csvdata.append([epochtime_now, total, self.csvverbruik])
            self.csvfm       = epochtime_now
            self.csvverbruik = []


    def flush_data(self):
        """

        Flush data to data file. Later this needs to be done to rrd type file.

        """
        # '%4s-W%02d' %( datetime.datetime.now().strftime("%Y"), datetime.datetime.now().isocalendar()[1])
        data_file = open('/home/user/data/P1reader-%4s-W%02d.log' % ( datetime.datetime.now().strftime("%Y"),
                                                      datetime.datetime.now().isocalendar()[1] ),
                          'a')
        for measurement in self.measurements:
            data_file.write( "%d:%7.3f:%7.3f:%5.3f\n" % ( measurement[0], measurement[1], measurement[2], measurement[3] ) )

        data_file.close()
        self.measurements = []


# ##############################################################################

#===============================================================================
def initialize_rrd_database(config):

    """
    Function to check whether the rrd db is available, if not create this one.
    """

    rrd_file = config.get('RRDdatabase', 'filename')
    sections = config.sections()

    print "sections: %s" % sections
    if not os.path.exists(rrd_file):
        # Ok, cannot find rrd file, so let's create one!
        if not config.has_section('RRDdatabase'):
            sys.exit("ERROR: missing section 'RRDdatabase' in config file!")

        items = config.items('RRDdatabase')
        print items




#===============================================================================
def main():

    """
    Program to connect to serial P1 port and process data from this.
      PURPOSE:..main function; initialize data/functions, loop to read P1 data
   PARAMETERS:  none
     COMMENTS:  none
     SEE ALSO:  n/a
    """

    # Some initialization
    #print ("Control-C om te stoppen")

    script_name = os.path.basename(__file__)
    configfile_name = __file__.replace('.py', '.ini').replace('/bin/', '/etc/')

    if not os.path.exists(configfile_name):
        sys.exit('ERROR: cannot find config file %s, quitting ....' % configfile_name)

    config = ConfigParser.ConfigParser()
    try:
        config.read(configfile_name)
    except ConfigParser.ParsingError as detail:
        print "ERROR: problem in config file %s: " % configfile_name
        print "details: ", detail
        sys.exit(2)

    #initialize_rrd_database(config)
    #sys.exit("We stoppen ermee")


    ser  = serial.Serial()
    power_meter = SlimmeMeter(ser)
    power_meter.open_port(ser)
    loop_iterator = 0

    signal.signal(signal.SIGINT,  do_exit)
    signal.signal(signal.SIGUSR1, do_exit)

    try:
        while True:
            loop_iterator += 1
            power_meter.read_port_value(ser)

            last_access_time = time.time() - os.path.getmtime('/var/log/nginx/access.log')
            if last_access_time < 24:
                loop_iterator = 0
            if (loop_iterator < 3)  or (loop_iterator % 240 == 0):
                power_meter.flush_data()
                power_meter.print_html()

            if (loop_iterator % 120 == 0):
                power_meter.print_csv()

    except KeyboardInterrupt:
        print "Interrupted, saving remaining data and than quit"
        power_meter.flush_data()
        power_meter.print_html()
        power_meter.print_csv()

        power_meter.close_port(ser)
        sys.exit(1)

#---------------------------------------------------------------------------
#  Main part here
#---------------------------------------------------------------------------
if __name__ == "__main__":
    main()

else:
    # Test several functions
    pass


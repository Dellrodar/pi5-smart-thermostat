#
# Thermostat - This is the Python code used to demonstrate
# the functionality of the thermostat that we have prototyped throughout
# the course. 
#
# This code works with the test circuit that was built for module 7.
#
# Functionality:
#
# The thermostat has three states: off, heat, cool
#
# The lights will represent the state that the thermostat is in.
#
# If the thermostat is set to off, the lights will both be off.
#
# If the thermostat is set to heat, the Red LED will be fading in 
# and out if the current temperature is blow the set temperature;
# otherwise, the Red LED will be on solid.
#
# If the thermostat is set to cool, the Blue LED will be fading in 
# and out if the current temperature is above the set temperature;
# otherwise, the Blue LED will be on solid.
#
# One button will cycle through the three states of the thermostat.
#
# One button will raise the setpoint by a degree.
#
# One button will lower the setpoint by a degree.
#
# The LCD display will display the date and time on one line and
# alternate the second line between the current temperature and 
# the state of the thermostat along with its set temperature.
#
# The Thermostat will send a status update to the TemperatureServer
# over the serial port every 30 seconds in a comma delimited string
# including the state of the thermostat, the current temperature
# in degrees Fahrenheit, and the setpoint of the thermostat.
#
#------------------------------------------------------------------
# Change History
#------------------------------------------------------------------
# Version   |   Description
#------------------------------------------------------------------
#    1          Initial Development
#------------------------------------------------------------------

##
## Import necessary to provide timing in the main loop
##
from time import sleep
from datetime import datetime

##
## Imports required to allow us to build a fully functional state machine
##
from statemachine import StateMachine, State

##
## Imports necessary to provide connectivity to the 
## thermostat sensor and the I2C bus
##
import board
import adafruit_ahtx0

##
## These are the packages that we need to pull in so that we can work
## with the GPIO interface on the Raspberry Pi board and work with
## the 16x2 LCD display
##
# import board - already imported for I2C connectivity
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd

## This imports the Python serial package to handle communications over the
## Raspberry Pi's serial port. 
import serial

##
## Imports required to handle our Button, and our PWMLED devices
##
from gpiozero import Button, PWMLED

##
## This package is necessary so that we can delegate the blinking
## lights to their own thread so that more work can be done at the
## same time
##
from threading import Thread

##
## This is needed to get coherent matching of temperatures.
##
from math import floor

##
## DEBUG flag - boolean value to indicate whether or not to print 
## status messages on the console of the program
## 
DEBUG = True

##
## Create an I2C instance so that we can communicate with
## devices on the I2C bus.
##
i2c = board.I2C()

##
## Initialize our Temperature and Humidity sensor
##
thSensor = adafruit_ahtx0.AHTx0(i2c)

##
## Initialize our serial connection
##
## Because we imported the entire package instead of just importing Serial and
## some of the other flags from the serial package, we need to reference those
## objects with dot notation.
##
## e.g. ser = serial.Serial
##
ser = serial.Serial(
        port='/dev/ttyUSB0', # This command assumes that the USB -> TTL cable
                             # is installed and the device that it uses is 
                             # /dev/ttyUSB0. This is the case with the USB -> TTL
                             # cable and Raspberry Pi 4B included in your kit.
        baudrate = 115200,   # This sets the speed of the serial interface in
                             # bits/second
        parity=serial.PARITY_NONE,      # Disable parity
        stopbits=serial.STOPBITS_ONE,   # Serial protocol will use one stop bit
        bytesize=serial.EIGHTBITS,      # We are using 8-bit bytes 
        timeout=1          # Configure a 1-second timeout
)

##
## Our two LEDs, utilizing GPIO 18, and GPIO 23
##
redLight = PWMLED(18)
blueLight = PWMLED(23)


##
## ManagedDisplay - Class intended to manage the 16x2 
## Display
##
## This code is largely taken from the work done in module 4, and
## converted into a class so that we can more easily consume the 
## operational capabilities.
##
class ManagedDisplay():
    ##
    ## Class Initialization method to setup the display
    ##
    def __init__(self):
        ##
        ## Setup the six GPIO lines to communicate with the display.
        ## This leverages the digitalio class to handle digital 
        ## outputs on the GPIO lines. There is also an analagous
        ## class for analog IO.
        ##
        ## You need to make sure that the port mappings match the
        ## physical wiring of the display interface to the 
        ## GPIO interface.
        ##
        ## compatible with all versions of RPI as of Jan. 2019
        ##
        self.lcd_rs = digitalio.DigitalInOut(board.D17)
        self.lcd_en = digitalio.DigitalInOut(board.D27)
        self.lcd_d4 = digitalio.DigitalInOut(board.D5)
        self.lcd_d5 = digitalio.DigitalInOut(board.D6)
        self.lcd_d6 = digitalio.DigitalInOut(board.D13)
        self.lcd_d7 = digitalio.DigitalInOut(board.D26)

        # Modify this if you have a different sized character LCD
        self.lcd_columns = 16
        self.lcd_rows = 2 

        # Initialise the lcd class
        self.lcd = characterlcd.Character_LCD_Mono(self.lcd_rs, self.lcd_en, 
                    self.lcd_d4, self.lcd_d5, self.lcd_d6, self.lcd_d7, 
                    self.lcd_columns, self.lcd_rows)

        # wipe LCD screen before we start
        self.lcd.clear()

    ##
    ## cleanupDisplay - Method used to cleanup the digitalIO lines that
    ## are used to run the display.
    ##
    def cleanupDisplay(self):
        # Clear the LCD first - otherwise we won't be abe to update it.
        self.lcd.clear()
        self.lcd_rs.deinit()
        self.lcd_en.deinit()
        self.lcd_d4.deinit()
        self.lcd_d5.deinit()
        self.lcd_d6.deinit()
        self.lcd_d7.deinit()
        
    ##
    ## clear - Convenience method used to clear the display
    ##
    def clear(self):
        self.lcd.clear()

    ##
    ## updateScreen - Convenience method used to update the message.
    ##
    def updateScreen(self, message):
        self.lcd.clear()
        self.lcd.message = message

    ## End class ManagedDisplay definition  

##
## Initialize our display
##
screen = ManagedDisplay()

##
## TemperatureMachine - This is our StateMachine implementation class.
## The purpose of this state machine is to manage the three states
## handled by our thermostat:
##
##  off
##  heat
##  cool
##
##
class TemperatureMachine(StateMachine):
    "A state machine designed to manage our thermostat"

    ##
    ## Define the three states for our machine.
    ##
    ##  off - nothing lit up
    ##  red - only red LED fading in and out
    ##  blue - only blue LED fading in and out
    ##
    off = State(initial = True)
    heat = State()
    cool = State()

    ##
    ## Default temperature setPoint is 72 degrees Fahrenheit
    ##
    setPoint = 72

    ##
    ## cycle - event that provides the state machine behavior
    ## of transitioning between the three states of our 
    ## thermostat
    ##
    cycle = (
        off.to(heat) |
        heat.to(cool) |
        cool.to(off)
    )

    ##
    ## on_enter_heat - Action performed when the state machine transitions
    ## into the 'heat' state
    ##
    def on_enter_heat(self):
        self.updateLights()

        if(DEBUG):
            print("* Changing state to heat")

    ##
    ## on_exit_heat - Action performed when the statemachine transitions
    ## out of the 'heat' state.
    ##
    def on_exit_heat(self):
        redLight.off()

    ##
    ## on_enter_cool - Action performed when the state machine transitions
    ## into the 'cool' state
    ##
    def on_enter_cool(self):
        self.updateLights()

        if(DEBUG):
            print("* Changing state to cool")
    
    ##
    ## on_exit_cool - Action performed when the statemachine transitions
    ## out of the 'cool' state.
    ##
    def on_exit_cool(self):
        blueLight.off()

    ##
    ## on_enter_off - Action performed when the state machine transitions
    ## into the 'off' state
    ##
    def on_enter_off(self):
        self.updateLights()

        if(DEBUG):
            print("* Changing state to off")
    
    ##
    ## processTempStateButton - Utility method used to send events to the 
    ## state machine. This is triggered by the button_pressed event
    ## handler for our first button
    ##
    def processTempStateButton(self):
        if(DEBUG):
            print("Cycling Temperature State")

        self.cycle()

    ##
    ## processTempIncButton - Utility method used to update the 
    ## setPoint for the temperature. This will increase the setPoint
    ## by a single degree. This is triggered by the button_pressed event
    ## handler for our second button
    ##
    def processTempIncButton(self):
        if(DEBUG):
            print("Increasing Set Point")

        self.setPoint = self.setPoint + 1
        self.updateLights()

    ##
    ## processTempDecButton - Utility method used to update the 
    ## setPoint for the temperature. This will decrease the setPoint
    ## by a single degree. This is triggered by the button_pressed event
    ## handler for our third button
    ##
    def processTempDecButton(self):
        if(DEBUG):
            print("Decreasing Set Point")

        self.setPoint = self.setPoint - 1
        self.updateLights()

    ##
    ## updateLights - Utility method to update the LED indicators on the 
    ## Thermostat
    ##
    def updateLights(self):
        ## Make sure we are comparing temperatires in the correct scale
        ## Change: Compare using the same rounding that the LCD displays (1 decimal)
        current_temp = self.getFahrenheit()
        temp = round(current_temp, 1)
        redLight.off()
        blueLight.off()
    
        ## Verify values for debug purposes
        if(DEBUG):
            print(f"State: {self.current_state.id}")
            print(f"SetPoint: {self.setPoint}")
            print(f"Temp: {temp}")

        # Determine visual identifiers
        if self.current_state.id == "off":
            # Off state - both lights are already off
            pass
        elif self.current_state.id == "heat":
            # Heat state - red LED behavior
            if temp < self.setPoint:
                # Current temp below setpoint - fade in and out
                redLight.pulse(fade_in_time=1, fade_out_time=1, n=None, background=True)
            else:
                # Current temp at or above setpoint - solid on
                redLight.on()
        elif self.current_state.id == "cool":
            # Cool state - blue LED behavior
            if temp > self.setPoint:
                # Current temp above setpoint - fade in and out
                blueLight.pulse(fade_in_time=1, fade_out_time=1, n=None, background=True)
            else:
                # Current temp at or below setpoint - solid on
                blueLight.on()

    ##
    ## run - kickoff the display management functionality of the thermostat
    ##
    def run(self):
        ## Change: Store thread reference so we can optionally join on shutdown
        self.displayThread = Thread(target=self.manageMyDisplay)
        self.displayThread.start()

    ##
    ## Get the temperature in Fahrenheit
    ##
    def getFahrenheit(self):
        t = thSensor.temperature
        return (((9/5) * t) + 32)
    
    ##
    ##  Configure output string for the Thermostat Server
    ##
    def setupSerialOutput(self):
        current_temp = self.getFahrenheit()
        ## Change: enforce lower case state names to match requirements exactly
        state = self.current_state.id.lower()
        output = f"{state},{current_temp:.2f},{self.setPoint}"
        
        return output
    
    ## Continue display output
    endDisplay = False

    ## Change: hold display thread reference for clean shutdown
    displayThread = None

    ##
    ##  This function is designed to manage the LCD Display
    ##
    def manageMyDisplay(self):
        counter = 1
        altCounter = 1
        while not self.endDisplay:
            try:
                ## Only display if the DEBUG flag is set
                if(DEBUG):
                    print("Processing Display Info...")
        
                ## Grab the current time        
                current_time = datetime.now()
        
                ## Setup display line 1
                lcd_line_1 = current_time.strftime("%m/%d/%Y %H:%M") + "\n"
        
                ## Setup Display Line 2
                if(altCounter < 6):
                    try:
                        current_temp = self.getFahrenheit()
                        lcd_line_2 = f"Temp: {current_temp:.1f}F"
                    except Exception as e:
                        if(DEBUG):
                            print(f"Error reading temperature: {e}")
                        lcd_line_2 = "Temp: --.-F"
    
                    altCounter = altCounter + 1
                else:
                    state_str = self.current_state.id.upper()
                    lcd_line_2 = f"{state_str} Set: {self.setPoint}F"
        
                    altCounter = altCounter + 1
                    if(altCounter >= 11):
                        # Run the routine to update the lights every 10 seconds
                        # to keep operations smooth
                        try:
                            self.updateLights()
                        except Exception as e:
                            if(DEBUG):
                                print(f"Error updating lights: {e}")
                        altCounter = 1
        
                ## Update Display
                try:
                    screen.updateScreen(lcd_line_1 + lcd_line_2)
                except Exception as e:
                    if(DEBUG):
                        print(f"Error updating display: {e}")
        
                ## Update server every 30 seconds
                if(DEBUG):
                   print(f"Counter: {counter}")
                if((counter % 30) == 0):
                    try:
                        ser.write((self.setupSerialOutput() + "\n").encode())
                    except Exception as e:
                        if(DEBUG):
                            print(f"Error writing to serial: {e}")
    
                    counter = 1
                else:
                    counter = counter + 1
            except Exception as e:
                ## Catch any unexpected errors and continue the loop
                if(DEBUG):
                    print(f"Unexpected error in display loop: {e}")
            
            sleep(1)

        ## Cleanup display
        try:
            screen.cleanupDisplay()
        except Exception as e:
            if(DEBUG):
                print(f"Error cleaning up display: {e}")

    ## End class TemperatureMachine definition


##
## Main execution block - only run if this file is executed directly
##
if __name__ == "__main__":
    ##
    ## Setup our State Machine
    ##
    tsm = TemperatureMachine()
    tsm.run()


    ##
    ## Configure our green button to use GPIO 24 and to execute
    ## the method to cycle the thermostat when pressed.
    ##
    greenButton = Button(24, bounce_time=0.2)
    greenButton.when_pressed = tsm.processTempStateButton

    ##
    ## Configure our Red button to use GPIO 25 and to execute
    ## the function to increase the setpoint by a degree.
    ##
    redButton = Button(25, bounce_time=0.2)
    redButton.when_pressed = tsm.processTempIncButton

    ##
    ## Configure our Blue button to use GPIO 12 and to execute
    ## the function to decrease the setpoint by a degree.
    ##
    blueButton = Button(12, bounce_time=0.2)
    blueButton.when_pressed = tsm.processTempDecButton

    ##
    ## Setup loop variable
    ##
    repeat = True

    ##
    ## Repeat until the user creates a keyboard interrupt (CTRL-C)
    ##
    while repeat:
        try:
            ## wait
            sleep(30)

        except KeyboardInterrupt:
            ## Catch the keyboard interrupt (CTRL-C) and exit cleanly
            ## we do not need to manually clean up the GPIO pins, the 
            ## gpiozero library handles that process.
            print("Cleaning up. Exiting...")

            ## Stop the loop
            repeat = False
            
            ## Close down the display
            tsm.endDisplay = True

            ## Change: allow the display thread time to exit cleanly
            sleep(1)
            try:
                if tsm.displayThread is not None:
                    tsm.displayThread.join(timeout=2)
            except Exception as e:
                if(DEBUG):
                    print(f"Error joining display thread: {e}")

            ## Change: ensure LEDs are turned off on exit
            try:
                redLight.off()
                blueLight.off()
            except Exception as e:
                if(DEBUG):
                    print(f"Error turning off LEDs: {e}")

            ## Change: close serial port cleanly on exit
            try:
                ser.close()
            except Exception as e:
                if(DEBUG):
                    print(f"Error closing serial port: {e}")

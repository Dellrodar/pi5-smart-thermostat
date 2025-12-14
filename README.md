# pi5-smart-thermostat

A smart thermostat prototype built on a Raspberry Pi 5 that demonstrates core embedded systems concepts, including peripheral integration, state-based control, user interaction, and simulated external communication. This project serves as a foundation for a future network-connected thermostat implementation.

---

## Overview

This project implements a smart thermostat prototype using a Raspberry Pi 5 with temperature sensing, state management, LED indicators, an LCD display, and serial communication. The system reads ambient temperature from a sensor, allows user interaction through physical buttons, visually indicates heating and cooling states, and periodically outputs system status over a serial interface.

While this version focuses on low-level functionality and direct hardware interaction, the architecture is intentionally designed to support future expansion, including Wi-Fi and cloud-based connectivity.

---

## Project Reflection

### Summarize the project and what problem it was solving
This project focuses on solving the challenge of coordinating multiple hardware peripherals within a single embedded system running on a Raspberry Pi 5. The goal was to reliably read environmental data, manage system behavior through a finite state machine, and present real-time information to the user while maintaining a clear path toward external system integration. The prototype simulates how a thermostat would monitor temperature, respond to user input, indicate system state, and transmit status information, providing a solid baseline for more advanced IoT functionality.

### What did you do particularly well?
A key strength of this project is the successful integration of several peripherals into a cohesive and predictable system. The finite state machine provides clear and deterministic behavior, making system operation easy to understand and verify. Button inputs, LED indicators, the LCD display, and serial output all function together without conflicting logic. The codebase is well-organized and documented, which simplified debugging and validation during development on the Raspberry Pi 5 platform.

### Where could you improve?
There are opportunities to improve robustness and extensibility beyond the prototype stage. Additional error handling and edge-case testing would improve reliability, particularly in long-running or unattended scenarios. Earlier abstraction of the communication layer would make it easier to transition from serial output to Wi-Fi or network-based communication with minimal refactoring. Power optimization and performance tuning would also be important considerations if this project were adapted for continuous operation on dedicated hardware.

### What tools and/or resources are you adding to your support network?
This project reinforced the usefulness of high-level hardware abstraction libraries such as GPIOZero and Adafruit’s CircuitPython drivers for rapid and readable hardware integration on the Raspberry Pi 5. Vendor documentation for Raspberry Pi hardware and peripheral components proved essential for understanding hardware capabilities and constraints. Structured debugging techniques for embedded systems are also tools that will continue to be used in future projects.

### What skills from this project will be particularly transferable?
The most transferable skills developed here include finite state machine design, event-driven programming, and peripheral integration. These concepts apply broadly across embedded systems, IoT projects, robotics, and systems-level software. Translating functional requirements into a working hardware–software solution and documenting technical decisions clearly are skills that extend well beyond this project and across platforms similar to the Raspberry Pi 5.

### How did you make this project maintainable, readable, and adaptable?
Maintainability and readability were achieved through clear code organization, consistent naming conventions, and thorough inline documentation. Separating state management from hardware interaction and display logic made the system easier to modify without unintended side effects. Centralizing behavior within a state machine allows new features or states to be added with minimal changes. Serial communication is used to simulate external data transfer, providing a clean transition path to future Wi-Fi or cloud-based connectivity.

---

## Project Files

- `Thermostat.py` – Main thermostat application with state machine implementation  
- `ThermostatServer-Simulator.py` – Server simulator for testing serial communication  
- `MultiButtonTest.py` – Button testing utility  

---

## Hardware Setup

### Target Platform
- **Raspberry Pi 5** running **Debian Server OS**

### GPIO Pin Configuration

| Component | GPIO Pin | Function |
|----------|----------|----------|
| Red LED | 18 | PWM output |
| Blue LED | 23 | PWM output |
| State Button | 24 | Digital input |
| Increase Button | 25 | Digital input |
| Decrease Button | 12 | Digital input |
| LCD RS | 17 | Digital output |
| LCD EN | 27 | Digital output |
| LCD D4–D7 | 5, 6, 13, 26 | Digital output |
| I2C SDA | I2C bus | I2C data |
| I2C SCL | I2C bus | I2C clock |
| UART TX | `/dev/ttyUSB0` or `/dev/ttyS0` | Serial transmit |
| UART RX | `/dev/ttyUSB0` or `/dev/ttyS0` | Serial receive |

---

## Prerequisites

On the Raspberry Pi 5 running Debian Server OS:

First, ensure Python 3 and pip are installed:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-dev
```

Then install the required Python packages:

```bash
pip3 install adafruit-blinka
pip3 install python-statemachine
pip3 install adafruit-circuitpython-ahtx0
pip3 install adafruit-circuitpython-charlcd
pip3 install gpiozero
pip3 install pyserial
```

**Notes:**
- `adafruit-blinka` provides CircuitPython compatibility for Raspberry Pi and is required for `board` and `digitalio` modules used by the LCD display and I2C communication.
- If `python-statemachine` installation fails, try `pip3 install statemachine` instead (package name may vary).
- You may need to install additional system packages for GPIO and I2C support: `sudo apt install libgpiod2 python3-lgpio` (if not already installed).

---

## Running the Application

### Main Thermostat Application

To run the thermostat on your Raspberry Pi 5:

```bash
python3 Thermostat.py
```

The application will:
- Initialize the temperature sensor, LCD display, LEDs, and buttons
- Display the current date/time and temperature on the LCD
- Respond to button presses to cycle states (off/heat/cool) and adjust the temperature setpoint
- Send status updates over the serial port every 30 seconds
- Run continuously until interrupted

To stop the application, press `CTRL-C`. The application will clean up GPIO resources and exit gracefully.

### Server Simulator (Optional)

To test serial communication, you can run the server simulator in a separate terminal:

```bash
python3 ThermostatServer-Simulator.py
```

This will read and display the status messages sent by the thermostat over the serial port. Press `CTRL-C` to stop the simulator.

**Note:** Ensure that the serial port configuration in both files matches your Raspberry Pi 5 setup. The main application uses `/dev/ttyUSB0` by default, while the simulator uses `/dev/ttyAMA0`. You may need to adjust these paths based on your hardware configuration.
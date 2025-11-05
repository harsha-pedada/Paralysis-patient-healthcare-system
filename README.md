# Paralysis Patient Healthcare System

This project helps paralysis patients communicate their needs using sensors and a GSM module.  
The system detects movements using flex sensors, monitors patient activity, and sends alerts via SMS.

## Technologies Used
- Python 3  
- Raspberry Pi  
- RPi.GPIO  
- smbus2  
- spidev  
- pyserial  

## Components
- Raspberry Pi  
- GSM Module (SIM800L / SIM900)  
- MPU6050 (Accelerometer)  
- Flex Sensors (2)  
- Water Sensor  
- Food Sensor  
- MCP3008 (ADC)  
- LEDs  

## Features
- Detects when the patient needs water, food, or help  
- Monitors movement and detects falls  
- Sends SMS alerts automatically through GSM  
- Uses LEDs for visual indication  

## How to Run
1. Connect all sensors and modules properly.  
2. Enable SPI and I2C on your Raspberry Pi (`sudo raspi-config`).  
3. Install dependencies:
   ```bash
   pip3 install RPi.GPIO smbus2 spidev pyserial
4.Update your phone number in the code: DEST_PHONE = "+91XXXXXXXXXX"
5.Run the program: python3 paralysis_system.py

## Alert Messages
| Condition          | Message Sent                           |
| ------------------ | -------------------------------------- |
| Water sensor low   | "I need water !!"                      |
| Food sensor low    | "I need food."                         |
| Flex sensor 1 bent | "I need fresh air."                    |
| Flex sensor 2 bent | "I need to go to washroom."            |
| Abnormal movement  | "I am in emergency help me please !!!" |



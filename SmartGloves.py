"""
Paralysis Patient Healthcare System - Python (Raspberry Pi)
Reads:
 - water, food, flex1, flex2 via MCP3008 (SPI ADC) channels 0..3
 - MPU6050 accel via I2C
 - controls two LEDs on GPIO pins
 - sends SMS/email via GSM module using AT commands (pyserial)

Adjust pins, thresholds, serial port, and contact info before running.
"""

import time
import serial
import spidev                 # for MCP3008 ADC
import RPi.GPIO as GPIO
from smbus2 import SMBus

# ---------------- CONFIG -----------------
GSM_PORT = "/dev/ttyUSB0"       # change to your GSM serial device
GSM_BAUD = 9600

LED_PIN = 4                     # BCM numbering
LED_PIN1 = 17

# MCP3008 channels for analog sensors
ADC_CHANNEL_WATER = 0
ADC_CHANNEL_FOOD  = 1
ADC_CHANNEL_FLEX1 = 2
ADC_CHANNEL_FLEX2 = 3

# Thresholds -- tune after testing sensors
WATER_THRESHOLD = 300      # 0..1023 for MCP3008
FOOD_THRESHOLD  = 300
FLEX_THRESHOLD_1 = 400
FLEX_THRESHOLD_2 = 400

# Acceleration thresholds (raw accelerometer value from MPU6050)
ACC_HIGH_POS = 26000.0
ACC_HIGH_NEG = -33000.0
ACC_MED_NEG  = -20000.0

# MPU6050 I2C addr
MPU_ADDR = 0x68

# Destination contact info
DEST_PHONE = "+919025940848"
DEST_EMAIL = "vasanthvitian@gmail.com"
# -----------------------------------------

# ---------------- setup ------------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(LED_PIN1, GPIO.OUT)
GPIO.output(LED_PIN, GPIO.LOW)
GPIO.output(LED_PIN1, GPIO.LOW)

# SPI for MCP3008
spi = spidev.SpiDev()
spi.open(0, 0)        # bus 0, cs 0 - adjust if using different SPI
spi.max_speed_hz = 1350000

# SMBus for MPU6050
bus = SMBus(1)  # I2C bus 1 on modern Pi

# Initialize MPU6050 (basic wakeup)
def init_mpu():
    # wake up MPU6050 (write 0 to power management register)
    bus.write_byte_data(MPU_ADDR, 0x6B, 0x00)  # PWR_MGMT_1 = 0
    # Optionally set accelerometer range / filters if required
    # Example: set accel FS_SEL to +/- 2g (0)
    bus.write_byte_data(MPU_ADDR, 0x1C, 0x00)

init_mpu()

# Init GSM serial
gsm = serial.Serial(GSM_PORT, GSM_BAUD, timeout=1)
time.sleep(1)
gsm.write(b"AT\r\n")
time.sleep(1)

# ---------------- helpers -----------------
def read_adc(channel):
    """Read MCP3008 channel (0-7). Returns 0..1023"""
    if not 0 <= channel <= 7:
        return 0
    # MCP3008 protocol: 1(start), (SGL/Diff + channel bits), 0
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    value = ((r[1] & 3) << 8) | r[2]
    return value

def read_mpu_accel():
    """Return ax, ay, az as signed 16-bit ints"""
    data = bus.read_i2c_block_data(MPU_ADDR, 0x3B, 6)
    ax = (data[0] << 8) | data[1]
    ay = (data[2] << 8) | data[3]
    az = (data[4] << 8) | data[5]
    # Convert to signed
    def to_signed(x):
        return x - 65536 if x >= 32768 else x
    return to_signed(ax), to_signed(ay), to_signed(az)

def blink_leds_once():
    GPIO.output(LED_PIN, GPIO.HIGH)
    GPIO.output(LED_PIN1, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.output(LED_PIN1, GPIO.LOW)

def send_sms(phone, message):
    """Send SMS via GSM module using AT commands"""
    try:
        gsm.write(b'AT+CMGF=1\r')  # set text mode
        time.sleep(0.5)
        cmd = 'AT+CMGS="{}"\r'.format(phone)
        gsm.write(cmd.encode())
        time.sleep(0.5)
        gsm.write(message.encode())
        time.sleep(0.2)
        gsm.write(bytes([26]))  # Ctrl+Z
        time.sleep(2)
        return True
    except Exception as e:
        print("SMS error:", e)
        return False

def send_email(email_addr, message):
    """Basic placeholder — most GSM modules don't send email over AT in standard setups.
       You may implement SMTP from the Pi directly instead (smtplib) if you have network access.
    """
    # Fallback: send SMS to a caregiver instead of email, or implement SMTP
    send_sms(DEST_PHONE, "EMAIL-> {} : {}".format(email_addr, message))

# ---------------- main loop ----------------
try:
    while True:
        water_val = read_adc(ADC_CHANNEL_WATER)
        food_val = read_adc(ADC_CHANNEL_FOOD)
        flex1_val = read_adc(ADC_CHANNEL_FLEX1)
        flex2_val = read_adc(ADC_CHANNEL_FLEX2)

        ax, ay, az = read_mpu_accel()
        accel_mag = float(ax)  # using ax as proxy similar to original sketch

        print("Water:", water_val, "Food:", food_val, "Flex1:", flex1_val, "Flex2:", flex2_val, "ax:", ax)

        # Water alert
        if water_val < WATER_THRESHOLD:
            blink_leds_once()
            send_sms(DEST_PHONE, "I need water !!")
            time.sleep(5)

        # Food alert
        if food_val < FOOD_THRESHOLD:
            blink_leds_once()
            send_sms(DEST_PHONE, "I need food.")
            time.sleep(5)

        # Fresh air
        if flex1_val < FLEX_THRESHOLD_1:
            blink_leds_once()
            send_sms(DEST_PHONE, "I need to get Fresh Air")
            time.sleep(5)

        # Washroom
        if flex2_val < FLEX_THRESHOLD_2:
            send_email(DEST_EMAIL, "I need to go to Washroom")
            send_sms(DEST_PHONE, "I need to go to Washroom")
            time.sleep(5)

        # Combined emergency
        if (food_val < FOOD_THRESHOLD) and (water_val < WATER_THRESHOLD) and (flex1_val < (FLEX_THRESHOLD_1 + 2)):
            blink_leds_once()
            send_sms(DEST_PHONE, "I am in emergency help me please !!!")
            time.sleep(5)

        # Abnormal accelerometer events
        if accel_mag > ACC_HIGH_POS:
            print("Abnormal activity detected (high pos):", accel_mag)
            blink_leds_once()
            send_sms(DEST_PHONE, "I am in emergency help me please !!!")
            time.sleep(5)

        if accel_mag < ACC_HIGH_NEG:
            print("Abnormal activity detected (high neg):", accel_mag)
            blink_leds_once()
            send_sms(DEST_PHONE, "I need water !!")
            time.sleep(5)

        if accel_mag < ACC_MED_NEG:
            print("Abnormal activity detected (med neg):", accel_mag)
            blink_leds_once()
            send_sms(DEST_PHONE, "I need food.")
            time.sleep(5)

        time.sleep(1)

except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()
    spi.close()
    gsm.close()
    bus.close()

# traffic_light.py
import RPi.GPIO as GPIO
import time

class TrafficLight:
    def __init__(self, red_pin, yellow_pin, green_pin):
        self.red_pin = red_pin
        self.yellow_pin = yellow_pin
        self.green_pin = green_pin
        self.pins = [self.red_pin, self.yellow_pin, self.green_pin]
        self._setup()

    def _setup(self):
        # GPIO.setmode(GPIO.BCM) # 假設 main.py 中已設定
        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW) # 預設全滅

    def set_light(self, color, state):
        """設定特定顏色的燈的狀態"""
        pin_map = {
            "red": self.red_pin,
            "yellow": self.yellow_pin,
            "green": self.green_pin
        }
        if color in pin_map:
            GPIO.output(pin_map[color], GPIO.HIGH if state else GPIO.LOW)

    def all_off(self):
        for pin in self.pins:
            GPIO.output(pin, GPIO.LOW)

    def red_on(self):
        self.all_off()
        self.set_light("red", True)

    def yellow_on(self):
        self.all_off()
        self.set_light("yellow", True)

    def green_on(self):
        self.all_off()
        self.set_light("green", True)

    def cleanup(self):
        self.all_off()
        # GPIO.cleanup(self.pins) # 主程式統一 cleanup

if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    # 假設紅燈接 GPIO 22, 黃燈接 GPIO 23, 綠燈接 GPIO 17
    traffic_light = TrafficLight(red_pin=4, yellow_pin=3, green_pin=2)
    try:
        print("交通信號燈測試...")
        print("紅燈亮")
        traffic_light.red_on()
        time.sleep(2)

        print("黃燈亮")
        traffic_light.yellow_on()
        time.sleep(2)

        print("綠燈亮")
        traffic_light.green_on()
        time.sleep(2)

        traffic_light.all_off()
        print("測試結束")
    finally:
        traffic_light.cleanup()
        GPIO.cleanup()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# buzzer.py - 音效模組，控制蜂鳴器提供聲音回饋

import RPi.GPIO as GPIO
import time

# 設定蜂鳴器的 GPIO 腳位
BUZZER_PIN = 18  # 使用 GPIO 18 作為 PWM 輸出

# 定義不同音效的頻率 (Hz) 和持續時間 (秒)
TONE_DEFINITIONS = {
    "navigate": {"frequency": 800, "duration": 0.05},   # 導航/選擇時的短音效
    "select": {"frequency": 1000, "duration": 0.1},     # 確認選擇的音效
    "back": {"frequency": 600, "duration": 0.1},        # 返回選單的音效
    "error": {"frequency": 300, "duration": 0.2},       # 錯誤提示音效
    "game_start": {"frequency": 1200, "duration": 0.2}, # 遊戲開始音效
    "game_over": {"frequency": 350, "duration": 0.3},   # 遊戲結束音效
    "score": {"frequency": 1500, "duration": 0.05},     # 得分音效
    "level_up": {"frequency": 1800, "duration": 0.5}    # 升級音效
}

# 預設音調
DEFAULT_FREQUENCY = 1000  # 1kHz
DEFAULT_DURATION = 0.1    # 0.1 秒

class BuzzerControl:
    """蜂鳴器控制類，提供遊戲音效回饋"""
    
    def __init__(self, pin=BUZZER_PIN):
        self.pin = pin
        self.pwm = None
        self.is_initialized = self._initialize()
        self.tone_definitions = TONE_DEFINITIONS.copy()
    
    def _initialize(self):
        """初始化蜂鳴器的 GPIO 和 PWM"""
        try:
            # GPIO 設定在主程式中已完成，這裡不再設定模式
            # GPIO.setmode(GPIO.BCM)
            
            # 設置蜂鳴器引腳為輸出
            GPIO.setup(self.pin, GPIO.OUT)
            
            # 初始化 PWM，頻率先設為 1 Hz (之後會動態變更)
            self.pwm = GPIO.PWM(self.pin, 1)
            # 初始佔空比設為 0 (關閉)
            self.pwm.start(0)
            
            print("蜂鳴器初始化成功")
            return True
        
        except Exception as e:
            print(f"蜂鳴器初始化失敗: {e}")
            return False
    
    def load_tones(self):
        """載入音調定義，可在此擴充更多音效"""
        # 目前使用預設定義，但保留擴充空間
        pass
    
    def play_tone(self, tone_name=None, frequency=None, duration=None):
        """
        播放指定的音調或自定義音調
        
        參數:
            tone_name: 預定義音調的名稱，如 "navigate", "select" 等
            frequency: 直接指定頻率 (Hz)，會覆蓋 tone_name 設定
            duration: 直接指定持續時間 (秒)，會覆蓋 tone_name 設定
        """
        if not self.is_initialized:
            print("蜂鳴器未成功初始化，無法播放音效")
            return
        
        # 獲取音調參數
        tone_freq = DEFAULT_FREQUENCY
        tone_duration = DEFAULT_DURATION
        
        # 如果有指定預設音調名稱且在定義中
        if tone_name and tone_name in self.tone_definitions:
            tone_def = self.tone_definitions[tone_name]
            tone_freq = tone_def["frequency"]
            tone_duration = tone_def["duration"]
        
        # 覆蓋參數 (若有指定)
        if frequency is not None:
            tone_freq = frequency
        if duration is not None:
            tone_duration = duration
        
        try:
            # 設定 PWM 頻率
            self.pwm.ChangeFrequency(tone_freq)
            # 設定 PWM 佔空比 (50% 通常產生最大音量)
            self.pwm.ChangeDutyCycle(50)
            
            # 等待指定時間
            time.sleep(tone_duration)
            
            # 停止音調
            self.pwm.ChangeDutyCycle(0)
        
        except Exception as e:
            print(f"播放音調時發生錯誤: {e}")
    
    def play_melody(self, notes):
        """
        播放旋律 (一系列音符)
        
        參數:
            notes: 音符列表，每個音符是一個字典，包含 frequency 和 duration
        """
        if not self.is_initialized:
            print("蜂鳴器未成功初始化，無法播放音效")
            return
        
        try:
            for note in notes:
                freq = note.get("frequency", DEFAULT_FREQUENCY)
                duration = note.get("duration", DEFAULT_DURATION)
                
                # 播放此音符
                self.play_tone(frequency=freq, duration=duration)
                
                # 音符之間短暫間隔
                time.sleep(0.02)
        
        except Exception as e:
            print(f"播放旋律時發生錯誤: {e}")
    
    def play_startup_melody(self):
        """播放啟動旋律"""
        startup_melody = [
            {"frequency": 523, "duration": 0.15},  # C5
            {"frequency": 659, "duration": 0.15},  # E5
            {"frequency": 784, "duration": 0.15},  # G5
            {"frequency": 1047, "duration": 0.3},  # C6
        ]
        self.play_melody(startup_melody)
    
    def play_game_over_melody(self):
        """播放遊戲結束旋律"""
        game_over_melody = [
            {"frequency": 784, "duration": 0.15},  # G5
            {"frequency": 659, "duration": 0.15},  # E5
            {"frequency": 523, "duration": 0.15},  # C5
            {"frequency": 392, "duration": 0.3},   # G4
        ]
        self.play_melody(game_over_melody)
    
    def play_win_melody(self):
        """播放勝利旋律"""
        win_melody = [
            {"frequency": 523, "duration": 0.1},   # C5
            {"frequency": 659, "duration": 0.1},   # E5
            {"frequency": 784, "duration": 0.1},   # G5
            {"frequency": 1047, "duration": 0.1},  # C6
            {"frequency": 784, "duration": 0.1},   # G5
            {"frequency": 1047, "duration": 0.3},  # C6
        ]
        self.play_melody(win_melody)
    
    def cleanup(self):
        """清理資源"""
        if self.is_initialized and self.pwm:
            self.pwm.stop()
            print("蜂鳴器資源已清理")

# 測試代碼
if __name__ == "__main__":
    try:
        # 設定 GPIO 模式
        GPIO.setmode(GPIO.BCM)
        
        # 建立蜂鳴器控制物件
        buzzer = BuzzerControl()
        
        # 測試各種音效
        print("測試不同音效...")
        print("播放導航音效")
        buzzer.play_tone("navigate")
        time.sleep(0.5)
        
        print("播放選擇音效")
        buzzer.play_tone("select")
        time.sleep(0.5)
        
        print("播放錯誤音效")
        buzzer.play_tone("error")
        time.sleep(0.5)
        
        print("播放遊戲開始音效")
        buzzer.play_tone("game_start")
        time.sleep(0.5)
        
        print("播放遊戲結束音效")
        buzzer.play_tone("game_over")
        time.sleep(0.5)
        
        # 測試自定義音調
        print("播放自定義音調 (1500 Hz, 0.2s)")
        buzzer.play_tone(frequency=1500, duration=0.2)
        time.sleep(0.5)
        
        # 測試旋律
        print("播放啟動旋律")
        buzzer.play_startup_melody()
        time.sleep(1)
        
        print("播放遊戲結束旋律")
        buzzer.play_game_over_melody()
        time.sleep(1)
        
        print("播放勝利旋律")
        buzzer.play_win_melody()
        
        # 清理資源
        buzzer.cleanup()
        GPIO.cleanup()
        
        print("測試完成")
    
    except KeyboardInterrupt:
        print("\n程式被使用者中斷")
    except Exception as e:
        print(f"測試時發生錯誤: {e}")
    finally:
        GPIO.cleanup()
        print("GPIO 資源已清理")

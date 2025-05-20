#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# matrix_keypad.py - 矩陣鍵盤控制邏輯

import time
import RPi.GPIO as GPIO

# 定義鍵盤的 GPIO 引腳 (請根據實際連接調整)
# 行 (ROW) 和列 (COL) 的 GPIO 引腳編號
ROW_PINS = [6, 13, 19, 26]  # 連接到鍵盤的四行
COL_PINS = [12, 16, 20, 21]  # 連接到鍵盤的四列

# 定義鍵盤映射
KEY_MAP = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]

# 防彈跳延遲 (秒)
DEBOUNCE_DELAY = 0.05

class MatrixKeypad:
    """4x4 矩陣鍵盤控制類"""
    
    def __init__(self, row_pins=ROW_PINS, col_pins=COL_PINS, key_map=KEY_MAP):
        self.row_pins = row_pins
        self.col_pins = col_pins
        self.key_map = key_map
        self.last_key_press_time = 0
        self.last_key = None
        self._setup()
    
    def _setup(self):
        """設置 GPIO 引腳"""
        try:
            # 設置 GPIO 模式
            # GPIO.setmode(GPIO.BCM)  # 使用 BCM 模式，在主程式中已設置
            
            # 設置列為輸出，行為輸入
            for pin in self.col_pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH)  # 預設為高電平
            
            for pin in self.row_pins:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 設置上拉電阻
            
            print("矩陣鍵盤初始化成功")
        
        except Exception as e:
            print(f"矩陣鍵盤初始化失敗: {e}")
    
    def get_key_raw(self):
        """
        掃描鍵盤並返回按下的鍵
        
        返回:
            按下的鍵值，若無按鍵按下則返回 None
        """
        try:
            # 掃描每一列
            for col_idx, col_pin in enumerate(self.col_pins):
                # 設置當前列為低電平
                GPIO.output(col_pin, GPIO.LOW)
                
                # 檢查每一行
                for row_idx, row_pin in enumerate(self.row_pins):
                    # 若偵測到低電平，表示該位置上的按鍵被按下
                    if GPIO.input(row_pin) == GPIO.LOW:
                        # 恢復該列為高電平
                        GPIO.output(col_pin, GPIO.HIGH)
                        # 返回按下的鍵
                        return self.key_map[row_idx][col_idx]
                
                # 恢復該列為高電平
                GPIO.output(col_pin, GPIO.HIGH)
            
            # 若無按鍵被按下，返回 None
            return None
        
        except Exception as e:
            print(f"鍵盤掃描錯誤: {e}")
            return None
    
    def get_key(self):
        """
        獲取鍵盤輸入，帶防彈跳處理
        
        返回:
            按下的鍵值，若無按鍵按下則返回 None
        """
        current_time = time.time()
        
        # 檢查是否超過防彈跳延遲
        if current_time - self.last_key_press_time < DEBOUNCE_DELAY:
            return None
        
        key = self.get_key_raw()
        
        # 若有按鍵被按下
        if key is not None:
            # 更新最後按鍵時間
            self.last_key_press_time = current_time
            
            # 若與上次不同或第一次，返回該鍵值
            if key != self.last_key:
                self.last_key = key
                return key
        else:
            # 重置最後按下的按鍵
            self.last_key = None
        
        return None
    
    def wait_for_key(self, timeout=None):
        """
        等待直到有按鍵被按下或超時
        
        參數:
            timeout: 超時時間 (秒)，若為 None 則無超時
        
        返回:
            按下的鍵值，若超時則返回 None
        """
        start_time = time.time()
        
        while timeout is None or time.time() - start_time < timeout:
            key = self.get_key()
            if key is not None:
                return key
            time.sleep(0.01)  # 短暫休眠以減少 CPU 負擔
        
        return None
    
    def cleanup(self):
        """清理 GPIO 資源"""
        # GPIO.cleanup() 將在主程式中處理
        print("矩陣鍵盤資源已清理")

# 測試代碼
if __name__ == "__main__":
    try:
        # 設置 GPIO 模式
        GPIO.setmode(GPIO.BCM)
        
        # 初始化鍵盤
        keypad = MatrixKeypad()
        
        print("按下鍵盤上的按鍵進行測試 (按 Ctrl+C 退出)...")
        
        while True:
            key = keypad.get_key()
            if key is not None:
                print(f"按下按鍵: {key}")
            time.sleep(0.1)  # 短暫休眠以減少 CPU 負擔
    
    except KeyboardInterrupt:
        print("\n程式被使用者中斷")
    except Exception as e:
        print(f"發生錯誤: {e}")
    finally:
        GPIO.cleanup()
        print("GPIO 資源已清理")

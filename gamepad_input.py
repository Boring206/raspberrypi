#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# gamepad_input.py - Xbox 控制器處理邏輯

import pygame
import os
import time

# 定義按鈕映射常量
BUTTON_A = 0       # A 按鈕
BUTTON_B = 1       # B 按鈕
BUTTON_X = 2       # X 按鈕
BUTTON_Y = 3       # Y 按鈕
BUTTON_LB = 4      # 左肩按鈕
BUTTON_RB = 5      # 右肩按鈕
BUTTON_BACK = 6    # Back 按鈕
BUTTON_START = 7   # Start 按鈕
BUTTON_LS = 8      # 左搖桿按鈕
BUTTON_RS = 9      # 右搖桿按鈕

# 定義搖桿軸映射常量
AXIS_LX = 0        # 左搖桿 X 軸
AXIS_LY = 1        # 左搖桿 Y 軸
AXIS_RX = 2        # 右搖桿 X 軸
AXIS_RY = 3        # 右搖桿 Y 軸
AXIS_TRIGGER = 4   # 扳機軸 (LT/RT)

# 方向閾值 (搖桿偏移多少才算是移動)
DIRECTION_THRESHOLD = 0.5

class XboxController:
    """Xbox 控制器輸入處理類"""
    
    def __init__(self):
        # 初始化 pygame 模組 (如果尚未初始化)
        if not pygame.get_init():
            pygame.init()
        
        # 初始化 joystick 模組
        pygame.joystick.init()
        
        # 嘗試初始化第一個控制器
        self.controller = None
        self.is_connected = False
        self.initialize_controller()
        
        # 上次讀取的輸入狀態
        self.last_input = {
            "up_pressed": False,
            "down_pressed": False,
            "left_pressed": False,
            "right_pressed": False,
            "a_pressed": False,
            "b_pressed": False,
            "x_pressed": False,
            "y_pressed": False,
            "start_pressed": False,
            "back_pressed": False,
            "lb_pressed": False,
            "rb_pressed": False,
            "lt_pressed": False,
            "rt_pressed": False
        }
        
        # 搖桿狀態
        self.joystick_position = {
            "left_x": 0.0,
            "left_y": 0.0,
            "right_x": 0.0,
            "right_y": 0.0
        }
        
        # 用於控制輸入處理頻率
        self.last_update_time = time.time()
        self.update_interval = 0.01  # 10ms
    
    def initialize_controller(self):
        """初始化可用的 Xbox 控制器"""
        try:
            # 檢查是否有連接的控制器
            joystick_count = pygame.joystick.get_count()
            
            if joystick_count == 0:
                print("警告: 未偵測到 Xbox 控制器連接")
                self.is_connected = False
                return
            
            # 獲取第一個可用控制器
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()
            
            # 輸出控制器資訊
            controller_name = self.controller.get_name()
            axes_count = self.controller.get_numaxes()
            buttons_count = self.controller.get_numbuttons()
            
            print(f"控制器連接成功: {controller_name}")
            print(f"軸數: {axes_count}, 按鈕數: {buttons_count}")
            
            self.is_connected = True
        
        except Exception as e:
            print(f"控制器初始化失敗: {e}")
            self.is_connected = False
    
    def check_connection(self):
        """檢查控制器是否仍然連接"""
        # 重新初始化 joystick 模組以更新連接狀態
        pygame.joystick.quit()
        pygame.joystick.init()
        
        if pygame.joystick.get_count() > 0:
            if not self.is_connected:
                # 如果之前沒連接但現在有，重新初始化
                self.initialize_controller()
                return True
            else:
                # 已經連接且仍連接
                return True
        else:
            # 沒有控制器連接
            self.is_connected = False
            return False
    
    def _process_events(self):
        """處理 pygame 事件以保持系統響應"""
        pygame.event.pump()
    
    def get_input(self):
        """
        獲取控制器輸入
        
        返回:
            包含所有控制器輸入狀態的字典
        """
        # 只在超過更新間隔後處理輸入，避免過度頻繁地讀取
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return self.last_input
        
        self.last_update_time = current_time
        
        # 如果控制器未連接，嘗試重新連接
        if not self.is_connected:
            self.check_connection()
            if not self.is_connected:
                return self.last_input
        
        # 處理 pygame 事件
        self._process_events()
        
        try:
            # 讀取搖桿位置
            if self.controller:
                # 讀取左搖桿
                self.joystick_position["left_x"] = self.controller.get_axis(AXIS_LX)
                self.joystick_position["left_y"] = self.controller.get_axis(AXIS_LY)
                
                # 讀取右搖桿
                self.joystick_position["right_x"] = self.controller.get_axis(AXIS_RX)
                self.joystick_position["right_y"] = self.controller.get_axis(AXIS_RY)
                
                # 獲取 D-pad 或搖桿方向
                up_pressed = self.joystick_position["left_y"] < -DIRECTION_THRESHOLD
                down_pressed = self.joystick_position["left_y"] > DIRECTION_THRESHOLD
                left_pressed = self.joystick_position["left_x"] < -DIRECTION_THRESHOLD
                right_pressed = self.joystick_position["left_x"] > DIRECTION_THRESHOLD
                
                # 獲取按鈕狀態
                a_pressed = self.controller.get_button(BUTTON_A) == 1
                b_pressed = self.controller.get_button(BUTTON_B) == 1
                x_pressed = self.controller.get_button(BUTTON_X) == 1
                y_pressed = self.controller.get_button(BUTTON_Y) == 1
                start_pressed = self.controller.get_button(BUTTON_START) == 1
                back_pressed = self.controller.get_button(BUTTON_BACK) == 1
                lb_pressed = self.controller.get_button(BUTTON_LB) == 1
                rb_pressed = self.controller.get_button(BUTTON_RB) == 1
                
                # 獲取扳機狀態 (可能需要根據實際控制器調整)
                trigger_value = self.controller.get_axis(AXIS_TRIGGER)
                lt_pressed = trigger_value < -0.5
                rt_pressed = trigger_value > 0.5
                
                # 更新輸入狀態
                self.last_input = {
                    "up_pressed": up_pressed,
                    "down_pressed": down_pressed,
                    "left_pressed": left_pressed,
                    "right_pressed": right_pressed,
                    "a_pressed": a_pressed,
                    "b_pressed": b_pressed,
                    "x_pressed": x_pressed,
                    "y_pressed": y_pressed,
                    "start_pressed": start_pressed,
                    "back_pressed": back_pressed,
                    "lb_pressed": lb_pressed,
                    "rb_pressed": rb_pressed,
                    "lt_pressed": lt_pressed,
                    "rt_pressed": rt_pressed
                }
            
        except Exception as e:
            print(f"讀取控制器輸入時發生錯誤: {e}")
            # 控制器可能已中斷連接
            self.is_connected = False
        
        return self.last_input
    
    def get_joystick_position(self):
        """
        獲取搖桿位置
        
        返回:
            包含搖桿位置的字典
        """
        # 由於 get_input 會同時更新搖桿位置，只需調用它並返回搖桿位置即可
        self.get_input()
        return self.joystick_position
    
    def cleanup(self):
        """清理資源"""
        if self.controller and self.is_connected:
            self.controller.quit()
        print("控制器資源已清理")

# 測試代碼
if __name__ == "__main__":
    try:
        # 初始化 pygame
        pygame.init()
        
        # 建立控制器物件
        controller = XboxController()
        
        print("開始測試 Xbox 控制器 (按 Ctrl+C 退出)...")
        print("移動搖桿和按下按鈕來查看輸入狀態")
        
        while True:
            # 獲取輸入
            input_state = controller.get_input()
            joystick_pos = controller.get_joystick_position()
            
            # 顯示搖桿位置和按鈕狀態
            os.system('cls' if os.name == 'nt' else 'clear')  # 清除終端
            
            print("Xbox 控制器輸入測試")
            print("-" * 30)
            
            print("搖桿位置:")
            print(f"  左搖桿: X={joystick_pos['left_x']:.2f}, Y={joystick_pos['left_y']:.2f}")
            print(f"  右搖桿: X={joystick_pos['right_x']:.2f}, Y={joystick_pos['right_y']:.2f}")
            
            print("\n方向輸入:")
            print(f"  上: {'按下' if input_state['up_pressed'] else '未按'}")
            print(f"  下: {'按下' if input_state['down_pressed'] else '未按'}")
            print(f"  左: {'按下' if input_state['left_pressed'] else '未按'}")
            print(f"  右: {'按下' if input_state['right_pressed'] else '未按'}")
            
            print("\n按鈕狀態:")
            print(f"  A: {'按下' if input_state['a_pressed'] else '未按'}")
            print(f"  B: {'按下' if input_state['b_pressed'] else '未按'}")
            print(f"  X: {'按下' if input_state['x_pressed'] else '未按'}")
            print(f"  Y: {'按下' if input_state['y_pressed'] else '未按'}")
            print(f"  LB: {'按下' if input_state['lb_pressed'] else '未按'}")
            print(f"  RB: {'按下' if input_state['rb_pressed'] else '未按'}")
            print(f"  LT: {'按下' if input_state['lt_pressed'] else '未按'}")
            print(f"  RT: {'按下' if input_state['rt_pressed'] else '未按'}")
            print(f"  Start: {'按下' if input_state['start_pressed'] else '未按'}")
            print(f"  Back: {'按下' if input_state['back_pressed'] else '未按'}")
            
            # 每 100ms 更新一次（實際使用時可能需要更高的更新率）
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n程式被使用者中斷")
    finally:
        pygame.quit()
        print("Pygame 資源已清理")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main.py - 主程式，負責整合所有模組

import os
import sys
import time
import pygame
from pygame.locals import *
import RPi.GPIO as GPIO
import subprocess # 用於執行 power_button.py
import signal # 用於處理信號

# 導入所需的本地模組
from screen_menu import SPIScreenManager
from matrix_keypad import MatrixKeypad
from gamepad_input import XboxController
from buzzer import BuzzerControl
from traffic_light import TrafficLight # 假設您已創建 traffic_light.py

# 遊戲模組導入
sys.path.append(os.path.join(os.path.dirname(__file__), 'games'))
from games.game1 import SnakeGame
from games.game2 import BrickBreakerGame
from games.game3 import SpaceInvadersGame
from games.game4 import TicTacToeGame
from games.game5 import MemoryMatchGame
from games.game6 import SimpleMazeGame
from games.game7 import WhacAMoleGame
from games.game8 import TetrisLikeGame
from games.game9 import ReactionTestGame

# 全域設定
VERSION = "1.0.1" # 版本更新
HDMI_SCREEN_WIDTH = 800
HDMI_SCREEN_HEIGHT = 600
FPS = 60

# 新硬體的 GPIO (BCM 編號) - 確保與 traffic_light.py 和 power_button.py 一致
TRAFFIC_LIGHT_RED_PIN = 22
TRAFFIC_LIGHT_YELLOW_PIN = 23
TRAFFIC_LIGHT_GREEN_PIN = 17
# POWER_BUTTON_PIN 在 power_button.py 中定義

class GameConsole:
    """多功能遊戲機主控制類"""
    
    def __init__(self):
        self.games = [
            {"id": 1, "name": "貪吃蛇 (Snake)", "description": "搖桿控制方向。按A鈕加速。", "game_class": SnakeGame},
            {"id": 2, "name": "打磚塊 (Brick Breaker)", "description": "搖桿左右移動擋板。按A鈕發射球。", "game_class": BrickBreakerGame},
            {"id": 3, "name": "太空侵略者 (Space Invaders)", "description": "搖桿左右移動。按A鈕射擊。", "game_class": SpaceInvadersGame},
            {"id": 4, "name": "井字遊戲 (Tic-Tac-Toe)", "description": "搖桿選擇格子。按A鈕確認。", "game_class": TicTacToeGame},
            {"id": 5, "name": "記憶翻牌 (Memory Match)", "description": "搖桿選擇牌。按A鈕翻牌。", "game_class": MemoryMatchGame},
            {"id": 6, "name": "簡易迷宮 (Simple Maze)", "description": "搖桿控制方向。", "game_class": SimpleMazeGame},
            {"id": 7, "name": "打地鼠 (Whac-A-Mole)", "description": "搖桿移動槌子。按A鈕敲擊。", "game_class": WhacAMoleGame},
            {"id": 8, "name": "俄羅斯方塊 (Tetris-like)", "description": "搖桿左右移動，上改變方向，下加速。按A鈕快速落下。", "game_class": TetrisLikeGame},
            {"id": 9, "name": "反應力測試 (Reaction Test)", "description": "出現信號時，按A鈕。", "game_class": ReactionTestGame}
        ]
        self.current_selection = 0
        self.current_game = None
        self.state = "MENU"
        
        self.hdmi_screen = None
        self.clock = None
        self.spi_screen = None
        self.keypad = None
        self.controller = None
        self.buzzer = None
        self.traffic_light = None # 新增交通信號燈物件
        self.main_process_pid = os.getpid() # 獲取主程式PID

        # 硬體初始化放在 initialize_hardware() 中
        # self.initialize_hardware() # 改為在 run_console 中呼叫
        self.load_resources()
        print(f"遊戲機系統準備完成，版本 {VERSION}")
        print(f"主程式 PID: {self.main_process_pid}")

    def initialize_hardware(self):
        """初始化所有硬體元件"""
        print("開始硬體初始化...")
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            pygame.init()
            pygame.display.set_caption(f"多功能遊戲機 v{VERSION}")
            self.hdmi_screen = pygame.display.set_mode((HDMI_SCREEN_WIDTH, HDMI_SCREEN_HEIGHT))
            self.clock = pygame.time.Clock()
            
            print("Pygame 初始化完成。")

            self.spi_screen = SPIScreenManager() # 使用更新後的 screen_menu.py
            if not self.spi_screen.device:
                print("警告: SPI 小螢幕初始化失敗，部分功能可能受影響。")
            else:
                print("SPI 小螢幕初始化成功。")
            
            self.keypad = MatrixKeypad()
            print("矩陣鍵盤初始化成功。")
            
            self.controller = XboxController()
            if not self.controller.is_connected:
                print("警告: Xbox 控制器未連接。")
            else:
                print("Xbox 控制器初始化成功。")

            self.buzzer = BuzzerControl()
            print("蜂鳴器初始化成功。")

            # 初始化交通信號燈
            self.traffic_light = TrafficLight(
                red_pin=TRAFFIC_LIGHT_RED_PIN,
                yellow_pin=TRAFFIC_LIGHT_YELLOW_PIN,
                green_pin=TRAFFIC_LIGHT_GREEN_PIN
            )
            print("交通信號燈初始化成功。")
            if self.traffic_light: # 播放啟動燈效
                self.traffic_light.green_on()
                time.sleep(0.3)
                self.traffic_light.yellow_on()
                time.sleep(0.3)
                self.traffic_light.red_on()
                time.sleep(0.3)
                self.traffic_light.all_off()

            print("所有硬體初始化流程完成。")
            return True
        
        except Exception as e:
            print(f"硬體初始化過程中發生嚴重錯誤: {e}")
            # 嘗試清理已初始化的部分
            self.cleanup_resources_on_error()
            return False

    def cleanup_resources_on_error(self):
        """在初始化失敗時清理已分配的資源"""
        print("初始化失敗，嘗試清理資源...")
        if self.spi_screen: self.spi_screen.cleanup()
        if self.keypad: self.keypad.cleanup()
        if self.controller: self.controller.cleanup()
        if self.buzzer: self.buzzer.cleanup()
        if self.traffic_light: self.traffic_light.cleanup()
        if pygame.get_init(): pygame.quit()
        GPIO.cleanup() # 最後清理 GPIO
        print("部分資源已清理。")

    def load_resources(self):
        self.assets_path = os.path.join(os.path.dirname(__file__), 'assets')
        if self.buzzer: # 確保蜂鳴器已初始化
            self.buzzer.load_tones()
        
    def run(self):
        """主循環"""
        if not self.initialize_hardware():
            print("硬體初始化失敗，無法啟動遊戲機。請檢查錯誤訊息。")
            # 即使初始化失敗，也短暫停留讓使用者看到錯誤
            time.sleep(5)
            return # 直接退出 run 方法

        if self.spi_screen and self.spi_screen.device:
            self.spi_screen.display_custom_message("遊戲機", f"版本 {VERSION}\n正在啟動...", duration=2)

        running = True
        
        # 範例：遊戲開始時閃爍交通燈
        game_starting_sequence_done = False 

        while running:
            # 狀態處理
            if self.state == "MENU":
                self.handle_menu()
            elif self.state == "INSTRUCTION":
                game_starting_sequence_done = False # 重置遊戲開始燈效標記
                self.handle_instruction()
            elif self.state == "GAME":
                if not game_starting_sequence_done and self.traffic_light:
                    print("遊戲開始 - 交通燈序列")
                    self.traffic_light.red_on()
                    self.buzzer.play_tone(frequency=300, duration=0.4)
                    time.sleep(0.5)
                    self.traffic_light.yellow_on()
                    self.buzzer.play_tone(frequency=600, duration=0.4)
                    time.sleep(0.5)
                    self.traffic_light.green_on()
                    self.buzzer.play_tone(frequency=1000, duration=0.4)
                    time.sleep(0.5)
                    self.traffic_light.all_off()
                    game_starting_sequence_done = True
                self.handle_game()
            
            self.clock.tick(FPS)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "GAME":
                            if self.buzzer: self.buzzer.play_tone("back")
                            if self.traffic_light: self.traffic_light.all_off() # 遊戲結束時關閉交通燈
                            self.end_current_game()
                            self.state = "MENU"
                            if self.spi_screen and self.spi_screen.device: # 返回選單時更新SPI
                                self.spi_screen.display_menu(self.games, self.current_selection)
                        else: # 在選單或說明頁按 ESC 直接退出
                            running = False
        
        self.cleanup() # 遊戲主循環結束後清理
    
    def handle_menu(self):
        if self.spi_screen and self.spi_screen.device:
            self.spi_screen.display_menu(self.games, self.current_selection)
        
        key_pressed = self.keypad.get_key()
        if key_pressed is not None:
            try:
                # 嘗試將按鍵轉換為數字
                key_value = int(key_pressed)
                if 1 <= key_value <= 9 and key_value <= len(self.games):
                    if self.buzzer: self.buzzer.play_tone("select")
                    self.current_selection = key_value - 1
                    self.state = "INSTRUCTION"
                    if self.traffic_light: self.traffic_light.yellow_on() # 進入說明時亮黃燈
                # elif key_pressed == 'A': # ...
                # (可以根據 KEY_MAP 添加其他按鍵功能)
            except ValueError:
                # 如果按鍵不是數字 (例如 A, B, C, D, *, #)
                print(f"選單中按下了非數字鍵: {key_pressed}")
                if key_pressed == 'D' and self.traffic_light: # 假設D是某種特殊操作
                     self.traffic_light.all_off()


        controller_input = self.controller.get_input()
        if controller_input:
            if controller_input["up_pressed"]:
                self.current_selection = (self.current_selection - 1 + len(self.games)) % len(self.games)
                if self.buzzer: self.buzzer.play_tone("navigate")
            elif controller_input["down_pressed"]:
                self.current_selection = (self.current_selection + 1) % len(self.games)
                if self.buzzer: self.buzzer.play_tone("navigate")
            elif controller_input["a_pressed"]:
                if self.buzzer: self.buzzer.play_tone("select")
                self.state = "INSTRUCTION"
                if self.traffic_light: self.traffic_light.yellow_on() # 進入說明時亮黃燈
        
        if self.hdmi_screen:
            self.hdmi_screen.fill((0, 0, 0))
            self.render_menu_on_hdmi()
            pygame.display.flip()
    
    def handle_instruction(self):
        selected_game_data = self.games[self.current_selection]
        if self.spi_screen and self.spi_screen.device:
            self.spi_screen.display_game_instructions(selected_game_data)
        
        key_pressed = self.keypad.get_key()
        if key_pressed == "A": 
            if self.buzzer: self.buzzer.play_tone("game_start")
            # self.traffic_light.green_on() # 改到 run 迴圈中處理，配合倒數
            self.start_game(selected_game_data)
        elif key_pressed == "D": 
            if self.buzzer: self.buzzer.play_tone("back")
            if self.traffic_light: self.traffic_light.all_off()
            self.state = "MENU"
        
        controller_input = self.controller.get_input()
        if controller_input:
            if controller_input["a_pressed"]:
                if self.buzzer: self.buzzer.play_tone("game_start")
                # self.traffic_light.green_on() # 改到 run 迴圈中處理
                self.start_game(selected_game_data)
            elif controller_input["b_pressed"]:
                if self.buzzer: self.buzzer.play_tone("back")
                if self.traffic_light: self.traffic_light.all_off()
                self.state = "MENU"

        if self.hdmi_screen:
            self.hdmi_screen.fill((0, 0, 0))
            self.render_instructions_on_hdmi(selected_game_data)
            pygame.display.flip()

    def handle_game(self):
        if self.current_game is not None:
            controller_input = self.controller.get_input()
            game_status = self.current_game.update(controller_input)
            
            if game_status.get("game_over", False):
                if self.buzzer: self.buzzer.play_tone("game_over")
                if self.traffic_light: self.traffic_light.red_on() # 遊戲結束亮紅燈
                
                if self.spi_screen and self.spi_screen.device:
                    self.spi_screen.display_game_over(game_status.get("score", 0))
                
                # 在HDMI螢幕上也顯示遊戲結束
                if self.hdmi_screen and hasattr(self.current_game, 'draw_game_over'):
                    # 有些遊戲可能在自己的 render 中處理 game_over 畫面
                    # 如果沒有，這裡可以強制繪製
                    self.current_game.render(self.hdmi_screen) # 先渲染最後一幀
                    # self.current_game.draw_game_over(self.hdmi_screen) # 如果有獨立的 game_over 繪製
                    pygame.display.flip()

                time.sleep(3) 
                self.end_current_game()
                self.state = "MENU"
                if self.traffic_light: self.traffic_light.all_off() # 返回選單時關閉交通燈
                if self.spi_screen and self.spi_screen.device: # 返回選單時更新SPI
                    self.spi_screen.display_menu(self.games, self.current_selection)
            
            elif self.hdmi_screen: # 遊戲進行中
                self.current_game.render(self.hdmi_screen)
                pygame.display.flip()
    
    def start_game(self, game_data):
        try:
            game_class = game_data["game_class"]
            self.current_game = game_class(
                width=HDMI_SCREEN_WIDTH,
                height=HDMI_SCREEN_HEIGHT,
                buzzer=self.buzzer # 將蜂鳴器實例傳遞給遊戲
            )
            # 在 GameConsole 的 run 方法中處理遊戲開始的交通燈和音效
            self.state = "GAME"
            # 清除 SPI 螢幕，或顯示遊戲名稱/分數等 (可選)
            if self.spi_screen and self.spi_screen.device:
                self.spi_screen.clear_screen() 
                # self.spi_screen.display_custom_message(game_data['name'], "遊戲進行中...")
        except Exception as e:
            print(f"啟動遊戲 '{game_data['name']}' 失敗: {e}")
            if self.buzzer: self.buzzer.play_tone("error")
            if self.traffic_light: self.traffic_light.red_on() # 啟動失敗亮紅燈
            time.sleep(1)
            if self.traffic_light: self.traffic_light.all_off()
            self.state = "MENU" # 返回選單

    def end_current_game(self):
        if self.current_game:
            if hasattr(self.current_game, 'cleanup'):
                self.current_game.cleanup()
            self.current_game = None
            print("當前遊戲已結束並清理。")
    
    def render_menu_on_hdmi(self):
        if not self.hdmi_screen: return
        font_title = pygame.font.Font(None, 72)
        font_item = pygame.font.Font(None, 48)
        
        title_surface = font_title.render(f"多功能遊戲機 v{VERSION}", True, (255, 255, 255))
        self.hdmi_screen.blit(title_surface, (HDMI_SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 50))
        
        for i, game in enumerate(self.games):
            color = (255, 255, 0) if i == self.current_selection else (200, 200, 200)
            y_pos = 150 + i * 50
            item_surface = font_item.render(f"{game['id']}. {game['name']}", True, color)
            self.hdmi_screen.blit(item_surface, (HDMI_SCREEN_WIDTH // 2 - item_surface.get_width() // 2, y_pos))

    def render_instructions_on_hdmi(self, game_data):
        if not self.hdmi_screen: return
        font_title = pygame.font.Font(None, 72)
        font_text = pygame.font.Font(None, 36) # 縮小一點字體以容納更多說明
        font_hint = pygame.font.Font(None, 48)

        title_surface = font_title.render(game_data["name"], True, (255, 255, 255))
        self.hdmi_screen.blit(title_surface, (HDMI_SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 100))
        
        # 處理多行說明
        desc_lines = game_data["description"].split('。') # 嘗試用句號分行
        y_offset = 0
        for line in desc_lines:
            if line.strip(): # 忽略空行
                desc_surface = font_text.render(line.strip() + "。", True, (200, 200, 200))
                self.hdmi_screen.blit(desc_surface, (HDMI_SCREEN_WIDTH // 2 - desc_surface.get_width() // 2, 200 + y_offset))
                y_offset += 40 # 行高

        hint_surface = font_hint.render("按 A/確認 開始遊戲 或 B/返回 返回選單", True, (150, 150, 150))
        self.hdmi_screen.blit(hint_surface, (HDMI_SCREEN_WIDTH // 2 - hint_surface.get_width() // 2, HDMI_SCREEN_HEIGHT - 100))
    
    def cleanup(self):
        """清理資源，關閉硬體連接"""
        print("開始系統清理...")
        
        if self.current_game:
            self.end_current_game()
        
        if self.spi_screen: self.spi_screen.cleanup()
        if self.keypad: self.keypad.cleanup()
        if self.controller: self.controller.cleanup()
        if self.buzzer: self.buzzer.cleanup()
        if self.traffic_light: self.traffic_light.cleanup()
        
        if pygame.get_init():
            pygame.quit()
            print("Pygame 已關閉。")
        
        # GPIO.cleanup() 會在主程式的 finally 區塊中執行，確保最後清理
        # print("GPIO 清理將由主 finally 區塊處理。")
        print("遊戲機資源清理完成。")

# 主程式入口
if __name__ == "__main__":
    power_button_process = None
    game_console_instance = None
    
    # 設定一個信號處理器來接收 power_button.py 的通知 (如果需要更優雅的關機)
    # def handle_custom_shutdown_signal(sig, frame):
    #     print("主程式接收到自訂關機信號，開始清理...")
    #     # 在這裡觸發 GameConsole 的清理邏輯
    #     if game_console_instance:
    #         # 這裡不能直接呼叫 game_console_instance.cleanup() 因為可能在不同執行緒
    #         # 需要一個更安全的機制，例如設定一個全域 flag
    #         # 或者讓 power_button.py 直接執行 shutdown，主程式的 finally 會處理清理
    #         pass
    # signal.signal(signal.SIGUSR1, handle_custom_shutdown_signal)


    try:
        # 獲取主程式 PID 並作為參數傳遞給 power_button.py
        main_pid = str(os.getpid())
        power_button_script_path = os.path.join(os.path.dirname(__file__), "power_button.py")
        
        # 檢查 power_button.py 是否存在
        if os.path.exists(power_button_script_path):
            print(f"嘗試啟動 power_button.py (PID: {main_pid})...")
            # 使用 sudo 執行 power_button.py，因為它裡面有 sudo shutdown
            # 並且將主程式的 PID 傳遞過去 (可選)
            power_button_process = subprocess.Popen(
                ['sudo', 'python3', power_button_script_path, main_pid],
                preexec_fn=os.setpgrp # 讓子行程成為新的行程組，方便一起終止
            )
            print(f"power_button.py 應該已在背景啟動 (子行程 PID: {power_button_process.pid})。")
        else:
            print(f"警告: power_button.py 未在預期路徑找到: {power_button_script_path}")

        game_console_instance = GameConsole()
        game_console_instance.run()

    except KeyboardInterrupt:
        print("\n主程式被使用者 (Ctrl+C) 中斷。")
    except Exception as e:
        print(f"主程式發生未預期錯誤: {e}")
    finally:
        print("主程式 finally 區塊開始執行清理...")
        if game_console_instance:
            game_console_instance.cleanup() # 呼叫 GameConsole 的清理方法
        
        if power_button_process:
            print(f"嘗試終止 power_button.py 子行程 (PID: {power_button_process.pid})...")
            try:
                # 嘗試發送 SIGTERM 給整個行程組
                os.killpg(os.getpgid(power_button_process.pid), signal.SIGTERM)
                power_button_process.wait(timeout=2) # 等待子行程結束
                print("power_button.py 子行程已終止。")
            except ProcessLookupError:
                print("power_button.py 子行程似乎已自行結束。")
            except subprocess.TimeoutExpired:
                print("等待 power_button.py 子行程超時，強制終止...")
                os.killpg(os.getpgid(power_button_process.pid), signal.SIGKILL)
            except Exception as e_term:
                print(f"終止 power_button.py 時發生錯誤: {e_term}")
        
        # 確保 GPIO 在所有其他清理之後執行
        # RPi.GPIO 的 cleanup 應該只被呼叫一次
        # GameConsole 的 cleanup 裡不呼叫 GPIO.cleanup()，而是由這裡統一處理
        if GPIO.getmode() is not None: # 檢查 GPIO 是否曾被設定模式
            print("執行最終的 GPIO.cleanup()...")
            GPIO.cleanup()
        
        print("主程式已結束。")
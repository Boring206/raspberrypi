#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main.py - 主程式，負責整合所有模組

import os
import sys
import time
import pygame
from pygame.locals import *
import RPi.GPIO as GPIO

# 導入所需的本地模組
from screen_menu import SPIScreenManager
from matrix_keypad import MatrixKeypad
from gamepad_input import XboxController
from buzzer import BuzzerControl

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
VERSION = "1.0.0"
HDMI_SCREEN_WIDTH = 800  # 大螢幕寬度
HDMI_SCREEN_HEIGHT = 600  # 大螢幕高度
FPS = 60  # 遊戲畫面更新頻率

class GameConsole:
    """多功能遊戲機主控制類"""
    
    def __init__(self):
        # 初始化硬體
        self.initialize_hardware()
        
        # 初始化遊戲資料
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
        
        self.current_selection = 0  # 目前選擇的遊戲索引
        self.current_game = None  # 當前執行中的遊戲
        self.state = "MENU"  # 目前狀態：MENU、INSTRUCTION、GAME
        
        # 載入資源
        self.load_resources()
        
        print(f"遊戲機初始化完成，版本 {VERSION}")
    
    def initialize_hardware(self):
        """初始化所有硬體元件"""
        try:
            # 初始化 GPIO
            GPIO.setmode(GPIO.BCM)  # 使用 BCM 編號模式
            GPIO.setwarnings(False)  # 禁用警告
            
            # 初始化 pygame 用於 HDMI 輸出和控制器輸入
            pygame.init()
            pygame.display.set_caption("多功能遊戲機")
            self.hdmi_screen = pygame.display.set_mode((HDMI_SCREEN_WIDTH, HDMI_SCREEN_HEIGHT))
            self.clock = pygame.time.Clock()
            
            # 初始化 SPI 小螢幕
            self.spi_screen = SPIScreenManager()
            
            # 初始化矩陣鍵盤
            self.keypad = MatrixKeypad()
            
            # 初始化 Xbox 控制器
            self.controller = XboxController()
            
            # 初始化蜂鳴器
            self.buzzer = BuzzerControl()
            
            print("所有硬體初始化成功")
            return True
        
        except Exception as e:
            print(f"硬體初始化失敗: {e}")
            self.cleanup()
            return False
    
    def load_resources(self):
        """載入遊戲資源，如圖片、聲音等"""
        # 這裡可以載入共用資源
        self.assets_path = os.path.join(os.path.dirname(__file__), 'assets')
        # 實際應用中載入字體、音效等資源
        self.buzzer.load_tones()  # 載入音效資源
        
    def run(self):
        """主循環"""
        running = True
        
        while running:
            if self.state == "MENU":
                self.handle_menu()
            elif self.state == "INSTRUCTION":
                self.handle_instruction()
            elif self.state == "GAME":
                self.handle_game()
            
            # 保持循環的穩定幀率
            self.clock.tick(FPS)
            
            # 檢查退出事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "GAME":
                            self.end_current_game()
                            self.state = "MENU"
                        else:
                            running = False
        
        # 清理資源
        self.cleanup()
    
    def handle_menu(self):
        """處理選單狀態的邏輯"""
        # 更新 SPI 螢幕顯示
        self.spi_screen.display_menu(self.games, self.current_selection)
        
        # 檢查矩陣鍵盤輸入
        key_pressed = self.keypad.get_key()
        if key_pressed is not None:
            if 1 <= key_pressed <= 9:
                # 選擇遊戲
                self.buzzer.play_tone("select")
                self.current_selection = key_pressed - 1
                self.state = "INSTRUCTION"
        
        # 可選：使用 Xbox 控制器選擇遊戲
        controller_input = self.controller.get_input()
        if controller_input:
            if controller_input["up_pressed"]:
                self.current_selection = (self.current_selection - 1) % len(self.games)
                self.buzzer.play_tone("navigate")
            elif controller_input["down_pressed"]:
                self.current_selection = (self.current_selection + 1) % len(self.games)
                self.buzzer.play_tone("navigate")
            elif controller_input["a_pressed"]:
                self.buzzer.play_tone("select")
                self.state = "INSTRUCTION"
        
        # 更新大螢幕顯示
        self.hdmi_screen.fill((0, 0, 0))
        self.render_menu_on_hdmi()
        pygame.display.flip()
    
    def handle_instruction(self):
        """處理遊戲說明狀態的邏輯"""
        selected_game = self.games[self.current_selection]
        
        # 顯示遊戲說明在 SPI 螢幕上
        self.spi_screen.display_game_instructions(selected_game)
        
        # 檢查輸入以開始遊戲或返回選單
        key_pressed = self.keypad.get_key()
        if key_pressed == "A":  # 假設 "A" 是確認鍵
            self.buzzer.play_tone("game_start")
            self.start_game(selected_game)
        elif key_pressed == "D":  # 假設 "D" 是返回鍵
            self.buzzer.play_tone("back")
            self.state = "MENU"
        
        # 使用 Xbox 控制器
        controller_input = self.controller.get_input()
        if controller_input:
            if controller_input["a_pressed"]:
                self.buzzer.play_tone("game_start")
                self.start_game(selected_game)
            elif controller_input["b_pressed"]:
                self.buzzer.play_tone("back")
                self.state = "MENU"
        
        # 更新大螢幕顯示
        self.hdmi_screen.fill((0, 0, 0))
        self.render_instructions_on_hdmi(selected_game)
        pygame.display.flip()
    
    def handle_game(self):
        """處理遊戲運行邏輯"""
        if self.current_game is not None:
            # 獲取控制器輸入
            controller_input = self.controller.get_input()
            
            # 更新遊戲狀態
            game_status = self.current_game.update(controller_input)
            
            # 檢查遊戲是否結束
            if game_status.get("game_over", False):
                self.buzzer.play_tone("game_over")
                self.spi_screen.display_game_over(game_status.get("score", 0))
                time.sleep(3)  # 顯示結束信息幾秒鐘
                self.end_current_game()
                self.state = "MENU"
            
            # 渲染遊戲畫面到 HDMI
            self.current_game.render(self.hdmi_screen)
            pygame.display.flip()
    
    def start_game(self, game_data):
        """啟動選定的遊戲"""
        try:
            # 初始化遊戲類
            game_class = game_data["game_class"]
            self.current_game = game_class(
                width=HDMI_SCREEN_WIDTH,
                height=HDMI_SCREEN_HEIGHT,
                buzzer=self.buzzer
            )
            self.state = "GAME"
        except Exception as e:
            print(f"啟動遊戲失敗: {e}")
            self.buzzer.play_tone("error")
            self.state = "MENU"
    
    def end_current_game(self):
        """結束當前遊戲並釋放資源"""
        if self.current_game:
            self.current_game.cleanup()
            self.current_game = None
    
    def render_menu_on_hdmi(self):
        """在 HDMI 大螢幕上渲染遊戲選單"""
        # 這裡實現更美觀的 HDMI 選單
        font_title = pygame.font.Font(None, 72)
        font_item = pygame.font.Font(None, 48)
        
        # 繪製標題
        title = font_title.render("多功能遊戲機", True, (255, 255, 255))
        self.hdmi_screen.blit(title, (HDMI_SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
        
        # 繪製選項
        for i, game in enumerate(self.games):
            color = (255, 255, 0) if i == self.current_selection else (200, 200, 200)
            y_pos = 150 + i * 50
            item = font_item.render(f"{game['id']}. {game['name']}", True, color)
            self.hdmi_screen.blit(item, (HDMI_SCREEN_WIDTH // 2 - item.get_width() // 2, y_pos))
    
    def render_instructions_on_hdmi(self, game):
        """在 HDMI 大螢幕上渲染遊戲說明"""
        font_title = pygame.font.Font(None, 72)
        font_text = pygame.font.Font(None, 48)
        
        # 繪製標題
        title = font_title.render(game["name"], True, (255, 255, 255))
        self.hdmi_screen.blit(title, (HDMI_SCREEN_WIDTH // 2 - title.get_width() // 2, 100))
        
        # 繪製說明
        desc = font_text.render(game["description"], True, (200, 200, 200))
        self.hdmi_screen.blit(desc, (HDMI_SCREEN_WIDTH // 2 - desc.get_width() // 2, 200))
        
        # 繪製提示
        hint = font_text.render("按 A 開始遊戲 或 B 返回選單", True, (150, 150, 150))
        self.hdmi_screen.blit(hint, (HDMI_SCREEN_WIDTH // 2 - hint.get_width() // 2, 400))
    
    def cleanup(self):
        """清理資源，關閉硬體連接"""
        print("清理系統資源...")
        
        # 關閉遊戲
        if self.current_game:
            self.end_current_game()
        
        # 釋放硬體資源
        self.spi_screen.cleanup()
        self.keypad.cleanup()
        self.controller.cleanup()
        self.buzzer.cleanup()
        
        # 清理 Pygame
        pygame.quit()
        
        # 清理 GPIO
        GPIO.cleanup()
        
        print("系統已安全關閉")

# 主程式入口
if __name__ == "__main__":
    try:
        # 建立並執行遊戲機
        game_console = GameConsole()
        game_console.run()
    except KeyboardInterrupt:
        print("程式被使用者中斷")
    except Exception as e:
        print(f"發生錯誤: {e}")
    finally:
        # 確保 GPIO 被清理
        GPIO.cleanup()
        pygame.quit()
        print("程式已結束")

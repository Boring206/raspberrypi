#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main.py - 主程式，負責整合所有模組 (Enhanced Version)

import os
import sys
import time
import json
import logging
import threading
import queue
from datetime import datetime
from enum import Enum
import pygame
from pygame.locals import *
import RPi.GPIO as GPIO
import subprocess
import signal
import psutil
import traceback

# 導入所需的本地模組
from screen_menu import SPIScreenManager
from matrix_keypad import MatrixKeypad
from gamepad_input import XboxController
from buzzer import BuzzerControl
from traffic_light import TrafficLight
from power_button import GameControlButton

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
VERSION = "2.0.0"
HDMI_SCREEN_WIDTH = 800
HDMI_SCREEN_HEIGHT = 600
FPS = 60

# 硬體 GPIO 設定
TRAFFIC_LIGHT_RED_PIN = 4
TRAFFIC_LIGHT_YELLOW_PIN = 3
TRAFFIC_LIGHT_GREEN_PIN = 2

class GameState(Enum):
    """遊戲狀態枚舉"""
    STARTUP = "startup"
    MENU = "menu"
    INSTRUCTION = "instruction"
    GAME_STARTING = "game_starting"
    GAME = "game"
    GAME_PAUSED = "game_paused"
    GAME_OVER = "game_over"
    SETTINGS = "settings"
    SHUTDOWN = "shutdown"
    ERROR = "error"

class SystemConfig:
    """系統配置管理類"""
    
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        self.default_config = {
            "display": {
                "hdmi_width": HDMI_SCREEN_WIDTH,
                "hdmi_height": HDMI_SCREEN_HEIGHT,
                "fps": FPS,
                "fullscreen": False
            },
            "audio": {
                "enable_buzzer": True,
                "volume": 80,
                "startup_sound": True
            },
            "hardware": {
                "spi_screen_enabled": True,
                "xbox_controller_enabled": True,
                "matrix_keypad_enabled": True,
                "traffic_light_enabled": True,
                "power_button_enabled": True
            },
            "debug": {
                "log_level": "INFO",
                "show_fps": False,
                "hardware_monitor": False
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        """載入配置檔案"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合併預設配置
                    return self._merge_config(self.default_config, config)
            else:
                self.save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            logging.error(f"載入配置失敗: {e}")
            return self.default_config.copy()
    
    def save_config(self, config=None):
        """儲存配置檔案"""
        try:
            config_to_save = config or self.config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"儲存配置失敗: {e}")
    
    def _merge_config(self, default, user):
        """合併配置"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result

class PerformanceMonitor:
    """性能監控類"""
    
    def __init__(self):
        self.start_time = time.time()
        self.frame_count = 0
        self.fps_history = []
        self.cpu_usage = 0
        self.memory_usage = 0
        self.temperature = 0
        
    def update(self):
        """更新性能數據"""
        self.frame_count += 1
        current_time = time.time()
        
        # 計算FPS
        if current_time - self.start_time >= 1.0:
            fps = self.frame_count / (current_time - self.start_time)
            self.fps_history.append(fps)
            if len(self.fps_history) > 60:  # 保留最近60秒
                self.fps_history.pop(0)
            
            self.frame_count = 0
            self.start_time = current_time
            
            # 更新系統資源使用率
            self.cpu_usage = psutil.cpu_percent()
            self.memory_usage = psutil.virtual_memory().percent
            
            # 嘗試讀取CPU溫度
            try:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    self.temperature = int(f.read()) / 1000.0
            except:
                self.temperature = 0
    
    def get_average_fps(self):
        """獲取平均FPS"""
        return sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0

class EnhancedGameConsole:
    """增強版多功能遊戲機主控制類"""
    
    def __init__(self):
        # 初始化日誌系統
        self._setup_logging()
        
        # 載入配置
        self.config = SystemConfig()
        logging.info(f"遊戲機系統啟動 v{VERSION}")
        
        # 初始化遊戲列表
        self.games = [
            {"id": 1, "name": "貪吃蛇 (Snake)", "description": "搖桿控制方向。按A鈕加速。避免撞牆和自己。", "game_class": SnakeGame, "difficulty": "Easy"},
            {"id": 2, "name": "打磚塊 (Brick Breaker)", "description": "搖桿左右移動擋板。按A鈕發射球。清除所有磚塊。", "game_class": BrickBreakerGame, "difficulty": "Medium"},
            {"id": 3, "name": "太空侵略者 (Space Invaders)", "description": "搖桿左右移動。按A鈕射擊。消滅所有外星人。", "game_class": SpaceInvadersGame, "difficulty": "Hard"},
            {"id": 4, "name": "井字遊戲 (Tic-Tac-Toe)", "description": "搖桿選擇格子。按A鈕確認。連成一線獲勝。", "game_class": TicTacToeGame, "difficulty": "Easy"},
            {"id": 5, "name": "記憶翻牌 (Memory Match)", "description": "搖桿選擇牌。按A鈕翻牌。記住位置配對。", "game_class": MemoryMatchGame, "difficulty": "Medium"},
            {"id": 6, "name": "簡易迷宮 (Simple Maze)", "description": "搖桿控制方向。找到出口。時間越短越好。", "game_class": SimpleMazeGame, "difficulty": "Medium"},
            {"id": 7, "name": "打地鼠 (Whac-A-Mole)", "description": "搖桿移動槌子。按A鈕敲擊。反應要快！", "game_class": WhacAMoleGame, "difficulty": "Hard"},
            {"id": 8, "name": "俄羅斯方塊 (Tetris-like)", "description": "搖桿移動旋轉。消除滿行得分。速度會加快。", "game_class": TetrisLikeGame, "difficulty": "Hard"},
            {"id": 9, "name": "反應力測試 (Reaction Test)", "description": "出現信號時按A鈕。測試反應速度極限。", "game_class": ReactionTestGame, "difficulty": "Medium"}
        ]
        
        # 系統狀態
        self.state = GameState.STARTUP
        self.previous_state = None
        self.current_selection = 0
        self.current_game = None
        self.running = True
        
        # 硬體組件
        self.hdmi_screen = None
        self.clock = None
        self.spi_screen = None
        self.keypad = None
        self.controller = None
        self.buzzer = None
        self.traffic_light = None
        self.power_button = None
        
        # 性能監控
        self.performance_monitor = PerformanceMonitor()
        
        # 事件佇列
        self.event_queue = queue.Queue()
        
        # 輸入處理
        self.last_input_time = 0
        self.input_cooldown = 0.2  # 輸入冷卻時間
        
        # 統計數據
        self.session_stats = {
            "start_time": datetime.now(),
            "games_played": 0,
            "total_score": 0,
            "best_scores": {}
        }
        
        # 線程控制
        self.monitor_thread = None
        self.monitor_running = False
        
        logging.info("遊戲機系統初始化完成")

    def _setup_logging(self):
        """設置日誌系統"""
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f'gamebox_{datetime.now().strftime("%Y%m%d")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def initialize_hardware(self):
        """初始化所有硬體元件 - 增強版"""
        logging.info("開始硬體初始化...")
        
        try:
            # GPIO 初始化
            if not self._init_gpio():
                return False
            
            # Pygame 初始化
            if not self._init_pygame():
                return False
            
            # 硬體組件初始化
            hardware_results = {}
            
            # SPI 螢幕
            if self.config.config["hardware"]["spi_screen_enabled"]:
                hardware_results["spi_screen"] = self._init_spi_screen()
            
            # 矩陣鍵盤
            if self.config.config["hardware"]["matrix_keypad_enabled"]:
                hardware_results["keypad"] = self._init_keypad()
            
            # Xbox 控制器
            if self.config.config["hardware"]["xbox_controller_enabled"]:
                hardware_results["controller"] = self._init_controller()
            
            # 蜂鳴器
            if self.config.config["audio"]["enable_buzzer"]:
                hardware_results["buzzer"] = self._init_buzzer()
            
            # 交通燈
            if self.config.config["hardware"]["traffic_light_enabled"]:
                hardware_results["traffic_light"] = self._init_traffic_light()
            
            # 電源按鈕
            if self.config.config["hardware"]["power_button_enabled"]:
                hardware_results["power_button"] = self._init_power_button()
            
            # 檢查硬體初始化結果
            failed_components = [k for k, v in hardware_results.items() if not v]
            if failed_components:
                logging.warning(f"以下硬體組件初始化失敗: {failed_components}")
                # 可以選擇繼續運行或停止
                if len(failed_components) > len(hardware_results) / 2:
                    logging.error("超過一半的硬體組件初始化失敗，停止啟動")
                    return False
            
            # 啟動系統監控
            if self.config.config["debug"]["hardware_monitor"]:
                self._start_system_monitor()
            
            # 播放啟動音效和燈效
            self._play_startup_sequence()
            
            logging.info("硬體初始化完成")
            return True
            
        except Exception as e:
            logging.error(f"硬體初始化過程中發生嚴重錯誤: {e}")
            logging.error(traceback.format_exc())
            self._cleanup_on_error()
            return False

    def _init_gpio(self):
        """初始化GPIO"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            logging.info("GPIO 初始化成功")
            return True
        except Exception as e:
            logging.error(f"GPIO 初始化失敗: {e}")
            return False

    def _init_pygame(self):
        """初始化Pygame"""
        try:
            pygame.init()
            pygame.display.set_caption(f"多功能遊戲機 v{VERSION}")
            
            flags = 0
            if self.config.config["display"]["fullscreen"]:
                flags |= pygame.FULLSCREEN
            
            self.hdmi_screen = pygame.display.set_mode(
                (self.config.config["display"]["hdmi_width"], 
                 self.config.config["display"]["hdmi_height"]), 
                flags
            )
            self.clock = pygame.time.Clock()
            
            logging.info("Pygame 初始化成功")
            return True
        except Exception as e:
            logging.error(f"Pygame 初始化失敗: {e}")
            return False

    def _init_spi_screen(self):
        """初始化SPI螢幕"""
        try:
            self.spi_screen = SPIScreenManager()
            if self.spi_screen.device:
                logging.info("SPI 螢幕初始化成功")
                return True
            else:
                logging.warning("SPI 螢幕初始化失敗")
                return False
        except Exception as e:
            logging.error(f"SPI 螢幕初始化錯誤: {e}")
            return False

    def _init_keypad(self):
        """初始化矩陣鍵盤"""
        try:
            self.keypad = MatrixKeypad()
            logging.info("矩陣鍵盤初始化成功")
            return True
        except Exception as e:
            logging.error(f"矩陣鍵盤初始化失敗: {e}")
            return False

    def _init_controller(self):
        """初始化Xbox控制器"""
        try:
            self.controller = XboxController()
            if self.controller.is_connected:
                logging.info("Xbox 控制器初始化成功")
                return True
            else:
                logging.warning("Xbox 控制器未連接")
                return False
        except Exception as e:
            logging.error(f"Xbox 控制器初始化失敗: {e}")
            return False

    def _init_buzzer(self):
        """初始化蜂鳴器"""
        try:
            self.buzzer = BuzzerControl()
            logging.info("蜂鳴器初始化成功")
            return True
        except Exception as e:
            logging.error(f"蜂鳴器初始化失敗: {e}")
            return False

    def _init_traffic_light(self):
        """初始化交通燈"""
        try:
            self.traffic_light = TrafficLight(
                red_pin=TRAFFIC_LIGHT_RED_PIN,
                yellow_pin=TRAFFIC_LIGHT_YELLOW_PIN,
                green_pin=TRAFFIC_LIGHT_GREEN_PIN
            )
            logging.info("交通燈初始化成功")
            return True
        except Exception as e:
            logging.error(f"交通燈初始化失敗: {e}")
            return False

    def _init_power_button(self):
        """初始化電源按鈕"""
        try:
            self.power_button = GameControlButton(main_console_instance=self)
            self.power_button.start_monitoring()
            logging.info("電源按鈕初始化成功")
            return True
        except Exception as e:
            logging.error(f"電源按鈕初始化失敗: {e}")
            return False

    def _start_system_monitor(self):
        """啟動系統監控線程"""
        try:
            self.monitor_running = True
            self.monitor_thread = threading.Thread(target=self._system_monitor_loop, daemon=True)
            self.monitor_thread.start()
            logging.info("系統監控已啟動")
        except Exception as e:
            logging.error(f"系統監控啟動失敗: {e}")

    def _system_monitor_loop(self):
        """系統監控循環"""
        while self.monitor_running:
            try:
                # 監控系統資源
                cpu_usage = psutil.cpu_percent()
                memory_usage = psutil.virtual_memory().percent
                
                # 如果資源使用率過高，記錄警告
                if cpu_usage > 80:
                    logging.warning(f"CPU 使用率過高: {cpu_usage}%")
                if memory_usage > 80:
                    logging.warning(f"記憶體使用率過高: {memory_usage}%")
                
                # 檢查硬體狀態
                if self.controller and not self.controller.is_connected:
                    self.controller.check_connection()
                
                time.sleep(5)  # 每5秒檢查一次
                
            except Exception as e:
                logging.error(f"系統監控錯誤: {e}")
                time.sleep(1)

    def _play_startup_sequence(self):
        """播放啟動序列"""
        if self.config.config["audio"]["startup_sound"] and self.buzzer:
            try:
                self.buzzer.play_startup_melody()
            except Exception as e:
                logging.error(f"播放啟動音效失敗: {e}")
        
        if self.traffic_light:
            try:
                self.traffic_light.green_on()
                time.sleep(0.3)
                self.traffic_light.yellow_on()
                time.sleep(0.3)
                self.traffic_light.red_on()
                time.sleep(0.3)
                self.traffic_light.all_off()
            except Exception as e:
                logging.error(f"啟動燈效失敗: {e}")

    def run(self):
        """主循環 - 增強版"""
        if not self.initialize_hardware():
            logging.error("硬體初始化失敗，無法啟動遊戲機")
            self._show_error_message("硬體初始化失敗")
            time.sleep(5)
            return

        # 顯示啟動畫面
        if self.spi_screen and self.spi_screen.device:
            self.spi_screen.display_custom_message("遊戲機", f"版本 {VERSION}\n正在啟動...", duration=2)

        # 狀態機主循環
        while self.running:
            try:
                # 處理電源按鈕事件
                self._handle_power_button_events()
                
                # 更新性能監控
                if self.config.config["debug"]["hardware_monitor"]:
                    self.performance_monitor.update()
                
                # 狀態處理
                self._handle_current_state()
                
                # 處理Pygame事件
                self._handle_pygame_events()
                
                # 控制幀率
                self.clock.tick(self.config.config["display"]["fps"])
                
            except Exception as e:
                logging.error(f"主循環錯誤: {e}")
                logging.error(traceback.format_exc())
                self.state = GameState.ERROR
                
        self.cleanup()

    def _handle_power_button_events(self):
        """處理電源按鈕事件"""
        if not self.power_button:
            return
        
        events = self.power_button.get_pending_events()
        for event in events:
            if event['action'] == 'toggle_pause':
                self._handle_pause_toggle()
            elif event['action'] == 'return_to_menu':
                self._handle_return_to_menu()

    def _handle_pause_toggle(self):
        """處理暫停切換"""
        if self.state == GameState.GAME:
            self.state = GameState.GAME_PAUSED
            if self.traffic_light:
                self.traffic_light.yellow_on()
            logging.info("遊戲已暫停")
        elif self.state == GameState.GAME_PAUSED:
            self.state = GameState.GAME
            if self.traffic_light:
                self.traffic_light.green_on()
            logging.info("遊戲已繼續")

    def _handle_return_to_menu(self):
        """處理返回主選單"""
        if self.state in [GameState.GAME, GameState.GAME_PAUSED, GameState.INSTRUCTION]:
            if self.current_game:
                self.end_current_game()
            self.state = GameState.MENU
            if self.traffic_light:
                self.traffic_light.all_off()
            logging.info("已返回主選單")

    def _handle_current_state(self):
        """處理當前狀態"""
        if self.state == GameState.STARTUP:
            self._handle_startup()
        elif self.state == GameState.MENU:
            self._handle_menu()
        elif self.state == GameState.INSTRUCTION:
            self._handle_instruction()
        elif self.state == GameState.GAME_STARTING:
            self._handle_game_starting()
        elif self.state == GameState.GAME:
            self._handle_game()
        elif self.state == GameState.GAME_PAUSED:
            self._handle_game_paused()
        elif self.state == GameState.GAME_OVER:
            self._handle_game_over()
        elif self.state == GameState.ERROR:
            self._handle_error()

    def _handle_startup(self):
        """處理啟動狀態"""
        self.state = GameState.MENU

    def _handle_menu(self):
        """處理選單狀態"""
        # ...existing menu code...
        if self.spi_screen and self.spi_screen.device:
            self.spi_screen.display_menu(self.games, self.current_selection)
        
        # 處理輸入
        if self._can_process_input():
            self._process_menu_input()
        
        # 渲染HDMI畫面
        if self.hdmi_screen:
            self.hdmi_screen.fill((0, 0, 0))
            self._render_menu_on_hdmi()
            
            # 顯示性能資訊（如果啟用）
            if self.config.config["debug"]["show_fps"]:
                self._render_debug_info()
            
            pygame.display.flip()

    def _can_process_input(self):
        """檢查是否可以處理輸入（避免過於頻繁）"""
        current_time = time.time()
        if current_time - self.last_input_time >= self.input_cooldown:
            return True
        return False

    def _process_menu_input(self):
        """處理選單輸入"""
        # 矩陣鍵盤輸入
        if self.keypad:
            key_pressed = self.keypad.get_key()
            if key_pressed is not None:
                self.last_input_time = time.time()
                
                try:
                    key_value = int(key_pressed)
                    if 1 <= key_value <= 9 and key_value <= len(self.games):
                        if self.buzzer: 
                            self.buzzer.play_tone("select")
                        self.current_selection = key_value - 1
                        self.state = GameState.INSTRUCTION
                        if self.traffic_light: 
                            self.traffic_light.yellow_on()
                except ValueError:
                    if key_pressed == 'D' and self.traffic_light:
                        self.traffic_light.all_off()

        # Xbox控制器輸入
        if self.controller:
            controller_input = self.controller.get_input()
            if controller_input:
                input_detected = False
                
                if controller_input["up_pressed"]:
                    self.current_selection = (self.current_selection - 1 + len(self.games)) % len(self.games)
                    input_detected = True
                elif controller_input["down_pressed"]:
                    self.current_selection = (self.current_selection + 1) % len(self.games)
                    input_detected = True
                elif controller_input["a_pressed"]:
                    if self.buzzer: 
                        self.buzzer.play_tone("select")
                    self.state = GameState.INSTRUCTION
                    if self.traffic_light: 
                        self.traffic_light.yellow_on()
                    input_detected = True
                
                if input_detected:
                    self.last_input_time = time.time()
                    if self.buzzer and controller_input["up_pressed"] or controller_input["down_pressed"]:
                        self.buzzer.play_tone("navigate")

    def _handle_instruction(self):
        """處理說明狀態"""
        selected_game_data = self.games[self.current_selection]
        if self.spi_screen and self.spi_screen.device:
            self.spi_screen.display_game_instructions(selected_game_data)
        
        if self._can_process_input():
            # 矩陣鍵盤輸入
            if self.keypad:
                key_pressed = self.keypad.get_key()
                if key_pressed == "A": 
                    self._start_game_sequence(selected_game_data)
                elif key_pressed == "D": 
                    self._return_to_menu()
            
            # Xbox控制器輸入
            if self.controller:
                controller_input = self.controller.get_input()
                if controller_input:
                    if controller_input["a_pressed"]:
                        self._start_game_sequence(selected_game_data)
                    elif controller_input["b_pressed"]:
                        self._return_to_menu()

        if self.hdmi_screen:
            self.hdmi_screen.fill((0, 0, 0))
            self._render_instructions_on_hdmi(selected_game_data)
            pygame.display.flip()

    def _start_game_sequence(self, game_data):
        """開始遊戲序列"""
        if self.buzzer: 
            self.buzzer.play_tone("game_start")
        self.state = GameState.GAME_STARTING
        self.game_start_time = time.time()
        self.selected_game_data = game_data

    def _return_to_menu(self):
        """返回選單"""
        if self.buzzer: 
            self.buzzer.play_tone("back")
        if self.traffic_light: 
            self.traffic_light.all_off()
        self.state = GameState.MENU

    def _handle_game_starting(self):
        """處理遊戲開始狀態（倒數動畫）"""
        elapsed = time.time() - self.game_start_time
        
        if elapsed < 1.5:
            # 顯示倒數動畫
            countdown = 3 - int(elapsed / 0.5)
            if countdown > 0:
                if self.traffic_light:
                    if countdown == 3:
                        self.traffic_light.red_on()
                    elif countdown == 2:
                        self.traffic_light.yellow_on()
                    elif countdown == 1:
                        self.traffic_light.green_on()
                
                if self.buzzer and int(elapsed * 2) != getattr(self, '_last_beep', -1):
                    self.buzzer.play_tone(frequency=300 + countdown * 200, duration=0.2)
                    self._last_beep = int(elapsed * 2)
        else:
            # 開始遊戲
            self._actually_start_game(self.selected_game_data)

    def _actually_start_game(self, game_data):
        """實際開始遊戲"""
        try:
            game_class = game_data["game_class"]
            self.current_game = game_class(
                width=self.config.config["display"]["hdmi_width"],
                height=self.config.config["display"]["hdmi_height"],
                buzzer=self.buzzer
            )
            self.state = GameState.GAME
            self.session_stats["games_played"] += 1
            
            if self.spi_screen and self.spi_screen.device:
                self.spi_screen.clear_screen()
            
            logging.info(f"遊戲 '{game_data['name']}' 已啟動")
            
        except Exception as e:
            logging.error(f"啟動遊戲 '{game_data['name']}' 失敗: {e}")
            self._show_error_message(f"遊戲啟動失敗: {str(e)}")
            self.state = GameState.MENU

    def _handle_game(self):
        """處理遊戲狀態"""
        if self.current_game is not None:
            controller_input = self.controller.get_input() if self.controller else {}
            game_status = self.current_game.update(controller_input)
            
            if game_status.get("game_over", False):
                self.state = GameState.GAME_OVER
                self.game_over_data = game_status
                
                # 更新統計數據
                score = game_status.get("score", 0)
                self.session_stats["total_score"] += score
                
                game_name = self.games[self.current_selection]["name"]
                if game_name not in self.session_stats["best_scores"]:
                    self.session_stats["best_scores"][game_name] = score
                else:
                    self.session_stats["best_scores"][game_name] = max(
                        self.session_stats["best_scores"][game_name], score
                    )
                
            elif self.hdmi_screen:
                self.current_game.render(self.hdmi_screen)
                pygame.display.flip()

    def _handle_game_paused(self):
        """處理遊戲暫停狀態"""
        # 顯示暫停畫面
        if self.hdmi_screen:
            self.hdmi_screen.fill((0, 0, 0))
            font = pygame.font.Font(None, 72)
            text = font.render("遊戲已暫停", True, (255, 255, 255))
            rect = text.get_rect(center=(self.hdmi_screen.get_width()//2, self.hdmi_screen.get_height()//2))
            self.hdmi_screen.blit(text, rect)
            
            hint_font = pygame.font.Font(None, 36)
            hint_text = hint_font.render("按電源按鈕繼續", True, (200, 200, 200))
            hint_rect = hint_text.get_rect(center=(self.hdmi_screen.get_width()//2, self.hdmi_screen.get_height()//2 + 100))
            self.hdmi_screen.blit(hint_text, hint_rect)
            
            pygame.display.flip()

    def _handle_game_over(self):
        """處理遊戲結束狀態"""
        if not hasattr(self, '_game_over_start_time'):
            self._game_over_start_time = time.time()
            
            if self.buzzer: 
                self.buzzer.play_tone("game_over")
            if self.traffic_light: 
                self.traffic_light.red_on()
            
            if self.spi_screen and self.spi_screen.device:
                self.spi_screen.display_game_over(
                    self.game_over_data.get("score", 0),
                    self.session_stats["best_scores"].get(self.games[self.current_selection]["name"])
                )
            
            logging.info(f"遊戲結束，分數: {self.game_over_data.get('score', 0)}")
        
        # 3秒後自動返回選單
        if time.time() - self._game_over_start_time > 3:
            self.end_current_game()
            self.state = GameState.MENU
            if self.traffic_light: 
                self.traffic_light.all_off()
            delattr(self, '_game_over_start_time')

    def _handle_error(self):
        """處理錯誤狀態"""
        if self.hdmi_screen:
            self.hdmi_screen.fill((50, 0, 0))  # 深紅色背景
            font = pygame.font.Font(None, 48)
            text = font.render("系統錯誤", True, (255, 255, 255))
            rect = text.get_rect(center=(self.hdmi_screen.get_width()//2, self.hdmi_screen.get_height()//2))
            self.hdmi_screen.blit(text, rect)
            pygame.display.flip()
        
        time.sleep(0.1)  # 避免錯誤狀態下的快速循環

    def _handle_pygame_events(self):
        """處理Pygame事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.GAME:
                        self._handle_return_to_menu()
                    else:
                        self.running = False
                elif event.key == pygame.K_F1:
                    # 切換除錯資訊顯示
                    self.config.config["debug"]["show_fps"] = not self.config.config["debug"]["show_fps"]

    def _render_debug_info(self):
        """渲染除錯資訊"""
        if not self.hdmi_screen:
            return
        
        font = pygame.font.Font(None, 24)
        y_offset = 10
        
        # FPS
        avg_fps = self.performance_monitor.get_average_fps()
        fps_text = font.render(f"FPS: {avg_fps:.1f}", True, (255, 255, 255))
        self.hdmi_screen.blit(fps_text, (10, y_offset))
        y_offset += 25
        
        # 系統資源
        cpu_text = font.render(f"CPU: {self.performance_monitor.cpu_usage:.1f}%", True, (255, 255, 255))
        self.hdmi_screen.blit(cpu_text, (10, y_offset))
        y_offset += 25
        
        memory_text = font.render(f"Memory: {self.performance_monitor.memory_usage:.1f}%", True, (255, 255, 255))
        self.hdmi_screen.blit(memory_text, (10, y_offset))
        y_offset += 25
        
        if self.performance_monitor.temperature > 0:
            temp_text = font.render(f"Temp: {self.performance_monitor.temperature:.1f}°C", True, (255, 255, 255))
            self.hdmi_screen.blit(temp_text, (10, y_offset))

    def _show_error_message(self, message):
        """顯示錯誤訊息"""
        logging.error(message)
        if self.spi_screen and self.spi_screen.device:
            self.spi_screen.display_custom_message("錯誤", message, duration=3)

    def _render_menu_on_hdmi(self):
        """在HDMI螢幕上渲染選單"""
        # ...existing menu rendering code...
        if not self.hdmi_screen: 
            return
        
        font_title = pygame.font.Font(None, 72)
        font_item = pygame.font.Font(None, 48)
        font_info = pygame.font.Font(None, 24)
        
        # 標題
        title_surface = font_title.render(f"多功能遊戲機 v{VERSION}", True, (255, 255, 255))
        self.hdmi_screen.blit(title_surface, (HDMI_SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 50))
        
        # 遊戲列表
        for i, game in enumerate(self.games):
            color = (255, 255, 0) if i == self.current_selection else (200, 200, 200)
            y_pos = 150 + i * 45
            
            # 遊戲名稱
            item_surface = font_item.render(f"{game['id']}. {game['name']}", True, color)
            self.hdmi_screen.blit(item_surface, (50, y_pos))
            
            # 難度指示
            difficulty_color = {
                "Easy": (0, 255, 0),
                "Medium": (255, 255, 0),
                "Hard": (255, 0, 0)
            }.get(game.get("difficulty", "Medium"), (255, 255, 255))
            
            diff_surface = font_info.render(f"[{game.get('difficulty', 'Medium')}]", True, difficulty_color)
            self.hdmi_screen.blit(diff_surface, (600, y_pos + 10))
        
        # 統計資訊
        stats_y = HDMI_SCREEN_HEIGHT - 100
        stats_text = f"本次遊玩: {self.session_stats['games_played']} 場 | 總分: {self.session_stats['total_score']}"
        stats_surface = font_info.render(stats_text, True, (150, 150, 150))
        self.hdmi_screen.blit(stats_surface, (50, stats_y))

    def _render_instructions_on_hdmi(self, game_data):
        """在HDMI螢幕上渲染遊戲說明"""
        # ...existing instruction rendering code...
        if not self.hdmi_screen: 
            return
        
        font_title = pygame.font.Font(None, 72)
        font_text = pygame.font.Font(None, 36)
        font_hint = pygame.font.Font(None, 48)

        title_surface = font_title.render(game_data["name"], True, (255, 255, 255))
        self.hdmi_screen.blit(title_surface, (HDMI_SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 100))
        
        # 難度顯示
        difficulty = game_data.get("difficulty", "Medium")
        diff_color = {
            "Easy": (0, 255, 0),
            "Medium": (255, 255, 0),
            "Hard": (255, 0, 0)
        }.get(difficulty, (255, 255, 255))
        
        diff_surface = font_text.render(f"難度: {difficulty}", True, diff_color)
        self.hdmi_screen.blit(diff_surface, (HDMI_SCREEN_WIDTH // 2 - diff_surface.get_width() // 2, 160))
        
        # 遊戲說明
        desc_lines = game_data["description"].split('。')
        y_offset = 0
        for line in desc_lines:
            if line.strip():
                desc_surface = font_text.render(line.strip() + "。", True, (200, 200, 200))
                self.hdmi_screen.blit(desc_surface, (HDMI_SCREEN_WIDTH // 2 - desc_surface.get_width() // 2, 220 + y_offset))
                y_offset += 40

        hint_surface = font_hint.render("按 A/確認 開始遊戲 或 B/返回 返回選單", True, (150, 150, 150))
        self.hdmi_screen.blit(hint_surface, (HDMI_SCREEN_WIDTH // 2 - hint_surface.get_width() // 2, HDMI_SCREEN_HEIGHT - 100))

    def end_current_game(self):
        """結束當前遊戲"""
        if self.current_game:
            if hasattr(self.current_game, 'cleanup'):
                self.current_game.cleanup()
            self.current_game = None
            logging.info("當前遊戲已結束並清理")

    def _cleanup_on_error(self):
        """錯誤時的清理"""
        logging.info("執行錯誤清理...")
        
        if self.spi_screen: 
            self.spi_screen.cleanup()
        if self.keypad: 
            self.keypad.cleanup()
        if self.controller: 
            self.controller.cleanup()
        if self.buzzer: 
            self.buzzer.cleanup()
        if self.traffic_light: 
            self.traffic_light.cleanup()
        if self.power_button:
            self.power_button.cleanup()
        if pygame.get_init(): 
            pygame.quit()

    def cleanup(self):
        """清理資源 - 增強版"""
        logging.info("開始系統清理...")
        
        # 停止系統監控
        if self.monitor_running:
            self.monitor_running = False
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2)
        
        # 結束當前遊戲
        if self.current_game:
            self.end_current_game()
        
        # 儲存配置和統計數據
        try:
            self.config.save_config()
            self._save_session_stats()
        except Exception as e:
            logging.error(f"儲存數據失敗: {e}")
        
        # 清理硬體組件
        hardware_components = [
            (self.spi_screen, "SPI螢幕"),
            (self.keypad, "矩陣鍵盤"),
            (self.controller, "Xbox控制器"),
            (self.buzzer, "蜂鳴器"),
            (self.traffic_light, "交通燈"),
            (self.power_button, "電源按鈕")
        ]
        
        for component, name in hardware_components:
            if component:
                try:
                    component.cleanup()
                    logging.info(f"{name} 清理完成")
                except Exception as e:
                    logging.error(f"{name} 清理失敗: {e}")
        
        # 清理Pygame
        if pygame.get_init():
            pygame.quit()
            logging.info("Pygame 已關閉")
        
        logging.info("遊戲機系統清理完成")

    def _save_session_stats(self):
        """儲存會話統計數據"""
        try:
            stats_file = os.path.join(os.path.dirname(__file__), 'session_stats.json')
            
            # 載入現有統計數據
            all_stats = {}
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    all_stats = json.load(f)
            
            # 新增本次會話數據
            session_id = self.session_stats["start_time"].strftime("%Y%m%d_%H%M%S")
            all_stats[session_id] = {
                "start_time": self.session_stats["start_time"].isoformat(),
                "end_time": datetime.now().isoformat(),
                "games_played": self.session_stats["games_played"],
                "total_score": self.session_stats["total_score"],
                "best_scores": self.session_stats["best_scores"]
            }
            
            # 只保留最近30次會話
            if len(all_stats) > 30:
                sorted_sessions = sorted(all_stats.keys())
                for old_session in sorted_sessions[:-30]:
                    del all_stats[old_session]
            
            # 儲存統計數據
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(all_stats, f, indent=2, ensure_ascii=False)
                
            logging.info(f"會話統計已儲存: {session_id}")
            
        except Exception as e:
            logging.error(f"儲存統計數據失敗: {e}")

# 主程式入口
if __name__ == "__main__":
    power_button_process = None
    game_console_instance = None
    
    try:
        # 啟動電源按鈕監控
        main_pid = str(os.getpid())
        power_button_script_path = os.path.join(os.path.dirname(__file__), "power_button.py")
        
        if os.path.exists(power_button_script_path):
            logging.info(f"嘗試啟動 power_button.py (PID: {main_pid})...")
            power_button_process = subprocess.Popen(
                ['sudo', 'python3', power_button_script_path, main_pid],
                preexec_fn=os.setpgrp
            )
            logging.info(f"power_button.py 已在背景啟動 (子程序 PID: {power_button_process.pid})")
        else:
            logging.warning(f"警告: power_button.py 未找到: {power_button_script_path}")

        # 啟動遊戲機
        game_console_instance = EnhancedGameConsole()
        game_console_instance.run()

    except KeyboardInterrupt:
        logging.info("主程式被使用者中斷 (Ctrl+C)")
    except Exception as e:
        logging.error(f"主程式發生未預期錯誤: {e}")
        logging.error(traceback.format_exc())
    finally:
        logging.info("主程式 finally 區塊開始執行清理...")
        
        if game_console_instance:
            game_console_instance.cleanup()
        
        # 終止電源按鈕程序
        if power_button_process:
            try:
                os.killpg(os.getpgid(power_button_process.pid), signal.SIGTERM)
                power_button_process.wait(timeout=2)
                logging.info("power_button.py 子程序已終止")
            except (ProcessLookupError, subprocess.TimeoutExpired) as e:
                logging.warning(f"終止 power_button.py 時發生問題: {e}")
            except Exception as e:
                logging.error(f"終止 power_button.py 時發生錯誤: {e}")
        
        # 最終GPIO清理
        if GPIO.getmode() is not None:
            logging.info("執行最終的 GPIO.cleanup()...")
            GPIO.cleanup()
        
        logging.info("主程式已結束")
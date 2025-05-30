#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# screen_menu.py - 2.8寸TFT SPI螢幕控制邏輯 (240x320)

import time
import os
import RPi.GPIO as GPIO
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import ili9341  # 2.8寸TFT通常使用ILI9341控制器
from PIL import Image, ImageDraw, ImageFont

# 2.8寸TFT SPI螢幕設定 (240x320)
SPI_PORT = 0      # SPI0
SPI_DEVICE = 0    # CE0
SPI_DC = 25       # Data/Command腳位
SPI_RST = 24      # Reset腳位
SPI_CS = 8        # Chip Select腳位
SPI_LED = 27      # 背光控制腳位

# 螢幕規格
DISPLAY_WIDTH = 240   # TFT螢幕寬度
DISPLAY_HEIGHT = 320  # TFT螢幕高度
DEFAULT_FONT_SIZE = 18  # 適合240x320解析度的字體大小

class SPIScreenManager:
    """2.8寸TFT SPI螢幕管理類 (240x320)"""
    
    def __init__(self, display_width=DISPLAY_WIDTH, display_height=DISPLAY_HEIGHT):
        self.width = display_width
        self.height = display_height
        
        # GPIO腳位設定
        self.SPI_DC = SPI_DC
        self.SPI_RST = SPI_RST
        self.SPI_CS_PIN = SPI_CS 
        self.SPI_LED = SPI_LED
        
        # 顏色定義
        self.BLACK = "black"
        self.WHITE = "white"
        self.RED = "red"
        self.GREEN = "green"
        self.BLUE = "blue"
        self.YELLOW = "yellow"
        self.CYAN = "cyan"
        self.MAGENTA = "magenta"
        
        # 初始化螢幕和字體
        self.device = self._initialize_device()
        self.font_small = None
        self.font_medium = None
        self.font_large = None
        self._load_fonts()
    
    def _initialize_device(self):
        """初始化2.8寸TFT SPI螢幕"""
        try:
            # 設定背光控制腳位
            GPIO.setup(self.SPI_LED, GPIO.OUT)
            GPIO.output(self.SPI_LED, GPIO.HIGH)  # 開啟背光
            
            # 建立SPI連接
            serial = spi(
                port=SPI_PORT, 
                device=SPI_DEVICE, 
                gpio_DC=self.SPI_DC, 
                gpio_RST=self.SPI_RST
            )
            
            # 初始化ILI9341控制器的TFT螢幕
            device = ili9341(
                serial, 
                width=self.width, 
                height=self.height, 
                rotate=0  # 0:正常, 1:90度, 2:180度, 3:270度
            )
            
            print(f"✓ 2.8寸TFT SPI螢幕初始化成功 ({self.width}x{self.height})")
            print(f"  使用ILI9341控制器，背光腳位: GPIO {self.SPI_LED}")
            
            # 顯示初始化畫面
            self._show_init_screen(device)
            
            return device
            
        except ImportError as e:
            print(f"✗ 套件導入失敗: {e}")
            print("請安裝必要套件: sudo pip3 install luma.lcd luma.core")
            return None
        except Exception as e:
            print(f"✗ 2.8寸TFT SPI螢幕初始化失敗: {e}")
            print("請檢查:")
            print(f"  1. SPI接線是否正確 (DC:{self.SPI_DC}, RST:{self.SPI_RST}, LED:{self.SPI_LED})")
            print("  2. SPI是否已啟用 (sudo raspi-config)")
            print("  3. 螢幕是否為ILI9341控制器")
            
            # 初始化失敗時關閉背光
            try:
                GPIO.output(self.SPI_LED, GPIO.LOW)
            except:
                pass
            return None
    
    def _show_init_screen(self, device):
        """顯示初始化畫面"""
        try:
            with canvas(device) as draw:
                # 黑色背景
                draw.rectangle(device.bounding_box, outline=self.BLACK, fill=self.BLACK)
                
                # 顯示初始化訊息
                init_text = "TFT 螢幕初始化"
                spec_text = f"{self.width}x{self.height}"
                
                # 使用預設字體
                font = ImageFont.load_default()
                
                # 計算文字位置
                try:
                    text_bbox = draw.textbbox((0, 0), init_text, font=font)
                    text_w = text_bbox[2] - text_bbox[0]
                    text_h = text_bbox[3] - text_bbox[1]
                except AttributeError:
                    text_w, text_h = draw.textsize(init_text, font=font)
                
                # 繪製文字
                draw.text(
                    ((self.width - text_w) // 2, self.height // 2 - text_h), 
                    init_text, 
                    fill=self.WHITE, 
                    font=font
                )
                
                try:
                    spec_bbox = draw.textbbox((0, 0), spec_text, font=font)
                    spec_w = spec_bbox[2] - spec_bbox[0]
                except AttributeError:
                    spec_w, _ = draw.textsize(spec_text, font=font)
                
                draw.text(
                    ((self.width - spec_w) // 2, self.height // 2 + 5), 
                    spec_text, 
                    fill=self.GREEN, 
                    font=font
                )
            
            time.sleep(1)  # 顯示1秒
            
        except Exception as e:
            print(f"初始化畫面顯示失敗: {e}")
    
    def _load_fonts(self):
        """載入中文字體，優先載入系統中文字體"""
        try:
            # 中文字體路徑列表（按優先順序）
            chinese_font_paths = [
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/truetype/arphic/ukai.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            ]
            
            # 嘗試載入字體
            font_loaded = False
            for font_path in chinese_font_paths:
                if os.path.exists(font_path):
                    try:
                        self.font_small = ImageFont.truetype(font_path, 14)
                        self.font_medium = ImageFont.truetype(font_path, 18)
                        self.font_large = ImageFont.truetype(font_path, 24)
                        print(f"✓ 成功載入中文字體: {font_path}")
                        font_loaded = True
                        break
                    except Exception as e:
                        print(f"載入字體 {font_path} 失敗: {e}")
                        continue
            
            if not font_loaded:
                print("⚠️ 無法載入任何中文字體，使用預設字體")
                self.font_small = ImageFont.load_default()
                self.font_medium = ImageFont.load_default()
                self.font_large = ImageFont.load_default()
                
        except Exception as e:
            print(f"字體載入過程發生錯誤: {e}")
            # 使用預設字體作為備援
            self.font_small = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_large = ImageFont.load_default()
    
    def clear_screen(self, color=None):
        """清除螢幕"""
        if not self.device:
            return
        
        if color is None:
            color = self.BLACK
            
        try:
            with canvas(self.device) as draw:
                draw.rectangle(self.device.bounding_box, outline=color, fill=color)
        except Exception as e:
            print(f"清除螢幕失敗: {e}")
    
    def display_menu(self, games, selected_index):
        """顯示遊戲選單，針對240x320解析度優化"""
        if not self.device or not self.font_medium:
            print("TFT螢幕或字體未初始化，無法顯示選單")
            return
        
        try:
            with canvas(self.device) as draw:
                # 黑色背景
                draw.rectangle(self.device.bounding_box, outline=self.BLACK, fill=self.BLACK)
                
                # 標題
                title_text = "🎮 遊戲選單"
                self._draw_centered_text(draw, title_text, 10, self.font_large, self.CYAN)
                
                # 分隔線
                draw.line([(10, 45), (self.width - 10, 45)], fill=self.WHITE, width=2)
                
                # 計算可顯示的遊戲項目數量
                item_height = 30  # 每個項目的高度
                available_height = self.height - 60 - 40  # 扣除標題和底部空間
                visible_count = available_height // item_height
                
                # 計算滾動偏移
                start_idx = 0
                if len(games) > visible_count:
                    start_idx = max(0, selected_index - (visible_count // 2))
                    start_idx = min(start_idx, len(games) - visible_count)
                
                # 繪製遊戲項目
                for i in range(visible_count):
                    actual_idx = start_idx + i
                    if actual_idx >= len(games):
                        break
                    
                    y_pos = 55 + i * item_height
                    
                    # 選中項目的背景
                    if actual_idx == selected_index:
                        draw.rectangle(
                            [(5, y_pos - 2), (self.width - 5, y_pos + item_height - 8)],
                            outline=self.BLUE,
                            fill=self.BLUE
                        )
                        text_color = self.WHITE
                        prefix = "▶ "
                    else:
                        text_color = self.WHITE
                        prefix = "  "
                    
                    # 遊戲文字
                    game_text = f"{prefix}{games[actual_idx]['id']}. {games[actual_idx]['name']}"
                    
                    # 確保文字不會超出螢幕
                    max_chars = 28  # 240寬度大約可容納28個字符
                    if len(game_text) > max_chars:
                        game_text = game_text[:max_chars-3] + "..."
                    
                    draw.text((10, y_pos), game_text, fill=text_color, font=self.font_medium)
                
                # 滾動指示器
                if len(games) > visible_count:
                    # 繪製滾動條
                    scrollbar_height = available_height
                    scrollbar_pos = (start_idx / (len(games) - visible_count)) * scrollbar_height
                    
                    draw.rectangle(
                        [(self.width - 8, 55), (self.width - 5, 55 + scrollbar_height)],
                        outline=self.WHITE,
                        fill=self.BLACK
                    )
                    
                    draw.rectangle(
                        [(self.width - 8, 55 + int(scrollbar_pos)), 
                         (self.width - 5, 55 + int(scrollbar_pos) + 20)],
                        fill=self.YELLOW
                    )
                
                # 底部提示
                hint_text = "🎯 A:選擇 B:退出"
                self._draw_centered_text(
                    draw, hint_text, 
                    self.height - 25, 
                    self.font_small, 
                    self.GREEN
                )
                
        except Exception as e:
            print(f"顯示選單失敗: {e}")
    
    def display_game_instructions(self, game):
        """顯示遊戲說明，針對240x320解析度優化"""
        if not self.device or not self.font_medium:
            print("TFT螢幕或字體未初始化，無法顯示遊戲說明")
            return
        
        try:
            with canvas(self.device) as draw:
                # 黑色背景
                draw.rectangle(self.device.bounding_box, outline=self.BLACK, fill=self.BLACK)
                
                # 遊戲名稱
                game_name = game['name']
                self._draw_centered_text(draw, game_name, 10, self.font_large, self.YELLOW)
                
                # 分隔線
                draw.line([(10, 45), (self.width - 10, 45)], fill=self.WHITE, width=2)
                
                # 說明標題
                draw.text((10, 55), "📋 操作說明:", fill=self.CYAN, font=self.font_medium)
                
                # 遊戲說明內容
                description = game.get('description', '暫無說明')
                wrapped_lines = self._wrap_text(description, self.width - 20, self.font_medium)
                
                y_pos = 85
                for line in wrapped_lines:
                    if y_pos > self.height - 80:  # 防止文字超出螢幕
                        break
                    draw.text((10, y_pos), line, fill=self.WHITE, font=self.font_medium)
                    y_pos += 25
                
                # 控制說明
                control_y = self.height - 70
                draw.text((10, control_y), "🎮 控制說明:", fill=self.CYAN, font=self.font_medium)
                
                controls = [
                    "搖桿：移動/選擇",
                    "A鈕：確認/行動", 
                    "B鈕：取消/暫停"
                ]
                
                for i, control in enumerate(controls):
                    draw.text((10, control_y + 25 + i * 20), f"• {control}", 
                             fill=self.GREEN, font=self.font_small)
                
                # 底部提示
                self._draw_centered_text(
                    draw, "A:開始遊戲 B:返回選單", 
                    self.height - 15, 
                    self.font_small, 
                    self.WHITE
                )
                
        except Exception as e:
            print(f"顯示遊戲說明失敗: {e}")
    
    def display_game_over(self, score, high_score=None):
        """顯示遊戲結束畫面"""
        if not self.device:
            return
        
        try:
            with canvas(self.device) as draw:
                # 黑色背景
                draw.rectangle(self.device.bounding_box, outline=self.BLACK, fill=self.BLACK)
                
                # 遊戲結束標題
                title_text = "🎯 遊戲結束"
                self._draw_centered_text(draw, title_text, 50, self.font_large, self.RED)
                
                # 分數顯示
                score_text = f"本次分數: {score}"
                self._draw_centered_text(draw, score_text, 120, self.font_large, self.YELLOW)
                
                # 最高分數（如果有）
                if high_score is not None:
                    if score > high_score:
                        record_text = "🏆 新紀錄！"
                        record_color = self.GREEN
                    else:
                        record_text = f"最高分數: {high_score}"
                        record_color = self.CYAN
                    
                    self._draw_centered_text(draw, record_text, 160, self.font_medium, record_color)
                
                # 評價
                if score >= 1000:
                    comment = "🌟 驚人表現！"
                    comment_color = self.GREEN
                elif score >= 500:
                    comment = "⭐ 表現不錯！"
                    comment_color = self.YELLOW
                elif score >= 100:
                    comment = "👍 繼續加油！"
                    comment_color = self.CYAN
                else:
                    comment = "💪 再接再厲！"
                    comment_color = self.WHITE
                
                self._draw_centered_text(draw, comment, 200, self.font_medium, comment_color)
                
                # 底部提示
                hint_text = "按任意鍵返回選單"
                self._draw_centered_text(draw, hint_text, self.height - 30, self.font_small, self.WHITE)
                
        except Exception as e:
            print(f"顯示遊戲結束畫面失敗: {e}")
    
    def display_custom_message(self, title, message, duration=0, title_color=None, message_color=None):
        """顯示自定義訊息"""
        if not self.device:
            return
        
        if title_color is None:
            title_color = self.CYAN
        if message_color is None:
            message_color = self.WHITE
        
        try:
            with canvas(self.device) as draw:
                # 黑色背景
                draw.rectangle(self.device.bounding_box, outline=self.BLACK, fill=self.BLACK)
                
                # 標題
                self._draw_centered_text(draw, title, 50, self.font_large, title_color)
                
                # 分隔線
                draw.line([(20, 90), (self.width - 20, 90)], fill=self.WHITE, width=2)
                
                # 訊息內容
                wrapped_lines = self._wrap_text(message, self.width - 20, self.font_medium)
                
                start_y = 110
                total_height = len(wrapped_lines) * 25
                current_y = start_y + (self.height - start_y - total_height) // 2
                
                for line in wrapped_lines:
                    self._draw_centered_text(draw, line, current_y, self.font_medium, message_color)
                    current_y += 25
            
            if duration > 0:
                time.sleep(duration)
                self.clear_screen()
                
        except Exception as e:
            print(f"顯示自定義訊息失敗: {e}")
    
    def display_loading(self, message="載入中...", progress=None):
        """顯示載入畫面"""
        if not self.device:
            return
        
        try:
            with canvas(self.device) as draw:
                # 黑色背景
                draw.rectangle(self.device.bounding_box, outline=self.BLACK, fill=self.BLACK)
                
                # 載入訊息
                self._draw_centered_text(draw, message, 100, self.font_large, self.CYAN)
                
                # 進度條（如果有進度值）
                if progress is not None:
                    bar_width = self.width - 40
                    bar_height = 20
                    bar_x = 20
                    bar_y = 150
                    
                    # 進度條框架
                    draw.rectangle(
                        [(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)],
                        outline=self.WHITE,
                        fill=self.BLACK
                    )
                    
                    # 進度填充
                    if progress > 0:
                        fill_width = int(bar_width * progress / 100)
                        draw.rectangle(
                            [(bar_x + 2, bar_y + 2), (bar_x + fill_width - 2, bar_y + bar_height - 2)],
                            fill=self.GREEN
                        )
                    
                    # 進度百分比
                    percent_text = f"{progress}%"
                    self._draw_centered_text(draw, percent_text, bar_y + 30, self.font_medium, self.WHITE)
                else:
                    # 簡單的載入動畫點
                    dots = "." * ((int(time.time() * 2) % 4))
                    dots_text = f"載入中{dots}"
                    self._draw_centered_text(draw, dots_text, 150, self.font_medium, self.WHITE)
                
        except Exception as e:
            print(f"顯示載入畫面失敗: {e}")
    
    def _draw_centered_text(self, draw, text, y, font, color):
        """繪製置中文字"""
        try:
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
        except AttributeError:
            text_width, _ = draw.textsize(text, font=font)
        
        x = (self.width - text_width) // 2
        draw.text((x, y), text, fill=color, font=font)
    
    def _wrap_text(self, text, max_width, font):
        """自動換行文字"""
        if not text:
            return []
        
        lines = []
        words = text.split(' ')
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            
            try:
                bbox = font.getbbox(test_line)
                line_width = bbox[2] - bbox[0]
            except AttributeError:
                try:
                    line_width, _ = font.getsize(test_line)
                except:
                    lines.append(test_line)
                    current_line = ""
                    continue
            
            if line_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def set_brightness(self, brightness):
        """設定螢幕亮度 (0-100)"""
        try:
            if 0 <= brightness <= 100:
                # 使用PWM控制背光亮度
                pwm = GPIO.PWM(self.SPI_LED, 1000)  # 1kHz頻率
                pwm.start(brightness)
                print(f"螢幕亮度設定為: {brightness}%")
            else:
                print("亮度值必須在0-100之間")
        except Exception as e:
            print(f"設定亮度失敗: {e}")
    
    def get_status(self):
        """獲取螢幕狀態"""
        return {
            'width': self.width,
            'height': self.height,
            'device_ready': self.device is not None,
            'font_loaded': self.font_medium is not None,
            'backlight_pin': self.SPI_LED
        }
    
    def cleanup(self):
        """清理資源"""
        try:
            if self.device:
                self.clear_screen()
                print("✓ TFT螢幕已清理")
            
            # 關閉背光
            if hasattr(self, 'SPI_LED') and self.SPI_LED is not None:
                GPIO.output(self.SPI_LED, GPIO.LOW)
                print("✓ 背光已關閉")
                
        except Exception as e:
            print(f"⚠️ 清理TFT螢幕時發生警告: {e}")


# 測試程式
def run_screen_test():
    """執行螢幕測試"""
    print("🖥️ 2.8寸TFT SPI螢幕測試程式")
    print("=" * 50)
    
    try:
        # 設定GPIO模式
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # 初始化螢幕
        screen = SPIScreenManager()
        
        if not screen.device:
            print("❌ 螢幕初始化失敗，測試終止")
            return
        
        # 測試資料
        games_data = [
            {"id": 1, "name": "貪吃蛇", "description": "使用搖桿控制蛇的移動方向，吃到食物會變長。按A鈕可以加速移動。"},
            {"id": 2, "name": "打磚塊", "description": "使用搖桿左右移動擋板，按A鈕發射球。打破所有磚塊即可過關。"},
            {"id": 3, "name": "太空侵略者", "description": "使用搖桿左右移動太空船，按A鈕發射子彈消滅入侵的外星人。"},
            {"id": 4, "name": "井字遊戲", "description": "經典的圈圈叉叉遊戲。使用搖桿選擇格子，按A鈕確認下棋。"},
            {"id": 5, "name": "記憶翻牌", "description": "翻開相同的牌配對。使用搖桿選擇牌，按A鈕翻牌。"},
            {"id": 6, "name": "簡易迷宮", "description": "使用搖桿控制角色在迷宮中移動，找到出口即可過關。"},
            {"id": 7, "name": "打地鼠", "description": "地鼠會隨機出現，使用搖桿移動槌子，按A鈕敲擊地鼠得分。"},
            {"id": 8, "name": "俄羅斯方塊", "description": "經典方塊遊戲。搖桿左右移動，上改變方向，下加速。按A鈕快速落下。"},
            {"id": 9, "name": "反應力測試", "description": "當螢幕出現信號時，盡快按A鈕。測試你的反應速度。"}
        ]
        
        print("✅ 螢幕初始化成功，開始測試...")
        
        # 測試1: 顯示載入畫面       
        print("📱 測試1: 載入畫面")
        screen.display_loading("系統啟動中...")
        time.sleep(2)
        
        # 測試2: 進度條載入
        print("📱 測試2: 進度載入")
        for progress in range(0, 101, 20):
            screen.display_loading("載入遊戲資源...", progress)
            time.sleep(0.5)
        
        # 測試3: 選單顯示
        print("📱 測試3: 遊戲選單")
        for i in range(len(games_data)):
            screen.display_menu(games_data, i)
            time.sleep(0.8)
        
        # 測試4: 遊戲說明
        print("📱 測試4: 遊戲說明")
        screen.display_game_instructions(games_data[0])
        time.sleep(3)
        
        # 測試5: 遊戲結束畫面
        print("📱 測試5: 遊戲結束")
        screen.display_game_over(1250, 1000)
        time.sleep(3)
        
        # 測試6: 自定義訊息
        print("📱 測試6: 系統訊息")
        screen.display_custom_message(
            "系統通知", 
            "遊戲機啟動完成！所有硬體模組運作正常。", 
            duration=3
        )
        
        # 測試7: 亮度測試
        print("📱 測試7: 亮度調整")
        for brightness in [100, 50, 20, 100]:
            screen.set_brightness(brightness)
            screen.display_custom_message("亮度測試", f"當前亮度: {brightness}%", duration=1)
        
        # 顯示測試完成
        screen.display_custom_message(
            "測試完成", 
            "所有顯示功能測試通過！螢幕工作正常。",
            duration=3
        )
        
        print("✅ 所有測試完成")
        
        # 顯示狀態資訊
        status = screen.get_status()
        print(f"📊 螢幕狀態: {status}")
        
    except KeyboardInterrupt:
        print("\n⚠️ 測試被使用者中斷")
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
    finally:
        if 'screen' in locals():
            screen.cleanup()
        print("🧹 測試程式結束")


if __name__ == "__main__":
    run_screen_test()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# screen_menu.py - SPI 螢幕控制邏輯

import time
import RPi.GPIO as GPIO
from luma.core.interface.serial import spi
from luma.core.render import canvas
# 根據您的螢幕型號 MSP2897，它可能使用 ILI9341 控制器
# 因此，我們嘗試使用 luma.lcd.device 中的 ili9341 驅動
# 如果不是 ILI9341，您需要查找 MSP2897 對應的 Luma 驅動或相容驅動
from luma.lcd.device import ili9341 # 嘗試使用 ILI9341 驅動
# from luma.oled.device import ssd1306, ssd1325, ssd1331, sh1106 # 保留OLED選項以供參考
from PIL import Image, ImageDraw, ImageFont

# 定義 SPI 連接的 GPIO 引腳 (根據 README.md 更新)
SPI_PORT = 0      # SPI0 (通常對應 MOSI: GPIO10, SCLK: GPIO11)
SPI_DEVICE = 0    # SPI Chip Select (CE0 通常對應 CS: GPIO8)

# 以下為需要明確指定的控制腳位 (BCM 編號)
SPI_DC = 25       # Data/Command - 更新後的腳位
SPI_RST = 24      # Reset - 更新後的腳位
SPI_CS = 8        # Chip Select - (Luma 的 spi() 會處理，但這裡保留以明確)

SPI_LED = 27      # 新增的 LED 背光控制腳位

# 預設設定
DEFAULT_FONT_SIZE = 16 # 對於較大螢幕，可以稍微增大字體
# 2.8吋 MSP2897 SPI LCD Module 通常解析度為 240x320 或 320x240
# 這裡假設為 240x320，如果方向不對，可以交換或使用 rotate 參數
DISPLAY_WIDTH = 240   # TFT 顯示寬度 (請根據您的螢幕規格確認)
DISPLAY_HEIGHT = 320  # TFT 顯示高度 (請根據您的螢幕規格確認)


class SPIScreenManager:
    """SPI 介面的小螢幕管理類"""
    
    def __init__(self, display_width=DISPLAY_WIDTH, display_height=DISPLAY_HEIGHT):
        self.width = display_width
        self.height = display_height
        
        # 將常數設為實例屬性，方便內部使用
        self.SPI_DC = SPI_DC
        self.SPI_RST = SPI_RST
        self.SPI_CS_PIN = SPI_CS 
        self.SPI_LED = SPI_LED

        self.device = self._initialize_device()
        self.font = self._load_font()
    
    def _initialize_device(self):
        """初始化 SPI 螢幕"""
        try:
            # 設定 LED 背光腳位
            # GPIO.setmode(GPIO.BCM) # 主程式 main.py 應已設定模式
            GPIO.setup(self.SPI_LED, GPIO.OUT)
            GPIO.output(self.SPI_LED, GPIO.HIGH) # 開啟背光

            serial = spi(port=SPI_PORT, device=SPI_DEVICE, gpio_DC=self.SPI_DC, gpio_RST=self.SPI_RST)
            
            # 初始化 TFT 設備
            # **重要：您需要根據您的 TFT 螢幕控制器選擇正確的 Luma device**
            # 嘗試使用 ili9341，如果您的螢幕是其他控制器，需要更改此處
            # rotate 參數可以調整螢幕方向 (0, 1, 2, 3 對應 0, 90, 180, 270 度旋轉)
            device = ili9341(serial, width=self.width, height=self.height, rotate=0) 
            
            print("SPI TFT 螢幕成功初始化 (嘗試使用 ili9341 驅動)")
            return device
            
        except Exception as e:
            print(f"SPI TFT 螢幕初始化失敗: {e}")
            print("請檢查：")
            print("1. Luma.lcd 是否已安裝 (sudo pip3 install luma.lcd)")
            print("2. 螢幕控制器是否為 ILI9341 或相容型號")
            print("3. 接線是否正確，特別是 DC, RST, CS, LED 腳位")
            print(f"4. DISPLAY_WIDTH ({self.width}) 和 DISPLAY_HEIGHT ({self.height}) 是否正確")
            if hasattr(self, 'SPI_LED') and self.SPI_LED is not None: # 確保屬性存在
                 GPIO.output(self.SPI_LED, GPIO.LOW) # 初始化失敗時關閉背光
            return None
    
    def _load_font(self, font_path=None, font_size=DEFAULT_FONT_SIZE):
        """載入字體，可指定字體檔案路徑或使用系統預設"""
        try:
            if font_path:
                font = ImageFont.truetype(font_path, font_size)
            else:
                # 嘗試載入一個常見的 TTF 字體 (如果系統中有)
                # 您可能需要安裝字體，例如：sudo apt-get install fonts-wqy-zenhei
                try:
                    font = ImageFont.truetype("DejaVuSans.ttf", font_size)
                except IOError:
                    print("警告: DejaVuSans.ttf 未找到，使用 PIL 預設點陣字體。")
                    font = ImageFont.load_default() # 可能較小且不支援中文
            return font
        except Exception as e:
            print(f"字體載入失敗: {e}")
            try:
                print("嘗試載入 PIL 預設點陣字體...")
                return ImageFont.load_default()
            except:
                print("錯誤: 連 PIL 預設點陣字體都無法載入。")
                return None 
    
    def clear_screen(self):
        """清除螢幕上的所有內容"""
        if self.device:
            with canvas(self.device) as draw:
                draw.rectangle(self.device.bounding_box, outline="black", fill="black")
    
    def display_menu(self, games, selected_index):
        """
        顯示遊戲選單
        """
        if not self.device or not self.font:
            print("SPI 螢幕或字體未初始化，無法顯示選單")
            return
        
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="black", fill="black") 
            title_text = "選擇遊戲:"
            try:
                # Pillow 9.1.0 之後 textsize 被移除，改用 textbbox
                bbox = draw.textbbox((0,0), title_text, font=self.font)
                title_w = bbox[2] - bbox[0]
                title_h = bbox[3] - bbox[1]
            except AttributeError: # 相容舊版 Pillow
                title_w, title_h = draw.textsize(title_text, font=self.font)

            draw.text(( (self.width - title_w) // 2 , 5), title_text, fill="white", font=self.font) # 稍微向下移動標題
            
            item_h_actual = title_h # 假設行高與標題同高
            item_height = item_h_actual + 4 # 加一點間距

            header_height = title_h + 10 # 標題區域高度
            visible_area_height = self.height - header_height - 5 # 底部也留點空間
            visible_count = max(1, visible_area_height // item_height) 
            
            start_idx = 0
            if len(games) > visible_count:
                start_idx = max(0, selected_index - (visible_count // 2))
                start_idx = min(start_idx, len(games) - visible_count)

            for i in range(visible_count):
                actual_idx = start_idx + i
                if actual_idx < len(games):
                    y_pos = header_height + i * item_height
                    prefix = "> " if actual_idx == selected_index else "  "
                    
                    game_name = games[actual_idx]['name']
                    
                    # 計算文字最大可用寬度
                    prefix_id_text = f"{prefix}{games[actual_idx]['id']}. "
                    try:
                        prefix_id_bbox = draw.textbbox((0,0), prefix_id_text, font=self.font)
                        prefix_id_w = prefix_id_bbox[2] - prefix_id_bbox[0]
                        char_a_bbox = draw.textbbox((0,0), "A", font=self.font)
                        char_a_w = char_a_bbox[2] - char_a_bbox[0]
                    except AttributeError:
                        prefix_id_w, _ = draw.textsize(prefix_id_text, font=self.font)
                        char_a_w, _ = draw.textsize("A", font=self.font)

                    if char_a_w > 0: # 避免除以零
                        max_name_chars = (self.width - prefix_id_w - 10) // char_a_w # 左右各留5px
                        if len(game_name) > max_name_chars and max_name_chars > 3:
                             game_name = game_name[:max_name_chars-3] + "..."
                    
                    text = f"{prefix}{games[actual_idx]['id']}. {game_name}"
                    draw.text((5, y_pos), text, fill="white", font=self.font)
    
    def display_game_instructions(self, game):
        """
        顯示遊戲說明
        """
        if not self.device or not self.font:
            print("SPI 螢幕或字體未初始化，無法顯示遊戲說明")
            return
        
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="black", fill="black")
            game_name = game['name']
            
            try:
                name_bbox = draw.textbbox((0,0), game_name, font=self.font)
                name_w = name_bbox[2] - name_bbox[0]
                name_h = name_bbox[3] - name_bbox[1]
                char_bbox = draw.textbbox((0,0), "Test", font=self.font) # 用於獲取一般行高
                line_h_actual = char_bbox[3] - char_bbox[1]
            except AttributeError:
                name_w, name_h = draw.textsize(game_name, font=self.font)
                _, line_h_actual = draw.textsize("Test", font=self.font)

            line_height_with_padding = line_h_actual + 4

            draw.text(((self.width - name_w) // 2, 5), game_name, fill="white", font=self.font)

            line_y_pos = 5 + name_h + 5 
            draw.line([(5, line_y_pos), (self.width - 5, line_y_pos)], fill="white", width=1)
            
            instr_title_y = line_y_pos + 5
            draw.text((5, instr_title_y), "操作說明:", fill="white", font=self.font)
            
            instr_text_y_start = instr_title_y + line_height_with_padding
            
            lines = self._wrap_text(game['description'], self.width - 10) 
            for i, line in enumerate(lines):
                draw.text((5, instr_text_y_start + i * line_height_with_padding), line, fill="white", font=self.font)
            
            bottom_text = "A:開始 B:返回"
            try:
                bottom_bbox = draw.textbbox((0,0), bottom_text, font=self.font)
                bottom_text_w = bottom_bbox[2] - bottom_bbox[0]
            except AttributeError:
                bottom_text_w, _ = draw.textsize(bottom_text, font=self.font)

            draw.text(((self.width - bottom_text_w) // 2, self.height - line_height_with_padding - 5), bottom_text, fill="white", font=self.font)
    
    def display_game_over(self, score):
        """
        顯示遊戲結束畫面
        """
        if not self.device or not self.font:
            print("SPI 螢幕或字體未初始化，無法顯示遊戲結束")
            return
        
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="black", fill="black") 
            title_text = "遊戲結束"
            score_text_str = f"分數: {score}"
            bottom_text = "按任意鍵返回"

            try:
                title_bbox = draw.textbbox((0,0), title_text, font=self.font)
                title_w, title_h = title_bbox[2]-title_bbox[0], title_bbox[3]-title_bbox[1]
                score_bbox = draw.textbbox((0,0), score_text_str, font=self.font)
                score_w, score_h = score_bbox[2]-score_bbox[0], score_bbox[3]-score_bbox[1]
                bottom_bbox = draw.textbbox((0,0), bottom_text, font=self.font)
                bottom_w, bottom_h = bottom_bbox[2]-bottom_bbox[0], bottom_bbox[3]-bottom_bbox[1]
                line_h_actual = bottom_h # 用作一般行高
            except AttributeError:
                title_w, title_h = draw.textsize(title_text, font=self.font)
                score_w, score_h = draw.textsize(score_text_str, font=self.font)
                bottom_w, bottom_h = draw.textsize(bottom_text, font=self.font)
                _, line_h_actual = draw.textsize("Test", font=self.font)

            line_height_with_padding = line_h_actual + 4

            draw.text(((self.width - title_w) // 2, self.height // 2 - title_h - score_h //2 - 5), title_text, fill="white", font=self.font)
            draw.text(((self.width - score_w) // 2, self.height // 2 - score_h // 2), score_text_str, fill="white", font=self.font)
            draw.text(((self.width - bottom_w)//2 , self.height - line_height_with_padding - 5), bottom_text, fill="white", font=self.font)
    
    def _wrap_text(self, text, max_pixel_width):
        """
        將文字進行自動換行以適應指定的像素寬度
        """
        if not self.font: 
            return [text]

        lines = []
        if not text:
            return lines

        words = text.split(' ') # 按空格分割
        current_line = ""

        for word in words:
            # 處理連續空格或空詞的情況
            if not word:
                if current_line and current_line[-1] != ' ': # 避免行尾多餘空格
                    current_line += " "
                continue

            test_line = current_line + word if not current_line else current_line + " " + word
            
            try:
                bbox = self.font.getbbox(test_line)
                line_width = bbox[2] - bbox[0]
            except AttributeError: # 相容舊版 Pillow 的 getsize
                # getsize 對多行文本返回 (width, height)，對單行返回 (width, height)
                # 但對 load_default() 的字體，getsize 可能不準確或不存在
                # 這裡假設 getsize 返回的是單行寬高
                try:
                    line_width, _ = self.font.getsize(test_line)
                except: # 如果 getsize 也失敗，則無法換行
                    lines.append(test_line) # 將剩餘部分作為一行
                    current_line = ""
                    break


            if line_width <= max_pixel_width:
                current_line = test_line
            else:
                if current_line: # 如果當前行有內容，先將當前行加入
                    lines.append(current_line)
                current_line = word # 新的一行從這個詞開始
                # 檢查這個詞本身是否就超長
                try:
                    word_bbox = self.font.getbbox(current_line)
                    word_width = word_bbox[2] - word_bbox[0]
                except AttributeError:
                    try:
                        word_width, _ = self.font.getsize(current_line)
                    except: # 無法獲取單詞寬度
                        lines.append(current_line)
                        current_line = ""
                        continue
                
                if word_width > max_pixel_width:
                    # 單詞本身超長，需要字符級換行 (這裡簡化，直接加入，可能溢出)
                    # TODO: 實現字符級換行
                    lines.append(current_line)
                    current_line = ""
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def display_custom_message(self, title, message, duration=0):
        """
        顯示自定義訊息，可選擇持續一段時間後自動清除
        """
        if not self.device or not self.font:
            print("SPI 螢幕或字體未初始化，無法顯示訊息")
            return
        
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="black", fill="black") 
            
            try:
                title_bbox = draw.textbbox((0,0), title, font=self.font)
                title_w, title_h = title_bbox[2]-title_bbox[0], title_bbox[3]-title_bbox[1]
                char_bbox = draw.textbbox((0,0), "Test", font=self.font)
                line_h_actual = char_bbox[3]-char_bbox[1]
            except AttributeError:
                title_w, title_h = draw.textsize(title, font=self.font)
                _, line_h_actual = draw.textsize("Test", font=self.font)

            line_height_with_padding = line_h_actual + 4
            
            draw.text(((self.width - title_w) // 2, 5), title, fill="white", font=self.font)
            
            line_y_pos = 5 + title_h + 5
            draw.line([(5, line_y_pos), (self.width - 5, line_y_pos)], fill="white", width=1)
            
            message_y_start = line_y_pos + 5
            lines = self._wrap_text(message, self.width - 10)
            for i, line in enumerate(lines):
                draw.text((5, message_y_start + i * line_height_with_padding), line, fill="white", font=self.font)
        
        if duration > 0:
            time.sleep(duration)
            self.clear_screen() 
    
    def cleanup(self):
        """清理資源"""
        if self.device:
            self.clear_screen()
        if hasattr(self, 'SPI_LED') and self.SPI_LED is not None:
             GPIO.output(self.SPI_LED, GPIO.LOW) 
        print("SPI 螢幕已清理")

# 測試代碼
if __name__ == "__main__":
    try:
        GPIO.setmode(GPIO.BCM) 
        GPIO.setwarnings(False)

        # **請根據您的螢幕規格修改 DISPLAY_WIDTH 和 DISPLAY_HEIGHT**
        screen = SPIScreenManager(display_width=DISPLAY_WIDTH, display_height=DISPLAY_HEIGHT)

        games_data = [
            {"id": 1, "name": "貪吃蛇 (Snake)", "description": "搖桿控制方向。按A鈕加速。"},
            {"id": 2, "name": "打磚塊 (Brick Breaker)", "description": "搖桿左右移動擋板。按A鈕發射球。"},
            {"id": 3, "name": "太空侵略者 (Space Invaders)", "description": "搖桿左右移動。按A鈕射擊。"},
            {"id": 4, "name": "井字遊戲 (Tic-Tac-Toe)", "description": "搖桿選擇格子。按A鈕確認。"},
            {"id": 5, "name": "記憶翻牌 (Memory Match)", "description": "搖桿選擇牌。按A鈕翻牌。"},
            {"id": 6, "name": "簡易迷宮 (Simple Maze)", "description": "搖桿控制方向。"},
            {"id": 7, "name": "打地鼠 (Whac-A-Mole)", "description": "搖桿移動槌子。按A鈕敲擊。"},
            {"id": 8, "name": "俄羅斯方塊 (Tetris-like)", "description": "搖桿左右移動，上改變方向，下加速。按A鈕快速落下。"},
            {"id": 9, "name": "反應力測試 (Reaction Test)", "description": "出現信號時，按A鈕。"},
        ]
        
        if screen.device: 
            print("顯示選單...")
            screen.display_menu(games_data, 0)
            time.sleep(2)
            
            print("移動選擇...")
            for i in range(1, len(games_data)):
                screen.display_menu(games_data, i)
                time.sleep(0.5) 
            
            print("顯示遊戲說明 (遊戲1)...")
            screen.display_game_instructions(games_data[0])
            time.sleep(2)
            
            print("顯示遊戲結束...")
            screen.display_game_over(100)
            time.sleep(2)

            print("顯示自定義訊息...")
            screen.display_custom_message("系統訊息", "正在載入資源，請稍候...", duration=3)
            
            screen.clear_screen()
            print("測試完成，清理螢幕。")
        else:
            print("螢幕未成功初始化，跳過部分測試。")
            
    except Exception as e:
        print(f"測試出錯: {e}")
    finally:
        if 'screen' in locals() and screen: 
            screen.cleanup()
        # GPIO.cleanup() # 應由主程式 main.py 負責最終的 GPIO 清理
        print("screen_menu.py 測試結束。")


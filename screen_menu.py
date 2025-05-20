#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# screen_menu.py - SPI 螢幕控制邏輯

import time
import RPi.GPIO as GPIO
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1325, ssd1331, sh1106
from PIL import Image, ImageDraw, ImageFont

# 定義 SPI 連接的 GPIO 引腳
SPI_PORT = 0  # SPI0
SPI_DEVICE = 0
SPI_DC = 24   # Data/Command
SPI_RST = 25  # Reset
SPI_CS = 8    # Chip Select

# 預設設定
DEFAULT_FONT_SIZE = 12
DISPLAY_WIDTH = 128   # OLED 顯示寬度
DISPLAY_HEIGHT = 64   # OLED 顯示高度

class SPIScreenManager:
    """SPI 介面的小螢幕管理類"""
    
    def __init__(self, display_width=DISPLAY_WIDTH, display_height=DISPLAY_HEIGHT):
        self.width = display_width
        self.height = display_height
        self.device = self._initialize_device()
        self.font = self._load_font()
    
    def _initialize_device(self):
        """初始化 SPI 螢幕"""
        try:
            # 建立 SPI 介面
            serial = spi(port=SPI_PORT, device=SPI_DEVICE, gpio_DC=SPI_DC, gpio_RST=SPI_RST, gpio_CS=SPI_CS)
            
            # 初始化 OLED 設備（根據您的硬體選擇適當的 OLED 型號）
            # 若為 SSD1306 型號
            device = ssd1306(serial, width=self.width, height=self.height)
            
            # 其他型號 (可能需要取消註解)
            # device = ssd1325(serial, width=self.width, height=self.height)
            # device = ssd1331(serial, width=self.width, height=self.height)
            # device = sh1106(serial, width=self.width, height=self.height)
            
            print("SPI 螢幕成功初始化")
            return device
            
        except Exception as e:
            print(f"SPI 螢幕初始化失敗: {e}")
            return None
    
    def _load_font(self, font_size=DEFAULT_FONT_SIZE):
        """載入字體，使用系統提供的默認字體"""
        try:
            # 使用 PIL 提供的默認字體
            font = ImageFont.load_default()
            return font
        except Exception as e:
            print(f"字體載入失敗: {e}")
            return None
    
    def clear_screen(self):
        """清除螢幕上的所有內容"""
        if self.device:
            with canvas(self.device) as draw:
                # 繪製空白
                pass
    
    def display_menu(self, games, selected_index):
        """
        顯示遊戲選單
        
        參數:
            games: 遊戲列表，每個元素為字典包含 id, name 等資訊
            selected_index: 目前選中的遊戲索引
        """
        if not self.device:
            print("SPI 螢幕未初始化，無法顯示選單")
            return
        
        with canvas(self.device) as draw:
            # 繪製標題
            draw.text((2, 0), "選擇遊戲:", fill="white", font=self.font)
            
            # 計算可顯示的遊戲數量和起始索引
            visible_count = 5  # 顯示區域能容納的項目數
            start_idx = max(0, min(selected_index - visible_count//2, len(games) - visible_count))
            
            # 繪製選單項目
            for i in range(start_idx, min(start_idx + visible_count, len(games))):
                y_pos = 14 + (i - start_idx) * 10
                prefix = ">" if i == selected_index else " "
                text = f"{prefix} {games[i]['id']}. {games[i]['name']}"
                draw.text((2, y_pos), text, fill="white", font=self.font)
    
    def display_game_instructions(self, game):
        """
        顯示遊戲說明
        
        參數:
            game: 遊戲資訊字典
        """
        if not self.device:
            print("SPI 螢幕未初始化，無法顯示遊戲說明")
            return
        
        with canvas(self.device) as draw:
            # 繪製遊戲名稱
            draw.text((2, 0), game['name'], fill="white", font=self.font)
            
            # 繪製分隔線
            draw.line([(0, 12), (self.width, 12)], fill="white")
            
            # 繪製操作說明
            draw.text((2, 14), "操作說明:", fill="white", font=self.font)
            
            # 分行顯示說明文字
            lines = self._wrap_text(game['description'], self.width - 4)
            for i, line in enumerate(lines):
                draw.text((2, 26 + i * 10), line, fill="white", font=self.font)
            
            # 繪製底部提示
            draw.text((2, self.height - 10), "A:開始 B:返回", fill="white", font=self.font)
    
    def display_game_over(self, score):
        """
        顯示遊戲結束畫面
        
        參數:
            score: 遊戲分數
        """
        if not self.device:
            print("SPI 螢幕未初始化，無法顯示遊戲結束")
            return
        
        with canvas(self.device) as draw:
            # 繪製遊戲結束標題
            draw.text((self.width//2 - 30, 10), "遊戲結束", fill="white", font=self.font)
            
            # 繪製分數
            draw.text((self.width//2 - 30, 30), f"分數: {score}", fill="white", font=self.font)
            
            # 繪製底部提示
            draw.text((self.width//2 - 30, self.height - 10), "按任意鍵返回", fill="white", font=self.font)
    
    def _wrap_text(self, text, max_width):
        """
        將文字進行自動換行以適應螢幕寬度
        
        參數:
            text: 要顯示的文字
            max_width: 每行最大寬度 (像素)
        
        返回:
            一個包含多行文字的列表
        """
        words = text.split()
        lines = []
        line = ""
        
        for word in words:
            test_line = line + word + " "
            # 測量文字寬度
            test_width = self.font.getsize(test_line)[0]
            
            if test_width > max_width:
                # 若超過寬度，添加目前行到列表，開始新行
                lines.append(line)
                line = word + " "
            else:
                # 否則繼續添加字到目前行
                line = test_line
        
        # 添加最後一行
        if line:
            lines.append(line)
        
        return lines
    
    def display_custom_message(self, title, message):
        """
        顯示自定義訊息
        
        參數:
            title: 訊息標題
            message: 訊息內容
        """
        if not self.device:
            print("SPI 螢幕未初始化，無法顯示訊息")
            return
        
        with canvas(self.device) as draw:
            # 繪製標題
            draw.text((2, 0), title, fill="white", font=self.font)
            
            # 繪製分隔線
            draw.line([(0, 12), (self.width, 12)], fill="white")
            
            # 分行顯示訊息內容
            lines = self._wrap_text(message, self.width - 4)
            for i, line in enumerate(lines):
                draw.text((2, 14 + i * 10), line, fill="white", font=self.font)
    
    def cleanup(self):
        """清理資源"""
        # 目前無需特殊清理操作，但保留此方法以便未來擴充
        if self.device:
            self.clear_screen()
            print("SPI 螢幕已清理")

# 測試代碼
if __name__ == "__main__":
    try:
        # 測試 SPI 螢幕功能
        screen = SPIScreenManager()
          # 測試顯示選單
        games = [
            {"id": 1, "name": "貪吃蛇 (Snake)", "description": "搖桿控制方向。按A鈕加速。"},
            {"id": 2, "name": "打磚塊 (Brick Breaker)", "description": "搖桿左右移動擋板。按A鈕發射球。"},
            {"id": 3, "name": "太空侵略者", "description": "搖桿左右移動。按A鈕射擊。"},
            {"id": 4, "name": "井字遊戲", "description": "搖桿選擇格子。按A鈕確認。"},
            {"id": 5, "name": "記憶翻牌", "description": "搖桿選擇牌。按A鈕翻牌。"},
            {"id": 6, "name": "簡易迷宮 (Simple Maze)", "description": "搖桿控制方向。"},
            {"id": 7, "name": "打地鼠 (Whac-A-Mole)", "description": "搖桿移動槌子。按A鈕敲擊。"},
            {"id": 8, "name": "俄羅斯方塊 (Tetris-like)", "description": "搖桿左右移動，上改變方向，下加速。按A鈕快速落下。"},
            {"id": 9, "name": "反應力測試 (Reaction Test)", "description": "出現信號時，按A鈕。"},
        ]
        
        # 顯示選單
        print("顯示選單...")
        screen.display_menu(games, 0)
        time.sleep(2)
        
        # 移動選擇並顯示
        print("移動選擇...")
        for i in range(1, len(games)):
            screen.display_menu(games, i)
            time.sleep(1)
        
        # 顯示遊戲說明
        print("顯示遊戲說明...")
        screen.display_game_instructions(games[0])
        time.sleep(2)
        
        # 顯示遊戲結束
        print("顯示遊戲結束...")
        screen.display_game_over(100)
        time.sleep(2)
        
        # 清理
        screen.cleanup()
        
    except Exception as e:
        print(f"測試出錯: {e}")
        GPIO.cleanup()

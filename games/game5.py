#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game5.py - 記憶翻牌遊戲實現

import random
import pygame
import time
from pygame.locals import *

class MemoryMatchGame:
    """記憶翻牌遊戲類"""
    
    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width       # 遊戲區域寬度
        self.height = height     # 遊戲區域高度
        self.buzzer = buzzer     # 蜂鳴器實例，用於音效回饋
        
        # 顏色定義
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        self.PURPLE = (255, 0, 255)
        self.CYAN = (0, 255, 255)
        self.ORANGE = (255, 165, 0)
        self.CARD_BACK = (50, 50, 150)
        
        # 遊戲參數
        self.rows = 4
        self.cols = 4
        self.card_margin = 10
        self.calculate_card_size()
        
        # 遊戲速度相關
        self.clock = pygame.time.Clock()
        self.fps = 30
        
        # 初始化遊戲狀態
        self.reset_game()
    
    def calculate_card_size(self):
        """計算卡牌尺寸和位置"""
        # 計算合適的卡牌尺寸
        available_width = self.width - (self.cols + 1) * self.card_margin
        available_height = self.height - (self.rows + 1) * self.card_margin - 100  # 上方留空間給分數等
        
        self.card_width = available_width // self.cols
        self.card_height = available_height // self.rows
        
        # 計算起始位置使整個卡牌區域置中
        self.start_x = (self.width - (self.cols * self.card_width + (self.cols - 1) * self.card_margin)) // 2
        self.start_y = (self.height - (self.rows * self.card_height + (self.rows - 1) * self.card_margin)) // 2 + 50  # 向下偏移
    
    def reset_game(self):
        """重置遊戲狀態"""
        # 游標位置
        self.cursor_row = 0
        self.cursor_col = 0
        
        # 生成卡牌
        self.cards = self.generate_cards()
        
        # 翻開的卡牌
        self.flipped = []
        
        # 已配對的卡牌
        self.matched = []
        
        # 分數和回合
        self.score = 0
        self.moves = 0
        
        # 遊戲狀態
        self.game_over = False
        self.paused = False
        
        # 用於控制輸入頻率和卡牌翻轉動畫
        self.last_input_time = time.time()
        self.input_delay = 0.2  # 秒
        
        self.card_flip_delay = 1.0  # 秒
        self.last_flip_time = 0
        self.is_checking_match = False
    
    def generate_cards(self):
        """生成卡牌，包含配對的圖案"""
        # 創建牌組
        symbols = ["A", "B", "C", "D", "E", "F", "G", "H"]
        cards = []
        
        # 確保足夠的符號
        if len(symbols) < (self.rows * self.cols) // 2:
            raise ValueError("需要更多符號來創建足夠的卡牌對")
        
        # 生成卡牌對
        pairs_needed = (self.rows * self.cols) // 2
        selected_symbols = symbols[:pairs_needed]
        
        for symbol in selected_symbols:
            # 每個符號出現兩次
            cards.append({"symbol": symbol, "color": self.get_color_for_symbol(symbol)})
            cards.append({"symbol": symbol, "color": self.get_color_for_symbol(symbol)})
        
        # 洗牌
        random.shuffle(cards)
        
        # 轉換為二維數組
        grid = []
        for row in range(self.rows):
            grid_row = []
            for col in range(self.cols):
                index = row * self.cols + col
                grid_row.append(cards[index])
            grid.append(grid_row)
        
        return grid
    
    def get_color_for_symbol(self, symbol):
        """為每個符號分配一個顏色"""
        colors = [self.RED, self.GREEN, self.BLUE, self.YELLOW, self.PURPLE, self.CYAN, self.ORANGE, self.WHITE]
        
        # 基於符號的雜湊值選擇顏色
        index = ord(symbol) % len(colors)
        return colors[index]
    
    def update(self, controller_input=None):
        """
        更新遊戲狀態
        
        參數:
            controller_input: 來自控制器的輸入字典
        
        返回:
            包含遊戲狀態的字典
        """
        if self.game_over or self.paused:
            # 處理遊戲結束或暫停狀態下的輸入
            if controller_input and controller_input.get("start_pressed"):
                if self.game_over:
                    self.reset_game()
                else:
                    self.paused = not self.paused
            
            return {"game_over": self.game_over, "score": self.score, "paused": self.paused}
        
        # 檢查是否所有卡牌都已配對
        if len(self.matched) == self.rows * self.cols:
            self.game_over = True
            if self.buzzer:
                self.buzzer.play_win_melody()
            return {"game_over": True, "score": self.score}
        
        # 處理卡牌配對檢查延遲
        current_time = time.time()
        if self.is_checking_match:
            if current_time - self.last_flip_time >= self.card_flip_delay:
                self.check_match()
                self.is_checking_match = False
            return {"game_over": self.game_over, "score": self.score}
        
        # 處理玩家輸入
        if current_time - self.last_input_time < self.input_delay:
            # 輸入延遲中，不處理輸入
            return {"game_over": self.game_over, "score": self.score}
        
        if controller_input:
            input_detected = False
            
            # 方向控制
            if controller_input.get("up_pressed"):
                self.cursor_row = max(0, self.cursor_row - 1)
                input_detected = True
            elif controller_input.get("down_pressed"):
                self.cursor_row = min(self.rows - 1, self.cursor_row + 1)
                input_detected = True
            
            if controller_input.get("left_pressed"):
                self.cursor_col = max(0, self.cursor_col - 1)
                input_detected = True
            elif controller_input.get("right_pressed"):
                self.cursor_col = min(self.cols - 1, self.cursor_col + 1)
                input_detected = True
            
            # 選擇控制
            if controller_input.get("a_pressed"):
                self.flip_card(self.cursor_row, self.cursor_col)
                input_detected = True
            
            # 暫停控制
            if controller_input.get("start_pressed"):
                self.paused = not self.paused
                input_detected = True
            
            # 如果檢測到輸入，重置輸入延遲計時器
            if input_detected:
                self.last_input_time = current_time
                if self.buzzer and not controller_input.get("a_pressed"):
                    self.buzzer.play_tone("navigate")
        
        return {"game_over": self.game_over, "score": self.score}
    
    def flip_card(self, row, col):
        """翻開卡牌"""
        # 檢查是否已翻開或已配對
        card_index = row * self.cols + col
        if card_index in self.flipped or card_index in self.matched:
            if self.buzzer:
                self.buzzer.play_tone("error")
            return
        
        # 翻開卡牌
        self.flipped.append(card_index)
        if self.buzzer:
            self.buzzer.play_tone("select")
        
        # 檢查是否已翻開兩張卡牌
        if len(self.flipped) == 2:
            self.moves += 1
            self.last_flip_time = time.time()
            self.is_checking_match = True
    
    def check_match(self):
        """檢查兩張翻開的卡牌是否配對"""
        if len(self.flipped) != 2:
            return
        
        # 獲取兩張卡牌的坐標
        idx1, idx2 = self.flipped
        row1, col1 = idx1 // self.cols, idx1 % self.cols
        row2, col2 = idx2 // self.cols, idx2 % self.cols
        
        # 檢查符號是否相同
        if self.cards[row1][col1]["symbol"] == self.cards[row2][col2]["symbol"]:
            # 配對成功
            self.matched.extend(self.flipped)
            self.score += 100
            if self.buzzer:
                self.buzzer.play_tone("level_up")
        else:
            # 配對失敗
            if self.buzzer:
                self.buzzer.play_tone("error")
        
        # 清空已翻開列表
        self.flipped = []
    
    def render(self, screen):
        """
        渲染遊戲畫面
        
        參數:
            screen: pygame 螢幕物件
        """
        # 清除螢幕
        screen.fill(self.BLACK)
        
        # 繪製卡牌
        for row in range(self.rows):
            for col in range(self.cols):
                card_index = row * self.cols + col
                card = self.cards[row][col]
                
                # 計算卡牌位置
                x = self.start_x + col * (self.card_width + self.card_margin)
                y = self.start_y + row * (self.card_height + self.card_margin)
                
                # 判斷卡牌狀態（背面、翻開或已配對）
                if card_index in self.matched:
                    # 已配對
                    color = card["color"]
                    pygame.draw.rect(screen, color, (x, y, self.card_width, self.card_height))
                    
                    # 繪製符號
                    self.draw_symbol(screen, card["symbol"], (x, y, self.card_width, self.card_height), self.BLACK)
                
                elif card_index in self.flipped:
                    # 已翻開
                    color = card["color"]
                    pygame.draw.rect(screen, color, (x, y, self.card_width, self.card_height))
                    
                    # 繪製符號
                    self.draw_symbol(screen, card["symbol"], (x, y, self.card_width, self.card_height), self.BLACK)
                
                else:
                    # 背面
                    pygame.draw.rect(screen, self.CARD_BACK, (x, y, self.card_width, self.card_height))
                    
                    # 繪製卡牌花紋
                    margin = min(self.card_width, self.card_height) // 10
                    pygame.draw.rect(screen, (30, 30, 100), 
                                    (x + margin, y + margin, 
                                     self.card_width - 2 * margin, self.card_height - 2 * margin))
                
                # 繪製卡牌邊框
                pygame.draw.rect(screen, self.WHITE, (x, y, self.card_width, self.card_height), 2)
        
        # 繪製游標
        if not self.game_over and not self.paused:
            cursor_x = self.start_x + self.cursor_col * (self.card_width + self.card_margin)
            cursor_y = self.start_y + self.cursor_row * (self.card_height + self.card_margin)
            
            # 使用閃爍效果
            if int(time.time() * 2) % 2:
                pygame.draw.rect(screen, self.YELLOW, 
                               (cursor_x - 2, cursor_y - 2, 
                                self.card_width + 4, self.card_height + 4), 
                               3)
        
        # 繪製遊戲資訊
        font = pygame.font.Font(None, 36)
        
        # 分數
        score_text = font.render(f"分數: {self.score}", True, self.WHITE)
        screen.blit(score_text, (20, 20))
        
        # 回合數
        moves_text = font.render(f"回合: {self.moves}", True, self.WHITE)
        screen.blit(moves_text, (self.width - moves_text.get_width() - 20, 20))
        
        # 配對進度
        progress = len(self.matched) // 2
        total_pairs = (self.rows * self.cols) // 2
        progress_text = font.render(f"配對: {progress}/{total_pairs}", True, self.WHITE)
        screen.blit(progress_text, (self.width // 2 - progress_text.get_width() // 2, 20))
        
        # 遊戲結束畫面
        if self.game_over:
            self.draw_game_over(screen)
        
        # 暫停畫面
        elif self.paused:
            self.draw_pause(screen)
    
    def draw_symbol(self, screen, symbol, rect, color):
        """繪製卡牌上的符號"""
        x, y, width, height = rect
        
        # 取決於符號，繪製不同的形狀
        font = pygame.font.Font(None, min(width, height) - 10)
        text = font.render(symbol, True, color)
        text_rect = text.get_rect(center=(x + width // 2, y + height // 2))
        screen.blit(text, text_rect)
    
    def draw_game_over(self, screen):
        """繪製遊戲結束畫面"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 72)
        text = font.render("遊戲結束!", True, self.YELLOW)
        screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 50))
        
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"最終分數: {self.score}", True, self.WHITE)
        screen.blit(score_text, (self.width // 2 - score_text.get_width() // 2, self.height // 2 + 10))
        
        moves_text = font.render(f"使用回合數: {self.moves}", True, self.WHITE)
        screen.blit(moves_text, (self.width // 2 - moves_text.get_width() // 2, self.height // 2 + 50))
        
        restart_text = font.render("按 Start 重新開始", True, self.WHITE)
        screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, self.height // 2 + 90))
    
    def draw_pause(self, screen):
        """繪製暫停畫面"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 72)
        text = font.render("暫停", True, self.YELLOW)
        screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 50))
        
        font = pygame.font.Font(None, 36)
        continue_text = font.render("按 Start 繼續", True, self.WHITE)
        screen.blit(continue_text, (self.width // 2 - continue_text.get_width() // 2, self.height // 2 + 10))
    
    def cleanup(self):
        """清理遊戲資源"""
        # 目前無需特殊清理，但保留此方法以便未來擴充
        pass

# 若獨立執行此腳本，用於測試
if __name__ == "__main__":
    try:
        # 初始化 pygame
        pygame.init()
        
        # 設置視窗
        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("記憶翻牌遊戲測試")
        
        # 建立遊戲實例
        game = MemoryMatchGame(screen_width, screen_height)
        
        # 模擬控制器輸入的鍵盤映射
        key_mapping = {
            pygame.K_UP: "up_pressed",
            pygame.K_DOWN: "down_pressed",
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_a: "a_pressed",
            pygame.K_RETURN: "start_pressed"
        }
        
        # 遊戲主迴圈
        running = True
        while running:
            # 處理事件
            controller_input = {key: False for key in key_mapping.values()}
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # 獲取當前按下的按鍵狀態
            keys = pygame.key.get_pressed()
            for key, input_name in key_mapping.items():
                if keys[key]:
                    controller_input[input_name] = True
            
            # 更新遊戲
            game.update(controller_input)
            
            # 渲染
            game.render(screen)
            pygame.display.flip()
            
            # 控制幀率
            pygame.time.Clock().tick(30)
        
        # 退出 pygame
        pygame.quit()
    
    except Exception as e:
        print(f"遊戲執行錯誤: {e}")
        pygame.quit()

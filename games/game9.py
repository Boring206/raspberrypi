#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game9.py - 反應力測試遊戲實現

import random
import pygame
import time
from pygame.locals import *

class ReactionTestGame:
    """反應力測試遊戲類"""
    
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
        
        # 遊戲參數
        self.trials = 5          # 每輪測試次數
        self.min_wait = 2.0      # 最短等待時間
        self.max_wait = 5.0      # 最長等待時間
        
        # 遊戲速度相關
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # 初始化遊戲狀態
        self.reset_game()
    
    def reset_game(self):
        """重置遊戲狀態"""
        # 遊戲狀態
        self.game_over = False
        self.paused = False
        self.current_trial = 0
        
        # 各種狀態標記
        self.waiting = True          # 是否在等待階段
        self.signal_on = False       # 是否顯示信號
        self.early_press = False     # 是否提前按下按鈕
        self.result_showing = False  # 是否顯示結果
        
        # 時間記錄
        self.wait_end_time = 0       # 等待結束時間
        self.signal_start_time = 0   # 信號開始時間
        self.response_time = 0       # 反應時間
        
        # 反應時間記錄
        self.reaction_times = []    # 所有試驗的反應時間
        
        # 設置第一次等待
        self.set_wait_time()
    
    def set_wait_time(self):
        """設置等待時間"""
        # a隨機等待時間
        wait_time = random.uniform(self.min_wait, self.max_wait)
        
        # 設置等待結束時間
        self.wait_end_time = time.time() + wait_time
        
        # 重置狀態
        self.waiting = True
        self.signal_on = False
        self.early_press = False
        self.result_showing = False
    
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
                    self.paused = False
            
            return {"game_over": self.game_over, "paused": self.paused}
        
        # 暫停控制
        if controller_input and controller_input.get("start_pressed"):
            self.paused = True
            return {"game_over": self.game_over, "paused": self.paused}
        
        # 當前時間
        current_time = time.time()
        
        # 處理等待階段
        if self.waiting:
            # 檢查是否提前按下
            if controller_input and controller_input.get("a_pressed"):
                self.early_press = True
                self.waiting = False
                self.result_showing = True
                
                # 計算下一次等待的開始時間
                self.wait_end_time = current_time + 2.0  # 顯示 2 秒結果後繼續
                
                # 播放錯誤音效
                if self.buzzer:
                    self.buzzer.play_tone("error")
            
            # 檢查等待時間是否結束
            elif current_time >= self.wait_end_time:
                self.waiting = False
                self.signal_on = True
                self.signal_start_time = current_time
                
                # 播放信號音效
                if self.buzzer:
                    self.buzzer.play_tone("select")
        
        # 處理信號顯示階段
        elif self.signal_on:
            # 檢查是否按下按鈕
            if controller_input and controller_input.get("a_pressed"):
                # 計算反應時間
                self.response_time = (current_time - self.signal_start_time) * 1000  # 毫秒
                self.reaction_times.append(self.response_time)
                
                # 切換到結果顯示
                self.signal_on = False
                self.result_showing = True
                
                # 計算下一次等待的開始時間
                self.wait_end_time = current_time + 2.0  # 顯示 2 秒結果後繼續
                
                # 播放成功音效
                if self.buzzer:
                    self.buzzer.play_tone("score")
                
                # 增加試驗次數
                self.current_trial += 1
                
                # 檢查是否完成所有試驗
                if self.current_trial >= self.trials:
                    self.game_over = True
                    if self.buzzer:
                        self.buzzer.play_win_melody()
        
        # 處理結果顯示階段
        elif self.result_showing:
            # 檢查是否到達顯示結果的時間限制
            if current_time >= self.wait_end_time:
                self.result_showing = False
                
                # 如果遊戲還沒結束，設置下一次等待
                if not self.game_over:
                    self.set_wait_time()
        
        return {"game_over": self.game_over, "paused": self.paused}
    
    def render(self, screen):
        """
        渲染遊戲畫面
        
        參數:
            screen: pygame 螢幕物件
        """
        # 清除螢幕
        screen.fill(self.BLACK)
        
        # 繪製遊戲資訊
        font_title = pygame.font.Font(None, 48)
        font_info = pygame.font.Font(None, 36)
        
        # 標題和進度
        title = font_title.render(f"反應力測試 ({self.current_trial}/{self.trials})", True, self.WHITE)
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 50))
        
        # 指示文字
        instructions = font_info.render("看到綠色信號後立即按 A 鈕", True, self.WHITE)
        screen.blit(instructions, (self.width // 2 - instructions.get_width() // 2, 120))
        
        # 繪製圓形信號
        signal_radius = 100
        signal_center = (self.width // 2, self.height // 2)
        
        if self.waiting:
            # 等待階段 - 顯示紅色圓圈
            pygame.draw.circle(screen, self.RED, signal_center, signal_radius)
            wait_text = font_info.render("請等待...", True, self.WHITE)
            screen.blit(wait_text, (self.width // 2 - wait_text.get_width() // 2, self.height // 2 + 120))
        
        elif self.signal_on:
            # 信號顯示階段 - 顯示綠色圓圈
            pygame.draw.circle(screen, self.GREEN, signal_center, signal_radius)
            action_text = font_info.render("立即按 A！", True, self.WHITE)
            screen.blit(action_text, (self.width // 2 - action_text.get_width() // 2, self.height // 2 + 120))
        
        elif self.result_showing:
            # 結果顯示階段
            if self.early_press:
                # 提前按下 - 顯示錯誤信息
                pygame.draw.circle(screen, self.YELLOW, signal_center, signal_radius)
                early_text = font_info.render("提前按下！請等待綠色信號", True, self.RED)
                screen.blit(early_text, (self.width // 2 - early_text.get_width() // 2, self.height // 2 + 120))
            else:
                # 正常反應 - 顯示反應時間
                pygame.draw.circle(screen, self.BLUE, signal_center, signal_radius)
                result_text = font_info.render(f"反應時間: {self.response_time:.1f} 毫秒", True, self.WHITE)
                screen.blit(result_text, (self.width // 2 - result_text.get_width() // 2, self.height // 2 + 120))
        
        # 顯示歷史反應時間
        if self.reaction_times:
            history_y = self.height - 150
            history_text = font_info.render("歷史反應時間 (毫秒):", True, self.WHITE)
            screen.blit(history_text, (50, history_y))
            
            # 顯示最多 5 個歷史記錄
            for i, time_ms in enumerate(self.reaction_times[-5:]):
                time_text = font_info.render(f"{i+1}. {time_ms:.1f}", True, self.WHITE)
                screen.blit(time_text, (50, history_y + 40 + i * 30))
        
        # 遊戲結束畫面
        if self.game_over:
            self.draw_game_over(screen)
        
        # 暫停畫面
        elif self.paused:
            self.draw_pause(screen)
    
    def draw_game_over(self, screen):
        """繪製遊戲結束畫面"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        font = pygame.font.Font(None, 36)
        
        # 標題
        text = font_large.render("測試完成", True, self.GREEN)
        screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 150))
        
        # 計算平均反應時間和最佳時間
        valid_times = [t for t in self.reaction_times if t > 0]
        if valid_times:
            avg_time = sum(valid_times) / len(valid_times)
            best_time = min(valid_times)
            worst_time = max(valid_times)
            
            avg_text = font_medium.render(f"平均反應時間: {avg_time:.1f} 毫秒", True, self.WHITE)
            screen.blit(avg_text, (self.width // 2 - avg_text.get_width() // 2, self.height // 2 - 50))
            
            best_text = font.render(f"最快時間: {best_time:.1f} 毫秒", True, self.WHITE)
            screen.blit(best_text, (self.width // 2 - best_text.get_width() // 2, self.height // 2 + 10))
            
            worst_text = font.render(f"最慢時間: {worst_time:.1f} 毫秒", True, self.WHITE)
            screen.blit(worst_text, (self.width // 2 - worst_text.get_width() // 2, self.height // 2 + 50))
            
            # 評級
            rating = ""
            if avg_time < 200:
                rating = "非常優秀！"
            elif avg_time < 300:
                rating = "很好！"
            elif avg_time < 400:
                rating = "良好"
            elif avg_time < 500:
                rating = "一般"
            else:
                rating = "需要練習"
            
            rating_text = font_medium.render(f"評級: {rating}", True, self.YELLOW)
            screen.blit(rating_text, (self.width // 2 - rating_text.get_width() // 2, self.height // 2 + 100))
        
        restart_text = font.render("按 Start 重新開始", True, self.WHITE)
        screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, self.height // 2 + 160))
    
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
        pygame.display.set_caption("反應力測試遊戲測試")
        
        # 建立遊戲實例
        game = ReactionTestGame(screen_width, screen_height)
        
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
            pygame.time.Clock().tick(60)
        
        # 退出 pygame
        pygame.quit()
    
    except Exception as e:
        print(f"遊戲執行錯誤: {e}")
        pygame.quit()

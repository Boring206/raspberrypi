#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game1.py - 貪吃蛇遊戲實現

import random
import pygame
import time
from pygame.locals import *

class SnakeGame:
    """貪吃蛇遊戲類"""
    
    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width       # 遊戲區域寬度
        self.height = height     # 遊戲區域高度
        self.buzzer = buzzer     # 蜂鳴器實例，用於音效回饋
        
        # 遊戲元素大小
        self.block_size = 20     # 蛇身體和食物的方塊大小
        self.grid_width = self.width // self.block_size
        self.grid_height = self.height // self.block_size
        
        # 顏色定義
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)
        
        # 遊戲速度相關
        self.clock = pygame.time.Clock()
        self.speed = 8           # 初始更新頻率 (每秒幀數)
        self.speed_boost = 15    # 加速時的更新頻率
        self.current_speed = self.speed
        
        # 初始化遊戲狀態
        self.reset_game()
    
    def reset_game(self):
        """重置遊戲狀態"""
        # 蛇的初始位置 (中央)
        self.snake = [(self.grid_width // 2, self.grid_height // 2)]
        
        # 初始方向 (右)
        self.direction = (1, 0)
        
        # 生成第一個食物
        self.food = self.generate_food()
        
        # 分數和遊戲狀態
        self.score = 0
        self.game_over = False
        self.paused = False
        self.boosting = False  # 是否正在加速
        
        # 用於控制蛇的移動頻率
        self.last_move_time = time.time()
        self.move_interval = 1.0 / self.speed  # 移動間隔時間
    
    def generate_food(self):
        """生成新食物，確保不在蛇身上"""
        while True:
            food = (random.randint(0, self.grid_width - 1), 
                   random.randint(0, self.grid_height - 1))
            if food not in self.snake:
                return food
    
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
            
            return {"game_over": self.game_over, "score": self.score, "paused": self.paused}
        
        # 處理輸入
        if controller_input:
            # 方向控制
            if controller_input.get("up_pressed") and self.direction != (0, 1):
                self.direction = (0, -1)
            elif controller_input.get("down_pressed") and self.direction != (0, -1):
                self.direction = (0, 1)
            elif controller_input.get("left_pressed") and self.direction != (1, 0):
                self.direction = (-1, 0)
            elif controller_input.get("right_pressed") and self.direction != (-1, 0):
                self.direction = (1, 0)
            
            # 加速控制
            self.boosting = controller_input.get("a_pressed", False)
            
            # 暫停控制
            if controller_input.get("start_pressed"):
                self.paused = not self.paused
                return {"game_over": self.game_over, "score": self.score, "paused": self.paused}
        
        # 設置當前速度
        self.current_speed = self.speed_boost if self.boosting else self.speed
        self.move_interval = 1.0 / self.current_speed
        
        # 檢查是否該移動蛇
        current_time = time.time()
        if current_time - self.last_move_time < self.move_interval:
            return {"game_over": self.game_over, "score": self.score}
        
        self.last_move_time = current_time
        
        # 移動蛇
        head_x, head_y = self.snake[0]
        new_head = (
            (head_x + self.direction[0]) % self.grid_width,
            (head_y + self.direction[1]) % self.grid_height
        )
        
        # 檢查碰撞到自己
        if new_head in self.snake:
            self.game_over = True
            if self.buzzer:
                self.buzzer.play_game_over_melody()
            return {"game_over": True, "score": self.score}
        
        # 添加新頭部
        self.snake.insert(0, new_head)
        
        # 檢查是否吃到食物
        if new_head == self.food:
            # 得分
            self.score += 1
            if self.buzzer:
                self.buzzer.play_tone("score")
            
            # 生成新食物
            self.food = self.generate_food()
            
            # 每 5 分增加一次速度
            if self.score % 5 == 0:
                self.speed += 1
                if self.buzzer:
                    self.buzzer.play_tone("level_up")
        else:
            # 沒吃到食物，移除尾巴
            self.snake.pop()
        
        return {"game_over": self.game_over, "score": self.score}
    
    def render(self, screen):
        """
        渲染遊戲畫面
        
        參數:
            screen: pygame 螢幕物件
        """
        # 清除螢幕
        screen.fill(self.BLACK)
        
        # 繪製食物
        food_rect = pygame.Rect(
            self.food[0] * self.block_size,
            self.food[1] * self.block_size,
            self.block_size,
            self.block_size
        )
        pygame.draw.rect(screen, self.RED, food_rect)
        
        # 繪製蛇
        for i, segment in enumerate(self.snake):
            # 頭部用不同顏色
            color = self.BLUE if i == 0 else self.GREEN
            
            segment_rect = pygame.Rect(
                segment[0] * self.block_size,
                segment[1] * self.block_size,
                self.block_size,
                self.block_size
            )
            pygame.draw.rect(screen, color, segment_rect)
        
        # 繪製分數
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"分數: {self.score}", True, self.WHITE)
        screen.blit(score_text, (10, 10))
        
        # 繪製速度
        speed_text = font.render(f"速度: {self.current_speed}", True, self.WHITE)
        screen.blit(speed_text, (10, 50))
        
        # 遊戲結束畫面
        if self.game_over:
            game_over_text = font.render("遊戲結束！按 Start 重新開始", True, self.WHITE)
            text_rect = game_over_text.get_rect(center=(self.width // 2, self.height // 2))
            screen.blit(game_over_text, text_rect)
            
            final_score_text = font.render(f"最終分數: {self.score}", True, self.WHITE)
            score_rect = final_score_text.get_rect(center=(self.width // 2, self.height // 2 + 40))
            screen.blit(final_score_text, score_rect)
        
        # 暫停畫面
        elif self.paused:
            pause_text = font.render("遊戲暫停", True, self.WHITE)
            text_rect = pause_text.get_rect(center=(self.width // 2, self.height // 2))
            screen.blit(pause_text, text_rect)
    
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
        pygame.display.set_caption("貪吃蛇遊戲測試")
        
        # 建立遊戲實例
        game = SnakeGame(screen_width, screen_height)
        
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# buzzer.py - 蜂鳴器控制模組

import time
import threading
import queue
import logging
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("RPi.GPIO 不可用，蜂鳴器將以模擬模式運行")

class BuzzerControl:
    """蜂鳴器控制類"""
    
    def __init__(self, pin=18):
        self.pin = pin
        self.enabled = True
        self.volume = 0.8  # 音量控制 (0.0 - 1.0)
        
        # 音樂佇列和播放控制
        self.music_queue = queue.Queue()
        self.is_playing = False
        self.stop_current = threading.Event()
        
        # 工作線程
        self.worker_thread = None
        self.running = True
        
        # 初始化GPIO
        if GPIO_AVAILABLE:
            try:
                GPIO.setup(self.pin, GPIO.OUT)
                self.pwm = GPIO.PWM(self.pin, 1000)  # 1000Hz 基準頻率
                logging.info(f"蜂鳴器初始化成功 (GPIO {self.pin})")
            except Exception as e:
                logging.error(f"蜂鳴器GPIO初始化失敗: {e}")
                GPIO_AVAILABLE = False
        
        # 啟動工作線程
        self._start_worker()
    
    def _start_worker(self):
        """啟動音樂播放工作線程"""
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
    
    def _worker_loop(self):
        """工作線程主循環"""
        while self.running:
            try:
                # 等待音樂任務
                task = self.music_queue.get(timeout=1.0)
                if task is None:  # 結束信號
                    break
                
                self.is_playing = True
                self.stop_current.clear()
                
                # 執行音樂任務
                if task['type'] == 'tone':
                    self._play_tone_internal(task['frequency'], task['duration'])
                elif task['type'] == 'melody':
                    self._play_melody_internal(task['notes'])
                elif task['type'] == 'sequence':
                    self._play_sequence_internal(task['sequence'])
                
                self.is_playing = False
                self.music_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"蜂鳴器工作線程錯誤: {e}")
                self.is_playing = False
    
    def _play_tone_internal(self, frequency, duration):
        """內部音調播放方法"""
        if not self.enabled or not GPIO_AVAILABLE:
            if not GPIO_AVAILABLE:
                logging.info(f"模擬播放音調: {frequency}Hz, {duration}s")
            time.sleep(duration)
            return
        
        try:
            if frequency > 0:
                self.pwm.ChangeFrequency(frequency)
                self.pwm.start(50 * self.volume)  # 占空比
            
            # 分段檢查停止信號
            elapsed = 0
            step = 0.05  # 50ms 步進
            while elapsed < duration and not self.stop_current.is_set():
                time.sleep(min(step, duration - elapsed))
                elapsed += step
            
            if frequency > 0:
                self.pwm.stop()
                
        except Exception as e:
            logging.error(f"播放音調失敗: {e}")
    
    def _play_melody_internal(self, notes):
        """內部旋律播放方法"""
        for note in notes:
            if self.stop_current.is_set():
                break
            
            if isinstance(note, tuple) and len(note) >= 2:
                frequency, duration = note[0], note[1]
                self._play_tone_internal(frequency, duration)
            elif isinstance(note, dict):
                frequency = note.get('frequency', 0)
                duration = note.get('duration', 0.5)
                self._play_tone_internal(frequency, duration)
    
    def _play_sequence_internal(self, sequence):
        """內部序列播放方法"""
        for item in sequence:
            if self.stop_current.is_set():
                break
            
            if item['type'] == 'tone':
                self._play_tone_internal(item['frequency'], item['duration'])
            elif item['type'] == 'pause':
                time.sleep(item['duration'])
    
    def play_tone(self, frequency=800, duration=0.5):
        """播放單一音調"""
        if not self.enabled:
            return
        
        task = {
            'type': 'tone',
            'frequency': frequency,
            'duration': duration
        }
        
        try:
            self.music_queue.put_nowait(task)
        except queue.Full:
            logging.warning("蜂鳴器音樂佇列已滿")
    
    def play_melody(self, notes):
        """播放旋律"""
        if not self.enabled:
            return
        
        task = {
            'type': 'melody',
            'notes': notes
        }
        
        try:
            self.music_queue.put_nowait(task)
        except queue.Full:
            logging.warning("蜂鳴器音樂佇列已滿")
    
    def play_startup_melody(self):
        """播放啟動音樂"""
        notes = [
            (440, 0.2),  # A4
            (554, 0.2),  # C#5
            (659, 0.2),  # E5
            (880, 0.4),  # A5
        ]
        self.play_melody(notes)
    
    def play_win_melody(self):
        """播放勝利音樂"""
        notes = [
            (523, 0.2),  # C5
            (659, 0.2),  # E5
            (784, 0.2),  # G5
            (1047, 0.6), # C6
        ]
        self.play_melody(notes)
    
    def play_game_over_melody(self):
        """播放遊戲結束音樂"""
        notes = [
            (330, 0.4),  # E4
            (294, 0.4),  # D4
            (262, 0.4),  # C4
            (196, 0.8),  # G3
        ]
        self.play_melody(notes)
    
    def play_victory_fanfare(self):
        """播放勝利號角"""
        notes = [
            (523, 0.15),  # C5
            (523, 0.15),  # C5
            (523, 0.15),  # C5
            (523, 0.45),  # C5
            (415, 0.45),  # G#4
            (466, 0.45),  # A#4
            (523, 0.15),  # C5
            (466, 0.15),  # A#4
            (523, 0.6),   # C5
        ]
        self.play_melody(notes)
    
    def stop_all(self):
        """停止所有音樂播放"""
        self.stop_current.set()
        
        # 清空佇列
        while not self.music_queue.empty():
            try:
                self.music_queue.get_nowait()
                self.music_queue.task_done()
            except queue.Empty:
                break
    
    def set_volume(self, volume):
        """設置音量 (0.0 - 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
    
    def set_enabled(self, enabled):
        """啟用/禁用蜂鳴器"""
        self.enabled = enabled
        if not enabled:
            self.stop_all()
    
    def wait_for_completion(self, timeout=None):
        """等待當前播放完成"""
        if self.is_playing:
            start_time = time.time()
            while self.is_playing:
                time.sleep(0.1)
                if timeout and (time.time() - start_time) > timeout:
                    break
    
    def cleanup(self):
        """清理資源"""
        logging.info("蜂鳴器清理開始...")
        
        self.running = False
        self.stop_all()
        
        # 結束工作線程
        if self.worker_thread:
            self.music_queue.put(None)  # 發送結束信號
            self.worker_thread.join(timeout=2)
        
        # 清理GPIO
        if GPIO_AVAILABLE:
            try:
                if hasattr(self, 'pwm'):
                    self.pwm.stop()
            except Exception as e:
                logging.error(f"蜂鳴器PWM清理失敗: {e}")
        
        logging.info("蜂鳴器清理完成")

# 測試代碼
if __name__ == "__main__":
    try:
        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
        
        buzzer = BuzzerControl(pin=18)
        
        print("測試蜂鳴器...")
        
        # 測試基本音調
        print("播放基本音調...")
        buzzer.play_tone(800, 1.0)
        buzzer.wait_for_completion()
        
        # 測試啟動音樂
        print("播放啟動音樂...")
        buzzer.play_startup_melody()
        buzzer.wait_for_completion()
        
        # 測試勝利音樂
        print("播放勝利音樂...")
        buzzer.play_win_melody()
        buzzer.wait_for_completion()
        
        print("測試完成")
        
    except KeyboardInterrupt:
        print("測試被中斷")
    except Exception as e:
        print(f"測試錯誤: {e}")
    finally:
        if 'buzzer' in locals():
            buzzer.cleanup()
        if GPIO_AVAILABLE:
            GPIO.cleanup()

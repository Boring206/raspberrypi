#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# power_button_fixed.py - 修正版遊戲控制按鈕程式

import RPi.GPIO as GPIO
import time
import threading
import queue
from datetime import datetime

# GPIO 設定
POWER_BUTTON_PIN = 22
HOLD_DURATION = 3.0      # 長按持續時間（秒）
SHORT_PRESS_MIN = 0.05   # 短按最小時間（秒）
DEBOUNCE_TIME = 0.02     # 去彈跳時間（秒）

class GameControlButton:
    """遊戲控制按鈕類別"""
    
    def __init__(self, main_console_instance=None):
        self.main_console = main_console_instance
        self.running = False
        self.monitor_thread = None
        
        # 按鈕狀態追蹤
        self.last_press_time = 0
        self.button_pressed_duration = 0
        self.was_pressed = False
        self.last_button_state = GPIO.HIGH  # 預設狀態為 HIGH（未按下）
        
        # 事件計數器
        self.short_press_count = 0
        self.long_press_count = 0
        
        # 事件佇列，用於與主程式通訊
        self.event_queue = queue.Queue()
        
        # 設定 GPIO
        self.setup_gpio()
    
    def setup_gpio(self):
        """設定 GPIO - 修正版本"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # 修正：使用上拉電阻，按鈕一端接 GPIO，另一端接 GND
            GPIO.setup(POWER_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            print(f"✓ 遊戲控制按鈕 GPIO {POWER_BUTTON_PIN} 設定完成")
            print("📋 正確接線方式：")
            print(f"  • 按鈕一端 → GPIO {POWER_BUTTON_PIN} (Pin 15)")
            print(f"  • 按鈕另一端 → GND (任一 GND 腳位)")
            print("📍 邏輯：未按下=HIGH，按下=LOW")
            return True
            
        except Exception as e:
            print(f"✗ GPIO 設定失敗: {e}")
            return False
    
    def start_monitoring(self):
        """開始監控按鈕"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_button, daemon=True)
        self.monitor_thread.start()
        print("🎮 遊戲控制按鈕監控已啟動")
    
    def stop_monitoring(self):
        """停止監控按鈕"""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
        print("⏹️ 遊戲控制按鈕監控已停止")
    
    def _monitor_button(self):
        """監控按鈕狀態（在背景執行緒中執行）"""
        print(f"🔍 開始監控遊戲控制按鈕... (GPIO {POWER_BUTTON_PIN})")
        print("📍 正常狀態：未按下=HIGH，按下=LOW")
        
        while self.running:
            try:
                time.sleep(DEBOUNCE_TIME)
                button_state = GPIO.input(POWER_BUTTON_PIN)
                current_time = time.time()
                
                # 檢測按鈕按下（HIGH → LOW）
                if button_state == GPIO.LOW and self.last_button_state == GPIO.HIGH:
                    self._handle_button_press(current_time)
                
                # 檢測按鈕釋放（LOW → HIGH）
                elif button_state == GPIO.HIGH and self.last_button_state == GPIO.LOW:
                    self._handle_button_release(current_time)
                
                # 更新按鈕持續時間（按下時為 LOW）
                if button_state == GPIO.LOW and self.was_pressed:
                    self.button_pressed_duration = current_time - self.last_press_time
                    
                    # 檢查長按
                    if self.button_pressed_duration >= HOLD_DURATION:
                        self._handle_long_press()
                        # 等待按鈕釋放以避免重複觸發
                        while GPIO.input(POWER_BUTTON_PIN) == GPIO.LOW and self.running:
                            time.sleep(0.1)
                
                self.last_button_state = button_state
                
            except Exception as e:
                print(f"按鈕監控錯誤: {e}")
                time.sleep(0.1)
    
    def _handle_button_press(self, current_time):
        """處理按鈕按下事件"""
        self.was_pressed = True
        self.last_press_time = current_time
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] 🔴 遊戲控制按鈕按下 (LOW)")
    
    def _handle_button_release(self, current_time):
        """處理按鈕釋放事件"""
        if not self.was_pressed:
            return
        
        press_duration = current_time - self.last_press_time
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 判斷是短按還是長按（如果還沒有觸發長按事件）
        if press_duration >= SHORT_PRESS_MIN and press_duration < HOLD_DURATION:
            self._handle_short_press()
            print(f"[{timestamp}] 🟢 按鈕釋放 (HIGH) - 短按 ({press_duration:.2f}s)")
        else:
            print(f"[{timestamp}] 🟢 按鈕釋放 (HIGH) ({press_duration:.2f}s)")
        
        # 重設狀態
        self.was_pressed = False
        self.button_pressed_duration = 0
        self.last_press_time = 0
    
    def _handle_short_press(self):
        """處理短按事件 - 暫停/繼續遊戲"""
        self.short_press_count += 1
        print(f"📝 短按檢測 (第 {self.short_press_count} 次) - 暫停/繼續遊戲")
        
        # 將事件加入佇列
        self.event_queue.put({
            'type': 'short_press',
            'action': 'toggle_pause',
            'timestamp': time.time()
        })
        
        # 如果有主控制台實例，直接調用相關方法
        if self.main_console:
            try:
                self._toggle_game_pause()
            except Exception as e:
                print(f"切換遊戲暫停狀態時發生錯誤: {e}")
    
    def _handle_long_press(self):
        """處理長按事件 - 返回主選單"""
        self.long_press_count += 1
        print(f"📝 長按檢測 (第 {self.long_press_count} 次) - 返回主選單")
        
        # 將事件加入佇列
        self.event_queue.put({
            'type': 'long_press',
            'action': 'return_to_menu',
            'timestamp': time.time()
        })
        
        # 如果有主控制台實例，直接調用相關方法
        if self.main_console:
            try:
                self._return_to_main_menu()
            except Exception as e:
                print(f"返回主選單時發生錯誤: {e}")
    
    def _toggle_game_pause(self):
        """切換遊戲暫停狀態"""
        if not self.main_console:
            return
        
        if self.main_console.state == "GAME" and self.main_console.current_game:
            # 如果遊戲有暫停功能
            if hasattr(self.main_console.current_game, 'paused'):
                current_pause_state = getattr(self.main_console.current_game, 'paused', False)
                self.main_console.current_game.paused = not current_pause_state
                
                if self.main_console.current_game.paused:
                    print("⏸️ 遊戲已暫停")
                    # 設定交通燈為黃色表示暫停
                    if self.main_console.traffic_light:
                        self.main_console.traffic_light.yellow_on()
                else:
                    print("▶️ 遊戲已繼續")
                    # 設定交通燈為綠色表示運行
                    if self.main_console.traffic_light:
                        self.main_console.traffic_light.green_on()
            else:
                print("⚠️ 當前遊戲不支援暫停功能")
        else:
            print("⚠️ 沒有正在運行的遊戲")
    
    def _return_to_main_menu(self):
        """返回主選單"""
        if not self.main_console:
            return
        
        if self.main_console.state == "GAME":
            print("🏠 正在返回主選單...")
            
            # 結束當前遊戲
            if self.main_console.current_game:
                try:
                    if hasattr(self.main_console.current_game, 'cleanup'):
                        self.main_console.current_game.cleanup()
                except Exception as e:
                    print(f"清理遊戲時發生錯誤: {e}")
            
            # 重設狀態
            self.main_console.current_game = None
            self.main_console.state = "MENU"
            self.main_console.current_selection = 0
            
            # 更新SPI螢幕顯示
            if self.main_console.spi_screen:
                try:
                    self.main_console.spi_screen.display_menu(
                        self.main_console.games,
                        self.main_console.current_selection
                    )
                except Exception as e:
                    print(f"更新SPI螢幕時發生錯誤: {e}")
            
            # 設定交通燈為紅色表示在選單
            if self.main_console.traffic_light:
                self.main_console.traffic_light.red_on()
            
            # 播放返回音效
            if self.main_console.buzzer:
                try:
                    self.main_console.buzzer.play_tone(440, 0.1)  # A4 音符
                    time.sleep(0.05)
                    self.main_console.buzzer.play_tone(330, 0.1)  # E4 音符
                except Exception as e:
                    print(f"播放音效時發生錯誤: {e}")
            
            print("✅ 已返回主選單")
        else:
            print("⚠️ 已經在主選單中")
    
    def get_pending_events(self):
        """獲取待處理的事件"""
        events = []
        while not self.event_queue.empty():
            try:
                events.append(self.event_queue.get_nowait())
            except queue.Empty:
                break
        return events
    
    def get_status(self):
        """獲取按鈕狀態資訊"""
        current_state = GPIO.input(POWER_BUTTON_PIN) if self.running else None
        return {
            'running': self.running,
            'short_press_count': self.short_press_count,
            'long_press_count': self.long_press_count,
            'current_gpio_state': 'HIGH' if current_state == GPIO.HIGH else 'LOW' if current_state == GPIO.LOW else 'UNKNOWN',
            'is_pressed': current_state == GPIO.LOW if self.running else False,  # LOW 表示按下
            'gpio_pin': POWER_BUTTON_PIN
        }
    
    def cleanup(self):
        """清理資源"""
        print("🧹 正在清理遊戲控制按鈕資源...")
        
        self.stop_monitoring()
        
        try:
            GPIO.cleanup([POWER_BUTTON_PIN])
            print("✓ GPIO 清理完成")
        except Exception as e:
            print(f"⚠️ GPIO 清理時發生警告: {e}")
        
        print(f"📊 按鈕使用統計: 短按 {self.short_press_count} 次, 長按 {self.long_press_count} 次")
        print("✅ 遊戲控制按鈕清理完成")


def test_button_wiring():
    """測試按鈕接線診斷程式"""
    print("🔧 按鈕接線診斷程式")
    print("=" * 50)
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        print("📋 測試不同的接線配置...")
        
        # 測試配置 1：上拉電阻 + 按鈕接 GND
        print("\n🔍 測試配置 1：上拉電阻 + 按鈕接 GND")
        print("  接線：一端 → GPIO 22，另一端 → GND")
        GPIO.setup(POWER_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        for i in range(10):
            state = GPIO.input(POWER_BUTTON_PIN)
            status = "HIGH (未按下)" if state == GPIO.HIGH else "LOW (按下)"
            print(f"\r  當前狀態: {status}     ", end='', flush=True)
            time.sleep(0.5)
        
        print(f"\n  ✓ 配置 1 測試完成")
        print(f"    正常情況：未按下=HIGH，按下=LOW")
        
        # 測試配置 2：下拉電阻 + 按鈕接 3.3V（您目前的錯誤配置）
        print("\n🔍 測試配置 2：下拉電阻 + 按鈕接 3.3V")
        print("  接線：一端 → GPIO 22，另一端 → 3.3V")
        GPIO.setup(POWER_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        for i in range(10):
            state = GPIO.input(POWER_BUTTON_PIN)
            status = "HIGH (按下)" if state == GPIO.HIGH else "LOW (未按下)"
            print(f"\r  當前狀態: {status}     ", end='', flush=True)
            time.sleep(0.5)
        
        print(f"\n  ✓ 配置 2 測試完成")
        print(f"    正常情況：未按下=LOW，按下=HIGH")
        
        # 建議
        print("\n💡 建議解決方案：")
        current_state = GPIO.input(POWER_BUTTON_PIN)
        if current_state == GPIO.HIGH:
            print("  🔴 您目前可能使用錯誤的接線方式！")
            print("  📝 請選擇以下修正方案之一：")
            print("\n  方案 A：修改接線（推薦）")
            print("    • 將按鈕另一端從 3.3V 改接到 GND")
            print("    • 使用上拉電阻配置")
            print("    • 邏輯：未按下=HIGH，按下=LOW")
            
            print("\n  方案 B：修改程式碼")
            print("    • 保持目前接線（一端接 GPIO 22，另一端接 3.3V）")
            print("    • 程式碼改用下拉電阻")
            print("    • 邏輯：未按下=LOW，按下=HIGH")
        else:
            print("  ✅ 接線配置正確！")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
    finally:
        try:
            GPIO.cleanup([POWER_BUTTON_PIN])
        except:
            pass


def run_corrected_test():
    """執行修正版按鈕測試"""
    print("🎮 修正版按鈕測試程式")
    print("=" * 50)
    
    try:
        button = GameControlButton()
        button.start_monitoring()
        
        print("✅ 按鈕監控已啟動")
        print("📋 請測試按鈕功能：")
        print("  • 短按：應該檢測到暫停/繼續功能")
        print("  • 長按 3 秒：應該檢測到返回選單功能")
        print("  • 按 Ctrl+C 停止測試")
        print()
        
        while True:
            time.sleep(1)
            
            # 檢查待處理事件
            events = button.get_pending_events()
            for event in events:
                print(f"🔔 事件觸發: {event['action']} ({event['type']})")
            
            # 顯示當前狀態
            status = button.get_status()
            if status['current_gpio_state']:
                print(f"\r📊 GPIO 狀態: {status['current_gpio_state']} | "
                      f"按下: {'是' if status['is_pressed'] else '否'} | "
                      f"短按: {status['short_press_count']} | "
                      f"長按: {status['long_press_count']}     ", end='', flush=True)
    
    except KeyboardInterrupt:
        print("\n\n⏹️ 測試停止")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
    finally:
        if 'button' in locals():
            button.cleanup()
        print("\n🧹 測試程式結束")


def main():
    """主程式選單"""
    print("🔧 按鈕問題診斷與修正工具")
    print("=" * 50)
    
    while True:
        print("\n請選擇:")
        print("1. 接線診斷測試")
        print("2. 修正版按鈕功能測試")
        print("3. 查看解決方案建議")
        print("4. 退出")
        
        try:
            choice = input("\n請輸入選項 (1-4): ").strip()
            
            if choice == '1':
                test_button_wiring()
            elif choice == '2':
                run_corrected_test()
            elif choice == '3':
                show_solution_guide()
            elif choice == '4':
                print("👋 再見！")
                break
            else:
                print("❌ 無效選項，請重新選擇")
                
        except KeyboardInterrupt:
            print("\n\n👋 程式被中斷，再見！")
            break
        except Exception as e:
            print(f"❌ 發生錯誤: {e}")


def show_solution_guide():
    """顯示解決方案指南"""
    print("\n📋 按鈕問題解決方案指南")
    print("=" * 50)
    
    print("🔴 問題描述：")
    print("  按鈕在沒有按下時一直顯示 HIGH (3.3V)")
    
    print("\n🔍 原因分析：")
    print("  您目前的接線配置有誤：")
    print("  ❌ 錯誤：一端接 GPIO 22，另一端接 3.3V + 使用下拉電阻")
    print("  📝 結果：GPIO 持續被拉到 HIGH，無法檢測按鈕變化")
    
    print("\n💡 解決方案（選擇其一）：")
    
    print("\n  🏆 方案 A：修改接線（推薦）")
    print("    1. 將按鈕另一端從 3.3V 改接到 GND")
    print("    2. 程式碼使用上拉電阻：GPIO.PUD_UP")
    print("    3. 邏輯：未按下=HIGH，按下=LOW")
    print("    4. 優點：標準做法，穩定可靠")
    
    print("\n  🔧 方案 B：修改程式碼")
    print("    1. 保持目前接線（一端接 GPIO 22，另一端接 3.3V）")
    print("    2. 程式碼改用下拉電阻：GPIO.PUD_DOWN") 
    print("    3. 邏輯：未按下=LOW，按下=HIGH")
    print("    4. 缺點：容易受雜訊干擾")
    
    print("\n📝 建議採用方案 A，因為：")
    print("  • 更穩定，抗雜訊能力強")
    print("  • 符合標準按鈕接線慣例")
    print("  • 不需要修改大量程式碼")
    
    print("\n🔌 正確接線圖：")
    print("  樹莓派           按鈕")
    print("  ┌─────────┐     ┌────┐")
    print("  │GPIO 22  ├─────┤ 1  │")
    print("  │         │     │    │")
    print("  │GND      ├─────┤ 2  │") 
    print("  └─────────┘     └────┘")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# power_button.py - 監控電源按鈕以執行關機

import RPi.GPIO as GPIO
import time
import os
import signal

# BCM 腳位編號
POWER_BUTTON_PIN = 4  # 假設按鈕接到 GPIO 4
HOLD_DURATION = 3     # 長按多少秒觸發關機
DEBOUNCE_TIME = 0.05  # 按鈕去彈跳時間 (秒)

# 全域變數用於信號處理
shutting_down_flag = False

def signal_handler(sig, frame):
    """處理終止信號，確保 GPIO 清理"""
    global shutting_down_flag
    if not shutting_down_flag: # 避免在關機過程中重複清理
        print("接收到終止信號，正在清理 power_button.py...")
        GPIO.cleanup([POWER_BUTTON_PIN]) # 只清理這個腳本使用的腳位
    print("power_button.py 已停止。")
    exit(0)

def setup_power_button():
    """設定電源按鈕的 GPIO"""
    GPIO.setmode(GPIO.BCM)  # 使用 BCM 編號模式
    GPIO.setwarnings(False) # 禁用警告
    GPIO.setup(POWER_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) # 使用上拉電阻，按鈕按下時為 LOW
    print(f"電源按鈕 (GPIO {POWER_BUTTON_PIN}) 初始化完成。使用上拉電阻。")

def perform_shutdown_tasks(main_pid=None):
    """執行關機前的任務 (如果需要從主程式觸發)"""
    global shutting_down_flag
    if shutting_down_flag:
        return

    shutting_down_flag = True
    print("準備執行關機...")

    # 嘗試通知主程式進行清理 (如果 main_pid 有效)
    # 這部分比較複雜，因為跨行程通訊或主程式需要設計接收機制
    # 簡化做法：主程式在 finally 中自行清理
    if main_pid:
        try:
            print(f"嘗試發送 SIGUSR1 信號給主程式 (PID: {main_pid}) 以進行清理...")
            # os.kill(main_pid, signal.SIGUSR1) # 主程式需要設定 SIGUSR1 處理器
        except ProcessLookupError:
            print(f"主程式 (PID: {main_pid}) 未找到。")
        except Exception as e:
            print(f"發送信號給主程式時出錯: {e}")
    
    # 實際的關機指令
    print("執行 sudo shutdown -h now")
    # 在實際部署時，確保此腳本有權限執行 shutdown，或者透過其他機制
    # 為了測試，可以先註解掉下面這行，用 print 替代
    os.system("sudo shutdown -h now")
    # print("模擬關機: sudo shutdown -h now")

def monitor_power_button_loop(main_process_pid_str=None):
    """監控電源按鈕的主循環"""
    print(f"開始監控電源按鈕 (GPIO {POWER_BUTTON_PIN})... 長按 {HOLD_DURATION} 秒關機。")
    if main_process_pid_str:
        print(f"將嘗試通知主程式 PID: {main_process_pid_str}")
        
    main_pid = None
    if main_process_pid_str:
        try:
            main_pid = int(main_process_pid_str)
        except ValueError:
            print(f"無效的主程式 PID: {main_process_pid_str}")

    last_press_time = 0
    button_pressed_duration = 0
    was_pressed = False

    while not shutting_down_flag:
        time.sleep(DEBOUNCE_TIME) # 稍微延遲，減少 CPU 使用並做基本去抖
        button_state = GPIO.input(POWER_BUTTON_PIN)

        if button_state == GPIO.LOW: # 按鈕被按下 (因為是上拉電阻)
            if not was_pressed: # 剛按下
                was_pressed = True
                last_press_time = time.time()
                print(f"電源按鈕在 {time.strftime('%Y-%m-%d %H:%M:%S')} 被按下。")
            
            button_pressed_duration = time.time() - last_press_time
            if button_pressed_duration >= HOLD_DURATION:
                print(f"電源按鈕已長按 {button_pressed_duration:.2f} 秒。")
                perform_shutdown_tasks(main_pid)
                break # 跳出循環，腳本即將結束或已被關機命令終止
        else: # 按鈕未被按下 (或已釋放)
            if was_pressed: # 剛被釋放
                print(f"電源按鈕在 {time.strftime('%Y-%m-%d %H:%M:%S')} 被釋放 (持續時間: {button_pressed_duration:.2f} 秒)。")
                was_pressed = False
                button_pressed_duration = 0 # 重置持續時間
                last_press_time = 0 # 重置開始時間
    
    if not shutting_down_flag: # 如果是因為其他原因跳出循環
        print("電源按鈕監控循環結束。")
        GPIO.cleanup([POWER_BUTTON_PIN])


if __name__ == "__main__":
    # 設定信號處理器
    signal.signal(signal.SIGINT, signal_handler)  # 處理 Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler) # 處理 kill 命令

    main_pid_arg = None
    if len(os.sys.argv) > 1:
        main_pid_arg = os.sys.argv[1]

    setup_power_button()
    try:
        monitor_power_button_loop(main_pid_arg)
    except Exception as e:
        print(f"power_button.py 執行時發生錯誤: {e}")
    finally:
        # 確保即使發生異常也嘗試清理 (雖然 signal_handler 應該會處理多數情況)
        if not shutting_down_flag:
            GPIO.cleanup([POWER_BUTTON_PIN])
        print("power_button.py 最終清理完成。")
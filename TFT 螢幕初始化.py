#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# tft_diagnosis.py - 2.8寸TFT螢幕完整診斷程式

import RPi.GPIO as GPIO
import time
import sys
import os

# TFT螢幕接線定義
SPI_DC = 25       # Data/Command腳位
SPI_RST = 24      # Reset腳位
SPI_CS = 8        # Chip Select腳位
SPI_LED = 27      # 背光控制腳位
SPI_MOSI = 10     # SPI數據腳位
SPI_SCLK = 11     # SPI時鐘腳位

class TFTDiagnosticTool:
    """TFT螢幕診斷工具"""
    
    def __init__(self):
        self.test_results = {}
        
    def run_complete_diagnosis(self):
        """執行完整診斷"""
        print("🔍 TFT螢幕完整診斷程式")
        print("=" * 60)
        print("此程式將檢測螢幕硬體、接線、軟體配置等各項問題")
        print("=" * 60)
        
        # 設定GPIO
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            print("✓ GPIO模式設定成功")
        except Exception as e:
            print(f"✗ GPIO設定失敗: {e}")
            return False
        
        # 執行各項測試
        self.test_spi_interface()
        self.test_gpio_pins()
        self.test_backlight()
        self.test_reset_functionality()
        self.test_power_supply()
        self.test_software_packages()
        self.test_device_initialization()
        
        # 顯示診斷結果
        self.display_diagnosis_results()
        
        # 建議修復方案
        self.suggest_repair_actions()
        
        # 清理GPIO
        GPIO.cleanup()
        
    def test_spi_interface(self):
        """測試SPI接口"""
        print("\n📡 測試SPI接口...")
        
        try:
            # 檢查SPI是否啟用
            spi_enabled = os.path.exists('/dev/spidev0.0')
            if spi_enabled:
                print("  ✓ SPI接口已啟用")
                self.test_results['spi_enabled'] = True
            else:
                print("  ✗ SPI接口未啟用")
                self.test_results['spi_enabled'] = False
                print("    執行: sudo raspi-config -> Interface Options -> SPI -> Enable")
            
            # 檢查SPI模組
            with open('/proc/modules', 'r') as f:
                modules = f.read()
                if 'spi_bcm2835' in modules:
                    print("  ✓ SPI驅動模組已載入")
                    self.test_results['spi_driver'] = True
                else:
                    print("  ✗ SPI驅動模組未載入")
                    self.test_results['spi_driver'] = False
            
        except Exception as e:
            print(f"  ✗ SPI測試失敗: {e}")
            self.test_results['spi_enabled'] = False
            self.test_results['spi_driver'] = False
    
    def test_gpio_pins(self):
        """測試GPIO腳位連接"""
        print("\n🔌 測試GPIO腳位連接...")
        
        gpio_pins = {
            'DC': SPI_DC,
            'RST': SPI_RST, 
            'CS': SPI_CS,
            'LED': SPI_LED,
            'MOSI': SPI_MOSI,
            'SCLK': SPI_SCLK
        }
        
        for pin_name, pin_number in gpio_pins.items():
            try:
                GPIO.setup(pin_number, GPIO.OUT)
                GPIO.output(pin_number, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(pin_number, GPIO.LOW)
                print(f"  ✓ GPIO {pin_number} ({pin_name}) 訊號正常")
                self.test_results[f'gpio_{pin_name.lower()}'] = True
            except Exception as e:
                print(f"  ✗ GPIO {pin_number} ({pin_name}) 測試失敗: {e}")
                self.test_results[f'gpio_{pin_name.lower()}'] = False
    
    def test_backlight(self):
        """測試背光功能"""
        print("\n💡 測試背光功能...")
        
        try:
            GPIO.setup(SPI_LED, GPIO.OUT)
            
            # 測試背光開關
            print("  📝 測試背光開啟...")
            GPIO.output(SPI_LED, GPIO.HIGH)
            time.sleep(1)
            
            print("  📝 測試背光關閉...")
            GPIO.output(SPI_LED, GPIO.LOW)
            time.sleep(1)
            
            # 測試PWM調光
            print("  📝 測試PWM調光...")
            pwm = GPIO.PWM(SPI_LED, 1000)
            for brightness in [0, 25, 50, 75, 100, 50]:
                pwm.start(brightness)
                time.sleep(0.5)
            pwm.stop()
            
            GPIO.output(SPI_LED, GPIO.HIGH)  # 恢復背光
            print("  ✓ 背光功能測試完成")
            print("  📋 請觀察螢幕是否有亮度變化")
            
            response = input("  ❓ 背光是否正常工作？(y/n): ").lower()
            self.test_results['backlight'] = response == 'y'
            
        except Exception as e:
            print(f"  ✗ 背光測試失敗: {e}")
            self.test_results['backlight'] = False
    
    def test_reset_functionality(self):
        """測試重置功能"""
        print("\n🔄 測試重置功能...")
        
        try:
            GPIO.setup(SPI_RST, GPIO.OUT)
            
            # 重置序列
            print("  📝 執行重置序列...")
            GPIO.output(SPI_RST, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(SPI_RST, GPIO.LOW)
            time.sleep(0.1)
            GPIO.output(SPI_RST, GPIO.HIGH)
            time.sleep(0.1)
            
            print("  ✓ 重置序列完成")
            self.test_results['reset'] = True
            
        except Exception as e:
            print(f"  ✗ 重置測試失敗: {e}")
            self.test_results['reset'] = False
    
    def test_power_supply(self):
        """測試電源供應"""
        print("\n⚡ 檢查電源供應...")
        
        try:
            # 讀取系統電壓資訊
            with open('/sys/class/hwmon/hwmon0/in1_input', 'r') as f:
                voltage_raw = int(f.read().strip())
                voltage = voltage_raw / 1000.0  # 轉換為伏特
                
                if voltage >= 3.2:
                    print(f"  ✓ 系統電壓正常: {voltage:.2f}V")
                    self.test_results['power_voltage'] = True
                else:
                    print(f"  ⚠️ 系統電壓偏低: {voltage:.2f}V (建議 > 3.2V)")
                    self.test_results['power_voltage'] = False
                    
        except Exception as e:
            print(f"  ⚠️ 無法讀取電壓資訊: {e}")
            self.test_results['power_voltage'] = None
        
        # 檢查電源適配器建議
        print("  📋 電源供應檢查清單:")
        print("    • 使用至少3A的5V電源適配器")
        print("    • 確保電源線品質良好")
        print("    • 檢查USB-C或Micro USB接頭是否緊密")
    
    def test_software_packages(self):
        """測試軟體套件"""
        print("\n📦 檢查軟體套件...")
        
        required_packages = [
            ('luma.lcd', 'luma-lcd'),
            ('luma.core', 'luma-core'),  
            ('PIL', 'pillow'),
            ('RPi.GPIO', 'rpi-gpio')
        ]
        
        for package_name, pip_name in required_packages:
            try:
                __import__(package_name)
                print(f"  ✓ {package_name} 已安裝")
                self.test_results[f'package_{package_name}'] = True
            except ImportError:
                print(f"  ✗ {package_name} 未安裝")
                print(f"    安裝指令: sudo pip3 install {pip_name}")
                self.test_results[f'package_{package_name}'] = False
    
    def test_device_initialization(self):
        """測試裝置初始化"""
        print("\n🖥️ 測試裝置初始化...")
        
        try:
            from luma.core.interface.serial import spi
            from luma.lcd.device import ili9341
            
            # 建立SPI連接
            serial = spi(port=0, device=0, gpio_DC=SPI_DC, gpio_RST=SPI_RST)
            
            # 嘗試初始化裝置
            device = ili9341(serial, width=240, height=320, rotate=0)
            
            print("  ✓ 裝置初始化成功！")
            self.test_results['device_init'] = True
            
            # 測試基本繪圖
            from luma.core.render import canvas
            with canvas(device) as draw:
                draw.rectangle(device.bounding_box, outline="white", fill="black")
                draw.text((10, 10), "診斷測試", fill="white")
            
            print("  ✓ 基本繪圖測試成功！")
            self.test_results['basic_drawing'] = True
            
            time.sleep(2)
            
        except ImportError as e:
            print(f"  ✗ 套件導入失敗: {e}")
            self.test_results['device_init'] = False
            self.test_results['basic_drawing'] = False
        except Exception as e:
            print(f"  ✗ 裝置初始化失敗: {e}")
            self.test_results['device_init'] = False
            self.test_results['basic_drawing'] = False
            print(f"    錯誤詳情: {str(e)}")
    
    def display_diagnosis_results(self):
        """顯示診斷結果"""
        print("\n" + "=" * 60)
        print("📊 診斷結果摘要")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for v in self.test_results.values() if v is True)
        failed_tests = sum(1 for v in self.test_results.values() if v is False)
        unknown_tests = sum(1 for v in self.test_results.values() if v is None)
        
        print(f"總測試項目: {total_tests}")
        print(f"通過測試: {passed_tests} ✓")
        print(f"失敗測試: {failed_tests} ✗")
        print(f"無法確定: {unknown_tests} ❓")
        
        print("\n詳細結果:")
        for test_name, result in self.test_results.items():
            if result is True:
                status = "✓ 通過"
            elif result is False:
                status = "✗ 失敗"
            else:
                status = "❓ 未知"
            print(f"  {test_name}: {status}")
    
    def suggest_repair_actions(self):
        """建議修復方案"""
        print("\n" + "=" * 60)
        print("🔧 修復建議")
        print("=" * 60)
        
        # 根據測試結果提供建議
        if not self.test_results.get('spi_enabled', True):
            print("🔨 SPI問題修復:")
            print("  1. 執行 sudo raspi-config")
            print("  2. 選擇 Interface Options → SPI → Enable")
            print("  3. 重新啟動樹莓派")
            print()
        
        if not self.test_results.get('device_init', True):
            print("🔨 螢幕初始化問題修復:")
            print("  1. 檢查接線是否正確")
            print("  2. 確認螢幕型號是否為ILI9341")
            print("  3. 嘗試不同的螢幕")
            print("  4. 檢查螢幕是否物理損壞")
            print()
        
        failed_gpio = [k for k, v in self.test_results.items() 
                      if k.startswith('gpio_') and v is False]
        if failed_gpio:
            print("🔨 GPIO連接問題修復:")
            print("  1. 檢查杜邦線連接")
            print("  2. 確認GPIO腳位編號正確")
            print("  3. 測試用萬用電表檢查導通性")
            print("  4. 更換杜邦線或麵包板")
            print()
        
        if not self.test_results.get('backlight', True):
            print("🔨 背光問題修復:")
            print("  1. 檢查背光腳位接線")
            print("  2. 確認螢幕電源供應充足")
            print("  3. 測試背光LED是否燒毀")
            print()
        
        # 螢幕損壞判斷
        critical_failures = [
            'device_init',
            'basic_drawing',
            'backlight'
        ]
        
        critical_failed = sum(1 for test in critical_failures 
                            if not self.test_results.get(test, True))
        
        if critical_failed >= 2:
            print("⚠️ 螢幕可能已損壞!")
            print("建議:")
            print("  1. 嘗試使用已知正常的螢幕進行測試")
            print("  2. 在另一個樹莓派上測試此螢幕")
            print("  3. 考慮更換新的螢幕模組")
            print("  4. 檢查是否有物理損傷(裂痕、燒毀等)")
        else:
            print("✅ 螢幕硬體可能正常")
            print("問題可能出在:")
            print("  1. 接線錯誤")
            print("  2. 軟體配置")
            print("  3. 電源供應不足")
            print("  4. GPIO腳位衝突")


def run_quick_test():
    """快速測試"""
    print("⚡ 快速螢幕測試")
    print("-" * 30)
    
    try:
        from luma.core.interface.serial import spi
        from luma.lcd.device import ili9341
        from luma.core.render import canvas
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SPI_LED, GPIO.OUT)
        GPIO.output(SPI_LED, GPIO.HIGH)
        
        serial = spi(port=0, device=0, gpio_DC=SPI_DC, gpio_RST=SPI_RST)
        device = ili9341(serial, width=240, height=320)
        
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="red")
            draw.text((50, 150), "螢幕正常!", fill="white")
        
        print("✅ 螢幕工作正常!")
        time.sleep(3)
        
    except Exception as e:
        print(f"❌ 螢幕測試失敗: {e}")
    finally:
        try:
            GPIO.output(SPI_LED, GPIO.LOW)
            GPIO.cleanup()
        except:
            pass


def main():
    """主程式"""
    print("TFT螢幕診斷工具")
    print("=" * 30)
    
    while True:
        print("\n請選擇:")
        print("1. 完整診斷")
        print("2. 快速測試")
        print("3. 退出")
        
        choice = input("\n請輸入選項 (1-3): ").strip()
        
        if choice == '1':
            diagnostic = TFTDiagnosticTool()
            diagnostic.run_complete_diagnosis()
            break
        elif choice == '2':
            run_quick_test()
            break
        elif choice == '3':
            print("👋 再見!")
            break
        else:
            print("❌ 無效選項")


if __name__ == "__main__":
    main()
# 樹莓派多功能遊戲機
**版本： 1.0.1**

## 專案總覽
本專案將樹莓派打造成一台多功能復古風格遊戲機。它包含多款經典遊戲，支援多種輸入方式（Xbox 控制器和矩陣鍵盤），主要遊戲畫面透過 HDMI 輸出，並使用一個 SPI TFT 小螢幕顯示選單和輔助資訊。此遊戲機還配備了蜂鳴器提供聲音回饋，交通號誌燈 LED 模組用於狀態指示，以及一個專用電源按鈕以安全關機。

## 主要功能
### 多款遊戲： 內建 9 款經典及簡易遊戲。

* 貪吃蛇
* 打磚塊`
* 太空侵略者
* 井字遊戲 (圈圈叉叉)
* 記憶翻牌
* 簡易迷宮
* 打地鼠
* 俄羅斯方塊 (類)
* 反應力測試

### 雙螢幕支援：

* 主要遊戲畫面透過 HDMI 顯示 (800x600 解析度)。
* SPI TFT LCD (2.8吋, 240x320, ILI9341 控制器) 用於顯示選單、遊戲說明及狀態。

### 多種輸入方式：

* Xbox 控制器：主要遊戲控制及選單導覽。
* 4x4 矩陣鍵盤：選單導覽及備用輸入。

### 其他功能：

* **聲音回饋：** 蜂鳴器提供音效及簡單旋律。
* **視覺指示燈：** 交通號誌燈 LED (紅、黃、綠) 用於顯示系統及遊戲狀態。
* **硬體電源按鈕：** 專用按鈕，長按可安全關閉系統。
* **選單系統：** 使用者友善的選單，可在雙螢幕上選擇遊戲及查看說明。

## 硬體需求
* 樹莓派 (建議 3B+ 或更新型號)
* MicroSD 卡 (已安裝 Raspberry Pi OS)
* HDMI 顯示器 (支援 800x600 解析度)
* USB Xbox 控制器
* SPI TFT LCD 模組 (2.8 吋, 240x320, ILI9341 控制器，例如 MSP2897)
* 4x4 矩陣鍵盤
* 有源蜂鳴器模組
* 交通號誌燈 LED 模組 (或獨立的紅、黃、綠 LED 及電阻)
* 按鈕 (用於電源/關機)
* 麵包板及杜邦線

## 軟體需求
* Python 3
* RPi.GPIO >= 0.7.0
* pygame >= 2.0.0
* luma.core >= 2.3.1
* luma.lcd (特別是 ILI9341 驅動，通常包含在 luma.oled 中，若 luma.oled>=3.8.1 未直接包含，可能需另外安裝。程式碼中使用 from luma.lcd.device import ili9341)
* evdev >= 1.4.0
* Pillow >= 8.0.0

使用以下指令安裝依賴套件：

```bash
sudo pip3 install -r requirements.txt
```

建議同時確認 luma.lcd 是否已安裝，如果 luma.oled 未包含的話。

## GPIO 接線說明 (BCM 編號模式)
請確保所有硬體元件依照以下列表連接至樹莓派的 GPIO 引腳。系統使用 BCM 編號模式。

### 蜂鳴器 (buzzer.py):
* BUZZER_PIN: GPIO 18

### 矩陣鍵盤 (matrix_keypad.py):
* 列 (Rows): GPIO 6, 13, 19, 26
* 行 (Columns): GPIO 12, 16, 20, 21

### SPI TFT 螢幕 (screen_menu.py):
使用 SPI0 介面:
* MOSI: GPIO 10 (實體引腳 Pin 19)
* SCLK: GPIO 11 (實體引腳 Pin 23)
* CS (Chip Select / 片選): GPIO 8 (實體引腳 Pin 24, CE0) - 對應 SPI_DEVICE = 0
* SPI_DC (Data/Command / 資料/指令選擇): GPIO 25
* SPI_RST (Reset / 重置): GPIO 24
* SPI_LED (Backlight Control / 背光控制): GPIO 27

### 交通號誌燈 LED (traffic_light.py, main.py):
* 紅燈 LED: GPIO 4
* 黃燈 LED: GPIO 3
* 綠燈 LED: GPIO 2

### 電源按鈕 (power_button.py):
* 按鈕輸入: GPIO 4 (另一端接地，程式使用內部上拉電阻)

### 重要接線提示：

* 所有 GPIO 接線都應在樹莓派 **未通電** 的情況下進行。
* LED 通常需要串聯一個限流電阻 (例如 220Ω 或 330Ω) 以免燒毀，除非您使用的 LED 模組已內建電阻。交通號誌燈模組通常已整合電阻。
* 蜂鳴器模組：有源蜂鳴器直接接 VCC, GND, 和訊號腳 (GPIO 18)。無源蜂鳴器則需要 PWM 訊號或額外驅動電路。本專案假設使用有源蜂鳴器或相容模組。
* SPI 螢幕：請仔細核對螢幕模組的 VCC, GND, MOSI (或 SDI), SCLK (或 SCK), CS, DC, RST, LED (或 BLK) 引腳定義，並正確連接。

## 檔案結構
```
raspberrypi/
├── main.py                 # 主應用程式，整合所有模組
├── screen_menu.py          # SPI 螢幕管理 (選單、說明)
├── matrix_keypad.py        # 矩陣鍵盤輸入處理
├── gamepad_input.py        # Xbox 控制器輸入處理
├── buzzer.py               # 蜂鳴器控制 (聲音回饋)
├── traffic_light.py        # 交通號誌燈 LED 控制
├── power_button.py         # 電源按鈕監控 (關機)
├── games/                  # 包含各個遊戲模組的目錄
│   ├── game1.py            # 貪吃蛇遊戲
│   ├── game2.py            # 打磚塊遊戲
│   ├── game3.py            # 太空侵略者遊戲
│   ├── game4.py            # 井字遊戲
│   ├── game5.py            # 記憶翻牌遊戲
│   ├── game6.py            # 簡易迷宮遊戲
│   ├── game7.py            # 打地鼠遊戲
│   ├── game8.py            # 俄羅斯方塊 (類)
│   └── game9.py            # 反應力測試遊戲
├── assets/                 # (目前未使用，為未來遊戲資源預留)
└── requirements.txt        # Python 依賴套件列表
```

## 設定與安裝
### 取得專案檔案：
將所有專案檔案複製到您的樹莓派上，例如 `/home/pi/raspberrypi_game_console` 目錄。

### 安裝依賴套件：
開啟終端機，進入專案目錄，然後執行：

```bash
cd /path/to/your_project_directory/raspberrypi
sudo pip3 install -r requirements.txt
```

確保 luma.lcd 已為您的 TFT 螢幕正確安裝並運作。

### 啟用 SPI 介面：
在終端機中執行 `sudo raspi-config`，進入 Interface Options -> SPI，選擇啟用 SPI 介面。

### 連接硬體：
依照【GPIO 接線說明】章節，仔細連接所有硬體元件 (SPI 螢幕、鍵盤、蜂鳴器、LED、電源按鈕)。

### 字型 (建議)：
為了在 SPI 螢幕上有較好的文字顯示效果，建議安裝常見的 TrueType 字型。腳本會嘗試使用 "DejaVuSans.ttf"。

```bash
sudo apt-get update
sudo apt-get install fonts-dejavu-core # 安裝 DejaVuSans 字型
# sudo apt-get install fonts-wqy-zenhei # 若未來需要中文，可安裝文泉驛正黑
```

## 如何執行
開啟終端機，進入專案所在的目錄：

```bash
cd /path/to/your_project_directory/raspberrypi
```

執行主應用程式：

```bash
sudo python3 main.py
```

建議使用 `sudo` 執行，因為程式需要存取 GPIO，且 `power_button.py` 腳本需要權限執行 shutdown 指令。

`main.py` 腳本會自動嘗試在背景啟動 `power_button.py` 來監控電源按鈕。

## 遊戲及按鈕介紹
### 通用導覽 (選單/說明頁面)
#### Xbox 控制器：

* 方向鍵 (D-Pad) / 左搖桿： 上下移動選擇項目。
* A 按鈕： 確認 / 選擇。
* B 按鈕： 返回上一頁。
* Start 按鈕： 從說明頁面開始遊戲 / 遊戲中暫停或繼續。

#### 矩陣鍵盤：

* 數字鍵 (1-9)： 選擇對應編號的遊戲。
* A (或對應映射的按鍵)： 確認。
* D (或對應映射的按鍵)： 返回。
(矩陣鍵盤的 A, B, C, D 可能因您的鍵盤型號和 matrix_keypad.py 中的 KEY_MAP 設定而異，預設 KEY_MAP 中 'A', 'B', 'C', 'D' 分別對應特定功能。)

### 各遊戲簡介與控制器操作
遊戲的具體操作說明會在選擇遊戲後，進入遊戲前的說明頁面顯示。

#### 貪吃蛇 (Snake / game1.py)

**簡介：** 控制不斷變長的蛇，吃食物得分，避免撞到自己或牆壁。

**Xbox 控制器：**
* 左搖桿/方向鍵： 控制蛇的移動方向 (上、下、左、右)。
* A 按鈕： 加速移動。

#### 打磚塊 (Brick Breaker / game2.py)

**簡介：** 控制擋板反彈小球，清除畫面上方的所有磚塊。

**Xbox 控制器：**
* 左搖桿/方向鍵 (左/右)： 移動擋板。
* A 按鈕： 發射小球 (遊戲開始或球重新發射時)。

#### 太空侵略者 (Space Invaders / game3.py)

**簡介：** 控制太空船左右移動，射擊消滅來襲的外星侵略者。

**Xbox 控制器：**
* 左搖桿/方向鍵 (左/右)： 移動太空船。
* A 按鈕： 射擊。

#### 井字遊戲 (Tic-Tac-Toe / game4.py)

**簡介：** 經典的圈圈叉叉遊戲，可雙人遊玩或對抗簡易電腦 AI。

**Xbox 控制器：**
* 左搖桿/方向鍵： 移動選擇游標至棋盤格子。
* A 按鈕： 在選擇的格子上放置棋子。
* Y 按鈕 (選單中或遊戲結束後)： 切換對戰模式 (玩家 vs 玩家 / 玩家 vs 電腦)。

#### 記憶翻牌 (Memory Match / game5.py)

**簡介：** 翻開蓋住的卡牌，找出所有成對的圖案。

**Xbox 控制器：**
* 左搖桿/方向鍵： 移動選擇游標至卡牌。
* A 按鈕： 翻開選擇的卡牌。

#### 簡易迷宮 (Simple Maze / game6.py)

**簡介：** 控制角色在隨機生成的迷宮中尋找出路。

**Xbox 控制器：**
* 左搖桿/方向鍵： 控制角色在迷宮中移動 (上、下、左、右)。

#### 打地鼠 (Whac-A-Mole / game7.py)

**簡介：** 地鼠會隨機從洞中冒出，用槌子快速敲擊它們得分。

**Xbox 控制器：**
* 左搖桿/方向鍵： 移動槌子的位置到對應的洞口。
* A 按鈕： 敲擊。

#### 俄羅斯方塊 (Tetris-like / game8.py)

**簡介：** 控制不同形狀的方塊下落，填滿行即可消除得分。

**Xbox 控制器：**
* 左搖桿/方向鍵 (左/右)： 水平移動方塊。
* 左搖桿/方向鍵 (上)： 旋轉方塊。
* 左搖桿/方向鍵 (下)： 加速方塊下落 (軟降)。
* A 按鈕： 使方塊快速直接落到底部 (硬降)。

#### 反應力測試 (Reaction Test / game9.py)

**簡介：** 測試玩家對視覺信號的反應速度。

**Xbox 控制器：**
* A 按鈕： 當看到綠色信號出現時，立即按下。

## 交通號誌燈狀態
* **遊戲機啟動時：** 綠 -> 黃 -> 紅 依序閃爍後熄滅。
* **進入遊戲說明頁面：** 黃燈亮。
* **遊戲開始倒數：** 紅 -> 黃 -> 綠 依序亮起，配合音效。
* **遊戲結束：** 紅燈亮。
* **返回選單：** 所有燈熄滅。
* **遊戲啟動失敗：** 紅燈亮，一段時間後熄滅。

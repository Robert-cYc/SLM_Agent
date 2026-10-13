# 🤖 SmolLM Studio - 本地小語言模型 (SLM) 桌面客戶端

這是一個使用 **Python + PyQt6 + Hugging Face Transformers + PyTorch** 開發的現代化桌面 AI 對話應用程式。
具備**免聯網**、**注重隱私**、**GPU 硬體加速**、**即時 Token 流式輸出 (Streaming)** 等特性，並支援一鍵打包為 Windows 獨立執行檔 (`.exe`)。

---

## ✨ 核心特色

1. **一鍵下載與載入 Hugging Face 小語言模型 (SLM)**：
   - 預設整合 Hugging Face 官方 SmolLM 系列：
     - `HuggingFaceTB/SmolLM2-135M-Instruct`（超輕量 135M，~270MB，秒下載秒載入，低配電腦也能高速運行）
     - `HuggingFaceTB/SmolLM2-360M-Instruct`（輕量 360M，~720MB，平衡度佳）
     - `HuggingFaceTB/SmolLM2-1.7B-Instruct`（高品質 1.7B，~3.4GB）
     - `HuggingFaceTB/SmolLM3-3B`（最新 SmolLM3 3B 模型，~6GB）
     - `Qwen/Qwen2.5-0.5B-Instruct`（阿里千問 0.5B，繁簡中文能力佳）
   - **支援自訂模型**：可自由輸入任何 Hugging Face Repo ID。
2. **自動硬體檢測與加速**：
   - 自動檢測 NVIDIA GPU（CUDA）並顯示顯卡型號與 VRAM 佔用情況。
   - 若無獨立顯卡，自動優雅降級為 CPU 運行模式。
3. **流暢對話與非同步多執行緒**：
   - 下載與推論皆在獨立背景執行緒 (`QThread`) 運作，UI 介面完全不卡頓。
   - 支援即時 Token 串流顯示（即問即答，即時逐字輸出）。
   - 支援「🛑 停止生成」按鈕，可隨時中途打斷推論。
   - 內建 **防複讀懲罰機制 (Repetition Penalty)**，避免小模型陷入語言循環。
4. **推論參數自訂**：
   - 支援自訂系統提示詞（System Prompt）。
   - 可即時調整最大長度（Max Tokens）、創意度（Temperature）、取樣核心（Top-P）、重複懲罰（Repetition Penalty）。
5. **深色現代化 UI**：
   - 基於精選深色調（Slate & Indigo）設計的高質感介面，氣泡對話排版清晰美觀。

---

## 🚀 快速啟動

### 方式 1：一鍵啟動（推薦）
在專案根目錄直接雙擊執行：
```text
Run_App.bat
```
或直接開啟位於 `dist` 目錄的正式執行檔：
```text
dist\SmolLMAssistant\SmolLMAssistant.exe
```

> ⚠️ **注意**：請務必開啟 **`dist`** 資料夾內的執行檔（或點擊 `Run_App.bat`），**切勿**點擊 `build` 資料夾（`build` 僅為編譯過程中的暫存暫存目錄，不包含執行所需之 DLL 模組）。

---

### 方式 2：使用 Python 原始碼執行

```bash
pip install -r requirements.txt
python app.py
```

---

## 📦 打包成 Windows 執行檔 (.exe)

本專案提供專屬打包腳本 `build_exe.py`，已配置好 PyTorch、Transformers、Tokenizers 與 PyQt6 的資源收集與 Hook：

```bash
python build_exe.py
```

打包完成後，執行檔將位於：
```
dist/SmolLMAssistant/SmolLMAssistant.exe
```

---

## 🧪 執行單元測試

專案包含測試套件，使用 `pytest` 驗證：

```bash
python -m pytest test_app.py -v
```

---

## 📂 專案檔案結構

- [`Run_App.bat`](file:///g:/我的雲端硬碟/Google%20Antigravity/Coding/SLM_Agent/Run_App.bat)：根目錄一鍵捷徑啟動腳本。
- [`app.py`](file:///g:/我的雲端硬碟/Google%20Antigravity/Coding/SLM_Agent/app.py)：GUI 主程式與對話介面邏輯。
- [`model_worker.py`](file:///g:/我的雲端硬碟/Google%20Antigravity/Coding/SLM_Agent/model_worker.py)：模型下載、載入與串流推論背景執行緒。
- [`styles.py`](file:///g:/我的雲端硬碟/Google%20Antigravity/Coding/SLM_Agent/styles.py)：現代深色風格 QSS 樣式表。
- [`build_exe.py`](file:///g:/我的雲端硬碟/Google%20Antigravity/Coding/SLM_Agent/build_exe.py)：PyInstaller 自動打包腳本。
- [`test_app.py`](file:///g:/My%20Drive/Google%20Antigravity/Coding/SLM_Agent/test_app.py)：單元測試。
- [`requirements.txt`](file:///g:/我的雲端硬碟/Google%20Antigravity/Coding/SLM_Agent/requirements.txt)：專案相依套件清單。

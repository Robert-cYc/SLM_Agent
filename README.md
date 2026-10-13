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
4. **推論參數自訂**：
   - 支援自訂系統提示詞（System Prompt）。
   - 可即時調整最大長度（Max Tokens）、創意度（Temperature）、取樣核心（Top-P）。
5. **深色現代化 UI**：
   - 基於精選深色調（Slate & Indigo）設計的高質感介面。

---

## 🚀 快速開始

### 1. 安裝環境依賴

```bash
pip install -r requirements.txt
```

### 2. 啟動 GUI 應用程式

```bash
python app.py
```

1. 在左側模型下拉選單選擇模型（初次使用建議選擇 `SmolLM2-135M-Instruct` 體驗秒速載入）。
2. 點擊 **「🚀 下載並載入模型」**。
3. 載入完成後，在下方輸入框輸入問題並按下 `Enter` 即可開始對話！

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

> 💡 **為何建議使用目錄模式 (`--onedir`)？**  
> 由於 PyTorch 與 CUDA 函式庫龐大（數 GB），如果打包成單一檔案（`--onefile`），每次雙擊執行時 Windows 都必須花費 40~60 秒解壓縮至 `%TEMP%` 目錄才啟動。採用目錄模式可達成 **1~2 秒瞬間秒開**，體驗極佳。

---

## 🧪 執行單元測試

專案包含測試套件，使用 `pytest` 驗證：

```bash
python -m pytest test_app.py -v
```

---

## 📂 專案檔案結構

- [`app.py`](file:///g:/我的雲端硬碟/Google%20Antigravity/Coding/SLM_Agent/app.py)：GUI 主程式與對話介面邏輯。
- [`model_worker.py`](file:///g:/我的雲端硬碟/Google%20Antigravity/Coding/SLM_Agent/model_worker.py)：模型下載、載入與串流推論背景執行緒。
- [`styles.py`](file:///g:/我的雲端硬碟/Google%20Antigravity/Coding/SLM_Agent/styles.py)：現代深色風格 QSS 樣式表。
- [`build_exe.py`](file:///g:/我的雲端硬碟/Google%20Antigravity/Coding/SLM_Agent/build_exe.py)：PyInstaller 自動打包腳本。
- [`test_app.py`](file:///g:/我的雲端硬碟/Google%20Antigravity/Coding/SLM_Agent/test_app.py)：單元測試。
- [`requirements.txt`](file:///g:/我的雲端硬碟/Google%20Antigravity/Coding/SLM_Agent/requirements.txt)：專案相依套件清單。

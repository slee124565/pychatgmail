#!/bin/bash
# 本腳本功能：
# 1. 從當前目錄下的 .q 檔案中讀取 JSON 格式資料，
#    每個元素為一個陣列，其中第一個元素為 gmail 帳號。
# 2. 對每個 gmail 帳號執行 chatgmail check-mail "{gmail}" 命令，
#    並將其查詢結果先直接輸出到終端機。
# 3. 再將 chatgmail 的輸出結果通過管道傳給 llm -t hwpm-hr 命令，
#    並將最終處理後的結果也輸出到終端機。
# 4. 每筆處理完成後等待使用者按 Enter 後再進行下一筆處理。

# 設定 JSON 檔案名稱，假設檔案名稱為 .q
FILE=".q"

# 檢查 .q 檔案是否存在於當前目錄
if [ ! -f "$FILE" ]; then
  echo "檔案 $FILE 不存在，請確認檔案是否在當前目錄中。"
  exit 1
fi

# 使用 jq 解析 JSON 資料，取得每個子陣列中的第一個元素（gmail 帳號）
# -r 參數表示以原始格式輸出，避免多餘的引號
gmail_ids=$(jq -r '.[] | .[0]' "$FILE")

# 若無法從檔案中取得 gmail id 則退出
if [ -z "$gmail_ids" ]; then
  echo "未從 $FILE 讀取到任何 gmail id，請檢查 JSON 格式是否正確。"
  exit 1
fi

# 依序處理每個 gmail 帳號
for gmail in $gmail_ids; do
  echo "-------------------------------------------"
  echo "開始處理 gmail 帳號：$gmail"

  # 執行 chatgmail check-mail 命令，將查詢結果存入 chat_output 變數
  chat_output=$(chatgmail check-mail "$gmail")

  # 輸出 chatgmail 的查詢結果到終端機
  echo "chatgmail check-mail 輸出結果："
  echo "$chat_output"

  # 將 chat_output 輸入到 llm -t hwpm-hr 命令中進行處理，並將結果存入 processed_result 變數
  processed_result=$(echo "$chat_output" | llm -t hwpm-hr)

  # 輸出 llm -t hwpm-hr 處理後的結果到終端機
  echo "llm -t hwpm-hr 處理後的結果："
  echo "$processed_result"

  echo "-------------------------------------------"

  # 等待使用者按下 Enter 鍵後再繼續處理下一個 gmail 帳號
  read -p "請按下 Enter 鍵繼續..."
done

echo "所有 gmail 帳號處理完畢。"

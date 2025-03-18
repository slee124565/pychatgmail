#!/bin/bash
# 本腳本功能：
# 1. 從當前目錄下的 .q 檔案讀取 JSON 格式資料，
#    每個元素為一個陣列，其中第一個元素為 gmail 帳號。
# 2. 可透過參數 -n 指定從第幾筆 gmail 帳號開始處理，
#    例如: ./process_q.sh -n 3 表示從第三筆開始。
# 3. 依序針對每個 gmail 帳號執行 chatgmail check-mail 命令，
#    並先將查詢結果直接輸出到終端機。
# 4. 在呼叫 llm 指令處理前，顯示進度提示 "llm 分析中 ... [n/m]"，
#    其中 n 為目前處理順序、m 為 gmail 帳號總數。
# 5. 將查詢結果透過管道傳給 llm -t hwpm-hr 命令，
#    並將處理後的結果輸出到終端機，然後等待使用者按 Enter 鍵後進行下一筆處理。

# 用法說明函數
usage() {
  echo "用法: $0 [-n 起始索引]"
  exit 1
}

# 預設從第一筆開始處理
start_index=1

# 解析參數 -n
while getopts ":n:" opt; do
  case $opt in
    n)
      # 檢查參數是否為正整數且大於0
      if ! [[ $OPTARG =~ ^[0-9]+$ ]] || [ "$OPTARG" -le 0 ]; then
        echo "錯誤: -n 參數必須為正整數。"
        usage
      fi
      start_index=$OPTARG
      ;;
    \?)
      echo "無效選項: -$OPTARG"
      usage
      ;;
    :)
      echo "選項 -$OPTARG 需要一個參數。"
      usage
      ;;
  esac
done

# 設定 JSON 檔案名稱，假設檔案名稱為 .q
FILE=".q"

# 檢查 .q 檔案是否存在於當前目錄
if [ ! -f "$FILE" ]; then
  echo "檔案 $FILE 不存在，請確認檔案是否在當前目錄中。"
  exit 1
fi

# 使用 jq 解析 JSON 資料，取得每個子陣列中的第一個元素（gmail 帳號）
# macOS 不支援 mapfile，因此用 while 迴圈讀取至陣列
gmail_ids=()
while IFS= read -r line; do
  gmail_ids+=("$line")
done < <(jq -r '.[] | .[0]' "$FILE")

# 若無法從檔案中取得 gmail id 則退出
if [ ${#gmail_ids[@]} -eq 0 ]; then
  echo "未從 $FILE 讀取到任何 gmail id，請檢查 JSON 格式是否正確。"
  exit 1
fi

# 計算 gmail 帳號總數
total=${#gmail_ids[@]}

# 檢查輸入的起始索引是否超出總數
if [ $start_index -gt $total ]; then
  echo "起始索引 $start_index 超出總數 $total。"
  exit 1
fi

# 計算實際陣列索引（bash 陣列從 0 開始）
current_index=$((start_index - 1))

# 依序處理每個 gmail 帳號，從 current_index 到陣列結尾
for ((i=current_index; i<total; i++)); do
  # 目前處理順序 n 為 i+1（對應原 JSON 中的順序）
  n=$((i + 1))
  gmail=${gmail_ids[$i]}

  echo "-------------------------------------------"
  echo "開始處理 gmail 帳號：$gmail (第 $n 筆 / 共 $total 筆)"

  # 執行 chatgmail check-mail 命令，取得查詢結果並存入 chat_output
  chat_output=$(chatgmail check-mail "$gmail")

  # 輸出 chatgmail 的查詢結果到終端機
  echo "chatgmail check-mail 輸出結果："
  echo "$chat_output"

  # 輸出進度提示，告知正在等待 llm 處理
  echo "llm 分析中 ... [${n}/${total}]"

  # 將 chat_output 輸入到 llm -t hwpm-hr 命令中進行處理，並取得處理後結果
  processed_result=$(echo "$chat_output" | llm -t hwpm-hr)

  # 輸出 llm 處理後的結果
  echo "llm -t hwpm-hr 處理後的結果："
  echo "$processed_result"

  echo "-------------------------------------------"

  # 等待使用者按下 Enter 鍵後再處理下一個 gmail 帳號
  read -p "請按下 Enter 鍵繼續..."
done

echo "所有 gmail 帳號處理完畢。"

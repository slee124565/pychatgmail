# gmailGPT

## gmail_msg_reader.py
從 gmail 信箱中讀取應徵者信件，並將信件內容存於 `html/<email_msg_id>.html`


## html_msg_parser.py
從 `html/<email_msg_id>.html` 當中擷取應徵者的關鍵資訊，
並另外存 `html/<email_msg_id>.json` 檔案


## openai_commenter
在 job_condition.csv 設定好職位和應徵條件

執行
`python openai_commenter.py -k <api key>` 

openai_commenter.py 會從 `html/*.json` 讀取應徵者資料，
並呼叫 openai api 取得回應資訊，最後輸出 openai_comment.csv
import os
import datetime
from bs4 import BeautifulSoup


def find_recent_html_files(days):
    # 當前日期
    current_date = datetime.datetime.now()

    # 搜尋目標路徑
    target_directory = os.path.join(os.getcwd(), '.gmail')

    # 符合條件的檔案列表
    results = []

    # 確保目標目錄存在
    if not os.path.exists(target_directory):
        return []

    # 迭代目標目錄中的所有檔案
    for root, dirs, files in os.walk(target_directory):
        for file in files:
            if file.endswith('.html'):
                # 完整檔案路徑
                file_path = os.path.join(root, file)

                # 檔案的最後修改時間
                file_modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

                # 計算檔案是否在指定天數內被修改過
                if (current_date - file_modified_time).days <= days:
                    # 取得 msg_id
                    msg_id = os.path.splitext(file)[0]

                    # 讀取 HTML 檔案內容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                        # 使用 BeautifulSoup 解析 HTML 並提取 <title> 標籤的文字
                        soup = BeautifulSoup(content, 'html.parser')
                        title_tag = soup.find('title')

                        # 確保 <title> 標籤存在
                        if title_tag:
                            title_text = title_tag.get_text().strip()

                            # 將結果加入列表
                            results.append({
                                'msg_id': msg_id,
                                'title': title_text,
                                'modified_datetime': file_modified_time
                            })

    # 根據 modified_datetime 排序
    results.sort(key=lambda x: x['modified_datetime'], reverse=True)

    return results


# Example usage
days = 2
founds = find_recent_html_files(days)
for found in founds:
    print(found)

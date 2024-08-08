#!/bin/bash

# 定义要搜索的字符串
search_string="GCP Cloud Architect"
pattern='alt>代碼：[0-9]+</div>'
date_pattern='>應徵快照：[0-9/ :]+<img'

# 初始化一个数组来存储符合条件的文件名
matched_files=()

# 在当前目录及其子目录中搜索 .gmail/*.html 文件
while IFS= read -r -d '' file; do
  # 检查文件内容是否包含搜索字符串
  if grep -q "$search_string" "$file"; then
    # 如果包含，则将文件名添加到数组中
    matched_files+=("$file")
  fi
done < <(find . -type f -path "*/.gmail/*.html" -print0)

# 处理匹配的文件
for file in "${matched_files[@]}"; do
  # 使用 grep 查找文件内容中符合 pattern 的行
  matched_line=$(grep -o 'alt>代碼：[0-9]\+</div>' "$file")

  if [ -n "$matched_line" ]; then
    # 使用 sed 提取数字部分
    resumeId=$(echo "$matched_line" | sed -n 's/.*代碼：\([0-9]\{1,\}\)<\/div>/\1/p')

    # 使用 grep 查找文件内容中符合 date_pattern 的行
    matched_date=$(grep -o '>應徵快照：[0-9/ :]\+<img' "$file")

    if [ -n "$matched_date" ]; then
      # 使用 sed 提取日期部分
      rdate=$(echo "$matched_date" | sed -n 's/.*應徵快照：\([0-9/ :]\{1,\}\)<img/\1/p')
    fi

#    if [ -n "$resumeId" ] && [ -n "$rdate" ]; then
      filename=$(basename "$file")
      # 输出文件名、日期和提取的 resumeId
      echo "$filename, $rdate, $resumeId"
#    fi
  fi
done

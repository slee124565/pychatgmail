import bs4
from lxml import etree

# 使用 with 语句确保文件正确关闭
with open('.gmail/18e1c222bb4ae653.html', 'r', encoding='utf-8') as file:
    # 读取文件内容赋值给 html_string
    html_string = file.read()

# 将 HTML 字符串解析为 XML 结构
soup = bs4.BeautifulSoup(html_string, 'html.parser')
dom = etree.HTML(str(soup))

# 关键词列表
keywords = [
    '應徵職務：',
    '個人資料',
    '求職者希望條件',
    '工作經歷',
    '教育背景',
    '語文能力',
    '技能專長',
    '自傳',
    '附件',
    '其他作品'
]

# 使用 XPath 找到所有 class 属性包含 mail__container 的 <table> 标签
xpath_string = "//table[contains(@class, 'mail__container')]"
tables = dom.xpath(xpath_string)

# 存储匹配到的信息
matches = []

for keyword in keywords:
    match_found = False
    if tables:
        # 在第一个 mail__container <table> 元素中，找到所有子 <table> 标签
        parent_table = tables[0]
        child_tables = parent_table.xpath(".//table")

        # 遍历所有找到的子 <table> 标签
        for index, child_table in enumerate(child_tables):
            # 使用 etree.tostring() 方法并设置 method="text" 来获取纯文本，然后清理空白符
            table_text = etree.tostring(child_table, method="text", encoding="unicode")
            table_text = ' '.join(table_text.split())  # 清理文本

            # 显示每个 child_table 的摘要信息
            print(f"Child Table Index: {index}, Table Digest: {table_text[:50]}...")

            # 检查关键词是否在文本开头
            if table_text.startswith(keyword):
                matches.append({
                    "keyword": keyword,
                    "child_table_index": index,
                    "position": 0
                })
                match_found = True
                break  # 匹配到后即跳出循环

    # 如果没有找到匹配项，则添加没有匹配的记录
    if not match_found:
        matches.append({
            "keyword": keyword,
            "child_table_index": None,
            "position": None
        })

# 输出匹配到的信息
for match in matches:
    print(
        f"Keyword: '{match['keyword']}', Child Table Index: {match['child_table_index']}, Position: {match['position']}")

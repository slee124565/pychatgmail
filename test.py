from lxml import etree

# 使用 with 語句來確保檔案正確關閉
with open('.gmail/18e1c222bb4ae653.html', 'r', encoding='utf-8') as file:
    # 讀取檔案內容並賦值給 html_string
    html_string = file.read()

# 將 HTML 字符串解析為 XML 結構
parser = etree.HTMLParser()
tree = etree.fromstring(html_string, parser)

# 定義 XPath
xpath_string = "/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[1]/b/a/span"

# 使用 XPath 找到對應的元素
elements = tree.xpath(xpath_string)

# 假設我們只對第一個匹配的元素感興趣
if elements:
    # .text 屬性用於獲取元素的內部文本
    inner_text = elements[0].text
    print(inner_text)
else:
    print("未找到匹配的元素")

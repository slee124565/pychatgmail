import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/src')

from resume_judge_bot import OpenaiRecruitJudgeBot
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--openai_key', help='openai api key', required=True)
    args = parser.parse_args()

    requirement = """
你是一個專業的UI/UX Designer，我會提供你應徵履歷資料，請判斷該名應徵者是否為合適的UI/UX Designer。
以下為應徵條件:
1. 具備3年以上的非實習經驗
2. 具備使用Sketch, Adobe XD, Figma, InVision, Axure, Protopie 等其中之一的工具經驗
3. 具備參與 Mobile 手機 App 專案開發設計經驗
4. 具備與客戶討論與分析客戶需求的非實習經驗
5. 具備與研發人員討論與分析客戶需求的非實習經驗
"""

    candidate_resume = """
工作經歷：

擔任UI/UX設計師，負責開發設計多個手機應用程式，為用戶提供優質的用戶體驗。
在某軟體公司擔任UI設計師，負責開發公司品牌形象、網站和應用程序的設計。
在一家互聯網公司擔任UI/UX設計師，為公司開發了多個網站、移動應用程序和數據分析產品的設計。
擅長使用的技術：

Adobe Creative Suite，如Photoshop、Illustrator等，用於創建網頁和應用程序的視覺設計元素。
Sketch和Figma等界面設計工具，用於創建和編輯UI元素和原型。
InVision和Marvel等交互設計工具，用於創建和測試交互式原型。
HTML、CSS和JavaScript等網頁技術，用於開發和測試網頁和應用程序的前端部分。
專案成果：

為某知名手機應用程序設計了新的用戶界面，大大提高了用戶的滿意度和忠誠度。
為一個大型企業客戶創建了一個基於响应式设计的網站，兼顧移動和桌面平台的設計，並為客戶提供了更好的品牌形象和市場曝光。
設計和開發了一個基於云的數據分析產品，提供了可靠的可視化和交互式分析工具，並為用戶提供了更好的數據分析體驗。
"""

    output = """
請把應徵條件是否符合做成表格，表格欄位要有<應徵條件>｜<符合/不符合/不確定>｜<原因>
若有其他符合優秀UI/UX Designer條件的部分也列出來。
最後給出總結。
"""

    judge_bot = OpenaiRecruitJudgeBot(args.openai_key)
    judge_result = judge_bot.judge(requirement, candidate_resume, output)
    print(judge_result)

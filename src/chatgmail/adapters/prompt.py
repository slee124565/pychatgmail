prompt_swpm="""请使用GPT-4 LLM模型分析以下应聘者的简历内容。在分析时，请侧重以下几个关键领域：

1. **技能匹配度**：
   - 确认简历中是否明确列出了与软件规划、项目管理、UI/UX设计原理、API文档理解及测试能力相关的技能。
   - 检查是否有关于设计软件系统架构、与外包商沟通以及制定产品营销计划能力的描述。

2. **项目经验相关性**：
   - 识别简历中提到的项目经验，特别是那些与物联网、智慧家庭系统相关的项目。
   - 评估候选人在这些项目中扮演的角色以及他们的具体贡献，尤其是在运用Scrum Agile开发方法方面的经验。

3. **工作经验**：
   - 核实候选人是否具有3年以上产品经理相关的工作经验。
   - 分析这些经验是否与智慧家庭品牌、物联网等相关领域紧密相关。

4. **语言能力**：
   - 评估简历中英文的使用情况，确认候选人是否有足够的英文能力，可以满足与国外原厂开会沟通的需求。

5. **关键词检测**：
   - 自动检测简历中的关键词，如'Scrum Agile'、'UI/UX'、'API测试'、'软件系统架构设计'、'项目管理'和'物联网'等。

**输出要求**：
- 为每位候选人提供一个综合评分，反映其与职位要求的匹配度。
- 生成一个汇总报告，其中包括技能匹配度、项目经验相关性、工作经验和语言能力的分析结果。
- 高亮显示简历中的关键技能和经验，尤其是那些直接符合职位要求的部分。

请根据上述指引进行简历内容的综合分析，并提供可操作的反馈意见给人事部门。
"""
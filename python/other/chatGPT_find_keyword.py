import openai
import os

# 設置 OpenAI API 金鑰
# export OPENAI_API_KEY=your_api_key_here export OPENAI_API_KEY=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
# echo $OPENAI_API_KEY
api_key = os.getenv("OPENAI_API_KEY")

def query_chat_model(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",  # 或其他 ChatGPT 模型
        prompt=prompt,
        max_tokens=100,  # 根据需要调整生成回复的长度
        temperature=0.7,  # 控制生成回复的多样性，可以根据需要进行调整
        n=1,  # 生成一条回复
        stop=None  # 可以设置用于终止回复生成的字符串，如 '>>'
    )

    if response.choices:
        return response.choices[0].text.strip()
    else:
        return ""

# 提供您的查询提示
prompt = "取得下列字串的關鍵字, 取得請假規定中特休的相關內容"

# 发起 API 请求并获取回复
response = query_chat_model(prompt)
print(response)

# Result
# commandline: python3 test.py
#特休：
#關鍵字：特休、請假規定
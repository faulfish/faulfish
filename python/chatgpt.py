import openai
import os
import socket

def check_network():
    try:
        socket.create_connection(("www.google.com", 80))
        print("網路連接正常")
    except OSError:
        print("無法連接到網路")

def chatgpt(content, assistant):
    try:
        # 設置 OpenAI API 金鑰
        # export OPENAI_API_KEY=your_api_key_here
        # echo $OPENAI_API_KEY
        api_key = os.getenv("OPENAI_API_KEY")

        # 與 ChatGPT API 進行互動
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": content},
                {"role": "assistant", "content": assistant},
            ],
            max_tokens=300,
            n=1,
            stop=None,
            temperature=0.6,
            api_key=api_key
        )

        # 提取助理的回答作為摘要結果
        summary = response.choices[0].message.content

        return summary

    except Exception as e:
        print(f"An error occurred during the chat: {e}")
        return content

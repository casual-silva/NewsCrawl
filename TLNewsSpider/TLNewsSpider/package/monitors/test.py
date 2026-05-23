import requests

url = 'https://open.feishu.cn/open-apis/bot/hook/b5b9c7dd-2504-4a64-a43a-141fc0e4e2e5'

data = {
    "title": "Hello Feishu",  # 选填
    "text": "https://open.feishu.cn/open-apis/bot/hook/b5b9c7dd-2504-4a64-a43a-141fc0e4e2e5"  # 必填
}

response = requests.post(url, json=data)

print(response.text)

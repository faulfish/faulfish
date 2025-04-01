# language_code.py
# 任何國家或地區的 ISO 3166-1 alpha-2 代碼
def get_language_code(geo_code): 
    language_map = {
        "us": "en-US",
        "tw": "zh-TW",
        "jp": "ja-JP",
        "kr": "ko-KR",
        "cn": "zh-CN",
        "hk": "zh-CN",
        "vn": "en-US",
        "my": "en-US",
        # 可根據需要添加更多地區和對應的語系
    }

    return language_map.get(geo_code.lower(), "en-US")  # 如果地區代號未知，預設為en-US

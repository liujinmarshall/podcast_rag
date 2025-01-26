# podcast_rag
使用 RAG (检索增强生成) 技术来理解播客并提问

已测试 Python 版本：3.9 (应该也适用于更新的版本和不太旧的版本)

## 前提条件
* Python 环境以及并了解如何运行 Python 程序
* Google Gemini API 密钥和 OpenAI API 密钥

## 步骤
1. 克隆此 Github 仓库
2. 创建一个名为 "data" 的目录
3. 将 podcasts.example.csv 复制到 data/podcasts.csv，并添加 RSS URL 条目
4. 通过 requirements.txt 安装 Python 依赖 (pip install -r requirments.txt)
5. 将 Google Gemini API 密钥导出为 GEMINI_API_KEY，并将 OpenAI API 密钥导出为 OPENAI_API_KEY
6. 运行以下脚本以实现以下功能（使用 python xxx.py）
    1. download.py: 将播客音频媒体文件以增量模式下载到本地。每个播客一个目录
    2. transcribe.py: 将音频媒体文件转录成文本。每个播客一个目录
    3. index.py: 将转录文本分块并索引到向量数据库 (ChromaDB) 中
    4. query.py: 启动一个聊天机器人来查询问题
        1. 运行程序
        2. 在浏览器中打开链接并开始提问 <img src="https://raw.githubusercontent.com/liujinmarshall/podcast_rag/refs/heads/main/docs/img/chatbot.png" />
    5. summarize.py: 将转录文本总结成简洁的摘要。每个播客一个目录
    6. delete_files.py: 删除音频媒体文件（超过 24 小时的文件），以防文件上传超出配额。无论如何，上传超过 48 小时的文件将被自动清除

## 语言支持
* 中文
* 英语 (待添加)

## 注意
请遵守播客提供商的用户协议。此仓库仅供个人研究使用。

## 历史
* 2025/1/26: 0.01 (初始版本)

import os
import re
import time
import subprocess
import openai
from openai import OpenAI
import logging

# Proxyを無視する設定
os.environ['NO_PROXY'] = '*'

# 翻訳前のファイルが入っているディレクトリを定義
SOURCE_DIR = "/home/t-yano/src/gptscript/docs/docs"

# 翻訳後のファイルを入れるディレクトリを定義
TARGET_DIR = "/home/t-yano/src/gptscript_docs_ja/docs/docs/"

# 翻訳実行日時を記録するファイル
EXEC_DATE_FILE = "exec_date_translation.txt"

# ロギングの設定
logging.basicConfig(filename='translator_en_to_ja.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S')

def split_markdown(content, chunk_size=10*1024):
    chunks = []
    current_chunk = ""
    in_code_block = False
    in_table = False

    for line in content.splitlines(keepends=True):
        if line.startswith("```"):
            in_code_block = not in_code_block
        if line.startswith("|") and not in_table:
            in_table = True
        elif not line.startswith("|") and in_table:
            in_table = False

        if in_code_block or in_table:
            if len(current_chunk) + len(line) > chunk_size:
                chunks.append(current_chunk)
                current_chunk = line  # コードブロックやテーブルの場合は、新しいチャンクに現在の行を追加
            else:
                current_chunk += line
        else:
            if len(current_chunk) + len(line) > chunk_size:
                chunks.append(current_chunk)
                current_chunk = ""
            current_chunk += line

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def translate_with_gpt4(text, api_key):
    client = OpenAI(api_key=api_key)
    
    logging.info(f"翻訳開始: {text[:50]}...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate the following English markdown text to Japanese, preserving the markdown format. "},
                {"role": "user", "content": text}
            ],
            max_tokens=4096,
            temperature=0
        )
        logging.info("翻訳完了")
        return response.choices[0].message.content
    except Exception as e:
        error_message = f"API要求が失敗しました: {str(e)}"
        logging.error(error_message)
        raise Exception(error_message)

def translate_markdown_file(input_file, output_file, api_key):
    logging.info(f"ファイル翻訳開始: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    chunks = split_markdown(content)
    translated_chunks = []
    
    for i, chunk in enumerate(chunks):
        log_message = f"チャンク {i+1}/{len(chunks)} を翻訳中..."
        print(log_message)
        logging.info(log_message)
        translated_chunk = translate_with_gpt4(chunk, api_key)
        translated_chunks.append(translated_chunk)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(translated_chunks))
    
    log_message = f"翻訳完了。出力先: {output_file}"
    print(log_message)
    logging.info(log_message)

def get_file_last_modified_date(file_path):
    try:
        result = subprocess.run(['git', 'log', '-1', '--format=%at', file_path], 
                                capture_output=True, text=True, check=True)
        return int(result.stdout.strip())
    except subprocess.CalledProcessError:
        return os.path.getmtime(file_path)

def get_last_translation_date():
    if os.path.exists(EXEC_DATE_FILE):
        with open(EXEC_DATE_FILE, 'r') as f:
            return int(f.read().strip())
    return 0

def update_translation_date():
    current_time = int(time.time())
    with open(EXEC_DATE_FILE, 'w') as f:
        f.write(str(current_time))

# メイン処理
if __name__ == "__main__":
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        error_message = "OPENAI_API_KEY 環境変数が設定されていません"
        logging.error(error_message)
        raise ValueError(error_message)
    
    logging.info("翻訳処理開始")
    last_translation_date = get_last_translation_date()

    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith('.md'):
                source_path = os.path.join(root, file)
                relative_path = os.path.relpath(source_path, SOURCE_DIR)
                target_path = os.path.join(TARGET_DIR, relative_path)
                
                # Markdownの要素を数える関数
                def count_markdown_elements(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return {
                        'コードブロック': content.count('```'),
                        '区切り線': content.count('\n---'),
                        'H1': content.count('\n# '),
                        'H2': content.count('\n## '),
                        'H3': content.count('\n### '),
                        '箇条書き': content.count('\n- '),
                        'notice': content.count(':::'),
                        'ハイパーリンク': content.count(']('),
                        '強調': len(re.findall(r'(?<!`)`[^`\n]+?`(?!`)', content, re.UNICODE))
                    }
                
                source_counts = count_markdown_elements(source_path)
                
                if not os.path.exists(target_path):
                    log_message = f"翻訳中: {relative_path} (新規ファイル)"
                    print(log_message)
                    logging.info(log_message)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    translate_markdown_file(source_path, target_path, api_key)
                else:
                    file_last_modified = get_file_last_modified_date(source_path)
                    if file_last_modified > last_translation_date:
                        log_message = f"翻訳中: {relative_path} (更新あり)"
                        print(log_message)
                        logging.info(log_message)
                        translate_markdown_file(source_path, target_path, api_key)
                    else:
                        log_message = f"スキップ: {relative_path} (変更なし)"
                        print(log_message)
                        logging.info(log_message)
                
                target_counts = count_markdown_elements(target_path)
                
                log_message = "Markdownの要素の比較:"
                print(log_message)
                logging.info(log_message)
                all_ok = True
                mismatches = []
                for element, source_count in source_counts.items():
                    target_count = target_counts[element]
                    if source_count != target_count:
                        mismatch_message = f"{element}: 不一致 (元: {source_count}, 翻訳後: {target_count})"
                        mismatches.append(mismatch_message)
                        all_ok = False
                
                if mismatches:
                    for mismatch in mismatches:
                        print(mismatch)
                        logging.warning(mismatch)
                    log_message = "★★一部の要素が一致していません。確認が必要です。★★\n-----"
                    print(log_message)
                    logging.warning(log_message)
                else:
                    log_message = "すべての要素が一致しています。\n-----"
                    print(log_message)
                    logging.info(log_message)

    update_translation_date()
    log_message = "全てのファイルの翻訳が完了しました。"
    print(log_message)
    logging.info(log_message)

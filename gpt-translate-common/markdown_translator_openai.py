#!/usr/bin/env python

import os
import re
import time
import subprocess
import openai
from openai import OpenAI
import logging
import json

# Setting to ignore proxy
os.environ['NO_PROXY'] = '*'

# Get current working directory
current_dir = os.getcwd()

# Define directory containing files to be translated
SOURCE_DIR = os.path.abspath(current_dir + "/../fleet-docs/docs")

# Define directory for translated files
TARGET_DIR = os.path.abspath(current_dir + "/../fleet-docs_ja/i18n/ja/docusaurus-plugin-content-docs")

# File to record translation execution date
EXEC_DATE_FILE = "exec_date_translation.txt"

# Debug flag
DEBUG = True

# Logging configuration
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
                current_chunk = line  # For code blocks or tables, add the current line to a new chunk
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
    
    logging.info(f"Translation started: {text[:50]}...")
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
        logging.info("Translation completed")
        return response.choices[0].message.content
    except Exception as e:
        error_message = f"API request failed: {str(e)}"
        logging.error(error_message)
        raise Exception(error_message)

def translate_markdown_file(input_file, output_file, api_key):
    logging.info(f"File translation started: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    chunks = split_markdown(content)
    translated_chunks = []
    
    if DEBUG:
        debug_dir = os.path.join(os.path.dirname(output_file), 'debug')
        os.makedirs(debug_dir, exist_ok=True)
        base_name = os.path.basename(input_file)
        
        # Save original chunks
        for i, chunk in enumerate(chunks):
            with open(os.path.join(debug_dir, f"{base_name}_chunk_{i}.md"), 'w', encoding='utf-8') as f:
                f.write(chunk)
    
    for i, chunk in enumerate(chunks):
        log_message = f"Translating chunk {i+1}/{len(chunks)}..."
        print(log_message)
        logging.info(log_message)
        translated_chunk = translate_with_gpt4(chunk, api_key)
        translated_chunks.append(translated_chunk)
        
        if DEBUG:
            # Save translated chunks
            with open(os.path.join(debug_dir, f"{base_name}_translated_chunk_{i}.md"), 'w', encoding='utf-8') as f:
                f.write(translated_chunk)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(translated_chunks))
    
    log_message = f"Translation completed. Output: {output_file}"
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

# Main process
if __name__ == "__main__":
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        error_message = "OPENAI_API_KEY environment variable is not set"
        logging.error(error_message)
        raise ValueError(error_message)
    
    logging.info("Translation process started")
    last_translation_date = get_last_translation_date()

    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith('.md'):
                source_path = os.path.join(root, file)
                relative_path = os.path.relpath(source_path, SOURCE_DIR)
                target_path = os.path.join(TARGET_DIR, relative_path)
                
                # Function to count Markdown elements
                def count_markdown_elements(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return {
                        'Code blocks': content.count('```'),
                        'Horizontal rules': content.count('\n---'),
                        'H1': content.count('\n# '),
                        'H2': content.count('\n## '),
                        'H3': content.count('\n### '),
                        'Bullet points': content.count('\n- '),
                        'Notice': content.count(':::'),
                        'Hyperlinks': content.count(']('),
                        'Emphasis': len(re.findall(r'(?<!`)`[^`\n]+?`(?!`)', content, re.UNICODE)),
                        'Bold': len(re.findall(r'\*\*[^*\n]+?\*\*', content, re.UNICODE))
                    }
                
                source_counts = count_markdown_elements(source_path)
                
                if not os.path.exists(target_path):
                    log_message = f"Translating: {relative_path} (new file)"
                    print(log_message)
                    logging.info(log_message)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    translate_markdown_file(source_path, target_path, api_key)
                else:
                    file_last_modified = get_file_last_modified_date(source_path)
                    if file_last_modified > last_translation_date:
                        log_message = f"Translating: {relative_path} (updated)"
                        print(log_message)
                        logging.info(log_message)
                        translate_markdown_file(source_path, target_path, api_key)
                    else:
                        log_message = f"Skipping: {relative_path} (no changes)"
                        print(log_message)
                        logging.info(log_message)
                
                target_counts = count_markdown_elements(target_path)
                
                log_message = "Comparing Markdown elements:"
                print(log_message)
                logging.info(log_message)
                all_ok = True
                mismatches = []
                for element, source_count in source_counts.items():
                    target_count = target_counts[element]
                    if source_count != target_count:
                        mismatch_message = f"{element}: Mismatch (Source: {source_count}, Translated: {target_count})"
                        mismatches.append(mismatch_message)
                        all_ok = False
                
                if mismatches:
                    for mismatch in mismatches:
                        print(mismatch)
                        logging.warning(mismatch)
                    log_message = "### Some elements do not match. Verification needed. ###\n-----"
                    print(log_message)
                    logging.warning(log_message)
                else:
                    log_message = "All elements match.\n-----"
                    print(log_message)
                    logging.info(log_message)
            update_translation_date()

    log_message = "----Translation of all files completed----"
    print(log_message)
    logging.info(log_message)

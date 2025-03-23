import os
import re
import markdown
from pathlib import Path

root_folder = '' # 当前目录

# 递归遍历目录树
def deep_directory(path, _type='md'):
    if _type == 'md':
        for item in path.rglob('*.md'):
            # 分离文件名和后缀
            path, _ext = os.path.splitext(item._raw_path)
            markdown_text = read_file(item._raw_path)
            HTML2File(markdown_text, path)
    else:
        # 地址转换
        for item in path.rglob('*.html'):
            HTML_PATH(item)

# 打开Markdown文件并读取内容
def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as md_file:
            return md_file.read()
    except Exception as e:
        print(f"▻ 读取{path}发生异常:", e)

# markdown内容转换
def content_convert(text, path):
    # 替换#和UUID
    pattern = r"(?:#)?\^.{8}-.{4}-.{4}-.{4}-.{12}"
    text = re.sub(pattern, "", text)

    # 替换md为html
    text = re.sub(f".md", ".html", text)
    return text

# 将HTML保存到文件
def HTML2File(text, path):
    # 转换Markdown到HTML
    html_output = markdown.markdown(content_convert(text, path))
    with open(path+'.html', 'w', encoding='utf-8') as file:
        file.write(html_output)

# 地址转换
def HTML_PATH(path):
    # 逐行读取文件
    text = read_file(path._raw_path)
    # 匹配所有的超链接
    pattern = r'<a href="([^"]+)">'
    matches = re.findall(pattern, text)
    if matches:
        for item in matches:
            html_file = list(root_folder.glob(f"**/{item}"))[0]
            text = text.replace(item, html_file._raw_path)
    with open(path._raw_path, 'w', encoding='utf-8') as file:
        file.write(text)


if __name__ == "__main__":
    # 指定目录路径
    path = os.getcwd() + "\\test"
    root_folder = Path(path)
    deep_directory(root_folder)
    deep_directory(root_folder, 'html')

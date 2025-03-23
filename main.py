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
            content_convert(markdown_text, path)
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
    # 替换md为html
    text = re.sub(f".md", ".html", text)
    # 转换Markdown到HTML
    html = markdown.markdown(text)
    write_file(html, f"{path}.html")

# 将HTML保存到文件
def write_file(text, path):
    try:
        with open(path, 'w', encoding='utf-8') as file:
            file.write(text)
    except Exception as e:
        print(f"▻ 写入{path}发生异常:", e)

# 地址转换
def HTML_PATH(path):
    # 读取文件
    html = read_file(path._raw_path)
    # 匹配所有的超链接
    pattern = r'<a href="([^"]+)">'
    matches = re.findall(pattern, html)
    if matches:
        for item in matches:
            name = item.split('#')
            html_file = list(root_folder.glob(f"**/{name[0]}"))[0]
            html = html.replace(item, html_file._raw_path)
    # 锚点
    html = html.replace('#^', '#')
    # 替换UUID为id
    html_list = html.split('\n')
    for i in range(len(html_list)):
        pattern = r"\^.{8}-.{4}-.{4}-.{4}-.{12}"
        match = re.search(pattern, html_list[i])
        if match:
            # 去除默认的锚点
            item = re.sub(pattern, "", html_list[i])
            # 去除前方的^
            _id = f" id=\"{match.group(0)[1:]}\""
            # 将锚点添加到a标签中作为id
            _pattern = r'<a href="([^"]+)"'
            _match = re.search(_pattern, item)
            # 超链接的情况
            if _match:
                _end = _match.end()
                html_list[i] = item[:_end] + _id + item[_end:]
            else:
                # 非超链接的情况
                _match = re.search(r'>', item)
                _start = _match.start()
                html_list[i] = item[:_start] + _id + item[_start:]
    html = ''.join(html_list)
    write_file(html, path._raw_path)

if __name__ == "__main__":
    # 指定目录路径
    path = os.getcwd() + "\\test"
    root_folder = Path(path)
    deep_directory(root_folder)
    deep_directory(root_folder, 'html')

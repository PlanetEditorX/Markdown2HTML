import os
import re
import shutil
import markdown
from pathlib import Path

root_folder = '' # 当前目录
css_path = ''
css_file = ''

# 递归遍历目录树
def deep_directory(path, _type='md'):
    global css_file
    if _type == 'md':
        for entry in os.scandir(path):
            if entry.is_dir():
                shutil.copy(css_path, entry)
                css_file = entry.path + "\\styles.css"
        for item in path.rglob('*.md'):
            # 分离文件名和后缀
            path, _ext = os.path.splitext(item._raw_path)
            markdown_text = read_file(item._raw_path)
            content_convert(markdown_text, path)
    else:
        # 地址转换, 因为需要查找文件是否存在，所以地址转换分离
        for item in path.rglob('*.html'):
            HTML_PATH(item)

# 打开Markdown文件并读取内容
def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as md_file:
            return md_file.read()
    except Exception as e:
        print(f"▻ 读取{path}发生异常:", e)

# 查找文件绝对地址
def find_absolute_path(path):
    _list = list(root_folder.glob(f"**/{path}"))
    # 文件存在时替换为绝对地址
    if _list:
        return list(root_folder.glob(f"**/{path}"))[0]._raw_path
    return path

# 替换图片路径
def replace_with_img(match):
    path = match.group(1)  # 图片路径
    path = find_absolute_path(path)
    try:
        align = match.group(2)  # L 或 R
        width = match.group(3)  # 宽度
    except IndexError:
        align = ''
        width = ''
    img_tag = f'<img src="{path}" alt="Image"'
    if align:
        # 如果有 |L 或 |R，可以添加对应的 CSS 类
        if align == 'L':
            img_tag += ' class="align-left"'
        elif align == 'R':
            img_tag += ' class="align-right"'
    if width:
        img_tag += f' width="{width}"'
    else:
        img_tag += f'  style="max-width: 80%;"'
    img_tag += '>'
    return img_tag

# markdown内容转换
def content_convert(text, path):
    # 替换md为html
    text = re.sub(f".md", ".html", text)
    # 转换Markdown到HTML
    body = markdown.markdown(text)
    pattern = r'!\[\[(assets/[^|]+)\|?([A-Z])?\|?(\d+)?\]\]'

    head = f"<!DOCTYPE html>\r\n<html lang=\"zh-CN\">\r\n<head>\r\n<meta charset=\"UTF-8\">\r\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\r\n<title>{Path(path).name}</title>\r\n<link rel=\"stylesheet\" href=\"{css_file}\">\r\n"

    # 有数学公式
    if re.search(r'(.*\$.*\^.*)|(frac)', text):
        head += "<script id=\"MathJax-script\" async src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\"></script>\r\n<script>MathJax={ tex: { inlineMath: [['$', '$'], ['\\(', '\\$']] } };</script>"
    # 有Mermaid图表
    if re.search(r'(mermaid)', text):
        head += "<script src=\"https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js\"></script>\r\n<script>mermaid.initialize({startOnLoad: true,theme: 'neutral',securityLevel: 'loose',flowchart: { useMaxWidth: false,htmlLabels: true } });</script>"

    head += "</head>"

    # 替换所有匹配的内容
    body = "<body>\r\n" + re.sub(pattern, replace_with_img, body).replace('target="_blank"', '') + "</body>\r\n"

    if re.search(r'(mermaid)', body):
        # 找到第一个匹配的```mermaid,并循环替换对应的```mermaid... ```
        _pattern = r"```mermaid"
        match = re.search(_pattern, body)
        while match:
            # 找到开始位置
            start_index = match.end()
            # 替换 ```mermaid 为 <div class="mermaid"> 只替换第一个
            start = re.sub(r'```mermaid', r'<div class="mermaid">', body[:start_index], count=1)
            # 找到结束位置
            match_2 = re.search(r"```", body[start_index:])
            end_index = start_index + match_2.end()
            # 替换第一个 ``` 为 </div>
            end = re.sub(r'```', r'</div>', body[start_index:end_index], count=1)
            cleaned_text = re.sub(r'<p>|</p>|</div>', '', end)
            # 确保 Mermaid 代码格式正确
            end = re.sub(r'--&gt;', '-->', cleaned_text) + "</div>"
            body = start + end + body[end_index:]
            match = re.search(_pattern, body)

    end = "</html>"

    write_file(head + body + end, f"{path}.html")

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
    pattern = r'<a[^>]*\s+href="([^"]+)"'
    matches = re.findall(pattern, html)
    if matches:
        for item in matches:
            name = item.split('#')
            # 文件存在时替换为绝对地址
            html = html.replace(item, find_absolute_path(name[0]))
    # 锚点
    html = html.replace('#^', '#')
    # 替换UUID为id
    html_list = [s for s in html.split('\n') if s != ""]
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
    html = '\n'.join(html_list)
    write_file(html, path._raw_path)

if __name__ == "__main__":
    # 指定目录路径
    path = os.getcwd() + "\\test"
    css_path = os.getcwd() + "\\src\\styles.css"
    root_folder = Path(path)
    deep_directory(root_folder)
    deep_directory(root_folder, 'html')

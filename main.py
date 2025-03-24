import os
import re
import sys
import shutil
import markdown
from pathlib import Path
from pypinyin import lazy_pinyin
from types import SimpleNamespace

root_folder = '' # 当前目录
css_path = ''
css_file = ''
# 标题列表
tilte_list = [
    ['一、','二、','三、','四、','五、','六、','七、','八、','九、','十、','十一、','十二、','十三、','十四、','十五、','十六、','十七、','十八、','十九、','二十、'],
    ['（一）','（二）','（三）','（四）','（五）','（六）','（七）','（八）','（九）','（十）','（十一）','（十二）','（十三）','（十四）','（十五）','（十六）','（十七）','（十八）','（十九）','（二十）']
]
# 对应目录字典
menu_dict = {}
# 转换类型
inline_folder = False

# 递归遍历目录树
def deep_directory(path, _type='md'):
    global css_file
    if _type == 'md':
        # 为直接目录
        if inline_folder:
            # 拷贝css样式
            shutil.copy(css_path, path._raw_path)
            css_file = path._raw_path + "\\styles.css"
        for item in path.rglob('*.md'):
            # 分离文件名和后缀
            path, _ext = os.path.splitext(item._raw_path)
            markdown_text = read_file(item._raw_path)
            content_convert(markdown_text, path)
    elif _type == 'html':
        # 地址转换, 因为需要查找文件是否存在，所以地址转换分离
        for item in path.rglob('*.html'):
            HTML_PATH(item)
    # 生成目录
    else:
        dir_list = []
        for entry in os.scandir(path):
            if entry.is_dir():
                if not inline_folder:
                    # 拷贝css样式
                    shutil.copy(css_path, entry)
                    css_file = entry.path + "\\styles.css"
                # 是否是全是文件夹的结构
                is_all_dir = True
                if not inline_folder:
                    dir_list = []
                inline_html_list = []
                for folder in os.scandir(entry.path):
                    if not inline_folder:
                        html_list = []
                        # 最外层目录
                        if folder.is_dir():
                            # 次级目录
                            for item in os.scandir(folder.path):
                                if item.name.endswith('html'):
                                    html_list.append(item)
                            # 按拼音排序
                            html_list = sorted(html_list, key=lambda x: lazy_pinyin(x.name))
                            if html_list:
                                dir_list.append({
                                    'father': folder,
                                    'childrens': html_list
                                })
                        elif folder.name not in ['styles.css', 'index.html']:
                            is_all_dir = False
                    else:
                        if folder.name.endswith('html'):
                            inline_html_list.append(folder)
                            inline_html_list = sorted(inline_html_list, key=lambda x: lazy_pinyin(x.name))

                if inline_folder:
                    dir_list.append({
                                'father': entry,
                                'childrens': inline_html_list
                            })

                if not inline_folder:
                    # 全是文件夹，生成目录页
                    dir_list = sorted(dir_list, key=lambda x: lazy_pinyin(x['father'].name))
                    if is_all_dir and not inline_folder:
                        index_page(dir_list, entry)
        # 直接目录
        if inline_folder:
            # 将字典转换为 SimpleNamespace 对象
            index_page(dir_list, SimpleNamespace(**{
                'name': path.name,
                'path': path._raw_path
            }))
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

# Mermaid图表样式
def mermaid_style(index, uuid):
    match index % 5:
        case 0:
            fill = "e1f5fe"
            stroke = "2196f3"
        case 1:
            fill = "e8f5e9"
            stroke = "4caf50"
        case 2:
            fill = "f3e5f6"
            stroke = "9c27b0"
        case 3:
            fill = "fff8e1"
            stroke = "ffc107"
        case 4:
            fill = "ffebee"
            stroke = "f44336"
    return f"style {uuid} fill:#{fill},stroke:#{stroke}"

# 数字转化
def num_to_seq(level, num):
    if not isinstance(num, int) or num < 0:
        return num
    # 小于20直接从参数中读取数据
    if num <= 20:
        return tilte_list[level-1][num-1]
    match level:
        case 3:
            return f"{num}."
        case 4:
            return f"({num})"

    units = ['', '十', '百', '千', '万', '十', '百', '千', '亿']
    chinese_num = {
        0: '零', 1: '一', 2: '二', 3: '三', 4: '四',
        5: '五', 6: '六', 7: '七', 8: '八', 9: '九'
    }
    result = ''
    str_num = str(num)
    length = len(str_num)
    for i in range(length):
        n = int(str_num[i])
        if n != 0:
            result += chinese_num[n] + units[length - i - 1]
        else:
            if not result.endswith('零'):
                result += '零'
    # 处理连续的零
    result = result.replace('零零', '零')
    # 处理零万、零亿
    result = result.replace('零万', '万')
    result = result.replace('零亿', '亿')
    # 处理最后的零
    result = result.rstrip('零')
    match level:
        case 1:
            return f"{result}、"
        case 2:
            return f"（{result}）"
    return result

# 目录页
def index_page(data, info):
    """
    生成目录页
    :param data: 首页网页数据
    :param info: 目录信息
        - name: 目录名字
        - path: 目录地址
    """
    global menu_list
    head = head_chunk(info.name) + "</head>"
    body_text = ''
    for folder in enumerate(data):
        # 最近序号，去除【数字】
        body_text += f"<h3><a href=\"{folder[1]['childrens'][0].path}\">{num_to_seq(1, folder[0]+1)}{re.sub(r'【\d+】', '', folder[1]['father'].name)}</a></h3></h3>\n"
        for child in enumerate(folder[1]['childrens']):
            body_text += f"<p><a href=\"{child[1].path}\">{num_to_seq(2, child[0]+1)}{child[1].name.replace(".html", "")}</a></p>\n"
            menu_dict[child[1].path.replace(".html", "")] = f"{info.path}\\index.html"
    body = "<body>\r\n<hr style='border-top-style: dotted !important;'>" + body_text + "</body>\r\n</html>"
    write_file(head + body, f"{info.path}\\index.html")

# head片段
def head_chunk(title):
    return f"<!DOCTYPE html>\r\n<html lang=\"zh-CN\">\r\n<head>\r\n<meta charset=\"UTF-8\">\r\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\r\n<title>{title}</title>\r\n<link rel=\"stylesheet\" href=\"{css_file}\">\r\n"

# markdown内容转换
def content_convert(text, path):
    global css_file
    is_root = False
    child_path = Path(path)
    ground_father_path = child_path.parent.parent
    # 直接目录当上上级为根目录时
    if inline_folder and ground_father_path._raw_path == root_folder._raw_path:
        is_root = True
        menu_start = f"<blockquote>\n<p><a href=\"{root_folder._raw_path}\index.html\">首页</a></p></blockquote>\n"
        menu_end = f"<hr style='border-top-style: dotted !important;'>\n<blockquote>\n<p><a href=\"{root_folder._raw_path}\index.html\">END</a></p></blockquote>\n"
    # 多一级目录
    if not inline_folder and ground_father_path.parent._raw_path == root_folder._raw_path:
        is_root = True
        menu_start = f"<blockquote>\n<p><a href=\"{ground_father_path._raw_path}\index.html\">首页</a></p></blockquote>\n"
        menu_end = f"<hr style='border-top-style: dotted !important;'>\n<blockquote>\n<p><a href=\"{ground_father_path._raw_path}\index.html\">END</a></p></blockquote>\n"
        # 拷贝css样式
        shutil.copy(css_path, ground_father_path._raw_path)
        css_file = ground_father_path._raw_path + "\\styles.css"

    # 替换md为html
    text = re.sub(f".md", ".html", text)
    # 转换Markdown到HTML
    body = markdown.markdown(text)
    pattern = r'!\[\[(assets/[^|]+)\|?([A-Z])?\|?(\d+)?\]\]'

    head = head_chunk(Path(path).name)

    # 有数学公式
    if re.search(r'(.*\$.*\^.*)|(frac)', text):
        head += "<script id=\"MathJax-script\" async src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\"></script>\r\n<script>MathJax={ tex: { inlineMath: [['$', '$'], ['\\(', '\\$']] } };</script>"
    # 有Mermaid图表
    if re.search(r'(mermaid)', text):
        head += "<script src=\"https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js\"></script>\r\n<script>mermaid.initialize({startOnLoad: true,theme: 'neutral',securityLevel: 'loose',flowchart: { useMaxWidth: false,htmlLabels: true } });</script>"

    head += "</head>"

    # 替换所有匹配的内容
    if is_root:
        body = "<body>\r\n" + menu_start + re.sub(pattern, replace_with_img, body).replace('target="_blank"', '') + menu_end + "</body>\r\n"
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
            # 颜色处理
            color_pattern = r'\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b'
            uuids_list = re.findall(color_pattern, cleaned_text)
            if uuids_list:
                line_style = "style emperor fill:#ffd700,stroke:#ffa500,stroke-width:2px"
                for _item in enumerate(uuids_list):
                    line_style += "\n" +mermaid_style(_item[0], _item[1])
            # 确保 Mermaid 代码格式正确
            end = re.sub(r'--&gt;', '-->', cleaned_text) + f"{line_style}</div>"
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
    if len(sys.argv) > 1:
        # 获取命令行参数，手动输入需要转换的目录
        # 参数1：外层地址，该地址下为多个需要转换的文件夹
        # 参数2：0: 外部有一层文件夹 1: 实际所在文件夹
        #       C:\Users\DearX\Documents\Github\Markdown2HTML\test ---> 外层文件夹，在里面具体目录下生成目录
        #       C:\Users\DearX\Documents\Github\Markdown2HTML\test\GWY 1 ---> 实际文件夹，直接在该地址下生成目录
        path = sys.argv[1]
        if len(sys.argv) > 2 and int(sys.argv[2]):
            inline_folder = True
    else:
        # 指定目录路径,将需要转为html的目录放在该目录下
        path = os.getcwd() + "\\test"
    css_path = os.getcwd() + "\\src\\styles.css"
    root_folder = Path(path)
    deep_directory(root_folder, 'md')
    deep_directory(root_folder, 'html')
    deep_directory(root_folder, 'menu')

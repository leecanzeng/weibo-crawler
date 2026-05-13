"""
通用 Markdown → HTML 转换器（咨询报告风格）

用法:
    python pitch_lantu/md_to_html.py <md路径> [<md路径2> ...]

不传参数时，转换 pitch_lantu/taskA_mpv/ 和 taskB_phev_suv/ 下的两份比稿报告。

输出: 同目录下同名 .html
"""
import os
import sys
from pathlib import Path

import markdown

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# 咨询报告风格 CSS：McKinsey / BCG 视觉语言（克制 + 灰阶 + 精确）
CSS = """
:root {
    --c-ink: #1d252d;
    --c-muted: #5a6471;
    --c-line: #e3e6ea;
    --c-bg: #fafbfc;
    --c-accent: #003a70;
    --c-accent-soft: #f0f4f9;
    --c-emph: #c5365b;
}

* { box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                 "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
    font-size: 15px;
    line-height: 1.7;
    color: var(--c-ink);
    background: #fff;
    max-width: 1100px;
    margin: 0 auto;
    padding: 48px 56px 64px 56px;
}

h1 {
    font-size: 30px;
    font-weight: 600;
    color: var(--c-accent);
    border-bottom: 3px solid var(--c-accent);
    padding-bottom: 16px;
    margin: 0 0 28px 0;
    letter-spacing: -0.5px;
}

h2 {
    font-size: 22px;
    font-weight: 600;
    color: var(--c-ink);
    margin: 48px 0 18px 0;
    padding-left: 14px;
    border-left: 4px solid var(--c-accent);
    letter-spacing: -0.2px;
}

h3 {
    font-size: 17px;
    font-weight: 600;
    color: var(--c-ink);
    margin: 26px 0 12px 0;
}

h4 {
    font-size: 15px;
    font-weight: 600;
    color: var(--c-muted);
    margin: 18px 0 8px 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

p, li { color: var(--c-ink); }

blockquote {
    margin: 14px 0;
    padding: 10px 16px;
    border-left: 3px solid var(--c-line);
    background: var(--c-bg);
    color: var(--c-muted);
    font-style: normal;
    font-size: 14px;
}

blockquote p { margin: 4px 0; }

a { color: var(--c-accent); text-decoration: none; }
a:hover { text-decoration: underline; }

code {
    background: var(--c-accent-soft);
    color: var(--c-accent);
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 13px;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}

pre {
    background: var(--c-bg);
    border: 1px solid var(--c-line);
    border-radius: 4px;
    padding: 14px 18px;
    overflow-x: auto;
    font-size: 13px;
}
pre code { background: transparent; color: var(--c-ink); padding: 0; }

hr {
    border: none;
    border-top: 1px solid var(--c-line);
    margin: 36px 0;
}

ul, ol { padding-left: 24px; margin: 10px 0; }
li { margin: 4px 0; }

strong { color: var(--c-ink); font-weight: 600; }

/* 表格：清晰的咨询风格 */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 18px 0;
    font-size: 13.5px;
    background: #fff;
}
thead {
    background: var(--c-accent);
    color: #fff;
}
th {
    text-align: left;
    padding: 10px 12px;
    font-weight: 600;
    font-size: 13px;
    border-bottom: 2px solid var(--c-accent);
}
td {
    padding: 9px 12px;
    border-bottom: 1px solid var(--c-line);
    vertical-align: top;
}
tbody tr:hover { background: var(--c-accent-soft); }
tbody tr:nth-child(2n) { background: var(--c-bg); }
tbody tr:nth-child(2n):hover { background: var(--c-accent-soft); }

/* 文档头部元信息（reference 风的引用块） */
.meta-block {
    background: var(--c-bg);
    border-left: 4px solid var(--c-accent);
    padding: 14px 20px;
    margin: 0 0 32px 0;
    font-size: 14px;
    color: var(--c-muted);
}
.meta-block p { margin: 4px 0; }

/* 章节锚点导航 */
.toc {
    background: var(--c-bg);
    border: 1px solid var(--c-line);
    border-radius: 6px;
    padding: 16px 24px;
    margin: 24px 0 40px 0;
    font-size: 14px;
}
.toc-title {
    font-weight: 600;
    color: var(--c-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 12px;
    margin-bottom: 8px;
}
.toc ol { padding-left: 20px; margin: 0; }
.toc li { margin: 3px 0; }

/* 高亮某些关键数字（互动 / 占比） */
em { color: var(--c-emph); font-style: normal; font-weight: 500; }
"""


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""


def convert(md_path: Path) -> Path:
    """转换单个 .md 文件，返回 .html 路径"""
    md_text = md_path.read_text(encoding="utf-8")

    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "nl2br"],
        output_format="html5",
    )
    body = md.convert(md_text)

    # 标题取 md 第一个 H1 (兜底用文件名)
    title = md_path.stem
    for line in md_text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    html_text = HTML_TEMPLATE.format(title=title, css=CSS, body=body)

    out_path = md_path.with_suffix(".html")
    out_path.write_text(html_text, encoding="utf-8")
    return out_path


def main():
    if len(sys.argv) > 1:
        paths = [Path(p) for p in sys.argv[1:]]
    else:
        # 默认转换两个比稿报告
        here = Path(__file__).parent
        paths = [
            here / "taskA_mpv" / "任务A_MPV比稿分析.md",
            here / "taskB_phev_suv" / "任务B_中大型SUV_PHEV比稿分析.md",
        ]

    for p in paths:
        if not p.is_file():
            print(f"[WARN] {p} 不存在，跳过")
            continue
        out = convert(p)
        print(f"  {p.name}  →  {out.name}")
    print(f"\n完成，共 {len(paths)} 份")


if __name__ == "__main__":
    main()

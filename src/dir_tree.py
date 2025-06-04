import os


def should_skip_file(name):
    """
    判断是否应该跳过显示某个文件或目录
    
    跳过的文件类型：
    - 以 .~ 开头的临时文件（如 Office 临时文件）
    - 以 . 开头的隐藏文件（除了 .gitignore, .env 等常见配置文件）
    - 以 ~ 结尾的备份文件
    - __pycache__ 目录
    - node_modules 目录
    - .DS_Store 文件
    - Thumbs.db 文件
    """
    # Office 临时文件
    if name.startswith('.~'):
        return True
    
    # 备份文件
    if name.endswith('~'):
        return True
    
    # 系统临时文件
    if name in ['.DS_Store', 'Thumbs.db', 'desktop.ini']:
        return True
    
    # 缓存目录
    if name in ['__pycache__', 'node_modules', '.pytest_cache']:
        return True
    
    # 隐藏文件（但保留常见的配置文件）
    if name.startswith('.'):
        # 保留的隐藏文件列表
        keep_hidden = {
            '.gitignore', '.env', '.env.example', '.dockerignore',
            '.editorconfig', '.eslintrc.js', '.prettierrc', '.babelrc',
            '.vscode', '.idea', '.git'
        }
        if name not in keep_hidden:
            return True
    
    return False


def get_dir_tree_markdown(directory, max_depth=3, max_entries=200):
    """
    获取目录树并以Markdown格式返回

    参数:
        directory: 要扫描的目录路径
        max_depth: 最大递归深度
        max_entries: 最大显示条目数

    返回:
        Markdown格式的目录树字符串
    """

    def build_tree(path, prefix="", depth=0):
        nonlocal entry_count
        if entry_count >= max_entries or depth > max_depth:
            return []

        name = os.path.basename(path)
        
        # 跳过不需要显示的文件
        if should_skip_file(name):
            return []
        
        if os.path.isdir(path):
            line = f"{prefix}📁 {name}"
            result = [line]
            entry_count += 1

            if depth < max_depth:
                try:
                    children = sorted(os.listdir(path))
                    # 过滤掉需要跳过的文件
                    children = [child for child in children if not should_skip_file(child)]
                    
                    for i, child in enumerate(children):
                        child_path = os.path.join(path, child)
                        is_last = i == len(children) - 1
                        new_prefix = prefix + ("    " if is_last else "│   ")
                        child_result = build_tree(
                            child_path,
                            prefix + ("└── " if is_last else "├── "),
                            depth + 1,
                        )
                        result.extend(child_result)
                except PermissionError:
                    # 如果没有权限访问目录，跳过
                    pass
            return result
        else:
            entry_count += 1
            return [f"{prefix}📄 {name}"]

    entry_count = 0
    tree_lines = build_tree(directory)
    markdown = "\n".join(tree_lines)

    if entry_count >= max_entries:
        markdown += "\n...\n[Listing truncated due to max entries limit]\n"

    return markdown

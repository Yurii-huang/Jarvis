import os
import re
from typing import Any, Dict, List
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from jarvis.jarvis_tools.read_code import ReadCodeTool
from jarvis.jarvis_utils import OutputType, PrettyOutput, get_single_line_input, user_confirm


def _parse_file_selection(input_str: str, max_index: int) -> List[int]:
    """Parse file selection expression
    
    Supported formats:
    - Single number: "1"
    - Comma-separated: "1,3,5"
    - Range: "1-5"
    - Combination: "1,3-5,7"
    
    Args:
        input_str: User input selection expression
        max_index: Maximum selectable index
        
    Returns:
        List[int]: Selected index list (starting from 0)
    """
    selected = set()
    
    # Remove all whitespace characters
    input_str = "".join(input_str.split())
    
    # Process comma-separated parts
    for part in input_str.split(","):
        if not part:
            continue
        
        # Process range (e.g.: 3-6)
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                # Convert to index starting from 0
                start = max(0, start - 1)
                end = min(max_index, end - 1)
                if start <= end:
                    selected.update(range(start, end + 1))
            except ValueError:
                PrettyOutput.print(f"忽略无效的范围表达式: {part}", OutputType.WARNING)
        # Process single number
        else:
            try:
                index = int(part) - 1  # Convert to index starting from 0
                if 0 <= index < max_index:
                    selected.add(index)
                else:
                    PrettyOutput.print(f"忽略超出范围的索引: {part}", OutputType.WARNING)
            except ValueError:
                PrettyOutput.print(f"忽略无效的数字: {part}", OutputType.WARNING)
    
    return sorted(list(selected))

def _get_file_completer(root_dir: str) -> Completer:
    """Create file path completer"""
    class FileCompleter(Completer):
        def __init__(self, root_dir: str):
            self.root_dir = root_dir
            
        def get_completions(self, document, complete_event):
            text = document.text_before_cursor
            
            if not text:
                for path in self._list_files(""):
                    yield Completion(path, start_position=0)
                return
                
            # Generate fuzzy matching pattern
            pattern = '.*'.join(map(re.escape, text))
            try:
                regex = re.compile(pattern, re.IGNORECASE)
            except re.error:
                return
                
            for path in self._list_files(""):
                if regex.search(path):
                    yield Completion(path, start_position=-len(text))
        
        def _list_files(self, current_dir: str) -> List[str]:
            """List all files in the specified directory (recursively)"""
            files = []
            search_dir = os.path.join(self.root_dir, current_dir)
            
            for root, _, filenames in os.walk(search_dir):
                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, self.root_dir)
                    if not any(part.startswith('.') for part in rel_path.split(os.sep)):
                        files.append(rel_path)
            
            return sorted(files)

    return FileCompleter(root_dir)

def _fuzzy_match_files(root_dir: str, pattern: str) -> List[str]:
    """Fuzzy match file path
    
    Args:
        pattern: Matching pattern
        
    Returns:
        List[str]: List of matching file paths
    """
    matches = []
    
    # 将模式转换为正则表达式
    pattern = pattern.replace('.', r'\.').replace('*', '.*').replace('?', '.')
    pattern = f".*{pattern}.*"  # 允许部分匹配
    regex = re.compile(pattern, re.IGNORECASE)
    
    # 遍历所有文件
    for root, _, files in os.walk(root_dir):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, root_dir)
            # 忽略 .git 目录和其他隐藏文件
            if not any(part.startswith('.') for part in rel_path.split(os.sep)):
                if regex.match(rel_path):
                    matches.append(rel_path)
    
    return sorted(matches)

def select_files(related_files: List[Dict[str, str]], root_dir: str) -> List[Dict[str, str]]:
    """Let the user select and supplement related files"""
    output = ""
    # Display found files
    selected_files = list(related_files)  # Default select all
    for i, file in enumerate(related_files, 1):
        output += f"[{i}] {file['file']} ({file['reason']})\n"

    # Filter out files that do not exist
    related_files = [f for f in related_files if os.path.isfile(os.path.join(root_dir, f["file"]))]

    if output:
        PrettyOutput.section("相关文件", OutputType.INFO)
        PrettyOutput.print(output, OutputType.INFO, lang="markdown")
    
    if len(related_files) > 0:
        # Ask the user if they need to adjust the file list
        if user_confirm("是否需要调整文件列表？", False):
            # Let the user select files
            numbers = get_single_line_input("请输入要包含的文件编号（支持: 1,3-6格式, 按回车保持当前选择）").strip()
            if numbers:
                selected_indices = _parse_file_selection(numbers, len(related_files))
                if selected_indices:
                    selected_files = [related_files[i] for i in selected_indices]
                else:
                    PrettyOutput.print("没有有效的文件被选择, 保持当前选择", OutputType.WARNING)
    
    tips = ""
    # Ask if they need to supplement files
    if user_confirm("是否需要补充其他文件？", False):
        # Create file completion session
        session = PromptSession(
            completer=_get_file_completer(root_dir),
            complete_while_typing=True
        )
        PrettyOutput.print("请输入要补充的文件路径（支持Tab补全和*?通配符, 输入空行结束）", OutputType.INFO)
        while True:
            try:
                file_path = session.prompt(">>> ").strip()
            except KeyboardInterrupt:
                break
                
            if not file_path:
                break
                
            # Process wildcard matching
            if '*' in file_path or '?' in file_path:
                matches = _fuzzy_match_files(root_dir, file_path)
                if not matches:
                    PrettyOutput.print("没有找到匹配的文件", OutputType.WARNING)
                    continue
                    
                # Display matching files
                tips = "找到以下匹配的文件:"
                for i, path in enumerate(matches, 1):
                    tips += f"\n[{i}] {path}"
                PrettyOutput.print(tips, OutputType.INFO)
                    
                # Let the user select
                numbers = get_single_line_input("请选择要添加的文件编号（支持: 1,3-6格式, 按回车选择所有）").strip()
                if numbers:
                    indices = _parse_file_selection(numbers, len(matches))
                    if not indices:
                        continue
                    paths_to_add = [matches[i] for i in indices]
                else:
                    paths_to_add = matches
            else:
                paths_to_add = [file_path]
            
            # Add selected files
            tips = "添加以下文件:"
            for path in paths_to_add:
                full_path = os.path.join(root_dir, path)
                if not os.path.isfile(full_path):
                    tips += f"\n文件不存在: {path}"
                    continue
                
                try:
                    selected_files.append({"file": path, "reason": "User Added"})
                    tips += f"\n文件已添加: {path}"
                except Exception as e:
                    tips += f"\n读取文件失败: {str(e)}"
    selected_files = [f for f in selected_files if os.path.isfile(os.path.join(root_dir, f["file"]))]
    if tips:
        PrettyOutput.print(tips, OutputType.INFO)
    return selected_files

def file_input_handler(user_input: str, agent: Any) -> str:
    """Handle file input with optional line ranges.
    
    Args:
        user_input: User input string containing file references
        agent: Agent instance (unused in current implementation)
        
    Returns:
        str: Prompt with file contents prepended if files are found
    """
    prompt = user_input
    files = []
    
    # Match file references in backticks
    file_refs = re.findall(r'`([^`]+)`', user_input)
    
    for ref in file_refs:
        # Handle file:start,end format
        if ':' in ref:
            file_path, line_range = ref.split(':', 1)
            # Initialize with default values
            start_line = 1  # 1-based
            end_line = -1
            
            # Process line range if specified
            if ',' in line_range:
                try:
                    raw_start, raw_end = map(int, line_range.split(','))
                    
                    # Handle special values and Python-style negative indices
                    with open(file_path, 'r', encoding='utf-8') as f:
                        total_lines = len(f.readlines())
                    
                    # Process start line
                    if raw_start == 0:  # 0表示整个文件
                        start_line = 1
                        end_line = total_lines
                    else:
                        start_line = raw_start if raw_start > 0 else total_lines + raw_start + 1
                    
                    # Process end line
                    if raw_end == 0:  # 0表示整个文件（如果start也是0）
                        end_line = total_lines
                    else:
                        end_line = raw_end if raw_end > 0 else total_lines + raw_end + 1
                    
                    # Auto-correct ranges
                    start_line = max(1, min(start_line, total_lines))
                    end_line = max(start_line, min(end_line, total_lines))
                    
                    # Final validation
                    if start_line < 1 or end_line > total_lines or start_line > end_line:
                        raise ValueError

                except (ValueError, FileNotFoundError) as e:
                    PrettyOutput.print(
                        f"无效的行号范围: {line_range} (文件总行数: {total_lines})", 
                        OutputType.WARNING
                    )
                    continue
            
            # Add file if it exists
            if os.path.isfile(file_path):
                files.append({
                    "path": file_path,
                    "start_line": start_line,
                    "end_line": end_line
                })
        else:
            # Handle simple file path
            if os.path.isfile(ref):
                files.append({
                    "path": ref,
                    "start_line": 1,  # 1-based
                    "end_line": -1
                })
    
    # Read and process files if any were found
    if files:
        result = ReadCodeTool().execute({"files": files})
        if result["success"]:
            return result["stdout"] + "\n" + prompt
    
    return prompt

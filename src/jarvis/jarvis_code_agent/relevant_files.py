import os
from typing import Dict, List

from jarvis.jarvis_code_agent.file_select import select_files
from jarvis.jarvis_codebase.main import CodeBase
from jarvis.utils import OutputType, PrettyOutput, is_disable_codebase


def find_relevant_files(user_input: str, root_dir: str) -> List[Dict[str, str]]:
    try:
        files_from_codebase = []
        if not is_disable_codebase():
            PrettyOutput.print("Find files from codebase...", OutputType.INFO)
            codebase = CodeBase(root_dir)
            files_from_codebase = codebase.search_similar(user_input)

        PrettyOutput.print("Find files by agent...", OutputType.INFO)

        selected_files = select_files(files_from_codebase, os.getcwd())
        return selected_files
    except Exception as e:
        return []
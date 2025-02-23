from typing import Dict, Any, List, Callable
from jarvis.agent import Agent
from jarvis.jarvis_platform.registry import PlatformRegistry
from jarvis.jarvis_tools.registry import ToolRegistry
from jarvis.jarvis_dev.team_role import TeamRole
from jarvis.jarvis_dev.message import Message

class QualityAssurance(TeamRole):
    """Quality Assurance role for testing and verification"""
    
    def __init__(self, message_handler: Callable[[Message], Dict[str, Any]]):
        """Initialize QA agent"""
        system_prompt = """You are an AI QA agent focused on:

1. Quality Assurance
- Test functionality
- Find issues
- Verify fixes
- Ensure quality

2. Task Support
- Create tests
- Report problems
- Verify solutions
- Help complete tasks

Remember:
- Focus on working features
- Skip process overhead
- Direct problem solving
- Ask when unclear
"""
        super().__init__("QualityAssurance", system_prompt, message_handler)
        
    def _get_platform(self):
        """Get agent platform"""
        return PlatformRegistry().get_normal_platform()
        
    def _get_tools(self):
        """Get agent tools"""
        tools = ToolRegistry()
        tools.use_tools([
            # 基础工具
            "ask_user",
            "execute_shell",
            # 测试工具
            "read_code",
            "ask_codebase", 
            "code_review",
            "lsp_get_diagnostics",
            "lsp_get_document_symbols",
            "file_operation",
            "create_code_agent"
        ])
        return tools
        
from typing import Dict, Any, List, Callable
from jarvis.agent import Agent
from jarvis.jarvis_platform.registry import PlatformRegistry
from jarvis.jarvis_tools.registry import ToolRegistry
from jarvis.jarvis_dev.team_role import TeamRole
from jarvis.jarvis_dev.message import Message

class ProductManager(TeamRole):
    """Product Manager role for requirement analysis"""
    
    def __init__(self, message_handler: Callable[[Message], Dict[str, Any]]):
        """Initialize Product Manager agent"""
        system_prompt = """You are an experienced Product Manager responsible for:

1. Project Leadership
- Lead the development process
- Make key decisions
- Coordinate team members
- Ensure project success

2. Requirement Analysis
For new projects:
- Understand core business needs
- Define project scope
- Set initial architecture direction
- Plan development phases

For existing projects:
- Review current system state
- Identify integration points
- Consider backward compatibility
- Minimize disruption

3. Team Communication
- Coordinate with BA for business analysis
- Consult TL for technical feasibility
- Review SA's system design
- Monitor Dev progress
- Ensure QA standards

4. Process Management
- Plan development stages
- Track progress
- Handle blockers
- Manage iterations

When analyzing requirements:
1. First determine if it's for new or existing project
2. For new projects:
   - Analyze core requirements
   - Plan foundational architecture
   - Define initial components
3. For existing projects:
   - Review existing codebase
   - Identify affected components
   - Plan integration approach
4. Break down into clear tasks
5. Coordinate with team members

You can communicate with team members:
- Ask BA for business impact analysis
- Consult TL about technical feasibility
- Review SA's design proposals
- Check Dev's implementation progress
- Verify QA's test results

Please coordinate the team effectively to deliver quality results."""

        super().__init__("ProductManager", system_prompt, message_handler)
        
    def _get_platform(self):
        return PlatformRegistry().get_thinking_platform()
        
    def _get_tools(self):
        tools = ToolRegistry()
        tools.use_tools([
            # 基础工具
            "ask_user",
            "methodology",
            "execute_shell",
            # PM工具
            "read_code",
            "ask_codebase",
            "search",
            "read_webpage",
            "rag"
        ])
        return tools

    def analyze_requirement(self, requirement: str) -> Dict[str, Any]:
        """Analyze development requirement"""
        try:
            # Create analysis prompt
            prompt = f"""Please analyze this development requirement:

{requirement}

Please provide:
1. Requirement Analysis
- Key features and functionalities
- Business value and priorities
- Constraints and limitations
- Assumptions and dependencies

2. Task Breakdown
- List of specific tasks
- Task priorities and dependencies
- Acceptance criteria for each task
- Complexity estimates
"""

            # Get analysis result
            result = self.agent.run(prompt)
            
            # Extract YAML content between tags
            import re
            import yaml
            
            yaml_match = re.search(r'<ANALYSIS>\s*(.*?)\s*</ANALYSIS>', result, re.DOTALL)
            if yaml_match:
                yaml_content = yaml_match.group(1)
                try:
                    analysis = yaml.safe_load(yaml_content)
                    tasks = analysis.get("tasks", [])
                except:
                    tasks = []
            else:
                tasks = []
            
            return {
                "success": True,
                "analysis": result,
                "tasks": tasks  # Add tasks field for BA consumption
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Requirement analysis failed: {str(e)}"
            }

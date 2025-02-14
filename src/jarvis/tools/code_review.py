from typing import Dict, Any
import subprocess
import yaml
from jarvis.models.registry import PlatformRegistry
from jarvis.tools.registry import ToolRegistry
from jarvis.utils import OutputType, PrettyOutput, init_env, find_git_root
from jarvis.agent import Agent

class CodeReviewTool:
    name = "code_review"
    description = "Autonomous code review agent for commit analysis"
    parameters = {
        "type": "object",
        "properties": {
            "commit_sha": {
                "type": "string",
                "description": "Target commit SHA to analyze"
            },
            "requirement_desc": {
                "type": "string",
                "description": "Development goal to verify"
            }
        },
        "required": ["commit_sha", "requirement_desc"]
    }

    def __init__(self):
        init_env()
        self.repo_root = find_git_root()

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            commit_sha = args["commit_sha"].strip()
            requirement = args["requirement_desc"].strip()
            
            system_prompt = """You are an autonomous code review expert. Perform in-depth analysis following these guidelines:

REVIEW FOCUS AREAS:
1. Requirement Alignment:
   - Verify implementation matches original requirements
   - Check for missing functionality
   - Identify over-implementation

2. Code Quality:
   - Code readability and structure
   - Proper error handling
   - Code duplication
   - Adherence to style guides
   - Meaningful variable/method names

3. Security:
   - Input validation
   - Authentication/Authorization checks
   - Sensitive data handling
   - Potential injection vulnerabilities
   - Secure communication practices

4. Testing:
   - Test coverage for new code
   - Edge case handling
   - Test readability and maintainability
   - Missing test scenarios

5. Performance:
   - Algorithm efficiency
   - Unnecessary resource consumption
   - Proper caching mechanisms
   - Database query optimization

6. Maintainability:
   - Documentation quality
   - Logging and monitoring
   - Configuration management
   - Technical debt indicators

7. Operational Considerations:
   - Backward compatibility
   - Migration script safety
   - Environment-specific configurations
   - Deployment impacts

REVIEW PROCESS:
1. Retrieve full commit context using git commands
2. Analyze code changes line-by-line
3. Cross-reference with project standards
4. Verify test coverage adequacy
5. Check documentation updates
6. Generate prioritized findings

OUTPUT REQUIREMENTS:
- Categorize issues by severity (Critical/Major/Minor)
- Reference specific code locations
- Provide concrete examples
- Suggest actionable improvements
- Highlight security risks clearly
- Separate technical debt from blockers"""

            summary_prompt = """Please generate a concise summary report of the code review, format as yaml:
<REPORT>
- file: xxxx.py
  location: [start_line_number, end_line_number]
  description: 
  severity: 
  suggestion: 
</REPORT>

Please describe in concise bullet points, highlighting important information.
"""

            tool_registry = ToolRegistry()
            tool_registry.use_tools(["execute_shell", "read_code", "ask_user", "ask_codebase", "find_in_codebase", "create_ctags_agent"])
            tool_registry.dont_use_tools(["code_review"])

            review_agent = Agent(
                name="Code Review Agent",
                platform=PlatformRegistry().get_thinking_platform(),
                system_prompt=system_prompt,
                is_sub_agent=True,
                tool_registry=tool_registry,
                summary_prompt=summary_prompt,
                auto_complete=True
            )
            
            result = review_agent.run(
                f"Analyze commit {commit_sha} for requirement: {requirement}"
            )

            return {
                "success": True,
                "stdout": {"report": result},
                "stderr": ""
            }
            
        except Exception as e:
            return {
                "success": False,
                "stdout": {},
                "stderr": f"Review failed: {str(e)}"
            }

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Autonomous code review tool')
    parser.add_argument('--commit', required=True)
    parser.add_argument('--requirement', required=True)
    args = parser.parse_args()
    
    tool = CodeReviewTool()
    result = tool.execute({
        "commit_sha": args.commit,
        "requirement_desc": args.requirement
    })
    
    if result["success"]:
        PrettyOutput.print("Autonomous Review Result:", OutputType.INFO)
        print(yaml.dump(result["stdout"], allow_unicode=True))
    else:
        PrettyOutput.print(result["stderr"], OutputType.ERROR)

if __name__ == "__main__":
    main()

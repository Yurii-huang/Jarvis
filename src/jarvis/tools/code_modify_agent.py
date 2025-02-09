from typing import Dict, Any

from jarvis.agent import Agent
from jarvis.utils import OutputType, PrettyOutput
from jarvis.jarvis_coder.patch_handler import PatchHandler


class CodeModifyTool:
    name = "execute_code_modification"
    description = "Execute code modifications according to the provided plan"
    parameters = {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "The code modification task description"
            },
            "raw_plan": {
                "type": "string",
                "description": "The complete modification plan in raw text format"
            },
            "structured_plan": {
                "type": "object",
                "description": "The structured modification plan with file paths and their modifications",
                "additionalProperties": {
                    "type": "string"
                }
            }
        },
        "required": ["task", "raw_plan", "structured_plan"]
    }

    def execute(self, args: Dict) -> Dict[str, Any]:
        """Execute code modifications using PatchHandler"""
        try:
            task = args["task"]
            raw_plan = args["raw_plan"]
            structured_plan = args["structured_plan"]

            PrettyOutput.print("Executing code modifications...", OutputType.INFO)

            # Create patch handler instance
            patch_handler = PatchHandler()

            # Apply patches and handle the process
            success = patch_handler.handle_patch_application(
                feature=task,
                structed_plan=structured_plan
            )

            if not success:
                return {
                    "success": False,
                    "error": "Code modification was cancelled or failed",
                    "stdout": "Changes have been rolled back",
                    "stderr": ""
                }

            return {
                "success": True,
                "stdout": "Code modifications have been successfully applied and committed",
                "stderr": ""
            }

        except Exception as e:
            PrettyOutput.print(str(e), OutputType.ERROR)
            return {
                "success": False,
                "error": f"Failed to execute code modifications: {str(e)}",
                "stdout": "",
                "stderr": str(e)
            }

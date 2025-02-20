import os
import shutil
import subprocess
from typing import List, Dict, Optional, Tuple, Any
import json
from jarvis.jarvis_lsp.base import BaseLSP
from jarvis.utils import PrettyOutput, OutputType

class CPPLSP(BaseLSP):
    """C++ LSP implementation using clangd."""
    
    language = "cpp"

    @staticmethod
    def check() -> bool:
        """Check if clangd is installed."""
        return shutil.which("clangd") is not None
    
    def __init__(self):
        self.workspace_path = ""
        self.clangd_process = None
        self.request_id = 0
    
    def initialize(self, workspace_path: str) -> bool:
        try:
            self.workspace_path = workspace_path
            # Start clangd process
            self.clangd_process = subprocess.Popen(
                ["clangd", "--background-index"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Send initialize request
            self._send_request("initialize", {
                "processId": os.getpid(),
                "rootUri": f"file://{workspace_path}",
                "capabilities": {}
            })
            
            return True
        except Exception as e:
            PrettyOutput.print(f"C++ LSP 初始化失败: {str(e)}", OutputType.ERROR)
            return False
    
    def _send_request(self, method: str, params: Dict) -> Optional[Dict]:
        """Send JSON-RPC request to clangd."""
        if not self.clangd_process:
            return None
            
        try:
            self.request_id += 1
            request = {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": method,
                "params": params
            }
            
            self.clangd_process.stdin.write(json.dumps(request).encode() + b"\n") # type: ignore
            self.clangd_process.stdin.flush() # type: ignore
            
            response = json.loads(self.clangd_process.stdout.readline().decode()) # type: ignore
            return response.get("result")
        except Exception:
            return None
    
    def find_references(self, file_path: str, position: Tuple[int, int]) -> List[Dict[str, Any]]:
        result = self._send_request("textDocument/references", {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": {"line": position[0], "character": position[1]},
            "context": {"includeDeclaration": True}
        })
        return result or [] # type: ignore
    
    def find_definition(self, file_path: str, position: Tuple[int, int]) -> Optional[Dict[str, Any]]:
        result = self._send_request("textDocument/definition", {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": {"line": position[0], "character": position[1]}
        })
        return result[0] if result else None
    
    def get_document_symbols(self, file_path: str) -> List[Dict[str, Any]]:
        result = self._send_request("textDocument/documentSymbol", {
            "textDocument": {"uri": f"file://{file_path}"}
        })
        return result or [] # type: ignore
    
    def get_diagnostics(self, file_path: str) -> List[Dict[str, Any]]:
        # Send didOpen notification to trigger diagnostics
        self._send_request("textDocument/didOpen", {
            "textDocument": {
                "uri": f"file://{file_path}",
                "languageId": "cpp",
                "version": 1,
                "text": open(file_path).read()
            }
        })
        
        # Wait for diagnostic notification
        try:
            response = json.loads(self.clangd_process.stdout.readline().decode()) # type: ignore
            if response.get("method") == "textDocument/publishDiagnostics":
                return response.get("params", {}).get("diagnostics", [])
        except Exception:
            pass
        return []
    
    def prepare_rename(self, file_path: str, position: Tuple[int, int]) -> Optional[Dict[str, Any]]:
        result = self._send_request("textDocument/prepareRename", {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": {"line": position[0], "character": position[1]}
        })
        return result
    
    def validate_edit(self, file_path: str, edit: Dict[str, Any]) -> bool:
        # Send workspace/willRenameFiles request to check validity
        result = self._send_request("workspace/willRenameFiles", {
            "files": [{
                "oldUri": f"file://{file_path}",
                "newUri": f"file://{file_path}.tmp"
            }]
        })
        return bool(result)
    
    def shutdown(self):
        if self.clangd_process:
            try:
                self._send_request("shutdown", {})
                self.clangd_process.terminate()
                self.clangd_process = None
            except Exception:
                pass

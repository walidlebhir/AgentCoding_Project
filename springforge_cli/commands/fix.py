from springforge_cli.core.agent import Agent
from springforge_cli.utils.logger import info, success, error, step, header


def handle(agent: Agent, bug_description: str, project_path: str | None = None) -> bool:
    header("SPRINGFORGE — Fix Bug")
    info(f"Bug : {bug_description}")
    if project_path:
        info(f"Project : {project_path}")
    step("Analyzing bug report...")
    step("Scanning codebase for issues...")
    step("Applying fix...")
    result = agent.fix(bug_description, project_path)
    if result:
        success("Bug fixed successfully")
    else:
        error("Failed to fix bug")
    return result

from springforge_cli.core.agent import Agent
from springforge_cli.utils.logger import info, success, error, step, header, warn


def handle(agent: Agent, project_path: str, prompt: str) -> bool:
    header("SPRINGFORGE — Edit")
    info(f"Project : {project_path}")
    info(f"Request : {prompt}")
    step("Analyzing project structure...")
    step("Applying modifications...")
    result = agent.edit(project_path, prompt)
    if result:
        success("Project modified successfully")
    else:
        error("Edit failed")
    return result

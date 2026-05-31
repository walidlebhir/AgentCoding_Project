from springforge_cli.core.agent import Agent
from springforge_cli.utils.logger import info, success, error, step, header


def handle(agent: Agent, prompt: str, output_dir: str | None = None) -> bool:
    header("SPRINGFORGE — Generate")
    info(f"Prompt: {prompt}")
    step("Analyzing request...")
    step("Generating Spring Boot architecture...")
    step("Writing files...")
    result = agent.generate(prompt, output_dir)
    if result:
        success("Project generated successfully")
    else:
        error("Generation failed")
    return result

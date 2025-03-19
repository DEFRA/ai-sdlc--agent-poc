"""Data Model Analysis Node for the code analysis workflow."""

import json
import logging
from datetime import datetime, timezone

import aiohttp
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from src.agents.states.code_analysis_state import CodeAnalysisState
from src.config.settings import settings
from src.models.code_analysis import CodeAnalysisStatus, CodeAnalysisUpdate
from src.repositories.code_analysis import code_analysis_repository

logger = logging.getLogger(__name__)

# Template for data model analysis
DATA_MODEL_ANALYSIS_TEMPLATE = """
You are an expert software architect tasked with analyzing data models in a codebase.

You have been provided with the contents of data model related files in the <files_content> tag.

<files_content>
{files_content}
</files_content>

Generate a comprehensive data model analysis document that includes:

1. Overview of the Data Architecture
   - High-level description of the data model
   - Key entities and their purposes
   - Data persistence approach

2. Logical Data Model
   - Detailed description of each entity
   - Attributes and their types
   - Relationships between entities

3. Entity Relationship Diagram
   - Create a mermaid.js ERD diagram showing all entities and their relationships
   - Use proper mermaid.js ERD syntax
   - Include cardinality in relationships

4. Implementation Details
   - How the data model is implemented
   - Any ORM or database specific details
   - Data validation and constraints

5. API Integration
   - How the data model is exposed via APIs
   - Data transfer objects (DTOs)
   - Serialization/deserialization approaches

Format the output in markdown, with the ERD diagram in a mermaid code block.
"""


def parse_xml_response(xml_content: str) -> dict:
    """
    Parse XML response from the Repo Files API into a dictionary.
    The response is in Repomix format which combines multiple files into a single document.

    Args:
        xml_content: XML string from the API in Repomix format

    Returns:
        Dictionary containing the parsed file contents, with file paths as keys
    """
    try:
        # Log the first part of XML content for debugging
        logger.debug("Received XML content (first 500 chars): %s", xml_content[:500])

        # Find the <files> section which contains all file contents
        files_start = xml_content.find("<files>")
        files_end = xml_content.find("</files>")

        if files_start == -1 or files_end == -1:
            logger.error("Could not find <files> section in XML response")
            error_msg = "Invalid XML format: missing <files> section"
            raise ValueError(error_msg)

        files_content = {}

        # Extract individual file sections
        files_text = xml_content[files_start:files_end]
        file_sections = files_text.split('<file path="')[
            1:
        ]  # Split and remove first empty part

        for file_section in file_sections:
            try:
                # Extract file path
                file_path = file_section[: file_section.find('">')]

                # Find content boundaries
                content_start = file_section.find('">') + 2
                content_end = file_section.find("</file>")

                if content_start == -1 or content_end == -1:
                    logger.warning(
                        "Could not find content boundaries for file: %s", file_path
                    )
                    continue

                # Extract and process content
                content = file_section[content_start:content_end]

                # Process the content: remove line numbers and clean up
                lines = []
                for line in content.split("\n"):
                    # Remove line numbers (e.g., " 1: ", "10: ")
                    line = line.strip()
                    if line:
                        # Match pattern "XX: " where X is a digit
                        colon_pos = line.find(": ")
                        if colon_pos > 0 and line[:colon_pos].strip().isdigit():
                            line = line[colon_pos + 2 :]
                        lines.append(line)

                # Store processed content
                files_content[file_path] = "\n".join(lines)
                logger.debug("Successfully parsed file: %s", file_path)

            except Exception as e:
                logger.warning("Error parsing file section: %s", str(e))
                continue

        if not files_content:
            logger.warning("No files were successfully parsed from the XML response")
            error_msg = "No files could be parsed from the response"
            raise ValueError(error_msg)

        return files_content

    except Exception as e:
        logger.error("Error parsing XML response: %s", e)
        logger.error(
            "Failed XML content: %s", xml_content[:1000]
        )  # Log first 1000 chars
        error_msg = f"Failed to parse XML response: {e}"
        raise ValueError(error_msg) from e


async def data_model_analysis_node(
    state: CodeAnalysisState,
) -> CodeAnalysisState:
    """
    Data Model Analysis Node for the code analysis workflow.

    This node analyzes the identified data model files and generates a comprehensive
    report including an ERD diagram in mermaid format.

    Args:
        state: The current state of the workflow.

    Returns:
        Updated state with data model analysis report.
    """
    logger.info(
        "Starting Data Model Analysis Node for repository: %s",
        state.repository_url,
    )

    # Check if we have the required data
    if not state.data_model_files:
        state.status = CodeAnalysisStatus.ERROR
        state.error = "No data model files identified for analysis"

        # Update the database record
        if state.analysis_id:
            # Get current state from database to preserve other fields
            current_doc = await code_analysis_repository.get(state.analysis_id)
            update_data = CodeAnalysisUpdate(
                status=CodeAnalysisStatus.ERROR,
                error=state.error,
                updated_at=datetime.now(timezone.utc),
                # Preserve existing fields
                data_model_files=current_doc.data_model_files if current_doc else None,
                data_model_analysis=current_doc.data_model_analysis
                if current_doc
                else None,
            )
            await code_analysis_repository.update(state.analysis_id, update_data)

        return state

    try:
        # Call Repo Files API to get file contents
        if not settings.REPOSITORY_INGEST_API_URL:
            error_msg = (
                "REPOSITORY_INGEST_API_URL is not set in the environment variables"
            )
            raise ValueError(error_msg)

        repo_files_url = f"{settings.REPOSITORY_INGEST_API_URL}/api/v1/repo-files"

        # Log the state of data_model_files
        logger.info(
            "Data model files to be analyzed: %s",
            json.dumps(state.data_model_files, indent=2),
        )

        # Prepare API request payload
        payload = {
            "repositoryUrl": str(state.repository_url),
            "filePaths": state.data_model_files,
        }

        async with aiohttp.ClientSession() as session:
            response = await session.post(
                repo_files_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/xml",  # Only accept XML since that's what the API returns
                },
            )

            if response.status != 200:
                error_text = await response.text()
                logger.error(
                    "Repo Files API failed with status %s: %s",
                    response.status,
                    error_text,
                )
                api_error_msg = f"Repo Files API failed: {error_text}"
                raise ValueError(api_error_msg)

            # Get response content
            response_text = await response.text()

            # Parse XML response
            try:
                files_content = parse_xml_response(response_text)

                # Log successful parsing
                logger.info(
                    "Successfully parsed response from Repo Files API with %d files: %s",
                    len(files_content),
                    ", ".join(files_content.keys()),
                )
            except ValueError as e:
                logger.error("Failed to parse API response: %s", e)
                raise

        # Create prompt
        prompt = ChatPromptTemplate.from_template(DATA_MODEL_ANALYSIS_TEMPLATE)

        # Initialize the language model
        model = ChatAnthropic(
            model="claude-3-sonnet-20240229",
            temperature=0,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
        )

        # Prepare messages
        messages = prompt.format_messages(
            files_content=files_content,
        )

        # Generate analysis
        response = await model.ainvoke(messages)
        data_model_analysis = response.content

        # Update state with analysis and timestamp
        state.data_model_analysis = data_model_analysis
        state.status = CodeAnalysisStatus.COMPLETED

        # Update the database record
        if state.analysis_id:
            # Get current state from database to preserve other fields
            current_doc = await code_analysis_repository.get(state.analysis_id)
            update_data = CodeAnalysisUpdate(
                data_model_analysis=data_model_analysis,
                status=CodeAnalysisStatus.COMPLETED,
                updated_at=datetime.now(timezone.utc),
                # Preserve existing fields
                data_model_files=current_doc.data_model_files if current_doc else None,
            )
            await code_analysis_repository.update(state.analysis_id, update_data)

            # Log the database update
            logger.info(
                "Updated MongoDB with data model analysis (length: %d chars) for analysis ID: %s",
                len(data_model_analysis),
                state.analysis_id,
            )

        logger.info(
            "Data Model Analysis Node completed successfully for repository: %s",
            state.repository_url,
        )

        return state
    except Exception as e:
        logger.error("Error in Data Model Analysis Node: %s", e)

        # Update state with error and timestamp
        state.status = CodeAnalysisStatus.ERROR
        error_msg = f"Data model analysis failed: {str(e)}"
        state.error = error_msg

        # Update the database record
        if state.analysis_id:
            # Get current state from database to preserve other fields
            current_doc = await code_analysis_repository.get(state.analysis_id)
            update_data = CodeAnalysisUpdate(
                status=CodeAnalysisStatus.ERROR,
                error=state.error,
                updated_at=datetime.now(timezone.utc),
                # Preserve existing fields
                data_model_files=current_doc.data_model_files if current_doc else None,
                data_model_analysis=current_doc.data_model_analysis
                if current_doc
                else None,
            )
            await code_analysis_repository.update(state.analysis_id, update_data)

            # Log the database update failure
            logger.error(
                "Failed to update MongoDB with data model analysis for analysis ID: %s. Error: %s",
                state.analysis_id,
                str(e),
            )

        return state

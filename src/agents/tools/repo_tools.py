"""Repository tools for retrieving file contents and other repository operations."""

import logging

import aiohttp
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.config.settings import settings

logger = logging.getLogger(__name__)


class RetrieveFilesInput(BaseModel):
    """Input schema for retrieve_files tool."""

    repository_url: str = Field(..., description="URL of the repository")
    file_paths: list[str] = Field(..., description="List of file paths to retrieve")


@tool
async def retrieve_files(repository_url: str, file_paths: list[str]) -> dict:
    """
    Retrieve file contents from a repository for the specified file paths.

    Args:
        repository_url: URL of the repository
        file_paths: List of file paths to retrieve

    Returns:
        Dictionary mapping file paths to their contents
    """
    try:
        if not settings.REPOSITORY_INGEST_API_URL:
            error_msg = (
                "REPOSITORY_INGEST_API_URL is not set in the environment variables"
            )
            raise ValueError(error_msg)

        repo_files_url = f"{settings.REPOSITORY_INGEST_API_URL}/api/v1/repo-files"

        logger.info(
            "Retrieving %d files from repository: %s",
            len(file_paths),
            repository_url,
        )

        # Prepare API request payload
        payload = {
            "repositoryUrl": repository_url,
            "filePaths": file_paths,
        }

        async with aiohttp.ClientSession() as session:
            response = await session.post(
                repo_files_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/xml",
                },
            )

            if response.status != 200:
                error_text = await response.text()
                logger.error(
                    "Repo Files API failed with status %s: %s",
                    response.status,
                    error_text,
                )
                return {"error": f"Repo Files API failed: {error_text}"}

            # Get response content
            response_text = await response.text()

            # Parse XML response
            try:
                files_content = parse_xml_response(response_text)
                logger.info(
                    "Successfully retrieved %d files from repository",
                    len(files_content),
                )
                return files_content
            except Exception as e:
                logger.error("Failed to parse API response: %s", e)
                return {"error": f"Failed to parse API response: {str(e)}"}

    except Exception as e:
        logger.error("Error retrieving files: %s", e)
        return {"error": f"Error retrieving files: {str(e)}"}


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


# Define tool collections
repo_tools = [retrieve_files]

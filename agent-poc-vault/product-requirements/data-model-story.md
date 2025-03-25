# User Story: Data Model Analysis in LangGraph

## User Story
As a LangGraph user, I want the system to provide a detailed analysis of the data model within a codebase, so that I can understand how data is defined, persisted, and used within the application.

## Acceptance Criteria

### Scenario 1: Data Model File Identification
- **Given** an ingested repository in the LangGraph state,
- **When** the system processes the repository,
- **Then** a language model (claude sonnet 3.7) should identify all files that define the data model, persist it, or expose it via external interfaces,
- **And** the system should store the resulting list of file paths as a new field in the state and persist it to the database.

### Scenario 2: Data Model Analysis
- **Given** the list of data model file paths stored in the state,
- **When** the Data Model Analysis Node is triggered,
- **Then** the system should invoke a ReAct Agent Node that calls the "Repo Files API" to retrieve the full code for the specified file paths,
- **And** a language model (claude sonnet 3.7) should analyze the code to generate a detailed report,
- **And** the report should include a logical data model description and an ERD in mermaid format, output as a markdown file.

### Scenario 3: Workflow Integration
- **Given** the existing code_analysis_graph workflow,
- **When** the new nodes are integrated,
- **Then** the workflow should route from the repository_ingest node to the Data Model File Identification Node, then to the Data Model Analysis Node, and finally conclude the process successfully.

## Technical Design

### 1. New LangGraph Nodes Implementation

#### Data Model File Identification Node
- **Input:** The `ingested_repository` from the current LangGraph state.
- **Process:**
  - Utilize a claude sonnet 3.7 model to analyze the ingested repository.
  - Identify files that define the data model, persist the model, or expose it via external interfaces.
  - For each file identified, take the `<file path="">` from the `ingested_repository`
- **Output:** Return an array of file paths and store it as a new field in the LangGraph state, persisting this change to the database.

#### Data Model Analysis Node
- **Input:** The array of file paths produced by the Data Model File Identification Node.
- **Process:**
  - Implement a ReAct Agent Node that uses a tool to call the "Repo Files API".
  - The tool accepts a list of file paths and retrieves the full code for all files in the list.
  - A claude sonnet 3.7 model then analyzes the retrieved code to generate a detailed analysis report.
  - The report includes how the data model is used in the application and produces a logical data model with an ERD in mermaid format.
- **Output:** A markdown file containing the detailed analysis report and the mermaid diagram, and store it as a new field in the LangGraph state, persisting this change to the database.

### 2. Workflow Integration
- **Graph Edges:**
  - Route from the existing `repository_ingest` node to the new Data Model File Identification Node.
  - Route from the Data Model File Identification Node to the new Data Model Analysis Node.
  - End the workflow after the analysis report is generated.

### 3. API Integration: "Repo Files API"
- **Endpoint:** `POST {REPOSITORY_INGEST_API_URL}/api/v1/repo-files`
- **Example Input Payload:**
  ```json
  {
    "repositoryUrl": "https://github.com/DEFRA/find-ffa-data-ingester",
    "filePaths": "src/api/files/controller/find-all-controller.js,src/api/files/controller/find-controller.js"
  }
  ```
- **Example Output Payload:**
  ```xml
  This file is a merged representation of a subset of the codebase, containing specifically included files, combined into a single document by Repomix.
  The content has been processed where line numbers have been added, security check has been disabled.


  <file_summary>
  This section contains a summary of this file.


      <purpose>
  This file contains a packed representation of the entire repository's contents.
  It is designed to be easily consumable by AI systems for analysis, code review,
  or other automated processes.
  </purpose>
      <file_format>
  The content is organized as follows:
  1. This summary section
  2. Repository information
  3. Directory structure
  4. Repository files, each consisting of:
    - File path as an attribute
    - Full contents of the file
  </file_format>
      <usage_guidelines>
  - This file should be treated as read-only. Any changes should be made to the
    original repository files, not this packed version.
  - When processing this file, use the file path to distinguish
    between different files in the repository.
  - Be aware that this file may contain sensitive information. Handle it with
    the same level of security as you would the original repository.
  </usage_guidelines>
      <notes>
  - Some files may have been excluded based on .gitignore rules and Repomix's configuration
  - Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
  - Only files matching these patterns are included: src/api/files/controller/find-all-controller.js,src/api/files/controller/find-controller.js
  - Files matching patterns in .gitignore are excluded
  - Files matching default ignore patterns are excluded
  - Line numbers have been added to the beginning of each line
  - Security check has been disabled - content may contain sensitive information
  </notes>
      <additional_info>

  </additional_info>
  </file_summary>
  <directory_structure>
  src/
    api/
      files/
        controller/
          find-all-controller.js
          find-controller.js
  </directory_structure>
  <files>
  This section contains the contents of the repository's files.


      <file path="src/api/files/controller/find-all-controller.js">
   1: import { findAllFiles } from '~/src/api/files/helpers/find-all-files.js'
   2:
   3: /**
   4:  * Controller for files on S3
   5:  * @satisfies {Partial
          <ServerRoute>}
   6:  */
   7: const findAllFilesController = {
   8:   /**
   9:    * @param { import('@hapi/hapi').Request } request
  10:    * @param { import('@hapi/hapi').ResponseToolkit } h
  11:    * @returns {Promise<*>}
  12:    */
  13:   handler: async (request, h) => {
  14:     const entities = await findAllFiles()
  15:
  16:     return h.response({ message: 'success', entities }).code(200)
  17:   }
  18: }
  19:
  20: export { findAllFilesController }
  21:
  22: /**
  23:  * @import { ServerRoute} from '@hapi/hapi'
  24:  */

          </file>
          <file path="src/api/files/controller/find-controller.js">
   1: import Boom from '@hapi/boom'
   2: import isNull from 'lodash/isNull.js'
   3:
   4: import { getManifest } from '~/src/api/gather-data/services/s3-client.js'
   5:
   6: /**
   7:  *
   8:  * @satisfies {Partial
           <ServerRoute>}
   9:  */
  10: const findFileController = {
  11:   /**
  12:    * @param { import('@hapi/hapi').Request } request
  13:    * @param { import('@hapi/hapi').ResponseToolkit } h
  14:    * @returns {Promise<*>}
  15:    */
  16:   handler: async (request, h) => {
  17:     const entity = await getManifest(request.params.fileName)
  18:     if (isNull(entity)) {
  19:       return Boom.boomify(Boom.notFound())
  20:     }
  21:
  22:     return h.response({ message: 'success', entity }).code(200)
  23:   }
  24: }
  25:
  26: export { findFileController }
  27:
  28: /**
  29:  * @import { ServerRoute} from '@hapi/hapi'
  30:  */

              </file>
  </files>
  ```

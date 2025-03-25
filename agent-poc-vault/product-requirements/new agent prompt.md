**ANALYSIS PHASE:**

We have 2 factory classes called @analysis_node_factory.py and @identification_node_factory.py that work together to first analyze what files the nodes need to analyze a code base, then perform the analysis.

A working example of this can be found in the @data_model_identification.py and @data_model_analysis.py files.

We also have a functioning linear graph that uses these agents in @code_analysis_graph.py .

**IMPLIMENTATION PHASE**

We would like to create a new set of nodes based on the @data_model_analysis.py and @data_model_identification.py nodes, using the same factory pattern. These new nodes will follow the same pattern, as follows:

# Routes and Interfaces nodes

- routes_interfaces_identification.py - which will be used to identify the files in the code base that may be needed to do a detailed analysis of any routes, user interfaces or api interfaces used in the code base. The resulting files array will be saved to the 'routes_interfaces_files' in the state store @code_analysis.
- routes_interfaces_analysis.py - which will be used to perform the detailed analysis on any any routes, user interfaces or api interfaces used in the code base. The resulting markdown analysis will be saved to the 'routes_interfaces_analysis' in the state store @code_analysis.

# LangGraph workflow updates

- We want the the new Routes and Interfaces nodes to run in parallel with current pair of data model ingest and analysis nodes

# LangGraph state updates

Because we are now running nodes in parallel, we will need to update the LangGraph workflow to update the state in parallel. To do this, we need to ensure that each node uses it's own state variables and any common state variables use reducers

In @anaylsis_state and @identification_sate the state model will be extended to include routes_interfaces_files and routes_interfaces_analysis. The new Routes and Interfaces nodes will update these states.

The existing data_model_files and data_model_analysis date will state still be updated by the existing Data Model Identification and Data Model Analysis nodes.

# mongodb schema updates

Make sure the new fields are included in the mongodb schema.

# Implementation plan

Please analyze the above requirements as follows:

1. First, outline your understanding of:
   - The specific requirements from this story
   - How this feature integrates with existing functionality
   - Any dependencies or prerequisites

2. Perform a codebase analysis focusing on:
   - Existing patterns and conventions to follow
   - Integration points for the new feature
   - Reusable components or utilities

3. Provide an implementation plan including:
   - Component/file structure
   - Required changes to existing code
   - New components/modules to be created

4. For the implementation:
   - Follow existing code conventions and patterns
   - Maintain consistent naming and structure
   - Add appropriate error handling

5. Verification checklist:
   - List each requirement from the user story
   - Confirm implementation status of each requirement
   - Note any assumptions or decisions made

Constraints:
- Maintain consistency with existing codebase
- Do not add any unit tests at this time

**VERIFICATION PHASE:**
- There should be the following new nodes: routes_interfaces_identification, routes_interfaces_analysis
- The LangGraph defined in @code_analysis_graph.py should be updated to use the new nodes, run the pairs of nodes in parallel asynchronously
- The mongoDB schema should be updated with any new state fields

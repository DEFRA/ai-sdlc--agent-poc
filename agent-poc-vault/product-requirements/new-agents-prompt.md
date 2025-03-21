**ANALYSIS PHASE:**  
  
We have 2 factory classes called @analysis_node_factory.py and @identification_node_factory.py that work together to first analyze what files the nodes need to analyze a code base, then perform the analysis.  
  
A working example of this can be found in the @data_model_identification.py and @data_model_analysis.py files.  
  
We also have a functioning linear graph that uses these agents in @code_analysis_graph.py .  
  
**IMPLIMENTATION PHASE**  
  
We would like to create 2 new sets of nodes based on the @data_model_analysis.py and @data_model_identification.py nodes, using the same factory pattern. The data model nodes perform the task of identifying the files needed to do a detailed analysis on the data model in the code base. These new nodes will follow the same pattern, as follows:  
  
# Routes and Interfaces nodes  
  
- routes_interfaces_identification.py - which will be used to identify the files in the code base that may be needed to do a detailed analysis of any routes, user interfaces or api interfaces used in the code base. The resulting files array will be saved to the 'routes_interfaces_files' in the state store.  
- routes_interfaces_analysis.py - which will be used to perform the detailed analysis on any any routes, user interfaces or api interfaces used in the code base. The resulting markdown analysis will be saved to the 'data_model_analysis' in the state store.  
  
  
# Business Logic nodes  
  
- business_logic_identification.py - which will be used to identify the files in the code base that may be needed to do a detailed analysis of the relationships, dependencies and business logic used in the code base, including a detailed relationship analysis of functions, classes and tests. The resulting files array will be saved to the 'business_logic_files' in the state store.  
- business_logic_analysis.py - which will be used to perform the detailed analysis of the relationships, dependencies and business logic used in the code base, including a detailed relationship analysis of functions, classes and tests. The resulting markdown analaysis will be saved to the 'data_model_analysis' in the state store.  
  
# LangGraph workflow updates  
  
- We want the pair of data model ingest and analysis nodes to be run in parallel (async) alongside the Routes and Interfaces nodes and Business Logic nodes  
- We then want a new node called 'product_requirements' that will combine the outputs from the above data_model_analysis, routes_interfaces_analysis, business_logic_analysis nodes that are stored in the mongodb state and then, using an anthropic LLM call, combine all the analysis state information to break down the product requirements of the code base into features and stories. This should return a detailed product requirements document in markdown format.  
  
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
- There should be the following new nodes: business_logic_identification, business_logic_analysis, routes_interfaces_identification, routes_interfaces_analysis and product_requirements  
- The LangGraph defined in @code_analysis_graph.py should be updated to use the new nodes, run the pairs of nodes async, then combine the output of the nodes into product_requirements node for processing  
- The mongoDB schema should be updated with any new state fields
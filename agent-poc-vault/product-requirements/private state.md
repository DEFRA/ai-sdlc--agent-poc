 **ANALYSIS PHASE:**
In the code analysis graph LangGraph, I want the data_model_identification_node to use private state IdentificationState, and the connected data_model_analysis_node to also private State AnalysisState. However these nodes are currently converting back to the overall Graph State CodeAnalysisState unnecessarily.

First read and understand this @ to ensure you're familiar with the patterns of LangGraph private state - including being able to use private state between internal nodes

Analyse the current codebase to identify all the components this will affect, including modules in @nodes @states @factory


**IMPLIMENTATION PHASE**
Utilise the existing @identification_state.py and @analysis_state.py. Simply replace the conversion to CodeAnalysisState with private state between these nodes

**VERIFICATRION PHASE**
no new modules are necessary
@data_model_identification.py input should be @identification_state.py and it should be outputting to @analysis_state.py and that should be the input to @data_model_analysis.py

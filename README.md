# Deploy Any LangGraph to Databricks

A comprehensive guide and template for deploying **any LangGraph multi-agent workflow** to Databricks Model Serving with Unity Catalog integration. This project demonstrates the complete conversion process using a SQL workflow as a practical example.

## Overview

This project shows you **how to convert any LangGraph-based workflow into a Databricks-compatible deployment**. While we use a SQL query generation workflow as a demonstration, the patterns and techniques apply to any LangGraph application:

### Key Conversion Principles:
- **Workflow Wrapper**: Creating MLflow-compatible orchestrator classes
- **Dependency Management**: Packaging LangGraph code for Databricks
- **Unity Catalog Integration**: Registering and versioning your models
- **Model Serving**: Deploying workflows as REST API endpoints
- **Testing & Validation**: Ensuring production readiness

### Example: SQL Workflow Agent

The included SQL workflow demonstrates these principles with:
- Natural language to SQL query generation
- SQL syntax and semantic validation
- Confidence-based routing for human approval
- Error handling with retry logic
- Complete deployment to Databricks Model Serving

## Features

### Core Databricks Integration
- 🔌 **ResponsesAgent Interface**: Complete implementation of MLflow's `ResponsesAgent` base class
- 📥 **ResponsesAgentRequest**: Standardized input handling from Databricks Model Serving
- 📤 **ResponsesAgentResponse**: Formatted output compatible with serving endpoints
- ⚡ **predict() Method**: Synchronous prediction for batch and simple workflows
- 🌊 **predict_stream() Method**: Real-time streaming for progressive results and long-running tasks
- 🎯 **Type-Safe**: Strongly-typed request/response objects for production reliability

### Universal LangGraph Conversion
- 📋 **Reusable Orchestrator Pattern**: Template for wrapping any LangGraph workflow
- 🔄 **State Management**: Handle LangGraph state transitions with Databricks checkpointing
- 📦 **Complete Code Architecture**: Reference implementation you can adapt
- 🏗️ **Production-Ready**: Battle-tested approach for enterprise deployments



## Architecture Overview

This project demonstrates the key components needed to convert any LangGraph workflow:

1. **LangGraph Workflow** → Your existing multi-agent graph (in our example: SQL generation workflow)
2. **Orchestrator Wrapper** → MLflow-compatible class that wraps your workflow
3. **Agent Script** → Entry point that initializes and exposes your workflow
4. **MLflow Logging** → Package all dependencies and register the model
5. **Unity Catalog** → Version and manage your deployed models
6. **Model Serving** → REST API endpoint for production inference

## Databricks ResponsesAgent Interface

The **critical component** for making any LangGraph work with Databricks is implementing the `ResponsesAgent` interface. This is the bridge between your LangGraph workflow and Databricks Model Serving.

### Request → Response Flow

```
Databricks Model Serving
         ↓
   ResponsesAgentRequest
   - input: [messages]
   - custom_inputs: {...}
   - context: {...}
         ↓
   Your Orchestrator (ResponsesAgent)
   - predict() or predict_stream()
         ↓
   Your LangGraph Workflow
   - Nodes execute
   - State updates
         ↓
   Format Results
         ↓
   ResponsesAgentResponse
   - output: [items]
   - custom_outputs: {...}
         ↓
   Back to Databricks Endpoint
```


### Why This Matters

Implementing `ResponsesAgent` correctly ensures:
- ✅ **MLflow compatibility**: Your model logs and deploys seamlessly
- ✅ **Databricks serving**: Endpoints work with standard inference APIs
- ✅ **Streaming support**: Real-time user experiences
- ✅ **Type safety**: Strongly-typed inputs/outputs
- ✅ **Production ready**: Built-in error handling and formatting

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-github-repo-url>
cd LanggraphToDatabricks
```

### 2. Create and Activate Virtual Environment

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```



### 4. Configure Environment

Update the configuration in `deploy-langgraph-to-databricks.ipynb` (Cell 7):

```python
# Catalog and Schema Configuration
CATALOG_NAME = "your_catalog_name"  # Your Unity Catalog name
GOLD_SCHEMA = "your_schema_name"    # Your schema name
EXPERIMENT_ID = "your_experiment_id"  # Your MLflow experiment ID

# Model Configuration
FOUNDATION_MODEL_NAME = "databricks-meta-llama-3-1-70b-instruct"
ENDPOINT_NAME = "sql-workflow-agent-endpoint"
```

### 5. Run Example Locally

Test the example SQL workflow locally before deployment:

```bash
python sql_workflow/run_sql_workflow.py
```

### 6. Deploy to Databricks

Open `deploy-langgraph-to-databricks.ipynb` in VS Code or Jupyter and:

1. **Select Python Interpreter**: Choose the venv Python interpreter
2. **Run Setup Cells**: Execute cells 1-2 to verify environment
3. **Configure**: Update cell 7 with your Databricks configuration
4. **Deploy**: Run cells 8-16 to:
   - Create agent script
   - Log model to MLflow
   - Register in Unity Catalog
   - Deploy to serving endpoint
5. **Test**: Run cells 17-18 to verify deployment





### Adapting for Your LangGraph

To convert your own LangGraph workflow:

1. **Replace the workflow logic**: Substitute `sql_workflow/` with your LangGraph implementation
2. **Create ResponsesAgent orchestrator**: 
   - Inherit from `ResponsesAgent`
   - Implement `predict()` and `predict_stream()` methods
   - Handle `ResponsesAgentRequest` → your workflow input
   - Convert workflow output → `ResponsesAgentResponse`
3. **Adjust dependencies**: Update `requirements.txt` with your specific packages
4. **Configure inputs/outputs**: Adapt the input/output schema in the agent script
5. **Follow the notebook**: Use the same deployment cells with your updated code

## Testing

### Local Testing

```bash
# Run the workflow locally
python sql_workflow/run_sql_workflow.py
```

### Endpoint Testing

After deployment, test the endpoint:

```python
from databricks.sdk import WorkspaceClient

ws = WorkspaceClient()
response = ws.serving_endpoints.query(
    name="sql-workflow-agent-endpoint",
    inputs={
        "messages": [
            {"role": "user", "content": "Show me top 5 customers by revenue"}
        ]
    }
)
print(response)
```


## Converting Your Own LangGraph

Follow these steps to adapt this project for your LangGraph workflow:

1. **Study the Example**: Review the SQL workflow structure in `sql_workflow/`
2. **Create ResponsesAgent Orchestrator**: This is the most critical step
   - Inherit from `mlflow.pyfunc.ResponsesAgent`
   - Implement `predict(request: ResponsesAgentRequest) -> ResponsesAgentResponse`
   - Implement `predict_stream(request: ResponsesAgentRequest) -> Generator[ResponsesAgentStreamEvent, ...]`
   - Convert `ResponsesAgentRequest.input` to your LangGraph's input format
   - Convert LangGraph outputs to `ResponsesAgentResponse.output` format
3. **Replace the Graph**: Substitute your LangGraph nodes, edges, and state
4. **Test Locally**: Run your workflow locally to verify functionality
5. **Deploy Using Notebook**: Follow the same deployment steps in the notebook
6. **Validate**: Test your deployed endpoint with real queries



**Built with** 🦜🔗 LangChain, 🔀 LangGraph, and ☁️ Databricks

**Note**: This is a template and guide for converting any LangGraph workflow to Databricks. The SQL workflow is provided as a complete working example to demonstrate the conversion process.

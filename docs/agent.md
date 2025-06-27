# Agents: Orchestrating Workflows with Graphs

Magma, an "agent" is not an opaque, magical black box. It is a structured, stateful workflow defined as a graph. This graph dictates how the agent thinks, what tools it can use, and how it moves from a user's query to a final answer. To power this, Magma uses **LangGraph** as its core execution engine.

The `magma.Agent` class is your primary tool for building these workflows. It provides a clean, explicit interface for defining the nodes (steps) and edges (transitions) of your agent's logic.

## Core Concept: The Agent as a State Machine

At its heart, a Magma agent is a state machine. You define a `state` object, and each node in the graph is a function that can read from and write to that state. This makes the agent's "memory" and "context" explicit and easy to manage.

The workflow for building an agent is:
1.  **Define the State:** Create a `TypedDict` that represents all the information your agent needs to track.
2.  **Define the Nodes:** Write Python functions that perform specific tasks, like calling an LLM or executing a tool.
3.  **Instantiate the Agent:** Create an instance of `magma.Agent`, passing it your state definition and any models or tools it needs.
4.  **Build the Graph:** Explicitly add your nodes and define the edges that connect them.
5.  **Compile and Run:** Compile the agent into a runnable application.

### 1. Defining State

The state is the memory of your agent. LangGraph uses a `TypedDict` to define its structure. The `add_messages` annotation from LangGraph is particularly useful for managing conversational history.

```python
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    Represents the state of our agent.

    Attributes:
        messages: The list of messages that make up the conversation.
                  The `add_messages` function ensures that new messages
                  are always appended to this list.
    """
    messages: Annotated[list, add_messages]
```

### 2. Defining Nodes

A node is just a Python function that takes the current state as input and returns a dictionary with the state updates.

```python
import magma
from baml_client import b

# Assume agent_prompt is a magma.Prompt(baml_fn=b.MyAgent)
# Assume get_stock_price is a @magma.tool decorated function

def agent_node(state: AgentState):
    """This node calls the LLM to decide what to do next."""
    query = state['messages'][0].content
    # The agent automatically injects the tools and model defined in its constructor
    response = agent_prompt(query=query)
    # The response is a BAML Pydantic object, which is a valid message type
    return {"messages": [response]}

def tool_node(state: AgentState):
    """This node executes any tools called by the agent_node."""
    last_message = state['messages'][-1]
    tool_calls = last_message.tool_calls
    
    outputs = []
    for call in tool_calls:
        tool_name = call.__class__.__name__
        tool_to_call = magma.registry.tools[tool_name]
        output = tool_to_call.invoke(call.model_dump())
        outputs.append({"tool_call_id": call.id, "content": str(output)})
        
    return {"messages": outputs}
```

### 3. Instantiating and Building the Agent

Once you have your state and nodes, you can construct the graph using the `magma.Agent` class. This is where you equip the agent with its core components.

```python
# Instantiate the agent, providing its state schema, tools, and default model.
agent = magma.Agent(
    state=AgentState,
    tools=[get_stock_price],
    model=magma.Model(id="openai/gpt-4o")
)

# Add the functions as nodes in the graph
agent.add_node("agent", agent_node)
agent.add_node("tools", tool_node)

# Define the entry point of the graph
agent.set_entry_point("agent")

# Define the conditional logic for routing
def should_call_tools(state: AgentState):
    """
    A function that determines the next step.
    If the LLM returned a tool_call, route to the 'tools' node.
    Otherwise, end the execution.
    """
    if state['messages'][-1].tool_calls:
        return "tools"
    return "__end__"

# Add the edges to connect the nodes
agent.add_conditional_edges("agent", should_call_tools)
agent.add_edge("tools", "agent") # After executing tools, go back to the agent node
```

This explicit building process (`add_node`, `add_edge`) gives you complete control over the agent's flow, making it transparent and easy to debug.

### 4. Compiling and Running

Finally, compile the agent into a runnable LangGraph application.

```python
# The compile() method finalizes the graph structure.
app = agent.compile()

# Now you can invoke or stream from the application.
query = "What is the price of NVDA?"
for event in app.stream({"messages": [("user", query)]}):
    print(event)
```

## Visualization

Because `magma.Agent` builds a standard LangGraph object, you can use all of LangGraph's powerful visualization features. Simply call the `get_graph()` method on your compiled application to generate a diagram of your agent's structure.

```python
from IPython.display import Image

# Compile the agent
app = agent.compile()

# Get the graph and draw it
graph_image = app.get_graph().draw_mermaid_png()
Image(graph_image)
```
This will produce a clear diagram of your nodes and edges, making it easy to understand and share your agent's architecture.

## Multi-Agent Systems

The `magma.Agent` class is the fundamental building block for more complex systems. Because each agent is a self-contained graph, you can compose them into multi-agent systems where the output of one agent becomes the input for another. This is achieved by treating a compiled agent `app` as a node within a higher-level "supervisor" graph. This advanced pattern will be covered in the Multi-Agent Systems guide.
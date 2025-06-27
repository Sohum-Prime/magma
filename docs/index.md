# Magma

Forge Production-Ready AI Agents with Python.

Magma is a Python library for building powerful, transparent, and production-ready AI agents and multi-agent systems. It provides a simple, Pythonic interface that unifies best-in-class libraries for model interaction, prompt management, observability, and agentic control flow—without opaque abstractions.

## Key Features

✨ **Type-Safe & Reliable**

Leverage BAML's DSL to move beyond string-based prompting. Define your inputs and outputs with strong types, ensuring your agent's interactions with LLMs are predictable and validated.
<br/>

🐍 **Python-Native & Composable**

Build agents by composing standard Python functions and classes. Magma's interface feels natural to Python developers, promoting clean, testable, and reusable code.
<br/>

🔍 **Transparent & Debuggable**

With first-class support for LangFuse, every step of your agent's execution—from model calls to tool execution—is automatically traced. Understand exactly what your agent is thinking and doing at all times.
<br/>

🛠️ **Powerful & Extensible**

Built on the shoulders of giants like LangGraph, LiteLLM, and smolagents. Magma gives you the power of stateful, cyclical graphs and access to any LLM or tool, all through a simplified interface.
<br/>

## Quickstart: A Weather Agent in Minutes

Let's build a simple agent that can check the weather using a tool.

### 1. Installation
[title2tab]
#### uv
```bash
uv add magma
# And the dependencies for this example
uv add litellm baml-py langfuse smolagents langgraph openai
```

#### pip
```bash
pip install magma
# And the dependencies for this example
pip install litellm baml-py langfuse smolagents langgraph openai
```

### 2. Define Components

#### 2.1 Initiate BAML into the project which will give some starter code in a `baml_src` directory
[title2tab]
##### uv
```bash
uv run baml-cli init
```

##### pip
```bash
baml-cli init
```

#### 2.2 Create your BAML file to define the agent's "thinking" process.

**`./baml_src/agent.baml`**
```baml
// The tool(s) our agent can use. We mark it as dynamic.
class GetWeather {
  city string @description("The city for which to get the weather.")
}
type Toolbox = GetWeather @@dynamic

// The agent's response can be a tool call or a final answer.
class AgentResponse {
  tool_calls Toolbox[]? @description("The tool(s) the model wants to call.")
  final_answer string? @description("The final answer to the user.")
}

// The BAML function that powers our agent's brain.
function WeatherAgent(query: string, tool_output: string?) -> AgentResponse {
  client openai/gpt-4o
  prompt #"
    You are a helpful assistant that can check the weather.

    User Query: {{ query }}

    {% if tool_output %}
    A tool has been run and returned this output:
    ---
    {{ tool_output }}
    ---
    Now, provide the final answer to the user.
    {% else %}
    Based on the query, decide if you need to call a tool.
    {% endif %}

    {{ ctx.output_format }}
  "#
}
```

#### 2.3 Generate the `baml_client` python module from `.baml` files
[title2tab]
##### uv
```bash
uv run baml-cli generate
```

##### pip
```bash
baml-cli generate
```

#### 2.4 Define your components in Python

**`main.py`**
```python
import magma
from baml_client import b
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

# --- 1. Define State ---
class AgentState(TypedDict):
    # The 'messages' field is the primary state, accumulating history.
    messages: Annotated[list, add_messages]

# --- 2. Define Tools ---
@magma.tool
def get_weather(city: str) -> str:
    """Gets the current weather for a specified city."""
    if "san francisco" in city.lower():
        return "The weather in San Francisco is 65°F and sunny."
    return f"Weather for {city} is currently unavailable."

# --- 3. Define Prompts and Models ---
weather_prompt = magma.Prompt(baml_fn=b.WeatherAgent)
llm = magma.Model(id="openai/gpt-4o")

# --- 4. Define Graph Nodes ---
def agent_node(state: AgentState):
    """The node that calls the LLM to decide the next action."""
    last_message = state['messages'][-1]
    tool_output = last_message.content if last_message.type == "tool" else None
    
    response = weather_prompt(
        query=state['messages'][0].content,
        tool_output=tool_output,
        # The agent automatically provides the right model and tools
    )
    return {"messages": [response]} # Return a BAML Pydantic object

def tool_node(state: AgentState):
    """This node executes tools. It is invoked when the agent requests a tool call."""
    tool_calls = state['messages'][-1].tool_calls
    tool_outputs = []
    for call in tool_calls:
        # The agent automatically finds and executes the right tool
        output = magma.tools.get(call.__class__.__name__).invoke(call.model_dump())
        tool_outputs.append({"tool_call_id": call.id, "content": output})
    return {"messages": tool_outputs}

# --- 5. Build the Agent Graph ---
agent = magma.Agent(state=AgentState, tools=[get_weather], model=llm)

agent.add_node("agent", agent_node)
agent.add_node("tools", tool_node)

agent.set_entry_point("agent")

def should_continue(state: AgentState):
    return "tools" if state['messages'][-1].tool_calls else "__end__"

agent.add_conditional_edges("agent", should_continue)
agent.add_edge("tools", "agent")

# --- 6. Compile and Run ---
app = agent.compile()
query = "What's the weather like in San Francisco?"
for event in app.stream({"messages": [("user", query)]}):
    for v in event.values():
        print(v['messages'][-1])
```

### 3. How It Works

Magma connects powerful, independent libraries into a single, cohesive workflow:

*   **`magma.Model`**: A simple, declarative pointer to any LLM supported by **LiteLLM**. It holds configuration like model ID and API keys.
*   **`magma.Tool`**: A decorator that instantly makes any Python function available to your agent. Magma automatically generates the necessary schemas for both the agent and BAML.
*   **`magma.Prompt`**: A type-safe bridge to your LLM, powered by a **BAML** function. It handles the complex work of templating, type validation, and dynamic tool injection.
*   **`magma.Agent`**: The central orchestrator. It uses **LangGraph** to build a stateful, cyclical graph from your nodes and edges, enabling complex, multi-step reasoning.
*   **`magma.registry`**: The magic glue. As you define components, they are automatically registered, allowing you to easily inspect what's available (`magma.tools`, `magma.models`) and enabling the framework to wire everything together at runtime.

### The Magma Stack

Magma stands on the shoulders of giants, providing a simplified interface without sacrificing power.

| Component | Role in Magma |
| :--- | :--- |
| **LangGraph** | The core execution engine. Provides the state machine for creating robust, cyclical agentic workflows. |
| **BAML** | The prompt and output management layer. Enforces type-safety and structured data exchange with LLMs. |
| **LiteLLM** | The universal model interface. Provides a single, consistent API to call over 100+ different LLM providers. |
| **LangFuse** | The observability layer. Automatically traces every operation, providing deep insight into agent behavior. |
| **smolagents** | The inspiration and foundation for our tool-handling philosophy, promoting simple and effective tool creation. |

## Next Steps

<div class="mt-10">
  <div class="w-full flex flex-col space-y-4 md:space-y-0 md:grid md:grid-cols-2 md:gap-y-4 md:gap-x-5">
    <a class="!no-underline border dark:border-gray-700 p-5 rounded-lg shadow hover:shadow-lg" href="./getting-started/guided-tour.md">
      <div class="w-full text-center bg-gradient-to-br from-blue-400 to-blue-500 rounded-lg py-1.5 font-semibold mb-5 text-white text-lg leading-relaxed">🚀 Guided Tour</div>
      <p class="text-gray-700">A step-by-step tutorial building a complete agent from scratch. Start here to get hands-on experience.</p>
    </a>
    <a class="!no-underline border dark:border-gray-700 p-5 rounded-lg shadow hover:shadow-lg" href="./concepts/core-abstractions.md">
      <div class="w-full text-center bg-gradient-to-br from-indigo-400 to-indigo-500 rounded-lg py-1.5 font-semibold mb-5 text-white text-lg leading-relaxed">🧠 Core Concepts</div>
      <p class="text-gray-700">A high-level explanation of Magma's architecture and the design philosophy behind its components.</p>
    </a>
  </div>
</div>
from langgraph.graph import StateGraph, END
from typing import TypedDict

class AgentState(TypedDict):
    messages: list

def agent_node(state):
    # Tool calling + LLM
    return {'messages': state['messages'] + ['Agent response nyaong~']}

graph = StateGraph(AgentState)
graph.add_node('agent', agent_node)
graph.set_entry_point('agent')
graph.add_edge('agent', END)

agent = graph.compile()
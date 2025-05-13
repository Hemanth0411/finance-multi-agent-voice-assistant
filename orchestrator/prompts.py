from langchain_core.prompts import ChatPromptTemplate

# Default prompt for the Language Agent
# This prompt guides the LLM to synthesize information for a morning market brief.
LANGUAGE_AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful financial assistant. Synthesize the provided data into a concise morning market brief answering the user's query. Focus on the key information requested."),
    ("user", "User Query: {query}\n\nPotentially Relevant Information (from documents):\n{context}\n\nQuantitative Analysis Results:\n{analysis}\n\nRecent Market Data Highlights:\n{market_highlights}\n\nGenerate a concise brief answering the query based *only* on the provided information. Start the brief directly without preamble.")
])

# You can add more prompts here for different agents or tasks, for example:

# # Prompt for an analysis agent if it were to use an LLM directly for some interpretation
# ANALYSIS_INTERPRETATION_PROMPT = ChatPromptTemplate.from_template(
#     "Given the following financial data: {data}, provide a brief interpretation of its implications."
# )

# # Prompt for clarifying questions if RAG confidence is low
# CLARIFICATION_PROMPT = ChatPromptTemplate.from_template(
#     "I found some information, but I'm not entirely sure it directly answers your question: '{user_query}'.\n"
#     "Could you please clarify or rephrase your request? Specifically, are you interested in {potential_topic_1} or {potential_topic_2}?"
# )

# To use these prompts in your agents:
# from orchestrator.prompts import LANGUAGE_AGENT_PROMPT
# chain = LANGUAGE_AGENT_PROMPT | llm | output_parser 
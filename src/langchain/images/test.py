import os
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# 1. Define chatbot personality
# We use a 'System' message to define Alex's persona
chatbot_personality = """
You are Alex, a friendly and knowledgeable AI companion. You are:
- Patient and understanding
- Enthusiastic about learning and helping
- Conversational and warm
- Clear and concise in explanations
Always respond in a friendly, natural way. Keep responses focused and helpful.
"""

# 2. Create the modern Chat Prompt Template
# This replaces the old 'PromptTemplate' and handles memory automatically
prompt = ChatPromptTemplate.from_messages([
    ("system", chatbot_personality),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

# 3. Initialize Azure LLM
llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("https://anfc-azopenai.openai.azure.com/"),
    api_key=os.getenv("c72e9614a1b54c38b836046ec01ec7de"),
    api_version="2024-02-15-preview",
    deployment_name="gpt-35-turbo",
    temperature=0.7
)

# 4. Memory Management (The Window Memory Logic)
store = {}


def get_session_history(session_id: str):
    if session_id not in store:
        # ChatMessageHistory stores all messages for the session
        store[session_id] = ChatMessageHistory()

    # Implementing 'Window' logic (k=5)
    # This keeps the context window clean for high-performance inference
    if len(store[session_id].messages) > 10:  # k=5 interactions * 2 messages each
        store[session_id].messages = store[session_id].messages[-10:]

    return store[session_id]


# 5. Build the modern chain
chain = prompt | llm

# Wrap with history logic
conversation = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# 6. Test the Chatbot
config = {"configurable": {"session_id": "alex_test_1"}}


def ask_alex(user_input):
    print(f"You: {user_input}")
    response = conversation.invoke({"input": user_input}, config)
    print(f"Alex: {response.content}\n")


print("Testing Alex the AI Companion:\n")
ask_alex("Hi Alex! How are you today?")
ask_alex("Can you help me with my studies?")
ask_alex("What was the first thing I asked you?")

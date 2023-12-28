
import autogen
import panel as pn
import openai
import os
from time import sleep
import time
import asyncio
from dotenv import load_dotenv
from chat_state import ChatState
from agents import *
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
import chromadb

#panel serve app.py --show 
file_path = None

load_dotenv()
brwoserless_api_key = os.getenv("BROWSERLESS_API_KEY")
serper_api_key = os.getenv("SERP_API_KEY")
airtable_api_key = os.getenv("AIRTABLE_API_KEY")
config_list = autogen.config_list_from_json("OAI_CONFIG_LIST")

mistral_7b_config={
    "config_list": config_list,
    "temperature":0, 
    # "timeout": 600,
     "cache_seed":42,
}

chat_state = ChatState.getInstance()

def print_messages( recipient, messages, sender, config):
    print(f"Messages from: {sender.name} sent to: {recipient.name} | num messages: {len(messages)} | message: {messages[-1]}")
    name = messages[-1].get('name',sender.name)

    avatar = {
        "assistant": "👩‍💼",
        "admin":"🧑‍💻",
        "user": "🧑",
        "coder": "👷‍♀️",
        "scientist": "👩‍🔬",
        "planner": "📅",
        "executor": "🔧",
        "critic": '🖋️',
        "content_creator":"🧑‍💻",
        "reviewer":"🧑‍💻",
        "ragproxyagent":"🧑‍💻",
    }
    if name.lower() not in avatar:
        name = 'Secret man'
        avatar_icon = '👤'
    elif name.lower() == 'admin':
        avatar_icon = avatar[name.lower()]
        name = 'Admin(you)'
    elif name.lower() == 'user':
        avatar_icon = avatar[name.lower()]
        name = 'You'
    else:
        avatar_icon = avatar[name.lower()]
    chat_interface.send(messages[-1]['content'], user=name,avatar= avatar_icon,respond=False)
    return False, None    

def register_agent_replies(agents):
    for agent in agents:
        agent.register_reply(
            [autogen.Agent, None],
            reply_func=print_messages,  
            config={"callback": None})

async def delayed_initiate_chat(agent, recipient, message):
    chat_state.initiate_chat_task_created = True
    await asyncio.sleep(2)
    if  chat_state.current_mode == "file":
        await agent.a_initiate_chat(recipient,problem=message)
    else:
        await agent.a_initiate_chat(recipient, message=message)
    
pn.extension(design="material")

async def callback(contents: str, user: str, instance: pn.chat.ChatInterface):
    global file_path
    mode_1 = "create a snake game with python and pygame library"
    mode_2 = "write content"
    mode_3 = "file"
    mode_normal = "other"

    # Khai báo biến toàn cục

    if contents == "exit":
        chat_state.reset()
        chat_interface.send("Exited chat mode.", user="System", respond=False)
        print("Exiting chat mode.")
        return

    if chat_state.in_chat_mode:
        #---------------------------------------------------------------------------------------
        if chat_state.current_mode == mode_1 :
            if not chat_state.initiate_chat_task_created:
                print("Chat mode: application_group")
                chat_agents = application_group(mistral_7b_config)
                register_agent_replies([chat_agents.user_proxy,chat_agents.user_proxy,
                chat_agents.engineer,chat_agents.scientist,chat_agents.planner,chat_agents.executor ,chat_agents.critic])
                asyncio.create_task(delayed_initiate_chat(chat_agents.user_proxy,chat_agents.manager , contents))
                chat_state.initiate_chat_task_created = True
            else:
                if chat_state.input_future and not chat_state.input_future.done():
                        chat_state.input_future.set_result(contents)
                else:
                    print("There is currently no input being awaited.")
        #---------------------------------------------------------------------------------------
        #---------------------------------------------------------------------------------------
        elif  chat_state.current_mode ==  mode_2 :
            if not chat_state.initiate_chat_task_created:
                print("Chat mode: content_group")
                chat_agents =  content_group(mistral_7b_config)
                register_agent_replies([chat_agents.user_proxy,
                chat_agents.coder,chat_agents.scientist,chat_agents.planner,chat_agents.executor ,chat_agents.critic])
                asyncio.create_task(delayed_initiate_chat(chat_agents.user_proxy,chat_agents.manager , contents))
                chat_state.initiate_chat_task_created = True
            else:
                if chat_state.input_future and not chat_state.input_future.done():
                        chat_state.input_future.set_result(contents)
                else:
                    print("There is currently no input being awaited.")
        #---------------------------------------------------------------------------------------
        #---------------------------------------------------------------------------------------
        elif  chat_state.current_mode ==  mode_3 :
            if not chat_state.initiate_chat_task_created: 
                print("Chat mode: application_group")
                chat_agents = content_group(mistral_7b_config)
                register_agent_replies([chat_agents.user_proxy,chat_agents.content_creator,chat_agents.reviewer])
                asyncio.create_task(delayed_initiate_chat(chat_agents.user_proxy, chat_agents.manager , contents))
                chat_state.initiate_chat_task_created = True
            else:
                if chat_state.input_future and not chat_state.input_future.done():
                    chat_state.input_future.set_result(contents)
                else:
                    print("There is currently no input being awaited.")
        #---------------------------------------------------------------------------------------
        #---------------------------------------------------------------------------------------
        else: 
            if not chat_state.initiate_chat_task_created:
                print("Chat mode: assistant_chat")
                chat_agents = assistant_chat(mistral_7b_config) 
                register_agent_replies(chat_agents.assistant)
                asyncio.create_task(delayed_initiate_chat(chat_agents.user_proxy,chat_agents.assistant , contents))
                chat_state.initiate_chat_task_created = True
            else:
                if chat_state.input_future and not chat_state.input_future.done():
                    chat_state.input_future.set_result(contents)
                else:
                    print("There is currently no input being awaited.")
        #---------------------------------------------------------------------------------------         
    else:
        if "create" in contents:
            chat_state.in_chat_mode = True
            chat_state.current_mode = mode_1 
#---------------------------------------------------------------------------------------
            if not chat_state.initiate_chat_task_created:
                print("Chat mode: application_group")
                chat_agents = application_group(mistral_7b_config)
                register_agent_replies([chat_agents.user_proxy,chat_agents.coder,chat_agents.scientist,chat_agents.planner,chat_agents.executor ,chat_agents.critic])
                asyncio.create_task(delayed_initiate_chat(chat_agents.user_proxy,chat_agents.manager , contents))
                chat_state.initiate_chat_task_created = True
            else:
                if chat_state.input_future and not chat_state.input_future.done():
                        chat_state.input_future.set_result(contents)
                else:
                    print("There is currently no input being awaited.")
#---------------------------------------------------------------------------------------
        elif "write" in contents:
            chat_state.in_chat_mode = True
            chat_state.current_mode = mode_2
#---------------------------------------------------------------------------------------
            if not chat_state.initiate_chat_task_created: 
                print("Chat mode: application_group")
                chat_agents = content_group(mistral_7b_config)
                register_agent_replies([chat_agents.user_proxy,chat_agents.content_creator,chat_agents.reviewer])
                asyncio.create_task(delayed_initiate_chat(chat_agents.user_proxy, chat_agents.manager , contents))
                chat_state.initiate_chat_task_created = True
            else:
                if chat_state.input_future and not chat_state.input_future.done():
                    chat_state.input_future.set_result(contents)
                else:
                    print("There is currently no input being awaited.")
#---------------------------------------------------------------------------------------
        elif file_path and "file" in contents:
            chat_state.in_chat_mode = True
            chat_state.current_mode = mode_3
#---------------------------------------------------------------------------------------
            path = f"C:/Project/LLM/{file_path}"
            print("path:",path)
            if not chat_state.initiate_chat_task_created: 
                print("Chat mode: file")
                assistant = RetrieveAssistantAgent(
                    name="assistant",
                    system_message="You are a helpful assistant.",
                    llm_config=mistral_7b_config,
                )
                ragproxyagent = RetrieveUserProxyAgent(
                    name="ragproxyagent",
                    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
                    llm_config=mistral_7b_config,
                    system_message="Assistant who has extra content retrieval power for solving difficult problems.",
                    human_input_mode="NEVER",
                    max_consecutive_auto_reply=3,   
                    retrieve_config={
                        "task": "code",
                        "docs_path":  path ,
                        # "docs_path": "https://raw.githubusercontent.com/microsoft/FLAML/main/website/docs/Examples/Integrate%20-%20Spark.md",
                        "chunk_token_size": 1000,
                        "custom_text_types": ["pdf"],
                        "client": chromadb.PersistentClient(path="/tmp/chromadb"),
                        "collection_name": "groupchat",
                        # "embedding_model": "all-mpnet-base-v2",
                        "get_or_create": True,
                    },
                    code_execution_config=False,  # set to False if you don't want to execute the code
                )
                assistant.reset()
                register_agent_replies([assistant,ragproxyagent])
                asyncio.create_task(delayed_initiate_chat(ragproxyagent,assistant, contents))
                chat_state.initiate_chat_task_created = True
            else:
                if chat_state.input_future and not chat_state.input_future.done():
                    chat_state.input_future.set_result(contents)
                else:
                    print("There is currently no input being awaited.")
        else:
            chat_state.in_chat_mode = True
            chat_state.current_mode = mode_normal
#---------------------------------------------------------------------------------------
            if not chat_state.initiate_chat_task_created:
                print("Chat mode: assistant_chat")
                chat_agents = assistant_chat(mistral_7b_config) 
                register_agent_replies([chat_agents.user_proxy])
                asyncio.create_task(delayed_initiate_chat(chat_agents.user_proxy,chat_agents.assistant , contents))
                chat_state.initiate_chat_task_created = True
            else:
                if chat_state.input_future and not chat_state.input_future.done():
                    chat_state.input_future.set_result(contents)
                else:
                    print("There is currently no input being awaited.")
#---------------------------------------------------------------------------------------

chat_interface = pn.chat.ChatInterface(
    callback=callback,

    show_button_name=False,
    sizing_mode="stretch_both",
    min_height=600,
)

# chat_interface.send("Ask your question about the document!!", user="System", respond=False)

uploading = pn.indicators.LoadingSpinner(value=False, size=50, name='No document')
file_input = pn.widgets.FileInput(name="PDF File", accept=".pdf")
text_area = pn.widgets.TextAreaInput(name='File Info', sizing_mode='stretch_both', min_height=400)
chat_interface.send("Send a message!", user="System", respond=False)

async def file_callback(*events):
    global file_path  # Khai báo biến toàn cục
    file_path = ""
    for event in events:
        if event.name == 'filename':
            file_name = event.new
        if event.name == 'value':
            file_content = event.new
       
    uploading.value = True
    uploading.name = 'Uploading'
    file_path = file_name
    with open(file_path, 'wb') as f:
        f.write(file_content)
    # print(file_path)
   
    text_area.value = str( file_path)
    uploading.value = False
    uploading.name = f"Document uploaded - {file_name}"
       

# Set up a callback on file input value changes
file_input.param.watch(file_callback, ['value', 'filename'])

title = '## Please upload your document for RAG'
file_app = pn.Column(pn.pane.Markdown(title), file_input, uploading, text_area, sizing_mode='stretch_width', min_height=300)

pn.template.FastListTemplate(
    title="📚Chat bot agents",
    header_background="#2F4F4F",
    accent_base_color="#2F4F4F",
    main=[
        chat_interface
    ],
    sidebar=[file_app],
    sidebar_width=400,
).servable()



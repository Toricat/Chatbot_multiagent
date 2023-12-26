
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

#panel serve app_test.py --show 


load_dotenv()
brwoserless_api_key = os.getenv("BROWSERLESS_API_KEY")
serper_api_key = os.getenv("SERP_API_KEY")
airtable_api_key = os.getenv("AIRTABLE_API_KEY")
config_list = autogen.config_list_from_json("OAI_CONFIG_LIST")

mistral_7b_config={
    "config_list": config_list,
    "temperature":0, 
    # "seed": 17
}

chat_state = ChatState.getInstance()

def print_messages( recipient, messages, sender, config):
    print(f"Messages from: {sender.name} sent to: {recipient.name} | num messages: {len(messages)} | message: {messages[-1]}")
    name = messages[-1].get('name',sender.name)

    avatar = {
        "assistant": "👩‍💼",
        "admin":"🧑‍💻",
        "user": "🧑",
        "engineer": "👷‍♀️",
        "scientist": "👩‍🔬",
        "planner": "📅",
        "executor": "🔧",
        "critic": '🖋️',
        "content_creator":"🧑‍💻",
        "reviewer":"🧑‍💻",
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
    await agent.a_initiate_chat(recipient, message=message)
    await chat_interface.send("press exit to close conversation", user="System", respond=False)
    
pn.extension(design="material")

async def callback(contents: str, user: str, instance: pn.chat.ChatInterface):

    mode_1 = "create a snake game with python and pygame library"
    mode_2 = "write content"
    mode_normal = "other"

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

chat_interface = pn.chat.ChatInterface(callback=callback)
chat_interface.send("Send a message!", user="System", respond=False)
chat_interface.servable()


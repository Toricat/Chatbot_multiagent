import autogen
import panel as pn
import openai
import os
from time import sleep
import time
import asyncio

from chat_state import ChatState
chat_state = ChatState.getInstance()

class MyConversableAgent(autogen.ConversableAgent):
    async def a_get_human_input(self, prompt: str) -> str:
        chat_state.input_future
        print('AGET!!!!!!')  

        if chat_state.input_future is None or chat_state.input_future.done():
            chat_state.input_future = asyncio.Future()
        await chat_state.input_future
        input_value = chat_state.input_future.result()
        chat_state.input_future = None
        return input_value

class assistant_chat:
    def __init__(self, llm_config):
        self.llm_config = llm_config
        self.init_agents()
        # self.register_agent_replies()
    def init_agents(self):
        self.assistant =  autogen.AssistantAgent("Assistant",
        system_message='''You are a helpful assistant.''',
        llm_config=self.llm_config)
        self.user_proxy = MyConversableAgent(
        name="user",
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("exit"),
        system_message="""A human admin.
        """,
        code_execution_config=False,
        #default_auto_reply="Approved", 
        human_input_mode="ALWAYS",
        llm_config= self.llm_config,)


class application_group:     
    
    def __init__(self, llm_config):
        self.llm_config = llm_config
        self.init_agents()

    def init_agents(self):
        self.user_proxy = MyConversableAgent(
        name="Admin",
        max_consecutive_auto_reply=20,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        system_message="""A human admin. Interact with the planner to discuss the plan. Plan execution needs to be approved by this admin. 
        Don reply thank you, only reply TERMINATE if the task has been solved at full satisfaction.
        Otherwise, reply CONTINUE, or the reason why the task is not solved yet.
        """,
        #Only say APPROVED in most cases, and say exit when nothing to be done further. Do not say others.
        code_execution_config={"work_dir": "web"},
        #default_auto_reply="Approved", 
        human_input_mode="ALWAYS",
        llm_config=self.llm_config,
        )

        self.coder = autogen.AssistantAgent(
            name="Coder",
            human_input_mode="NEVER",
            llm_config=self.llm_config,
            system_message='''Engineer. You follow an approved plan. You write python/shell code to solve tasks. Wrap the code in a code block that specifies the script type. The user can't modify your code. So do not suggest incomplete code which requires others to modify. Don't use a code block if it's not intended to be executed by the executor.
            Don't include multiple code blocks in one response. Do not ask others to copy and paste the result. Check the execution result returned by the executor.
            If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
        
            ''',
        )
        self.scientist = autogen.AssistantAgent(
            name="Scientist",
            human_input_mode="NEVER",
            llm_config=self.llm_config,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            system_message="""Scientist. You follow an approved plan. If have paper, you are able to categorize papers after seeing their abstracts printed. You don't write code.
            Don reply thank you, only reply TERMINATE if the task has been solved at full satisfaction.
            Otherwise, reply CONTINUE, or the reason why the task is not solved yet.
            """
        )
        self.planner = autogen.AssistantAgent(
            name="Planner",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            system_message='''Planner. Suggest a plan. Revise the plan based on feedback from admin and critic, until admin approval.
        The plan may involve an engineer who can write code and a scientist who doesn't write code.
        Explain the plan first. Be clear which step is performed by an engineer, and which step is performed by a scientist.
        Don reply thank you, only reply TERMINATE if the task has been solved at full satisfaction.
        Otherwise, reply CONTINUE, or the reason why the task is not solved yet.
        ''',
            llm_config=self.llm_config,
        )
        self.executor = autogen.UserProxyAgent(
            name="Executor",
            system_message="""Executor. Execute the code written by the engineer and report the result. Reply TERMINATE if the task has been solved at full satisfaction.
            Otherwise, reply CONTINUE, or the reason why the task is not solved yet.""",
            human_input_mode="NEVER",
            llm_config=self.llm_config,
            code_execution_config={"work_dir": "web"},
        )
        # self.critic = autogen.AssistantAgent(
        #     name="Critic",
        #     system_message="""Critic. Double check plan, claims, code from other agents and provide feedback. 
        #     Check whether the plan includes adding verifiable info such as source URL. 
        #     """,
        #     llm_config=self.llm_config,
        #     human_input_mode="NEVER",
        # )
        self.critic = autogen.AssistantAgent(
            name="Critic",
            system_message="""Critic. You are a helpful assistant highly skilled in evaluating the quality of a given visualization code by providing a score from 1 (bad) - 10 (good) while providing clear rationale. YOU MUST CONSIDER VISUALIZATION BEST PRACTICES for each evaluation. Specifically, you can carefully evaluate the code across the following dimensions
            - bugs (bugs):  are there bugs, logic errors, syntax error or typos? Are there any reasons why the code may fail to compile? How should it be fixed? If ANY bug exists, the bug score MUST be less than 5.
            - Data transformation (transformation): Is the data transformed appropriately for the visualization type? E.g., is the dataset appropriated filtered, aggregated, or grouped  if needed? If a date field is used, is the date field first converted to a date object etc?
            - Goal compliance (compliance): how well the code meets the specified visualization goals?
            - Visualization type (type): CONSIDERING BEST PRACTICES, is the visualization type appropriate for the data and intent? Is there a visualization type that would be more effective in conveying insights? If a different visualization type is more appropriate, the score MUST BE LESS THAN 5.
            - Data encoding (encoding): Is the data encoded appropriately for the visualization type?
            - aesthetics (aesthetics): Are the aesthetics of the visualization appropriate for the visualization type and the data?

            YOU MUST PROVIDE A SCORE for each of the above dimensions.
            {bugs: 0, transformation: 0, compliance: 0, type: 0, encoding: 0, aesthetics: 0}
            Do not suggest code. 
            Finally, based on the critique above, suggest a concrete list of actions that the coder should take to improve the code.
            Don reply thank ypu, only reply TERMINATE if the task has been solved at full satisfaction.
            Otherwise, reply CONTINUE, or the reason why the task is not solved yet.
            """,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            llm_config= self.llm_config,
            human_input_mode="NEVER",
        )
        # self.user_proxy.reset()
        # self.coder.reset()
        # self.scientist.reset()
        # self.planner.reset()
        # self.executor.reset()
        # self.critic.reset()
        self.groupchat = autogen.GroupChat(
            agents=[self.user_proxy, self.coder, self.scientist, self.planner, self.executor, self.critic],
            messages=[],
            max_round=50,
        )
        self.manager = autogen.GroupChatManager(groupchat=self.groupchat, llm_config=self.llm_config)



class content_group:     
    def __init__(self, llm_config):
        self.llm_config = llm_config
        self.init_agents()

    def init_agents(self):
        self.user_proxy = MyConversableAgent(
        name="Admin",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
        system_message="A human admin. You need to giving a task for all Employee.",
        code_execution_config=False,
        #default_auto_reply="Approved", 
        human_input_mode="ALWAYS",
        llm_config= self.llm_config,
        )
        self.content_creator = autogen.AssistantAgent(
            name="Content_creator",
            human_input_mode="NEVER",
            llm_config= self.llm_config,
            system_message="Content creator, you are an excellent content creator who can write about any topic requested by the admin. This includes a full range of diverse fields from content creation to writing. You will receive a content creation request from the admin and from there, please create content that corresponds with the request. After creating content, you should submit it to the Reviewer for evaluation and feedback. Only reply with TERMINATE once the entire project is completed.",
        )
        self.reviewer = autogen.AssistantAgent(
            name="reviewer",
            human_input_mode="NEVER",
            llm_config= self.llm_config,
            system_message="As a reviewer, your key task is to assess and critique content from our creators. You'll evaluate its quality, relevance, and engagement, offering suggestions for improvement. Your responsibility to provide constructive feedback directly to the content creators. It's imperative that you consistently provide constructive feedback  that encourages innovation and enhancement. Only reply with TERMINATE once the entire project is completed.",
        )
        self.user_proxy.reset()
        self.reviewer.reset()
        self.reviewer.reset()
        self.groupchat = autogen.GroupChat(
            agents=[self.user_proxy, self.content_creator, self.reviewer],
            messages=[],
            max_round=20,
        )
        self.manager = autogen.GroupChatManager(groupchat=self.groupchat, llm_config=self.llm_config)

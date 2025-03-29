"""
Core chat system implementation for RALPh.
"""

import time
# from langchain.memory import ChatMessageHistory  # deprecated
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from chat.logger import ChatSystemLogger
from chat.prompts import (
    build_counselling_system_prompt,
    build_verification_system_prompt,
    SYSTEM_PROMPT_IDENTIFY_TOPICS,
    SYSTEM_PROMPT_EMPATHY
)
from knowledge_base.vector_store import KnowledgeBase


class ChatSystem:
    """
    Core chat system for handling user interactions.
    """
    
    def __init__(self, 
                 chatllm, 
                 chatllm_large, 
                 summaryllm, 
                 patient_details, 
                 prescription_details, 
                 memory_char_limit=5000):
        """
        Initialize ChatSystem with required LLMs and settings.
        
        Args:
            chatllm: Primary chat language model
            chatllm_large: More powerful language model for complex queries
            summaryllm: Model for summarization
            patient_details: Patient information
            prescription_details: Prescription details
            memory_char_limit: Character limit for chat memory before summarizing
        """
        self.chatllm = chatllm
        self.chatllm_large = chatllm_large
        self.summaryllm = summaryllm
        self.patient_details = patient_details
        self.prescription_details = prescription_details
        self.memory_char_limit = memory_char_limit
        
        # Initialize chat memory and state
        self.chat_memory = ChatMessageHistory()
        self.status_verified = False  # Set to TRUE for testing
        self.convo_number = 0
        self.turn_counter = 0
        
        # Initialize logger and knowledge base
        self.logger = ChatSystemLogger()
        self.logger.start_conversation()
        self.knowledge_base = KnowledgeBase()
        
    def _get_chat_history_length(self):
        """
        Calculate total length of messages in chat history.
        
        Returns:
            int: Total character length
        """
        return sum(len(str(msg.content)) for msg in self.chat_memory.messages)
    
    def _summarize_chat_history(self):
        """
        Summarize chat history if it exceeds character limit.
        
        Returns:
            bool: True if summarization occurred
        """
        if len(self.chat_memory.messages) == 0:
            return False
        
        self.logger.logger.info("Summarising chat history...")

        summary_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "placeholder"
            ),
            MessagesPlaceholder(variable_name="chat_history"),
        ])
        
        messages = summary_prompt.format_messages(chat_history=(self.chat_memory.messages))
        summary = self.summaryllm(str(messages))
        
        self.chat_memory.clear()
        self.chat_memory.add_message(summary)
        
        return True
    
    def process_message(self, user_input):
        """
        Process user input and return response.
        
        Args:
            user_input (str): User's message
            
        Returns:
            str: Response from the LLM
        """
        # Start timing the process_message function
        start_time = time.time()

        kb_search_input = None
        kb_metadata = None
        kb_scores = None
        
        # Trigger summarisation of chat history if it exceeds the char limit
        if self._get_chat_history_length() > self.memory_char_limit:
            self._summarize_chat_history()
        
        # Check if status is already verified
        if self.status_verified:
            # Pre-knowledge base query step
            pre_kb_prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT_IDENTIFY_TOPICS),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}")
            ])
            pre_kb_messages = pre_kb_prompt.format_messages(
                input=user_input,
                chat_history=self.chat_memory.messages
            )
            pre_kb_response = self.chatllm(pre_kb_messages)
            pre_kb_output_message = pre_kb_response.content

            user_input_with_metadata = user_input + "\n" + pre_kb_output_message
            kb_search_input = pre_kb_output_message

            # Retrieve relevant data from knowledge base
            context_retrieved, metadata_list, score_list = self.knowledge_base.search(
                user_input_with_metadata, 5
            )
            kb_metadata = metadata_list
            kb_scores = score_list

            # Build the counselling system prompt
            counsel_system_prompt = build_counselling_system_prompt(
                self.patient_details, 
                self.prescription_details, 
                context_retrieved
            )

            chat_prompt = ChatPromptTemplate.from_messages([
                ("system", counsel_system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}")
            ])
            
            messages = chat_prompt.format_messages(
                input=user_input,
                chat_history=self.chat_memory.messages
            )
            
            response = self.chatllm_large(messages)
            output_message = response.content
            
        # Perform verification if status is not yet verified
        else:
            verification_system_prompt = build_verification_system_prompt(
                self.patient_details, self.prescription_details
            ) 

            verify_prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(verification_system_prompt),
                HumanMessagePromptTemplate.from_template("{user_input}")
            ])
            
            messages = verify_prompt.format_messages(user_input=user_input)
            response = self.chatllm(messages)
            output_message = response.content
            
            if "verified" in output_message.lower():
                self.status_verified = True
        
        # Store the interaction in chat history
        self.chat_memory.add_message(HumanMessage(content=user_input))
        self.chat_memory.add_message(SystemMessage(content=output_message))
        
        # Increase the turn counter
        self.turn_counter += 1

        # Calculate process_message duration
        process_duration = time.time() - start_time

        # Log the complete interaction
        self.logger.log_interaction(
            convo_number=self.convo_number,
            turn_number=self.turn_counter,
            user_input=user_input,
            start_time=start_time,
            kb_search_input=kb_search_input,
            kb_metadata=kb_metadata,
            kb_scores=kb_scores,
            verification_status=self.status_verified,
            intermediate_output=output_message,
            process_duration=process_duration
        )

        return output_message

    def reset_chat(self):
        """Reset chat memory and turn counter to initial state"""
        self.chat_memory.clear()  # clear chat memory
        self.turn_counter = 0   # reset turn counter
        self.convo_number += 1  # increase the convo number
        self.logger.logger.info("Chat system reset: memory cleared and started new convo")
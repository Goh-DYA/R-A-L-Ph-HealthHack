# Module for initializing and configuring language models.

from langchain_openai import ChatOpenAI, OpenAI
import openai
from config import OPENAI_API_KEY

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY


def initialize_models():
    """
    Initialize and return language models.
    
    Returns:
        tuple: (chatllm, chatllm_large, summaryllm)
    """
    # Main chat model - smaller/faster version
    chatllm = ChatOpenAI(
        model_name="gpt-4o-mini", 
        temperature=0, 
        top_p=0.8, 
        streaming=True
    )
    
    # More powerful model for complex queries
    chatllm_large = ChatOpenAI(
        model_name="gpt-4o", 
        temperature=0, 
        top_p=0.8, 
        streaming=True
    )
    
    # Model for summarization (can use the same as chatllm)
    summaryllm = ChatOpenAI(
        model_name="o3-mini", 
        reasoning_effort="medium"
    )
    
    return chatllm, chatllm_large, summaryllm
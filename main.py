"""
Main entry point for the RALPh application.
"""

import os
import argparse

# Import configuration
from config import (
    PATIENT_DETAILS_EXAMPLE,
    PRESCRIPTION_DETAILS_EXAMPLE,
    MEMORY_CHAR_LIMIT
)

# Import LLM models
from models.llm import initialize_models

# Import chat system
from chat.system import ChatSystem

# Import UI
from ui.gradio_interface import GradioInterface


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="RALPh - Your Personalised Pocket Pharmacist")
    parser.add_argument("--share", action="store_true", help="Create a public link for the Gradio interface")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    return parser.parse_args()


def main():
    """Main function to run the RALPh application"""
    # Parse command line arguments
    args = parse_args()
    
    # Initialize LLM models
    chatllm, chatllm_large, summaryllm = initialize_models()
    print("LLM models initialized")
    
    # Initialize chat system
    chat_system = ChatSystem(
        chatllm=chatllm,
        chatllm_large=chatllm_large,
        summaryllm=summaryllm,
        patient_details=PATIENT_DETAILS_EXAMPLE,
        prescription_details=PRESCRIPTION_DETAILS_EXAMPLE,
        memory_char_limit=MEMORY_CHAR_LIMIT
    )
    print("Chat system initialized")
    
    # Initialize and launch Gradio interface
    gradio_interface = GradioInterface(chat_system, summaryllm)
    print("Launching Gradio interface...")
    gradio_interface.launch_interface(share=args.share)


if __name__ == "__main__":
    main()
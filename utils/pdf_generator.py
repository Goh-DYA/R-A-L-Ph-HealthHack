"""
PDF generation functionality for RALPh.
"""

import os
from datetime import datetime
from fpdf import FPDF
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from chat.prompts import SYSTEM_PROMPT_SUMMARIZE
from config import SUMMARIES_DIR


def summarize_content(content, summaryllm):
    """
    Summarize chat content for the PDF report.
    
    Args:
        content (str): Content to summarize
        summaryllm: LLM for summarization
        
    Returns:
        str: Summarized content
    """
    try:
        # Define summarization prompt
        system_prompt = SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT_SUMMARIZE)
        human_prompt = HumanMessagePromptTemplate.from_template("{content_to_summarize}")
        summarization_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
        
        # Generate summary
        messages = summarization_prompt.format_messages(content_to_summarize=content)
        response = summaryllm(messages)
        print("Content successfully summarised...")
        
        return response.content
    except Exception as e:
        return f"Error in summarization: {e}"


def generate_pdf(chat_memory, prescription_details, summaryllm):
    """
    Generate a PDF summary of the conversation.
    
    Args:
        chat_memory: Chat memory from the chat system
        prescription_details (str): Prescription details
        summaryllm: LLM for summarization
        
    Returns:
        str: Path to the generated PDF
    """
    try:
        # Ensure summaries directory exists
        os.makedirs(SUMMARIES_DIR, exist_ok=True)
        
        # Combine chat history and prescription details
        full_content = "\n".join(str(chat_memory.messages) + "\n\n#PRESCRIPTION DETAILS:" + prescription_details)
        
        # Summarize content
        summary = summarize_content(full_content, summaryllm)
        
        # Generate the PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Try to find an appropriate font that supports Unicode
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        if not os.path.exists(font_path):
            font_path = "C:/Windows/Fonts/Arial.ttf"
        
        # Add font with Unicode support
        pdf.add_font('Unicode', '', font_path, uni=True)
        pdf.set_font('Unicode', size=12)
        
        # Add content to PDF
        pdf.multi_cell(0, 10, summary if summary else "No conversation to save.")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = os.path.join(SUMMARIES_DIR, f"Chatbot_Summary_{timestamp}.pdf")
        
        # Save PDF
        pdf.output(file_name)
        print("PDF report generated!")
        
        return file_name
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None
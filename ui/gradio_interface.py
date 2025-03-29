"""
Gradio UI implementation for RALPh chatbot.
"""

import os
import gradio as gr

from utils.pdf_generator import generate_pdf
from utils.email_sender import send_email_with_pdf
from utils.speech import audio_to_text, text_to_audio


class GradioInterface:
    """
    Gradio UI interface for the RALPh chatbot.
    """
    
    def __init__(self, chat_system, summaryllm):
        """
        Initialize Gradio interface.
        
        Args:
            chat_system: RALPh chat system
            summaryllm: Model for summarization
        """
        self.chat_system = chat_system
        self.summaryllm = summaryllm
        self.introduction_msg = """💊 **Welcome to RALPh!** 🤖👨‍⚕️
As your personalised pocket pharmacist, I'm here to help with all your medication-related questions. Whether you're curious about dosages, side effects, or your medications, I'm here to guide you every step of the way! 🌟

Firstly, may i verify your name, date of birth & allergy status?
"""
        
    def print_like_dislike(self, x: gr.LikeData):
        """
        Handle like/dislike button clicks.
        
        Args:
            x: Like data
        """
        print(x.index, x.value, x.liked)
    
    def add_text_audio(self, history, text, audio=None):
        """
        Handle text input or use audio input if provided.
        
        Args:
            history: Chat history
            text: Text input
            audio: Audio input file
            
        Returns:
            tuple: (updated_history, textbox)
        """
        if audio is not None:
            # Convert audio input to text
            transcribed_text, _, _, _ = audio_to_text(audio)
            user_input = transcribed_text
        else:
            user_input = text
        
        history = history + [(user_input, None)]
        return history, gr.Textbox(value="", interactive=False)
    
    def trigger_bot_response(self, history, play_audio=False):
        """
        Process user input and generate bot response.
        
        Args:
            history: Chat history
            play_audio: Whether to convert response to audio
            
        Yields:
            tuple: (updated_history, audio_path)
        """
        query = history[-1][0]  # Get the user's query
    
        # Call the chatLLM, pass in the input & gather a response
        response_content = self.chat_system.process_message(query)
    
        # Set up empathy prompt
        # from langchain_core.messages import SystemMessage, AIMessage
        # empathy_prompt = [
        #     SystemMessage(content="placeholder."),
        #     AIMessage(content=response_content)
        # ]
    
        # Stream the final empathy LLM
        full_response = "" 
        audio_path = None
        
        # for chunk in self.chat_system.chatllm.stream(input=empathy_prompt):
            # full_response += chunk.content  # Append the chunk to the full response
            
        for chunk in response_content:  # Stream response content
            full_response += chunk

            history[-1][1] = full_response
            yield history, audio_path
        
        # Convert the full response to audio if play_audio is True
        if play_audio:
            print("--- Converting to audio ---")
            _, audio_path = text_to_audio(full_response)
            print("+++ Converted to audio +++")
            
            # Yield the final update with the audio path
            yield history, audio_path
            
        # Update the log with the final response
        self.chat_system.logger.update_final_response(full_response)
    
    def save_to_pdf_and_send_email(self, recipient_email):
        """
        Generate PDF summary and send via email.
        
        Args:
            recipient_email: Recipient's email address
            
        Returns:
            str: Success message or error
        """
        try:
            # Generate PDF
            pdf_path = generate_pdf(
                self.chat_system.chat_memory,
                self.chat_system.prescription_details,
                self.summaryllm
            )
            
            if not pdf_path:
                return "Failed to generate PDF summary."
            
            # Send email
            return send_email_with_pdf(pdf_path, recipient_email)
            
        except Exception as e:
            return f"Error while generating or sending PDF: {e}"
    
    def launch_interface(self, share=False):
        """
        Build and launch the Gradio interface.
        
        Args:
            share (bool): Whether to create a public link
            
        Returns:
            gr.Blocks: Gradio interface
        """
        # Get the current directory for image assets
        current_directory = os.getcwd()
        
        # Create the Gradio interface
        with gr.Blocks() as main_interface: 
            chatbot = gr.Chatbot(
                value=[[None, self.introduction_msg]],
                elem_id="chatbot",
                avatar_images=((os.path.join(current_directory, "static/user.png")), 
                               (os.path.join(current_directory, "static/pharm_logo.jpeg"))),
                height=600,
                scale=1,
                label = "RALPh - Your Personalised Pocket Pharmacist",
                show_copy_button=True,
                render_markdown=True
            )
    
            with gr.Row():
                txt_input = gr.Textbox(
                    scale=5,
                    show_label=False,
                    placeholder="Enter text and press enter",
                    container=False,
                    interactive=True
                )
                clear = gr.Button("Clear")
    
            with gr.Row():
                # Audio input using Gradio's microphone interface
                mic_input = gr.Audio(
                    sources="microphone",
                    type="filepath",
                    label="Voice your query",
                    interactive=True,
                    scale=5
                )
    
                # Audio output component for playing the bot's response
                audio_output = gr.Audio(
                    label="RALPh's Voice Response", 
                    type="filepath", 
                    interactive=False,
                    visible=False,
                    autoplay=True,
                    scale=5
                )
    
                # Audio playback toggle
                play_audio_checkbox = gr.Checkbox(
                    label="Play response as audio",
                    value=False,
                    scale=1
                )
    
            # Trigger chatbot with text input
            txt_msg = txt_input.submit(
                self.add_text_audio, [chatbot, txt_input], [chatbot, txt_input], queue=False
            ).then(
                self.trigger_bot_response, [chatbot, play_audio_checkbox], [chatbot, audio_output], api_name="bot_response"
            ).then(
                lambda: gr.Textbox(interactive=True), None, [txt_input], queue=False  # re-enable the textbox
            )
            
            # Trigger chatbot with voice input
            voice_msg = mic_input.stop_recording(
                self.add_text_audio, [chatbot, txt_input, mic_input], [chatbot, txt_input], queue=False
            ).then(
                self.trigger_bot_response, [chatbot, play_audio_checkbox], [chatbot, audio_output]
            ).then(
                lambda: gr.Textbox(interactive=True), None, [txt_input], queue=False  # re-enable the textbox
            )  
    
            chatbot.like(self.print_like_dislike, None, None)  # like-dislike button
            clear.click(lambda: self.chat_system.reset_chat(), None, chatbot, queue=False)  # button to reset chat
    
            # Update audio output visibility based on checkbox
            play_audio_checkbox.change(
                lambda x: gr.Audio(visible=x), 
                [play_audio_checkbox], 
                [audio_output]
            )
    
            with gr.Row():
                email_input = gr.Textbox(
                    show_label=False, 
                    container=False, 
                    placeholder="Enter your email to receive the conversation PDF", 
                    scale=5
                )
                save_button = gr.Button("Send PDF to Email", scale=3)
            
            save_button.click(
                self.save_to_pdf_and_send_email,
                inputs=email_input,
                outputs=email_input  # status response provided in the same box
            )
            
            warning_footnote = gr.HTML("""<p style="color: #ff9900; text-align: center;">⚠️ RALPh may display inaccurate information, do double-check its responses or consult a pharmacist. It is not a basis for therapeutic decisions, nor a substitute for professional judgement. ⚠️</p>""")
    
        # Configure interface
        main_interface.queue()
        
        # Launch the interface
        main_interface.launch(show_api=False, share=share)
        
        return main_interface
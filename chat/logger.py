"""
Logging functionality for RALPh chatbot.
"""

import os
import json
import logging
import codecs
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import LOG_DIR


class ChatSystemLogger:
    """
    Logger class for ChatSystem that handles both text and structured logging with Unicode support.
    """
    
    def __init__(self, log_dir=LOG_DIR):
        """
        Initialize logger with file and console handlers.
        
        Args:
            log_dir (str): Directory for log files
        """
        # Create log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Generate timestamp for log files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.text_log_filename = os.path.join(log_dir, f"chat_system_{timestamp}.log")
        self.json_log_filename = os.path.join(log_dir, f"chat_system_{timestamp}.json")
        
        # Configure text file handler with UTF-8 encoding
        file_handler = logging.FileHandler(self.text_log_filename, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Configure console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Set up logger
        self.logger = logging.getLogger('ChatSystem')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers if any
        if self.logger.handlers:
            self.logger.handlers.clear()
            
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Initialize conversation ID
        self._conversation_id: Optional[str] = None
        
        # Initialize structured logs
        self.structured_logs: List[Dict[str, Any]] = []

    def _save_structured_log(self):
        """Save structured logs to JSON file with UTF-8 encoding"""
        try:
            with codecs.open(self.json_log_filename, 'w', encoding='utf-8') as f:
                json.dump(self.structured_logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving structured log: {str(e)}")
            
    def _sanitize_for_logging(self, data: Any) -> Any:
        """
        Sanitize data for logging to handle potential Unicode issues.
        
        Args:
            data: The data to sanitize
            
        Returns:
            Sanitized data
        """
        if isinstance(data, str):
            # Replace any problematic characters with their closest ASCII equivalent
            return data.encode('ascii', 'replace').decode('ascii')
        elif isinstance(data, dict):
            return {k: self._sanitize_for_logging(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_for_logging(item) for item in data]
        return data
            
    def start_conversation(self):
        """Generate a new conversation ID for tracking chat sessions"""
        self._conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger.info(f"Starting new conversation with ID: {self._conversation_id}")

    def log_interaction(self, 
                       convo_number: int,
                       turn_number: int,                       
                       user_input: str,
                       start_time: float,
                       kb_search_input: str = None,
                       kb_metadata: list = None,
                       kb_scores: list = None,
                       verification_status: bool = None,
                       intermediate_output: str = None,
                       process_duration: float = None):
        """
        Log a complete interaction in both text and structured formats.
        
        Args:
            convo_number: Conversation number
            turn_number: Turn number in conversation
            user_input: User's input text
            start_time: Start time of interaction (timestamp)
            kb_search_input: Knowledge base search input
            kb_metadata: Knowledge base result metadata
            kb_scores: Knowledge base result scores
            verification_status: Whether user is verified
            intermediate_output: LLM output before empathy processing
            process_duration: Processing time in seconds
        """
        try:
            # Convert start_time to ISO format
            timestamp = datetime.fromtimestamp(start_time).isoformat()
            
            # Text logging - handle potential Unicode issues
            safe_user_input = self._sanitize_for_logging(user_input)
            safe_kb_search = self._sanitize_for_logging(kb_search_input)
            safe_kb_metadata = self._sanitize_for_logging(kb_metadata)
            safe_kb_scores = self._sanitize_for_logging(kb_scores)
            safe_output = self._sanitize_for_logging(intermediate_output)

            # Text logging
            self.logger.info(f"Convo: {convo_number}")
            self.logger.info(f"Turn: {turn_number}")
            self.logger.info(f"INPUT: {safe_user_input}")
            if kb_search_input:
                self.logger.info(f"KB SEARCH INPUT: {safe_kb_search}")
            if kb_metadata and kb_scores:
                self.logger.info(f"KB Results - Metadata: {safe_kb_metadata}")
                self.logger.info(f"KB Results - Scores: {safe_kb_scores}")
            if intermediate_output:
                self.logger.info(f"INTERMEDIATE OUTPUT: {safe_output}")
            if process_duration is not None:
                self.logger.info(f"Process Message Duration: {process_duration:.3f} seconds")
                
            # Structured logging
            structured_log = {
                "conversation_id": self._conversation_id,
                "convo_number": convo_number,
                "turn_number": turn_number,
                "timestamp": timestamp,  # Use timestamp from start_time
                "user_input": user_input,
                "verification_done": verification_status,
                "kb_search_input": kb_search_input,
                "kb_results": {
                    "metadata": kb_metadata,
                    "scores": kb_scores
                },
                "intermediate_output": intermediate_output,
                "final_response": None,
                "final_response_timestamp": None,
                "process_message_duration": process_duration,
                "total_query_duration": None
            }
            
            self.structured_logs.append(structured_log)
            self._save_structured_log()
            
        except Exception as e:
            self.logger.error(f"Error in log_interaction: {str(e)}")
            try:
                self.logger.error(f"Failed to log interaction for turn {turn_number}")
                self._save_structured_log()
            except:
                pass

    def update_final_response(self, full_response: str):
        """
        Update the last structured log entry with the final response and timing information.
        
        Args:
            full_response: The final response from the LLM
        """
        try:
            if not self.structured_logs:
                self.logger.error("No log entries found to update")
                return
                
            # Get the last log entry
            log = self.structured_logs[-1]
            
            # Update final response and timestamp
            log["final_response"] = full_response
            log["final_response_timestamp"] = datetime.now().isoformat()
            
            # Calculate and update total query duration
            log["total_query_duration"] = self.calculate_query_duration(
                log["timestamp"],
                log["final_response_timestamp"]
            )
            
            # Log timing information
            self.logger.info(f"Process Message Duration: {log['process_message_duration']:.3f} seconds")
            self.logger.info(f"Total Query Duration: {log['total_query_duration']:.3f} seconds")

            # Update text and JSON logs
            self.logger.info(f"FINAL RESPONSE: {self._sanitize_for_logging(full_response)}")
            self.logger.info("##################################################")
            self._save_structured_log()

        except Exception as e:
            self.logger.error(f"Error updating final response: {str(e)}")


    def calculate_query_duration(self, start_time: str, end_time: str) -> float:
        """
        Calculate duration between two ISO format timestamps.
        
        Args:
            start_time: Start time in ISO format
            end_time: End time in ISO format
            
        Returns:
            float: Duration in seconds
        """
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            return (end - start).total_seconds()
        except Exception as e:
            self.logger.error(f"Error calculating query duration: {str(e)}")
            return 0.0
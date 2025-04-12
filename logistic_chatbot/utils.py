import os
import json
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from typing import List, Dict, Optional
from datetime import datetime

# Load environment variables
load_dotenv()

class ChatbotError(Exception):
    """Custom exception for chatbot errors"""
    pass

def get_groq_client() -> Groq:
    """Initialize and return Groq client with API key"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ChatbotError("GROQ_API_KEY not found in environment variables")
    return Groq(api_key=api_key)

def summarize_data(df: pd.DataFrame, sample_size: int = 3) -> str:
    """
    Generate a comprehensive summary of the dataframe
    Args:
        df: DataFrame to summarize
        sample_size: Number of sample values to show for text columns
    Returns:
        str: Markdown-formatted summary
    """
    try:
        summary = [
            f"## Data Summary ({len(df)} rows × {len(df.columns)} columns)",
            f"**Columns:** {', '.join(f'`{col}`' for col in df.columns)}",
            f"**Missing values:** {df.isna().sum().sum()} total",
        ]
        
        # Numeric columns analysis
        numeric_cols = df.select_dtypes(include='number').columns
        if not numeric_cols.empty:
            summary.append("\n### Numeric Columns")
            stats = df[numeric_cols].describe().transpose()
            stats['range'] = stats['max'] - stats['min']
            summary.append(stats[['mean', 'min', 'max', 'range', 'std']].to_markdown())
        
        # Text columns analysis
        text_cols = df.select_dtypes(include=['object', 'string']).columns
        if not text_cols.empty:
            summary.append("\n### Text Columns")
            for col in text_cols:
                unique_count = df[col].nunique()
                sample_values = df[col].dropna().sample(min(sample_size, len(df))).tolist()  # Fixed here
                summary.append(
                    f"- `{col}`: {unique_count} unique values\n"
                    f"  Sample: {', '.join(str(v) for v in sample_values)}"
                )
        
        # Date columns analysis
        date_cols = df.select_dtypes(include=['datetime', 'datetimetz']).columns
        if not date_cols.empty:
            summary.append("\n### Date Columns")
            for col in date_cols:
                date_range = f"{df[col].min()} to {df[col].max()}"
                summary.append(f"- `{col}`: {date_range}")
        
        return "\n".join(summary)
    except Exception as e:
        raise ChatbotError(f"Data summarization error: {str(e)}")

def ask_gpt(prompt: str, system_content: str = None) -> str:
    """Get response from LLM with proper error handling"""
    if not system_content:
        system_content = """You are an expert Logistics and Supply Chain AI Assistant.
        Provide accurate, concise answers with practical recommendations."""
    
    client = get_groq_client()
    
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4000,  # Increased for data analysis
            top_p=0.9
        )
        return response.choices[0].message.content
    except Exception as e:
        raise ChatbotError(f"API Error: {str(e)}")

def ask_gpt_with_data(prompt: str, df: pd.DataFrame, system_content: str = None) -> str:
    """
    Enhanced version that includes full data context
    Args:
        prompt: User question
        df: DataFrame to analyze
        system_content: Optional custom system message
    Returns:
        str: Generated response
    """
    if not system_content:
        system_content = """You are an expert Logistics and Supply Chain AI Assistant
        skilled at data analysis and visualization."""
    
    data_context = summarize_data(df)
    full_system = f"""
    {system_content}
    You are analyzing logistics data with these characteristics:
    {data_context}
    Provide specific insights from the data when possible.
    """
    
    enhanced_prompt = f"""
    When answering this logistics question: {prompt}
    Consider this detailed data context:
    {data_context}
    Provide specific numbers and insights from the data where relevant.
    """
    
    return ask_gpt(enhanced_prompt, full_system)

def save_chat_history(history: List[Dict], filename: str = "chat_history.json") -> None:
    """Save chat history to JSON file"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except IOError as e:
        raise ChatbotError(f"Failed to save chat history: {str(e)}")

def clear_chat_history(filename: str = "chat_history.json") -> None:
    """Clear chat history from file"""
    try:
        if os.path.exists(filename):
            os.remove(filename)
    except IOError as e:
        raise ChatbotError(f"Failed to clear chat history: {str(e)}")

def validate_dataframe(df: pd.DataFrame) -> bool:
    """Check if dataframe meets analysis requirements"""
    if len(df) < 1:
        raise ChatbotError("Dataframe has no rows")
    if len(df.columns) < 1:
        raise ChatbotError("Dataframe has no columns")
    return True
# Add these new functions to utils.py
def get_chat_history(filename: str = "chat_history.json") -> List[Dict]:
    """Load chat history from JSON file"""
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        raise ChatbotError(f"Failed to load chat history: {str(e)}")

def save_conversation_metadata(conversations: List[Dict], filename: str = "conversations.json") -> None:
    """Save conversation metadata"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(conversations, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise ChatbotError(f"Failed to save conversations: {str(e)}")

def get_conversation_metadata(filename: str = "conversations.json") -> List[Dict]:
    """Load conversation metadata"""
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        raise ChatbotError(f"Failed to load conversations: {str(e)}")
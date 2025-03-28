import json
import logging
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from .prompts import SYSTEM_PROMPT
from .tools import get_tools, handle_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple OpenAI client initialization
api_key = os.getenv("OPENAI_API_KEY")
client = None

if api_key:
    client = OpenAI(api_key=api_key)
    logger.info("OpenAI client initialized with provided API key")
else:
    logger.warning("No OPENAI_API_KEY environment variable found. Using mock responses.")

def validate_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate and clean messages to ensure they're in the correct format for OpenAI's API.
    Specifically handles tool messages and tool_calls to prevent errors.
    """
    valid_messages = []
    has_tool_call = False
    tool_call_id = None
    
    for i, msg in enumerate(messages):
        # Skip messages without role or content (unless it's a tool message with tool_call_id)
        if "role" not in msg:
            logger.warning(f"Skipping message at index {i}: missing 'role'")
            continue
            
        # Handle tool messages specifically
        if msg["role"] == "tool":
            # Tool messages must have a tool_call_id and follow a message with tool_calls
            if not has_tool_call:
                logger.warning(f"Skipping tool message at index {i}: no preceding message with tool_calls")
                continue
                
            # Ensure tool messages have tool_call_id
            if "tool_call_id" not in msg:
                logger.warning(f"Skipping tool message at index {i}: missing 'tool_call_id'")
                continue
                
            # Add the tool message
            valid_msg = {
                "role": "tool",
                "tool_call_id": msg["tool_call_id"],
                "content": msg.get("content", "")
            }
            valid_messages.append(valid_msg)
            continue
            
        # All non-tool messages must have content
        if "content" not in msg and msg["role"] != "assistant":
            logger.warning(f"Skipping message at index {i}: missing 'content'")
            continue
            
        # Create a copy of the message with only the fields OpenAI expects
        valid_msg = {"role": msg["role"]}
        
        # Include content if present (can be None for assistant messages with tool_calls)
        if "content" in msg:
            valid_msg["content"] = msg["content"]
        elif msg["role"] == "assistant":
            valid_msg["content"] = ""  # Empty string for missing content
            
        # Add tool_calls for assistant messages if present
        if msg["role"] == "assistant" and "tool_calls" in msg and msg["tool_calls"]:
            valid_msg["tool_calls"] = msg["tool_calls"]
            has_tool_call = True
        else:
            has_tool_call = False
            
        valid_messages.append(valid_msg)
    
    logger.info(f"Validated messages: {len(valid_messages)} valid out of {len(messages)} input messages")
    return valid_messages

def chat_completion(
    messages: List[Dict[str, str]], 
    tools: Optional[List[Dict[str, Any]]] = None,
    stream: bool = False
):
    """Call OpenAI API to get chat completion"""
    model = "gpt-4o"
    
    if tools is None:
        tools = get_tools()
    
    # Validate and clean the messages
    validated_messages = validate_messages(messages)
    
    # If we have a valid client, use the OpenAI API
    if client and api_key:
        try:
            logger.info(f"Calling OpenAI API with {len(validated_messages)} messages")
            
            # Log the last few messages for debugging (without system prompt)
            if len(validated_messages) > 0:
                logger.info(f"Last message: {validated_messages[-1].get('role')}: {validated_messages[-1].get('content')[:100] if validated_messages[-1].get('content') else '[No content]'}...")
            
            response = client.chat.completions.create(
                model=model,
                messages=validated_messages,
                tools=tools,
                stream=stream
            )
            
            logger.info(f"OpenAI API response received with status: {response.choices[0].finish_reason}")
            
            return response
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            # Fall back to mock response
    
    # Create a mock response for development without API key
    logger.info("Using mock response for chat completion")
    
    # Get the last user message
    last_message = "Hello"
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_message = msg.get("content", "")
            break
    
    # Generate mock response based on user message
    if "generate" in last_message.lower() and "sequence" in last_message.lower():
        # Mock a tool call for sequence generation
        mock_response = create_mock_completion_with_tool_call("generate_sequence", last_message)
    elif "research" in last_message.lower() and "industry" in last_message.lower():
        # Mock a tool call for industry research
        mock_response = create_mock_completion_with_tool_call("research_industry", last_message)
    elif any(keyword in last_message.lower() for keyword in ["sales sequence", "outreach", "homeowner", "fire", "aid", "program", "gov", "assistance", "support", "california", "LA", "los angeles", "california"]):
        # More aggressive tool call triggering for sales/outreach scenarios
        logger.info("Detected sales/outreach related keywords, triggering sequence generation")
        mock_response = create_mock_completion_with_tool_call("generate_sequence", last_message)
    else:
        # Regular response
        mock_response = create_mock_completion(
            f"I'm Eunoia, your AI recruiting assistant. How can I help you create effective outreach sequences today? (Note: This is a mock response as no OpenAI API key was provided.)"
        )
    
    return mock_response

def create_mock_completion(content):
    """Create a mock ChatCompletion object with a simple structure"""
    # Create a simple dict-based mock that mimics the OpenAI response structure
    message = {
        "content": content,
        "role": "assistant",
        "function_call": None,
        "tool_calls": None
    }
    
    choice = {
        "finish_reason": "stop",
        "index": 0,
        "message": message,
        "logprobs": None
    }
    
    # Convert to an object with attribute access for compatibility
    class DictToObject:
        def __init__(self, data):
            for key, value in data.items():
                if isinstance(value, dict):
                    setattr(self, key, DictToObject(value))
                else:
                    setattr(self, key, value)
    
    mock_completion = {
        "id": "mock-completion-id",
        "choices": [DictToObject(choice)],
        "created": 1234567890,
        "model": "mock-model",
        "object": "chat.completion",
        "system_fingerprint": None
    }
    
    return DictToObject(mock_completion)

def create_mock_completion_with_tool_call(tool_name, last_message=""):
    """Create a mock ChatCompletion with a tool call"""
    
    # Parse important keywords from the last message
    target_role = ""
    company_name = "your company"
    industry = ""
    value_proposition = ""
    
    # Extract possible target role/audience
    if "homeowner" in last_message.lower():
        target_role = "Homeowners"
    elif "developer" in last_message.lower():
        target_role = "Software Developers"
    elif "sales" in last_message.lower() and "sequence" in last_message.lower():
        target_role = "Sales Prospects"
    
    # Extract possible industry information
    if "tech" in last_message.lower() or "software" in last_message.lower():
        industry = "Technology"
    elif "real estate" in last_message.lower() or "home" in last_message.lower():
        industry = "Real Estate"
    elif "LA" in last_message or "california" in last_message.lower() or "los angeles" in last_message.lower():
        industry = "Real Estate"
        target_role = "Homeowners in LA"
    
    # Extract possible value proposition
    if "fire" in last_message.lower() and ("support" in last_message.lower() or "aid" in last_message.lower()):
        value_proposition = "provide emergency support after recent fires"
    elif "gov" in last_message.lower() and "aid" in last_message.lower():
        value_proposition = "access government aid programs"
    elif "program" in last_message.lower():
        value_proposition = "join our special assistance program"
    
    if tool_name == "generate_sequence":
        # Use extracted info or defaults
        args = json.dumps({
            "company_name": company_name,
            "target_role": target_role or "Potential Customers",
            "industry": industry or "General",
            "value_proposition": value_proposition or ""
        })
    elif tool_name == "research_industry":
        args = json.dumps({
            "industry": industry or "technology"
        })
    else:
        args = json.dumps({})
    
    # Create tool call object
    function_obj = {
        "name": tool_name,
        "arguments": args
    }
    
    tool_call = {
        "id": f"mock-{tool_name}-call",
        "function": function_obj,
        "type": "function"
    }
    
    message = {
        "content": "I'll help you with that.",
        "role": "assistant",
        "tool_calls": [tool_call]
    }
    
    choice = {
        "finish_reason": "tool_calls",
        "index": 0,
        "message": message,
        "logprobs": None
    }
    
    # Convert to an object with attribute access for compatibility
    class DictToObject:
        def __init__(self, data):
            for key, value in data.items():
                if isinstance(value, dict):
                    setattr(self, key, DictToObject(value))
                elif isinstance(value, list):
                    setattr(self, key, [DictToObject(item) if isinstance(item, dict) else item for item in value])
                else:
                    setattr(self, key, value)
    
    mock_completion = {
        "id": "mock-completion-id-with-tool",
        "choices": [DictToObject(choice)],
        "created": 1234567890,
        "model": "mock-model",
        "object": "chat.completion",
        "system_fingerprint": None
    }
    
    return DictToObject(mock_completion)

def handle_tool_calls(tool_calls):
    """Process the tool calls from the model response"""
    results = []
    for tool_call in tool_calls:
        try:
            function_name = tool_call.function.name
            arguments_json = tool_call.function.arguments
            
            # Parse arguments
            try:
                arguments = json.loads(arguments_json)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in tool call arguments: {arguments_json}")
                arguments = {}
            
            # Call the appropriate tool handler
            result = handle_tool(function_name, arguments)
            
            # Add metadata to result
            results.append({
                "tool_call_id": tool_call.id,
                "function_name": function_name,
                "result": result
            })
            
            logger.info(f"Successfully executed tool {function_name}")
        except Exception as e:
            logger.error(f"Error processing tool call: {e}", exc_info=True)
            results.append({
                "tool_call_id": getattr(tool_call, "id", "unknown"),
                "function_name": getattr(tool_call, "function", {}).get("name", "unknown"),
                "result": {"error": f"Tool execution failed: {str(e)}"}
            })
    
    return results

def update_sequence(args):
    """Update an existing sequence"""
    sequence_id = args.get("sequence_id")
    changes = args.get("changes", [])
    
    # In a production environment, you would fetch the sequence from database
    # For this implementation, we'll just echo back the changes as if applied
    
    success_messages = []
    
    # If changes is a whole sequence object, just return it
    if isinstance(changes, dict) and "steps" in changes:
        return {
            "sequence_id": sequence_id,
            "status": "updated",
            "message": "Sequence updated with all new content",
            "updated_sequence": changes
        }
    
    # Otherwise, process individual changes
    for change in changes:
        if isinstance(change, dict):
            if "step_index" in change and "field" in change and "value" in change:
                step_index = change.get("step_index")
                field = change.get("field")
                value = change.get("value")
                success_messages.append(f"Updated step {step_index+1}, set {field} to new value")
            elif "add_step" in change and change["add_step"] is True:
                new_step = change.get("step_data", {})
                success_messages.append(f"Added new step with channel {new_step.get('channel', 'unspecified')}")
            elif "remove_step" in change and "step_index" in change:
                step_index = change.get("step_index")
                success_messages.append(f"Removed step {step_index+1}")
            elif "metadata" in change:
                metadata = change.get("metadata", {})
                fields = ", ".join(metadata.keys())
                success_messages.append(f"Updated sequence metadata: {fields}")
    
    return {
        "sequence_id": sequence_id,
        "status": "updated", 
        "message": "Sequence updated successfully",
        "changes_applied": success_messages
    }

def research_industry(args):
    """Research information about an industry"""
    industry = args.get("industry", "").lower()
    
    industry_info = {
        "technology": {
            "overview": "The technology industry is fast-paced and constantly evolving, driving innovation across all sectors.",
            "trends": [
                "Artificial Intelligence and Machine Learning",
                "Cloud Computing and Edge Computing",
                "Cybersecurity",
                "Internet of Things (IoT)",
                "5G and Advanced Connectivity"
            ],
            "skills_in_demand": [
                "Software Development",
                "Data Science and Analytics",
                "Cloud Architecture",
                "Cybersecurity Expertise",
                "AI/ML Engineering"
            ],
            "recruitment_tips": [
                "Highlight opportunities for technical growth and innovation",
                "Emphasize work-life balance as tech burnout is common",
                "Showcase modern tech stack and engineering practices",
                "Mention remote work options as tech workers value flexibility",
                "Include details about learning and development resources"
            ]
        },
        "healthcare": {
            "overview": "Healthcare is focused on patient outcomes, regulatory compliance, and improving care delivery systems.",
            "trends": [
                "Telehealth and Remote Patient Monitoring",
                "Healthcare Data Analytics",
                "Value-based Care Models",
                "Healthcare AI Applications",
                "Personalized Medicine"
            ],
            "skills_in_demand": [
                "Clinical Expertise",
                "Healthcare IT",
                "Regulatory Compliance Knowledge",
                "Patient Care Coordination",
                "Healthcare Data Analysis"
            ],
            "recruitment_tips": [
                "Emphasize mission and impact on patient care",
                "Highlight stability and career advancement",
                "Mention training for regulatory compliance",
                "Discuss work-life balance and burnout prevention",
                "Feature supportive team environment"
            ]
        },
        "finance": {
            "overview": "The finance industry requires attention to detail, risk management, and adaptation to changing regulations and technologies.",
            "trends": [
                "Financial Technology (FinTech) Integration",
                "Blockchain and Cryptocurrency",
                "Automated Financial Analysis",
                "ESG (Environmental, Social, Governance) Investing",
                "Regulatory Technology (RegTech)"
            ],
            "skills_in_demand": [
                "Financial Analysis",
                "Regulatory Compliance Expertise",
                "Data Analysis",
                "Risk Management",
                "FinTech Knowledge"
            ],
            "recruitment_tips": [
                "Highlight competitive compensation packages",
                "Emphasize career growth and advancement paths",
                "Mention stability and company reputation",
                "Discuss training and certification support",
                "Feature cutting-edge financial technologies"
            ]
        },
        "manufacturing": {
            "overview": "Manufacturing focuses on operational efficiency, quality control, and increasingly, technological innovation.",
            "trends": [
                "Industry 4.0 and Smart Manufacturing",
                "Automation and Robotics",
                "Sustainable Manufacturing Practices",
                "Digital Twins and Simulation",
                "Supply Chain Optimization"
            ],
            "skills_in_demand": [
                "Process Engineering",
                "Supply Chain Management",
                "Quality Assurance",
                "Automation Engineering",
                "Sustainable Manufacturing Knowledge"
            ],
            "recruitment_tips": [
                "Highlight technological advancement in processes",
                "Emphasize stability and growth potential",
                "Mention safety focus and improvements",
                "Discuss training and upskilling programs",
                "Feature innovation initiatives"
            ]
        },
        "retail": {
            "overview": "Retail is undergoing digital transformation, with focus on customer experience across online and physical channels.",
            "trends": [
                "Omnichannel Retail Experiences",
                "E-commerce Integration",
                "Personalized Shopping",
                "Supply Chain Efficiency",
                "Retail Analytics"
            ],
            "skills_in_demand": [
                "Digital Marketing",
                "Customer Experience Design",
                "Supply Chain Management",
                "Data Analysis",
                "E-commerce Platform Management"
            ],
            "recruitment_tips": [
                "Highlight innovation in customer experience",
                "Emphasize flexible schedules where applicable",
                "Mention employee discounts and benefits",
                "Discuss career progression from entry-level",
                "Feature technology adoption stories"
            ]
        }
    }
    
    # Default information if industry not found
    default_info = {
        "overview": f"The {industry} industry has unique challenges and opportunities.",
        "trends": [
            "Digital Transformation",
            "Sustainability Focus",
            "Data-Driven Decision Making",
            "Customer-Centric Approaches",
            "Workforce Development"
        ],
        "skills_in_demand": [
            "Technical Expertise",
            "Communication Skills",
            "Adaptability",
            "Problem-Solving",
            "Collaboration"
        ],
        "recruitment_tips": [
            "Highlight industry-specific growth opportunities",
            "Emphasize company culture and values",
            "Mention professional development resources",
            "Discuss work-life balance initiatives",
            "Feature employee success stories"
        ]
    }
    
    return {
        "industry": industry,
        "information": industry_info.get(industry, default_info)
    } 

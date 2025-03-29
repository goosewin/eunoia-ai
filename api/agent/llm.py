import json
import logging
import os
from typing import Any

from openai import APIError, OpenAI, OpenAIError, RateLimitError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:

    logger.error("CRITICAL: OPENAI_API_KEY environment variable not found. Real LLM calls will fail.")

    client = None
else:
    client = OpenAI(api_key=api_key)
    logger.info("OpenAI client initialized with provided API key")

def validate_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    
    valid_messages = []
    assistant_message_indices_with_tool_calls = set()

    for i, msg in enumerate(messages):
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            assistant_message_indices_with_tool_calls.add(i)

    for i, msg in enumerate(messages):

        if "role" not in msg:
            logger.warning(f"Skipping message at index {i}: missing 'role'")
            continue
        if msg["role"] not in ["system", "user", "assistant", "tool"]:
             logger.warning(f"Skipping message at index {i}: invalid 'role' {msg['role']}")
             continue

        if msg["role"] == "tool":

            if "tool_call_id" not in msg:
                logger.warning(f"Skipping tool message at index {i}: missing 'tool_call_id'")
                continue

            preceded_by_assistant_tool_call = False
            for assistant_idx in assistant_message_indices_with_tool_calls:
                if assistant_idx < i:
                    preceded_by_assistant_tool_call = True
                    break
            if not preceded_by_assistant_tool_call:
                 logger.warning(f"Skipping tool message at index {i}: does not follow an assistant message with tool_calls in the current history slice.")
                 continue

            valid_msg = {
                "role": "tool",
                "tool_call_id": msg["tool_call_id"],
                "content": str(msg.get("content", ""))
            }
            valid_messages.append(valid_msg)

        elif msg["role"] == "assistant":
            valid_msg = {"role": "assistant"}

            if "content" in msg and msg["content"] is not None:
                 valid_msg["content"] = str(msg["content"])
            elif "tool_calls" not in msg or not msg["tool_calls"]:
                 valid_msg["content"] = ""

            if "tool_calls" in msg and msg["tool_calls"]:
                if not isinstance(msg["tool_calls"], list):
                     logger.warning(f"Skipping assistant message at index {i}: 'tool_calls' is not a list.")
                     continue
                valid_tool_calls = []
                for tc in msg["tool_calls"]:
                    if isinstance(tc, dict) and "id" in tc and "type" in tc and "function" in tc:
                        if isinstance(tc["function"], dict) and "name" in tc["function"] and "arguments" in tc["function"]:
                             valid_tool_calls.append(tc)

                if not valid_tool_calls:

                    if "content" not in valid_msg:
                         valid_msg["content"] = ""
                else:
                     valid_msg["tool_calls"] = valid_tool_calls

            if "content" in valid_msg or "tool_calls" in valid_msg:
                valid_messages.append(valid_msg)
            else:
                logger.warning(f"Skipping assistant message at index {i}: No content or valid tool_calls.")

        elif msg["role"] in ["user", "system"]:
            if "content" not in msg or msg["content"] is None:
                logger.warning(f"Skipping {msg['role']} message at index {i}: missing 'content'")
                continue
            valid_msg = {
                "role": msg["role"],
                "content": str(msg["content"])
            }
            valid_messages.append(valid_msg)

    if valid_messages and valid_messages[0]["role"] in ["assistant", "tool"]:
         logger.warning("History starts with an assistant or tool message, which might be problematic.")

    logger.info(f"Validated messages: {len(valid_messages)} valid out of {len(messages)} input messages")
    return valid_messages

def chat_completion(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | None = "auto"
):
    model = "gpt-4o"

    if not client:
        logger.error("OpenAI client not available. Cannot make API call.")
        raise OpenAIError("OpenAI client is not configured. Check OPENAI_API_KEY.")

    validated_messages = validate_messages(messages)

    if not validated_messages:
        logger.error("No valid messages to send to OpenAI API after validation.")
        raise ValueError("Cannot call OpenAI API with an empty message list.")

    try:
        logger.info(f"Calling OpenAI API with {len(validated_messages)} messages. First role: {validated_messages[0]['role']}, Last role: {validated_messages[-1]['role']}")

        last_msg = validated_messages[-1]
        last_content_preview = str(last_msg.get('content'))[:100] + '...' if last_msg.get('content') else '[No content]'
        if last_msg.get("tool_calls"):
             last_content_preview += f" (Tool Calls: {len(last_msg['tool_calls'])})"
        logger.info(f"Last message preview: {last_msg.get('role')}: {last_content_preview}")

        api_params = {
            "model": model,
            "messages": validated_messages,
        }
        if tools:
             api_params["tools"] = tools
             api_params["tool_choice"] = tool_choice

        response = client.chat.completions.create(**api_params)

        finish_reason = response.choices[0].finish_reason if response.choices else "unknown"
        logger.info(f"OpenAI API response received successfully. Finish reason: {finish_reason}")

        return response

    except RateLimitError as e:
        logger.error(f"OpenAI API rate limit exceeded: {e}")
        raise OpenAIError(f"API Rate Limit Exceeded: {e.body.get('message', 'Please try again later.')}") from e
    except APIError as e:
        logger.error(f"OpenAI API returned an API Error: {e}")
        raise OpenAIError(f"API Error: {e.body.get('message', 'An unexpected error occurred.')}") from e
    except OpenAIError as e:
        logger.error(f"OpenAI API request failed: {e}")

        error_message = str(e)
        try:

             if hasattr(e, 'response') and e.response and e.response.content:
                  response_data = json.loads(e.response.content.decode('utf-8'))
                  error_message = response_data.get('error', {}).get('message', str(e))
             elif hasattr(e, 'body') and e.body and 'message' in e.body:
                  error_message = e.body['message']
        except (json.JSONDecodeError, AttributeError, TypeError):
             pass
        raise OpenAIError(f"API Request Failed: {error_message}") from e
    except Exception as e:

        logger.error(f"Unexpected error calling OpenAI API: {e}", exc_info=True)
        raise OpenAIError(f"An unexpected error occurred while communicating with the AI model: {str(e)}") from e

def handle_tool_calls(tool_calls):
    
    results = []

    if not isinstance(tool_calls, list):
        logger.error(f"Expected tool_calls to be a list, but got {type(tool_calls)}")
        return results

    for tool_call in tool_calls:
        try:

            if not hasattr(tool_call, 'function') or not hasattr(tool_call.function, 'name') or not hasattr(tool_call.function, 'arguments'):
                 logger.error(f"Skipping invalid tool_call structure: {tool_call}")
                 continue

            function_name = tool_call.function.name
            arguments_json = tool_call.function.arguments

            try:
                arguments = json.loads(arguments_json)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in tool call arguments for {function_name}: {arguments_json}")

                result_content = {"error": f"Invalid arguments format for {function_name}."}
                arguments = None
            except Exception as e:
                 logger.error(f"Unexpected error parsing arguments for {function_name}: {e}")
                 result_content = {"error": f"Error parsing arguments for {function_name}."}
                 arguments = None

            if arguments is not None:

                 from .tools import handle_tool
                 result_content = handle_tool(function_name, arguments)

            results.append({
                "tool_call_id": getattr(tool_call, "id", "unknown"),
                "function_name": function_name,
                "result": result_content
            })

            logger.info(f"Successfully prepared result for tool {function_name}")

        except Exception as e:

            logger.error(f"Error processing tool call {getattr(tool_call, 'function', {}).get('name', 'unknown')}: {e}", exc_info=True)
            results.append({
                "tool_call_id": getattr(tool_call, "id", "unknown"),
                "function_name": getattr(tool_call, "function", {}).get("name", "unknown"),
                "result": {"error": f"Tool execution failed: {str(e)}"}
            })

    return results

def update_sequence(args):
    
    sequence_id = args.get("sequence_id")
    changes = args.get("changes", [])

    success_messages = []

    if isinstance(changes, dict) and "steps" in changes:
        return {
            "sequence_id": sequence_id,
            "status": "updated",
            "message": "Sequence updated with all new content",
            "updated_sequence": changes
        }

    for change in changes:
        if isinstance(change, dict):
            if "step_index" in change and "field" in change:
                step_index = change.get("step_index")
                field = change.get("field")
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

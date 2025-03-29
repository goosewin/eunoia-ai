import logging
import time
import uuid
from typing import Any

logger = logging.getLogger(__name__)

def generate_sequence_tool():
    return {
        "type": "function",
        "function": {
            "name": "generate_sequence",
            "description": "Generate a recruiting outreach sequence based on the role, company, and other parameters. IMPORTANT: When the user requests a specific channel (Email, LinkedIn, Phone, Text), you MUST include that as the preferred_channel parameter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_role": {
                        "type": "string",
                        "description": "The job role being recruited for (e.g., Software Engineer, Product Manager)"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "The name of the company doing the recruiting"
                    },
                    "industry": {
                        "type": "string",
                        "description": "The industry of the role or company (e.g., Technology, Healthcare)"
                    },
                    "num_steps": {
                        "type": "integer",
                        "description": "Number of steps in the sequence (1-5)"
                    },
                    "tone": {
                        "type": "string",
                        "description": "The communication tone (e.g., Professional, Casual, Friendly)"
                    },
                    "value_proposition": {
                        "type": "string",
                        "description": "Key selling points about the role or company"
                    },
                    "preferred_channel": {
                        "type": "string",
                        "description": "IMPORTANT: The preferred communication channel for ALL steps (LinkedIn, Email, Phone, or Text). If user specifies ANY channel preference, this MUST be included."
                    }
                },
                "required": ["target_role"]
            }
        }
    }

def update_sequence_tool():
    return {
        "type": "function",
        "function": {
            "name": "update_sequence",
            "description": "Update an existing recruiting sequence based on user feedback. Use this to modify steps, add new steps, change messages, or adjust channel preferences.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sequence_id": {"type": "string", "description": "The unique identifier of the sequence to update."},
                    "changes": {
                        "type": "array", 
                        "description": "List of changes to apply to the sequence",
                        "items": {
                            "type": "object",
                            "properties": {
                                "step_id": {"type": "string", "description": "ID of the step to modify"},
                                "field": {"type": "string", "description": "Field to update (message, subject, channel, timing, day)"},
                                "value": {"type": "string", "description": "New value for the field"}
                            },
                            "required": ["step_id", "field", "value"]
                        }
                    },
                    "add_step": {
                        "type": "boolean", 
                        "description": "Whether to add a new step to the sequence"
                    },
                    "preferred_channel": {
                        "type": "string", 
                        "description": "If adding a step, the channel to use for the new step"
                    }
                },
                "required": ["sequence_id"]
            }
        }
    }

def research_industry_tool():
    return {
        "type": "function",
        "function": {
            "name": "research_industry",
            "description": "Research information about an industry to enhance recruiting outreach. Provides relevant details about industry trends, skills in demand, and appropriate messaging.",
            "parameters": {
                "type": "object",
                "properties": {
                    "industry": {"type": "string", "description": "The industry to research (e.g., 'Technology', 'Healthcare', 'Finance')"}
                },
                "required": ["industry"]
            }
        }
    }

def generate_sequence(
    target_role: str,
    company_name: str = "Your Company",
    industry: str = "Technology",
    num_steps: int = None,
    tone: str = "Professional",
    value_proposition: str = "",
    preferred_channel: str | None = None
) -> dict[str, Any]:
    
    try:
        if not num_steps or num_steps < 1:
            num_steps = 3
        elif num_steps > 8:
            logger.warning(f"Requested {num_steps} steps, limiting to 8")
            num_steps = 8

        sequence_id = f"seq_{int(time.time())}"
        
        normalized_channel = "Email"
        if preferred_channel:
            if preferred_channel.lower() in ["email", "e-mail", "mail"]:
                normalized_channel = "Email"
            elif preferred_channel.lower() in ["linkedin", "linked in", "li"]:
                normalized_channel = "LinkedIn"
            elif preferred_channel.lower() in ["phone", "call", "telephone"]:
                normalized_channel = "Phone"
            elif preferred_channel.lower() in ["text", "sms", "message"]:
                normalized_channel = "Text"
            else:
                logger.warning(f"Unrecognized channel: {preferred_channel}, defaulting to Email")
        
        if normalized_channel not in ["Email", "LinkedIn", "Phone", "Text"]:
            normalized_channel = "Email"
        
        steps = []
        
        if normalized_channel:
            logger.info(f"Creating sequence with all steps using channel: {normalized_channel}")
            
            for i in range(num_steps):
                step_id = f"step_{uuid.uuid4().hex[:8]}"
                day = i * 3
                
                step = {
                    "id": step_id,
                    "step": i + 1,
                    "day": day,
                    "channel": normalized_channel,
                    "timing": f"Day {day}" + (" - Initial Outreach" if i == 0 else f" - Follow-up {i}")
                }
                
                if normalized_channel == "Email":
                    if i == 0:
                        step["message"] = generate_initial_message(target_role, company_name, industry, tone, value_proposition)
                        step["subject"] = f"Exciting opportunity for {target_role}s at {company_name}"
                        step["timing"] = "Initial Outreach"
                    else:
                        step["message"] = generate_followup_message(target_role, company_name, tone, day)
                        step["subject"] = f"Following up: {target_role} opportunity at {company_name}"
                        step["timing"] = f"Day {day} - Follow-up"
                
                elif normalized_channel == "LinkedIn":
                    if i == 0:
                        step["message"] = generate_linkedin_message(target_role, company_name, tone)
                        step["timing"] = "Initial LinkedIn Connection"
                    else:
                        step["message"] = generate_linkedin_followup(target_role, company_name, tone)
                        step["timing"] = f"Day {day} - LinkedIn Follow-up"
                
                elif normalized_channel == "Phone":
                    step["message"] = f"Call script for {target_role} at {company_name} - Day {day}\n\nHi {{first_name}},\n\nI'm {{recruiter_name}} from {company_name}. I'm reaching out about an exciting {target_role} opportunity. I noticed your background in {industry} and thought you might be a great fit.\n\nIs this a good time to talk about the role?"
                    step["timing"] = f"Day {day} - Phone Call"
                
                elif normalized_channel == "Text":
                    step["message"] = f"Hi {{first_name}}, this is {{recruiter_name}} from {company_name}. I found your profile while looking for experienced {target_role}s. Would you be interested in hearing about an opportunity with us? Let me know when you have a moment to connect."
                    step["timing"] = f"Day {day} - Text Message"
                
                steps.append(step)
        else:
            logger.info("No channel specified, defaulting to Email channel for all steps")
            normalized_channel = "Email"
            
            for i in range(num_steps):
                step_id = f"step_{uuid.uuid4().hex[:8]}"
                day = i * 3
                
                step = {
                    "id": step_id,
                    "step": i + 1,
                    "day": day,
                    "channel": "Email",
                    "timing": f"Day {day}" + (" - Initial Outreach" if i == 0 else f" - Follow-up {i}")
                }
                
                if i == 0:
                    step["message"] = generate_initial_message(target_role, company_name, industry, tone, value_proposition)
                    step["subject"] = f"Exciting opportunity for {target_role}s at {company_name}"
                    step["timing"] = "Initial Outreach"
                else:
                    step["message"] = generate_followup_message(target_role, company_name, tone, day)
                    step["subject"] = f"Following up: {target_role} opportunity at {company_name}"
                    step["timing"] = f"Day {day} - Follow-up"
                
                steps.append(step)

        if normalized_channel and steps:
            step_channels = set(step["channel"] for step in steps)
            if len(step_channels) > 1 or normalized_channel not in step_channels:
                logger.error(f"Channel mismatch in generated steps. Expected all {normalized_channel} but got {step_channels}")

                for step in steps:
                    step["channel"] = normalized_channel

                    if normalized_channel == "LinkedIn" and "subject" in step:
                        del step["subject"]
                    elif normalized_channel == "Email" and "subject" not in step:
                        step["subject"] = f"Regarding {target_role} position at {company_name}"

        sequence = {
            "id": sequence_id,
            "title": f"{normalized_channel} {target_role} Recruitment for {company_name}",
            "target_role": target_role,
            "industry": industry,
            "company": company_name,
            "steps": steps
        }
        
        logger.info(f"Generated sequence with {len(steps)} steps")
        logger.info(f"All steps use channel: {normalized_channel}")

        if preferred_channel and sequence and 'steps' in sequence and sequence['steps']:
            if not isinstance(sequence['steps'], list):
                logger.error(f"Expected steps to be a list, got {type(sequence['steps'])}")
                sequence['steps'] = []

            valid_steps = []
            for i, step in enumerate(sequence['steps']):
                if not isinstance(step, dict):
                    logger.error(f"Expected step to be a dict, got {type(step)}")
                    continue

                if 'id' not in step:
                    step['id'] = f"step_{int(time.time())}_{i}"
                    
                if 'step' not in step:
                    step['step'] = i + 1
                    
                if 'day' not in step:
                    step['day'] = i * 2
                    
                if 'message' not in step or not step['message']:
                    logger.warning(f"Step {i+1} is missing message content")
                    step['message'] = f"[Message content for {preferred_channel} step {i+1}]"

                if 'channel' not in step or step['channel'] != preferred_channel:
                    logger.warning(f"Step {i+1} has incorrect channel: {step.get('channel', 'None')}, fixing to {preferred_channel}")
                    step['channel'] = preferred_channel

                if preferred_channel == 'Email' and ('subject' not in step or not step['subject']):
                    step['subject'] = f"Follow-up {i+1}"
                    logger.info(f"Added missing subject for Email step {i+1}")

                if 'timing' not in step or not step['timing']:
                    day_value = step.get('day', i * 2)
                    step['timing'] = f"Day {day_value}"
                    
                valid_steps.append(step)

            sequence['steps'] = valid_steps
            
            logger.info(f"Validated and fixed sequence with {len(valid_steps)} steps using {preferred_channel} channel")

        return sequence
        
    except Exception as e:
        logger.error(f"Error generating sequence: {str(e)}", exc_info=True)

        return {
            "id": f"seq_{uuid.uuid4().hex[:8]}",
            "title": f"{target_role} Recruitment Sequence",
            "target_role": target_role,
            "industry": industry or "Technology",
            "company": company_name,
            "steps": [
                {
                    "id": f"step_{uuid.uuid4().hex[:8]}",
                    "step": 1,
                    "day": 0,
                    "channel": "Email",
                    "subject": f"Opportunity for {target_role} at {company_name}",
                    "message": f"Hi {{first_name}},\n\nI'm {{recruiter_name}} from {company_name}, and I'm reaching out about an exciting opportunity for a {target_role} position.\n\nWould you be interested in learning more?\n\nBest regards,\n{{recruiter_name}}",
                    "timing": "Initial Outreach"
                }
            ]
        }

def handle_update_sequence(arguments: dict[str, Any]) -> dict[str, Any]:
    
    try:
        logger.info(f"Updating sequence with arguments: {arguments}")
        sequence_id = arguments.get("sequence_id")
        changes = arguments.get("changes", [])
        add_step = arguments.get("add_step", False)
        preferred_channel = arguments.get("preferred_channel")
        
        if not sequence_id:
            logger.error("No sequence_id provided for update")
            return {"error": "No sequence_id provided"}

        from api.db import SessionLocal
        from api.models import Sequence
        
        db = SessionLocal()
        try:

            db_sequence = db.query(Sequence).filter(Sequence.id == int(sequence_id)).first()
            
            if not db_sequence:
                logger.error(f"Sequence {sequence_id} not found")
                return {"error": f"Sequence {sequence_id} not found"}

            sequence_data = db_sequence.sequence_data

            sequence_data["id"] = db_sequence.id

            if changes:
                if isinstance(changes, dict) and "steps" in changes:

                    logger.info("Received full sequence replacement")

                    changes["id"] = db_sequence.id

                    for key, value in changes.items():
                        if key != "id":
                            sequence_data[key] = value

                    if "steps" in changes and isinstance(changes["steps"], list):
                        for i, step in enumerate(changes["steps"]):

                            if "id" not in step:
                                step["id"] = f"step_{int(time.time())}_{i}"

                            step["step"] = i + 1

                            if preferred_channel and step.get("channel") != preferred_channel:
                                logger.warning(f"Fixing step {i+1} channel from {step.get('channel')} to {preferred_channel}")
                                step["channel"] = preferred_channel

                            if step.get("channel") == "Email" and not step.get("subject"):
                                step["subject"] = f"Follow-up {i+1}"
                else:

                    for change in changes:
                        step_id = change.get("step_id")
                        field = change.get("field")
                        value = change.get("value")
                        
                        if not step_id or not field:
                            continue

                        for step in sequence_data["steps"]:
                            if step["id"] == step_id:

                                step[field] = value
                                logger.info(f"Updated step {step_id}, field {field} to value {value}")
                                break

            if add_step:

                if "steps" not in sequence_data or not isinstance(sequence_data["steps"], list):
                    sequence_data["steps"] = []

                new_step_number = len(sequence_data["steps"]) + 1
                last_step_day = sequence_data["steps"][-1]["day"] if sequence_data["steps"] else 0
                new_day = last_step_day + 3

                channel = preferred_channel or "Email"
                subject = f"Follow-up {new_step_number}: {sequence_data.get('target_role', 'Role')} at {sequence_data.get('company', 'Company')}"

                if channel.lower() == "linkedin":
                    message = generate_linkedin_followup(
                        sequence_data.get("target_role", "candidate"), 
                        sequence_data.get("company", "Your Company"), 
                        "Professional"
                    )
                else:
                    message = generate_followup_message(
                        sequence_data.get("target_role", "candidate"), 
                        sequence_data.get("company", "Your Company"), 
                        "Professional", 
                        new_day
                    )

                new_step = {
                    "id": f"step_{int(time.time())}_{new_step_number}",
                    "step": new_step_number,
                    "day": new_day,
                    "channel": channel,
                    "subject": subject,
                    "message": message,
                    "timing": f"Day {new_day} - Follow-up"
                }

                sequence_data["steps"].append(new_step)
                logger.info(f"Added new step {new_step['id']} to sequence {sequence_id}")

            db_sequence.sequence_data = sequence_data
            db.commit()
            logger.info(f"Sequence {sequence_id} updated in database")
            
            return sequence_data
            
        except Exception as e:
            logger.error(f"Error updating sequence: {e}", exc_info=True)
            db.rollback()
            return {"error": f"Failed to update sequence: {str(e)}"}
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error handling update_sequence: {e}", exc_info=True)
        return {"error": f"Failed to handle update_sequence: {str(e)}"}

def handle_research_industry(arguments: dict[str, Any]) -> dict[str, Any]:
    
    try:
        industry = arguments.get("industry", "").strip()
        
        if not industry:
            return {
                "error": "No industry specified",
                "message": "Please specify an industry to research."
            }
        
        logger.info(f"Researching industry: {industry}")

        industry_data = {
            "technology": {
                "trends": [
                    "Remote and hybrid work models are now standard",
                    "Artificial Intelligence and Machine Learning roles in high demand",
                    "Cybersecurity professionals facing talent shortage",
                    "Cloud engineering and DevOps skills highly sought after",
                    "Increasing focus on diverse hiring practices"
                ],
                "key_skills": [
                    "Cloud platforms (AWS, Azure, GCP)",
                    "Programming languages (Python, JavaScript, Rust)",
                    "AI/ML frameworks",
                    "DevOps and CI/CD",
                    "Cybersecurity expertise"
                ],
                "effective_channels": [
                    "LinkedIn for professional networking",
                    "GitHub for code-focused outreach",
                    "Tech conferences and meetups",
                    "Developer communities and forums"
                ],
                "messaging_tips": [
                    "Focus on technical challenges and interesting problems",
                    "Highlight engineering culture and team dynamics",
                    "Mention specific technologies used in the role",
                    "Address work-life balance and remote options",
                    "Include opportunities for growth and learning"
                ]
            },
            "healthcare": {
                "trends": [
                    "Telehealth expansion creating new technical roles",
                    "Increasing use of AI in diagnostics and patient care",
                    "Data privacy and HIPAA compliance specialists needed",
                    "Focus on patient experience and care coordination",
                    "Aging population driving demand for specialized care"
                ],
                "key_skills": [
                    "Electronic Health Records (EHR) experience",
                    "Healthcare data analytics",
                    "Regulatory compliance knowledge",
                    "Patient care coordination",
                    "Medical terminology"
                ],
                "effective_channels": [
                    "Professional healthcare networks",
                    "Medical conferences and events",
                    "Healthcare-specific job boards",
                    "LinkedIn for professional networking"
                ],
                "messaging_tips": [
                    "Emphasize mission and impact on patient care",
                    "Highlight stability and growth in the healthcare sector",
                    "Address work-life balance for clinical roles",
                    "Mention continuing education opportunities",
                    "Discuss team culture and interdisciplinary collaboration"
                ]
            },
            "finance": {
                "trends": [
                    "FinTech disruption creating new roles and skill needs",
                    "Increasing focus on data analytics and business intelligence",
                    "Regulatory compliance specialists in high demand",
                    "Remote and hybrid work models becoming more common",
                    "Greater emphasis on diversity in financial services"
                ],
                "key_skills": [
                    "Financial analysis and modeling",
                    "Risk assessment and management",
                    "Regulatory compliance knowledge",
                    "Data analysis and visualization",
                    "Programming skills for quantitative finance"
                ],
                "effective_channels": [
                    "LinkedIn for professional networking",
                    "Financial industry conferences",
                    "Alumni networks from business schools",
                    "Professional finance associations"
                ],
                "messaging_tips": [
                    "Emphasize stability and career progression",
                    "Highlight company reputation and market position",
                    "Address work-life balance concerns",
                    "Mention compensation and benefits package",
                    "Discuss team culture and mentorship opportunities"
                ]
            }
        }

        normalized_industry = industry.lower().strip()

        if normalized_industry not in industry_data:

            normalized_industry = "technology"
            for key in industry_data.keys():
                if normalized_industry in key or key in normalized_industry:
                    normalized_industry = key
                    break

        industry_info = industry_data.get(normalized_industry, industry_data["technology"])

        response = {
            "industry": industry,
            "normalized_industry": normalized_industry,
            "trends": industry_info["trends"],
            "key_skills": industry_info["key_skills"],
            "effective_channels": industry_info["effective_channels"],
            "messaging_tips": industry_info["messaging_tips"],
            "summary": f"The {industry} industry is evolving with several key trends including {', '.join(industry_info['trends'][:2])}. When recruiting for this industry, focus on candidates with skills in {', '.join(industry_info['key_skills'][:3])}. The most effective outreach channels are {', '.join(industry_info['effective_channels'][:2])}."
        }
        
        logger.info(f"Research completed for industry: {industry}")
        return response
        
    except Exception as e:
        logger.error(f"Error researching industry: {e}", exc_info=True)
        return {
            "error": str(e),
            "industry": arguments.get("industry", "unknown"),
            "message": "Failed to research industry information. Please try a different industry or check your query."
        }

def generate_initial_message(target_role, company_name, industry, tone, value_proposition):
    
    if not value_proposition:
        value_proposition = "join our growing team in a collaborative environment with competitive compensation and opportunities for professional growth"
    
    message = f"""Hi {{first_name}},

I hope this message finds you well. I'm {{recruiter_name}} from {company_name}, and I'm reaching out because we're looking for a talented {target_role} to {value_proposition}.

Based on your experience in {industry}, I believe you could be a great fit for this role. Would you be interested in learning more about this opportunity?

I'd be happy to share more details about the role, our company culture, and the exciting projects you'd be working on.

Best regards,
{{recruiter_name}}
{company_name}
"""
    
    return message

def generate_followup_message(target_role, company_name, tone, day):
    
    message = f"""Hi {{first_name}},

I wanted to follow up on my previous message about the {target_role} position at {company_name}. 

I'm still interested in connecting with you about this opportunity. If you have any questions or would like to discuss the role further, please don't hesitate to reach out.

Looking forward to hearing from you!

Best regards,
{{recruiter_name}}
{company_name}
"""
    
    return message

def generate_linkedin_message(target_role, company_name, tone):
    
    message = f"""Hi {{first_name}},

I noticed your profile and was impressed by your background. I'm a recruiter at {company_name}, and we're looking for a {target_role}. Would you be open to discussing this opportunity?

Best,
{{recruiter_name}}
"""
    
    return message

def generate_final_email(target_role, company_name, tone):
    
    message = f"""Hi {{first_name}},

I've reached out a couple of times regarding the {target_role} position at {company_name}. 

If you're interested in this opportunity, please let me know. If I don't hear back, I'll assume you're not interested at this time, but I'd be happy to keep you in mind for future roles that might be a better fit.

Best regards,
{{recruiter_name}}
{company_name}
"""
    
    return message

def generate_linkedin_followup(target_role, company_name, tone):
    
    message = f"""Hi {{first_name}},

Just following up on my previous message about the {target_role} role at {company_name}. I'd love to tell you more about this opportunity if you're interested. Let me know if you'd like to connect!

Best,
{{recruiter_name}}
"""
    
    return message

def generate_linkedin_inmail(target_role, company_name, tone):
    
    message = f"""Hi {{first_name}},

I came across your profile and wanted to reach out about a {target_role} opportunity with {company_name}. Your experience caught my attention, and I believe you could be a great fit for our team. 

Would you be interested in a brief conversation about the role? I'm happy to share more details.

Best regards,
{{recruiter_name}}
"""
    
    return message

def handle_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:

    logger.info(f"Handling tool call: {tool_name} with arguments: {arguments}")
    
    try:
        if tool_name == "generate_sequence":
            target_role = arguments.get("target_role")
            company_name = arguments.get("company_name", "Your Company")
            industry = arguments.get("industry", "Technology")
            num_steps = arguments.get("num_steps", None)
            tone = arguments.get("tone", "Professional")
            value_proposition = arguments.get("value_proposition", "")
            preferred_channel = arguments.get("preferred_channel", None)

            if preferred_channel:
                logger.info(f"Tool call includes preferred_channel: {preferred_channel}")

                channel_mapping = {
                    "linkedin": "LinkedIn",
                    "linked in": "LinkedIn", 
                    "linked-in": "LinkedIn",
                    "email": "Email",
                    "mail": "Email",
                    "e-mail": "Email",
                    "phone": "Phone",
                    "call": "Phone",
                    "calling": "Phone",
                    "text": "Text",
                    "sms": "Text",
                    "text message": "Text"
                }
                
                preferred_channel_lower = preferred_channel.lower()
                for key, value in channel_mapping.items():
                    if key in preferred_channel_lower:
                        preferred_channel = value
                        logger.info(f"Normalized channel to: {preferred_channel}")
                        break

                valid_channels = ["LinkedIn", "Email", "Phone", "Text"]
                if preferred_channel not in valid_channels:
                    logger.warning(f"Unsupported channel: {preferred_channel}, defaulting to Email")
                    preferred_channel = "Email"

            sequence = generate_sequence(
                target_role=target_role,
                company_name=company_name,
                industry=industry,
                num_steps=num_steps,
                tone=tone,
                value_proposition=value_proposition,
                preferred_channel=preferred_channel
            )

            if preferred_channel and sequence and 'steps' in sequence and sequence['steps']:
                channel_mismatch = False
                for step in sequence['steps']:
                    if step.get('channel') != preferred_channel:
                        channel_mismatch = True
                        logger.warning(f"Step channel mismatch: requested {preferred_channel}, got {step.get('channel')}")

                        step['channel'] = preferred_channel
                
                if channel_mismatch:
                    logger.info(f"Fixed channel mismatches to ensure all steps use {preferred_channel}")
            
            return sequence
            
        elif tool_name == "update_sequence":
            return handle_update_sequence(arguments)
            
        elif tool_name == "research_industry":
            return handle_research_industry(arguments)
            
        else:
            return {"error": f"Unknown tool: {tool_name}"}
            
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
        return {"error": str(e)}

def get_tools():
    
    return [
        generate_sequence_tool(),
        update_sequence_tool(),
        research_industry_tool()
    ]

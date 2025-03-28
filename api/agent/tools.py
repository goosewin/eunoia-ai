import json
import logging
import random
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

def generate_sequence_tool():
    return {
        "type": "function",
        "function": {
            "name": "generate_sequence",
            "description": "Generate a recruiting or sales outreach sequence",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "target_role": {"type": "string"},
                    "industry": {"type": "string"},
                    "num_steps": {"type": "integer"},
                    "tone": {"type": "string"},
                    "value_proposition": {"type": "string"}
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
            "description": "Update an existing sequence",
            "parameters": {
                "type": "object",
                "properties": {
                    "sequence_id": {"type": "string"},
                    "changes": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["sequence_id", "changes"]
            }
        }
    }

def research_industry_tool():
    return {
        "type": "function",
        "function": {
            "name": "research_industry",
            "description": "Research information about industry",
            "parameters": {
                "type": "object",
                "properties": {
                    "industry": {"type": "string"}
                },
                "required": ["industry"]
            }
        }
    }

def generate_sequence(
    company_name: str,
    target_role: str,
    industry: str = "Technology",
    num_steps: int = 3,
    tone: str = "Professional",
    value_proposition: str = ""
) -> Dict[str, Any]:
    """Generate a recruiting outreach sequence"""
    try:
        import logging
        import uuid
        from datetime import datetime
        
        logger = logging.getLogger(__name__)
        logger.info(f"Generating sequence for {target_role} in {industry} industry")
        
        # Default days for each step if none provided
        step_days = [0, 3, 7, 14, 21]
        
        sequence_id = f"seq_{uuid.uuid4().hex[:8]}"
        
        # Generate steps based on requested number
        steps = []
        sequence_title = f"{target_role} Recruitment for {company_name}"
        
        # Ensure num_steps is valid
        if not isinstance(num_steps, int) or num_steps < 1:
            num_steps = 3
        
        # Limit to reasonable number
        num_steps = min(num_steps, 5)
        
        # Generate step data
        for i in range(num_steps):
            step_id = f"step_{uuid.uuid4().hex[:8]}"
            day = step_days[i] if i < len(step_days) else step_days[-1] + (i - len(step_days) + 1) * 7
            
            # First contact is always email
            if i == 0:
                channel = "Email"
                subject = f"Exciting opportunity for {target_role}s at {company_name}"
                message = generate_initial_message(target_role, company_name, industry, tone, value_proposition)
                timing = "Initial Outreach"
            # Second contact is usually a follow-up email
            elif i == 1:
                channel = "Email" 
                subject = f"Following up: {target_role} opportunity at {company_name}"
                message = generate_followup_message(target_role, company_name, tone, day)
                timing = f"Day {day} - Follow-up"
            # Third contact might be LinkedIn
            elif i == 2:
                channel = "LinkedIn"
                subject = f"Opportunity at {company_name}" 
                message = generate_linkedin_message(target_role, company_name, tone)
                timing = f"Day {day} - LinkedIn connection"
            # Fourth could be another email
            elif i == 3:
                channel = "Email"
                subject = f"One more thing about {company_name}"
                message = generate_final_email(target_role, company_name, tone)
                timing = f"Day {day} - Final attempt"
            # Fifth could be a phone call script
            else:
                channel = "Phone"
                subject = f"Call about {company_name} opportunity"
                message = generate_phone_script(target_role, company_name, tone)
                timing = f"Day {day} - Phone call"
            
            step = {
                "id": step_id,
                "step": i + 1,
                "day": day,
                "channel": channel,
                "message": message,
                "timing": timing,
                "subject": subject  # Always include subject for all steps
            }
                
            steps.append(step)
            
        logger.info(f"Generated sequence with {len(steps)} steps")
        
        # Format the output
        sequence_data = {
            "id": sequence_id,
            "title": sequence_title,
            "target_role": target_role,
            "industry": industry,
            "company": company_name,
            "steps": steps
        }
        
        # Validate steps before returning
        if not steps or len(steps) == 0:
            logger.warning("No steps generated, creating a default step")
            sequence_data["steps"] = [{
                "id": f"step_{uuid.uuid4().hex[:8]}",
                "step": 1,
                "day": 0,
                "channel": "Email",
                "subject": f"Opportunity for {target_role}s at {company_name}",
                "message": f"Hi [Name],\n\nI hope this message finds you well! I'm reaching out because we're looking for talented {target_role}s to join our team at {company_name}.\n\nWould you be open to discussing this opportunity?\n\nBest regards,\n[Your Name]",
                "timing": "Initial Outreach"
            }]
        
        return sequence_data
        
    except Exception as e:
        import logging
        logging.error(f"Error generating sequence: {str(e)}", exc_info=True)
        return {
            "id": "error_sequence",
            "title": f"Error: {str(e)}",
            "target_role": target_role, 
            "industry": industry,
            "company": company_name,
            "steps": [{
                "id": "error_step",
                "step": 1,
                "day": 0,
                "channel": "Email",
                "subject": "Error generating sequence",
                "message": f"There was an error generating the sequence: {str(e)}. Please try again with different parameters.",
                "timing": "Error"
            }]
        }

def create_recruiting_email_templates(company_name, target_role, industry, value_proposition):
    """Create email templates for recruiting sequences"""
    return {
        1: {
            "subject": f"Opportunity for experienced {target_role} at {company_name}",
            "message": f"""Hi {{first_name}},

I'm {{recruiter_name}} from {company_name}, and I came across your profile. Your experience in {industry} caught my attention, particularly your background in {{relevant_skill}}.

We're looking for a {target_role} to join our team{' and ' + value_proposition if value_proposition else ''}. 

Would you be open to a quick chat about this opportunity? I'd be happy to share more details about the role and answer any questions.

Best regards,
{{recruiter_name}}
{company_name}
"""
        },
        2: {
            "subject": f"Following up: {target_role} at {company_name}",
            "message": f"""Hi {{first_name}},

I wanted to follow up on my previous message about the {target_role} position at {company_name}.

Some highlights about the role:
- {value_proposition if value_proposition else 'Competitive compensation and benefits'}
- Collaborative team environment with growth opportunities
- Chance to work on cutting-edge projects in {industry}

I'd love to discuss this opportunity with you. Are you available for a quick 15-minute call this week?

Looking forward to connecting,
{{recruiter_name}}
{company_name}
"""
        },
        3: {
            "subject": f"One more note about {company_name} opportunity",
            "message": f"""Hi {{first_name}},

I hope you're doing well. I'm reaching out one more time about the {target_role} position at {company_name}.

We're looking to fill this role soon, and based on your experience, I think you'd be a great fit. I'd be happy to share more details about the team and projects you'd be working on.

If you're interested, please let me know a convenient time to connect this week.

Best regards,
{{recruiter_name}}
{company_name}
"""
        }
    }

def create_recruiting_linkedin_templates(company_name, target_role, industry, value_proposition):
    """Create LinkedIn templates for recruiting sequences"""
    return {
        1: {
            "message": f"""Hi {{first_name}},

I'm {{recruiter_name}} from {company_name}. I noticed your experience in {industry} and thought you might be interested in our {target_role} position.

{value_proposition if value_proposition else 'We offer a competitive package and great growth opportunities.'}

Would you be open to learning more about this role?

Best,
{{recruiter_name}}
"""
        },
        2: {
            "message": f"""Hi {{first_name}},

Just following up on my previous message about the {target_role} role at {company_name}.

We're building an exceptional team, and your background would be valuable to us. I'd love to share more details if you're interested.

{{recruiter_name}}
"""
        }
    }

def create_sales_email_templates(company_name, target_role, industry, value_proposition):
    """Create email templates for sales sequences"""
    target_audience = target_role if target_role else "valued customer"
    vp = value_proposition if value_proposition else f"help you achieve better results in {industry}"
    
    return {
        1: {
            "subject": f"Help for {target_audience} with {company_name}",
            "message": f"""Hi {{first_name}},

I'm {{sender_name}} from {company_name}. I work with {target_audience}s like yourself who are looking to {vp}.

Our clients in {industry} have seen significant improvements in their results by working with us. For example, [Brief Success Story].

I'd love to share how we might be able to help you too. Would you be open to a quick 15-minute call this week?

Best regards,
{{sender_name}}
{company_name}
"""
        },
        2: {
            "subject": f"Following up: {company_name} solutions for {target_audience}s",
            "message": f"""Hi {{first_name}},

I wanted to follow up on my previous message about how {company_name} has been helping {target_audience}s like you.

A few key benefits our clients enjoy:
- {vp}
- Simplified processes saving time and resources
- Dedicated support from industry experts

Would Tuesday or Thursday this week work for a brief call to discuss your specific needs?

Best regards,
{{sender_name}}
{company_name}
"""
        },
        3: {
            "subject": f"Quick question about your {industry} goals",
            "message": f"""Hi {{first_name}},

I hope you're doing well. I'm reaching out one more time because I believe we can really help you as a {target_audience}.

Many in your position are facing [common challenge]. Is this something you're dealing with too?

If so, I'd be happy to share some insights on how we've helped others overcome this. Just let me know a good time to connect.

Best regards,
{{sender_name}}
{company_name}
"""
        }
    }

def create_sales_linkedin_templates(company_name, target_role, industry, value_proposition):
    """Create LinkedIn templates for sales sequences"""
    target_audience = target_role if target_role else "business professional" 
    vp = value_proposition if value_proposition else f"help you achieve better results in {industry}"
    
    return {
        1: {
            "message": f"""Hi {{first_name}},

I'm {{sender_name}} from {company_name} and I work with {target_audience}s to {vp}.

I noticed your profile and thought you might benefit from our approach. Would you be open to a quick conversation?

Best,
{{sender_name}}
"""
        },
        2: {
            "message": f"""Hi {{first_name}},

Just following up on my previous message about how we're helping {target_audience}s like you in {industry}.

I'd love to learn about your current challenges and see if we might be able to help. Are you available for a quick chat this week?

{{sender_name}}
{company_name}
"""
        }
    }

def create_aid_email_templates(company_name, target_role, industry, value_proposition):
    """Create email templates for aid/support sequences"""
    target_audience = target_role if target_role else "community member"
    vp = value_proposition if value_proposition else "access essential support and resources"
    
    return {
        1: {
            "subject": f"Support available for {target_audience}s through {company_name}",
            "message": f"""Hi {{first_name}},

I'm {{sender_name}} from {company_name}. I'm reaching out because we're providing assistance to {target_audience}s who may be eligible for our support program.

We understand this may be a challenging time, and we're here to help you {vp}.

Would you be interested in learning more about the resources and support available to you? I'm happy to answer any questions you might have.

Warm regards,
{{sender_name}}
{company_name}
"""
        },
        2: {
            "subject": f"Following up: Resources available through {company_name}",
            "message": f"""Hi {{first_name}},

I wanted to follow up on my previous message about the support available for {target_audience}s through {company_name}.

Our program offers:
- {vp}
- Simplified application process
- Dedicated support throughout the process

Are you available for a quick call this week to discuss how we can help?

Warm regards,
{{sender_name}}
{company_name}
"""
        },
        3: {
            "subject": f"Important information about available assistance",
            "message": f"""Hi {{first_name}},

I hope you're doing well. I'm reaching out one more time regarding the support program for {target_audience}s through {company_name}.

Many people aren't aware of all the resources available to them. We'd like to make sure you have all the information you need to access any assistance you may be eligible for.

If you're interested, please let me know a convenient time to connect this week.

Warm regards,
{{sender_name}}
{company_name}
"""
        }
    }

def create_aid_linkedin_templates(company_name, target_role, industry, value_proposition):
    """Create LinkedIn templates for aid/support sequences"""
    target_audience = target_role if target_role else "community member"
    vp = value_proposition if value_proposition else "access essential support and resources"
    
    return {
        1: {
            "message": f"""Hi {{first_name}},

I'm {{sender_name}} from {company_name}. We're currently connecting with {target_audience}s to provide information about our support program that helps you {vp}.

Would you be interested in learning more about the assistance available to you?

Warm regards,
{{sender_name}}
"""
        },
        2: {
            "message": f"""Hi {{first_name}},

Just following up on my previous message about the support program we offer for {target_audience}s like you.

Many people find this program helpful during challenging times. I'd be happy to provide more information if you're interested.

{{sender_name}}
{company_name}
"""
        }
    }

def handle_update_sequence(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing sequence with the specified changes"""
    logger.info(f"Updating sequence with arguments: {arguments}")
    
    sequence_id = arguments.get("sequence_id", "")
    changes = arguments.get("changes", [])
    
    # In a real app, this would fetch and update a sequence in the database
    return {
        "success": True,
        "sequence_id": sequence_id,
        "message": f"Updated sequence {sequence_id} with {len(changes)} changes"
    }

def handle_research_industry(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Perform research about an industry"""
    logger.info(f"Researching industry with arguments: {arguments}")
    
    industry = arguments.get("industry", "")
    
    # Enhanced industry information
    industry_info = {
        "Technology": {
            "growth_rate": "14% annually",
            "key_trends": [
                "AI and machine learning integration in business processes",
                "Cloud computing and serverless architectures",
                "Cybersecurity and zero-trust security models",
                "Remote work technology and digital collaboration tools"
            ],
            "top_companies": ["Google", "Microsoft", "Apple", "Amazon", "Meta"],
            "recruiting_challenges": [
                "High competition for skilled talent",
                "Rapidly evolving skill requirements",
                "High salary expectations",
                "Work-life balance expectations"
            ],
            "candidate_priorities": [
                "Interesting technical challenges",
                "Remote/flexible work options",
                "Growth and learning opportunities",
                "Competitive compensation and equity"
            ],
            "effective_outreach_strategies": [
                "Emphasize technical challenges and impact",
                "Highlight team culture and engineering practices",
                "Be transparent about tech stack and development processes",
                "Showcase learning and growth opportunities"
            ]
        },
        "Healthcare": {
            "growth_rate": "8% annually",
            "key_trends": [
                "Telehealth and remote patient monitoring",
                "AI in diagnostics and predictive healthcare",
                "Electronic health records and interoperability",
                "Personalized medicine and genomics"
            ],
            "top_companies": ["UnitedHealth Group", "CVS Health", "Johnson & Johnson", "Pfizer", "Roche"],
            "recruiting_challenges": [
                "Specialized certifications and credentials",
                "Regulatory knowledge requirements",
                "High pressure environments",
                "24/7 operation requirements for some roles"
            ],
            "candidate_priorities": [
                "Mission and impact on patient care",
                "Work-life balance",
                "Job stability",
                "Advanced technology and resources"
            ],
            "effective_outreach_strategies": [
                "Emphasize mission and patient impact",
                "Highlight stability and professional development",
                "Detail specific practice areas or specialties",
                "Showcase innovative approaches to care"
            ]
        },
        "Finance": {
            "growth_rate": "5% annually",
            "key_trends": [
                "Digital banking and fintech integration",
                "Blockchain and cryptocurrency adoption",
                "Algorithmic trading and automation",
                "ESG (Environmental, Social, Governance) investing"
            ],
            "top_companies": ["JPMorgan Chase", "Bank of America", "Wells Fargo", "Goldman Sachs", "BlackRock"],
            "recruiting_challenges": [
                "Regulatory compliance knowledge",
                "Balance of technical and financial expertise",
                "Competition with fintech startups",
                "Image and reputation management"
            ],
            "candidate_priorities": [
                "Compensation and bonus structure",
                "Career advancement opportunities",
                "Prestige and reputation",
                "Technology adoption and innovation"
            ],
            "effective_outreach_strategies": [
                "Be specific about compensation structure",
                "Highlight career trajectory and advancement",
                "Emphasize stability with innovation",
                "Detail specific projects or clients when possible"
            ]
        },
        "Manufacturing": {
            "growth_rate": "3% annually",
            "key_trends": [
                "Industry 4.0 and smart factories",
                "IoT and connected devices",
                "Sustainable manufacturing practices",
                "Reshoring and supply chain resilience"
            ],
            "top_companies": ["GE", "Siemens", "Toyota", "Volkswagen", "3M"],
            "recruiting_challenges": [
                "Skills gap in advanced manufacturing",
                "Negative perceptions of factory work",
                "Geographic constraints for physical locations",
                "Competition with higher-paying sectors"
            ],
            "candidate_priorities": [
                "Job security and stability",
                "Safety and work environment",
                "Training and skills development",
                "Company longevity and financial health"
            ],
            "effective_outreach_strategies": [
                "Highlight modern technology and innovation",
                "Emphasize training and development programs",
                "Focus on stability and growth opportunities",
                "Showcase sustainability initiatives"
            ]
        }
    }
    
    # If industry isn't in our database, provide a generic response
    result = industry_info.get(industry, {
        "growth_rate": "Varies by region and segment",
        "key_trends": ["Research needed for specific trends"],
        "top_companies": ["Research needed for specific companies"],
        "recruiting_challenges": ["Varies by specific industry segment"],
        "candidate_priorities": ["Further research required"],
        "effective_outreach_strategies": ["Customize based on target role and company"]
    })
    
    result["industry"] = industry
    return result

def handle_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a tool call from the LLM
    
    Args:
        tool_name: The name of the tool to call
        arguments: The arguments to pass to the tool
        
    Returns:
        The result of the tool call
    """
    logger.info(f"Handling tool call: {tool_name} with arguments: {arguments}")
    
    try:
        if tool_name == "generate_sequence":
            # Extract arguments with defaults if not provided
            company_name = arguments.get("company_name", "Your Company")
            target_role = arguments.get("target_role", "Software Developer")
            industry = arguments.get("industry", "Technology")
            num_steps = arguments.get("num_steps", 3)
            tone = arguments.get("tone", "Professional")
            value_proposition = arguments.get("value_proposition", "")
            
            # Generate sequence
            logger.info(f"Generating sequence for {target_role} in {industry} industry")
            sequence_data = generate_sequence(
                company_name=company_name,
                target_role=target_role,
                industry=industry,
                num_steps=min(num_steps, 5) if isinstance(num_steps, int) else 3,  # Limit to 5 steps max
                tone=tone,
                value_proposition=value_proposition
            )
            
            # Ensure the sequence has all required fields
            if not sequence_data.get("steps") or not isinstance(sequence_data.get("steps"), list):
                logger.warning("Generated sequence missing steps array, creating default")
                sequence_data["steps"] = []
                
                # Add at least one default step
                if len(sequence_data["steps"]) == 0:
                    sequence_data["steps"].append({
                        "id": f"step_{int(time.time())}",
                        "step": 1,
                        "day": 0,
                        "channel": "LinkedIn",
                        "subject": "Exciting opportunity",
                        "message": f"Hi [Name],\n\nI hope this message finds you well! I'm reaching out because we're looking for a talented {target_role} to join our team at {company_name}. Based on your profile, I think you'd be a great fit.\n\nWould you be open to discussing this opportunity?\n\nBest regards,\n[Your Name]",
                        "timing": "Initial Outreach"
                    })
            
            # Verify we have at least one step with required fields
            for i, step in enumerate(sequence_data["steps"]):
                # Ensure step has an ID
                if "id" not in step or not step["id"]:
                    step["id"] = f"step_{int(time.time())}_{i+1}"
                
                # Ensure step has required fields
                if "step" not in step:
                    step["step"] = i + 1
                if "day" not in step:
                    step["day"] = i * 3  # Default: each step 3 days apart
                if "channel" not in step:
                    step["channel"] = "Email" if i % 2 == 0 else "LinkedIn"
                if "message" not in step:
                    step["message"] = "Enter your message here..."
                if "timing" not in step:
                    step["timing"] = f"Day {step.get('day', i*3)}"
                if "subject" not in step and step.get("channel") == "Email":
                    step["subject"] = f"Follow up {i+1}"
            
            logger.info(f"Returning sequence with {len(sequence_data['steps'])} steps")
            return sequence_data
            
        elif tool_name == "update_sequence":
            return handle_update_sequence(arguments)
            
        elif tool_name == "research_industry":
            return handle_research_industry(arguments)
            
        else:
            logger.warning(f"Unknown tool: {tool_name}")
            return {"error": f"Unknown tool: {tool_name}"}
            
    except Exception as e:
        logger.error(f"Error handling tool {tool_name}: {str(e)}", exc_info=True)
        return {"error": f"Error processing {tool_name}: {str(e)}"}

def get_tools():
    """Return all available tools for the agent"""
    return [
        generate_sequence_tool(),
        update_sequence_tool(),
        research_industry_tool()
    ]

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
    elif "LA" in last_message or "california" in last_message.lower() or "cali" in last_message.lower():
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
            "value_proposition": value_proposition
        })
    elif tool_name == "research_industry":
        args = json.dumps({
            "industry": industry or "technology"
        })
    else:
        args = json.dumps({})

    # Simulate a delay for a more realistic experience
    time.sleep(1)
    
    # Return the generated sequence
    return {
        "id": "seq_" + str(int(time.time())),
        "title": f"{target_role} {'Sales' if 'sales' in target_role.lower() else 'Recruiting'} Sequence",
        "target_role": target_role,
        "industry": industry,
        "steps": [
            {
                "id": 1,
                "type": "email",
                "subject": f"How {company_name} can help you {value_proposition or 'today'}",
                "body": f"""Hi {{first_name}},

I'm reaching out from {company_name} because we specialize in helping {target_role} in the {industry} sector {value_proposition or 'achieve better results'}.

{value_proposition and f"Given the recent developments in your area, our {value_proposition} program could be particularly valuable to you right now." or ""}

Do you have 15 minutes this week to discuss how we might be able to help?

Best,
{{sender_name}}
{company_name}
                """,
                "timing": "Day 1"
            },
            {
                "id": 2,
                "type": "linkedin",
                "subject": "Connection Request",
                "body": f"""I'm from {company_name} and we help {target_role} {value_proposition or 'succeed'}. I'd love to connect and share some insights about how we've helped others like you.""",
                "timing": "Day 3"
            },
            {
                "id": 3,
                "type": "email",
                "subject": f"Following up: {company_name} {value_proposition or 'solutions'}",
                "body": f"""Hi {{first_name}},

I wanted to follow up on my previous email about how {company_name} has been helping {target_role} in {industry}.

{value_proposition and f"Our {value_proposition} program has already helped many individuals in your situation." or ""}

I'd be happy to share specific examples of how we've helped others in similar situations.

Let me know if you'd like to schedule a brief call.

Best regards,
{{sender_name}}
{company_name}
                """,
                "timing": "Day 5"
            },
            {
                "id": 4,
                "type": "email",
                "subject": "One last thing...",
                "body": f"""Hi {{first_name}},

I understand you're busy, so this will be my last outreach for now.

If you're interested in learning how {company_name} can help you {value_proposition or 'achieve better results'}, here's a link to our calendar: [CALENDAR_LINK]

Feel free to reach out anytime.

Best,
{{sender_name}}
{company_name}
                """,
                "timing": "Day 9"
            }
        ]
    }

def generate_initial_message(target_role, company_name, industry, tone, value_proposition):
    """Generate the initial outreach message"""
    message = f"""Hi {{first_name}},

I'm {{recruiter_name}} from {company_name}, and I came across your profile. Your experience in {industry} caught my attention, particularly your background as a {target_role}.

We're looking for talented {target_role}s to join our team{' and ' + value_proposition if value_proposition else ''}. 

Would you be open to a quick chat about this opportunity? I'd be happy to share more details about the role and answer any questions.

Best regards,
{{recruiter_name}}
{company_name}
"""
    return message

def generate_followup_message(target_role, company_name, tone, day):
    """Generate a follow-up message"""
    message = f"""Hi {{first_name}},

I wanted to follow up on my previous message about the {target_role} position at {company_name}.

Some highlights about the role:
- Competitive compensation and benefits
- Collaborative team environment with growth opportunities
- Chance to work on cutting-edge projects in our field

I'd love to discuss this opportunity with you. Are you available for a quick 15-minute call this week?

Looking forward to connecting,
{{recruiter_name}}
{company_name}
"""
    return message

def generate_linkedin_message(target_role, company_name, tone):
    """Generate a LinkedIn connection message"""
    message = f"""Hi {{first_name}},

I'm {{recruiter_name}} from {company_name}. I noticed your profile and experience as a {target_role}, and I thought you might be interested in an opportunity we have.

Would you be open to a conversation about joining our team?

Best,
{{recruiter_name}}
"""
    return message

def generate_final_email(target_role, company_name, tone):
    """Generate a final follow-up email"""
    message = f"""Hi {{first_name}},

I hope you're doing well. I'm reaching out one more time about the {target_role} position at {company_name}.

We're looking to fill this role soon, and based on your experience, I think you'd be a great fit. I'd be happy to share more details about the team and projects you'd be working on.

If you're interested, please let me know a convenient time to connect this week.

Best regards,
{{recruiter_name}}
{company_name}
"""
    return message

def generate_phone_script(target_role, company_name, tone):
    """Generate a phone call script"""
    message = f"""Hello {{first_name}}, this is {{recruiter_name}} from {company_name}.

I sent you a couple of emails about a {target_role} position we're looking to fill. I'm calling to see if you might be interested in learning more about this opportunity.

We're looking for someone with your background and skills. Do you have a few minutes to chat about it now, or would you prefer to schedule a time later this week?
"""
    return message

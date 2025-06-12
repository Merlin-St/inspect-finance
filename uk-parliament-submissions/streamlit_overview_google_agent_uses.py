# %% Imports
import streamlit as st
import pandas as pd
import plotly.express as px
import re # For parsing

# %% Main Functions (Data Loading and Processing)

def parse_and_classify_entry(org_name_line, description_text, current_sector, current_agent_type_text):
    """
    Helper function to parse a single entry and apply classification heuristics.
    """
    org_name = org_name_line.replace("*", "").strip()
    # Handle cases like "Organization (Clarification)" by trying to keep the core name
    # For the plot, sometimes a slightly modified name is better for uniqueness if one org has many entries.
    # This will be handled by how org_name_line is passed.
    
    full_description = description_text.strip()
    
    # Simplified description for plot, more detailed for tooltip
    # Try to get the first sentence or a reasonable chunk.
    description_summary_match = re.search(r"([^.!?]+[.!?])", full_description)
    if description_summary_match:
        description_summary = description_summary_match.group(1)
    elif len(full_description) > 150:
        description_summary = full_description[:150] + "..."
    else:
        description_summary = full_description

    kind_of_agent = "Info-retrieval agent (computer)" # Default
    economic_value = 2 # Default
    proximity_ncf = 2 # Default

    # Keywords for Kind_of_Agent
    desc_lower = full_description.lower()
    # Prioritize Robotics and Chatbot/LLM as they are often more distinct
    if any(k in desc_lower for k in ["robot", "autonomous vehicle", "autonomous driving", "digital twin ", "physical store", "factory worker", "3d models", "3d model", "vehicle", "trucks", "hardware", "sensor", "geospatial ai workloads", "expedition vehicles", "smart cockpit", "in-vehicle", "on the road", "fulfillment solutions", "smartest billboard", "digital twin of its entire distribution network"]):
        kind_of_agent = "Robotics agent (real-world)"
    elif any(k in desc_lower for k in ["conversational ai", "virtual assistant", "chatbot", "natural language", "summaries", "text generation", "translation", "gemini for google workspace", "gemini in gmail", "gemini in docs", "dialogflow", "speech-command", "voice", "chat features", "language model", "llm", "generative ai-powered virtual assistant"]):
        kind_of_agent = "Chatbot / LLM"
    elif any(k in desc_lower for k in ["code assist", "software development", "developer productivity", "coding", "debug", "deploy code", "software engineering", "ticket-to-code", "codebase", "code generation", "gemini code assist"]):
        kind_of_agent = "Execution agent (computer)" # Often code related, but can be broader
    elif any(k in desc_lower for k in ["automate", "streamline process", "deploy model", "workflow automation", "order management", "risk score", "claims processing", "gen ai framework", "api", "sdk", "platform for building", "automating tasks", "engine", "automating the generation", "automates", "operational impact", "process documents", "make decisions", "system", "platform", "tool", "solution", "ai models to streamline", "ai agent that helps", "ai-powered solutions", "intelligent search", "prediction", "predictive ai tools", "machine learning models", "ai platform"]):
        kind_of_agent = "Execution agent (computer)"
    elif any(k in desc_lower for k in ["search", "find information", "knowledge center", "data analysis", "document processing", "insights", "analytics", "vertex ai search", "bigquery", "looker", "reporting", "monitoring", "classif", "analyze data", "data points", "information retrieval", "data-driven", "research tool", "data insights", "data foundation", "data management", "data governance"]): # "classif" for classify
        kind_of_agent = "Info-retrieval agent (computer)"


    # Heuristics for Economic Value
    if any(k in desc_lower for k in ["revolutioniz", "transforming industry", "next-generation platform", "first-of-its-kind", "50% total-cost-of-ownership savings", "market leader", "$1.9 million roi", "doubling underwriter productivity", "brl 1.5 million since adoption", "global leader", "significant roi", "substantial market impact", "game-changing", "breakthrough", "pioneering", "10x faster", "90% reduction in costs", "brl 15 million in tax overcharges", "profit of $22.3 million", "200% growth", "100,000 transactions per second"]):
        economic_value = 5
    elif any(k in desc_lower for k in ["major operational transformation", "significant reduction", "significant improvements", "significant improvement", "10,000 man-hours per year", "400% performance", "90% faster", "80% reduction in errors", "$20 million in savings", "20% price and performance improvement", "accelerate", "optimize", "enhance efficiency", "streamline", "boost productivity", "increase revenue", "large scale", "billions of data points", "millions of users", "thousands of simulations", "75% in the time taken", "99% reduction in audit costs", "10-20% in accuracy", "95% reduction in time", "30% to 40% efficiency", "5x faster", "double-digit reduction", "workload gains", "transform massive volumes", "speeding up campaign creations from eight weeks to eight hours"]):
        economic_value = 4
    elif any(k in desc_lower for k in ["cost savings", "customer impact", "new product feature", "improved", "faster", "more efficient", "better", "20% faster", "15% increase", "operational cost savings", "increased efficiency", "time savings", "enhanced communication", "higher quality work", "reduced time", "reduction in technical debt", "improved click-through rate", "increased conversion rates", "boost accuracy", "unlock unique insights", "save time", "increase productivity", "streamlining workflows", "more culturally diverse and inclusive workplace", "reduces the time", "speeds inventory tracking", "automating insights", "13% increase in productivity", "average five hours per week", "20% faster", "30-35% reduction in time", "40% improvement in forecasting accuracy", "reduce food waste", "75% reduction in calls abandoned", "30% decrease in case handling times", "50% faster investigations"]):
        economic_value = 3
    elif any(k in desc_lower for k in ["departmental improvement", "some enhancement", "more effective", "easier", "helpful", "better able to recognize", "more responsive features", "simplify", "user-focused", "make marketing processes more efficient", "keeping customers secure", "convenient self-service", "easier to find", "more agile, intuitive, and fluid", "valuable productivity and collaboration tool", "enhance the workplace experience", "personalized guidance", "smoother stays", "better and more cost-effective services", "more time to focus", "winning back time", "more time and flexibility", "improve the quality of work", "better work and customer experiences", "getting things done faster", "greater productivity", "better security monitoring", "making it easier", "more accessible", "more personalized", "better tailored recommendations"]):
        economic_value = 2
    else: # Basic utility, not enough info, or very niche
        economic_value = 1 

    # Heuristics for Proximity to NCF
    sector_lower = current_sector.lower()
    org_name_lower = org_name.lower()
    agent_type_lower = current_agent_type_text.lower()

    if "security agent" in agent_type_lower: # Security agents are generally higher NCF
        if any(s in sector_lower for s in ["financial services", "telecommunications", "public sector", "technology", "healthcare"]):
            proximity_ncf = 5
        elif any(s in sector_lower for s in ["manufacturing", "retail", "automotive"]):
            proximity_ncf = 4
        else:
            proximity_ncf = 3
    elif any(k in org_name_lower for k in ["u.s. air force", "u.s. dept. of veterans affairs", "national institutes of health", "government of singapore", "qatari ministry of labour", "state of nevada", "new york state department of motor vehicles", "air force research laboratory", "colombia’s ministry of information", "brazil’s ministry of education", "noaa", "usaid", "world bank", "serpro", "prodam", "minas gerais state government", "israel antiquities authority", "belo horizonte municipal finance office"]):
        proximity_ncf = 5 # Government and critical public services
    elif "public sector" in sector_lower:
        proximity_ncf = 4 # General public sector, can be 5 if description implies critical function
        if any(k in desc_lower for k in ["national security", "emergency management", "critical infrastructure", "public safety", "essential services"]):
            proximity_ncf = 5
    elif any(s in sector_lower for s in ["healthcare & life sciences", "financial services", "telecommunications"]):
        proximity_ncf = 4 # These sectors often have high NCF impact
        if any(k in desc_lower for k in ["cancer detection", "drug discovery", "diagnostics", "patient care", "life-threatening diseases", "critical patient insights", "financial markets", "banking", "insurance", "payment systems", "anti money laundering", "network operations", "critical communications", "emergency services", "national critical functions", "supply chain resilience", "energy grid", "power generation", "water management"]):
            proximity_ncf = 5
    elif any(s in sector_lower for s in ["automotive & logistics", "manufacturing, industrial & electronics"]):
        proximity_ncf = 3 # Important for economy and infrastructure
        if any(k in desc_lower for k in ["supply chain", "transportation network", "autonomous driving safety", "critical manufacturing", "energy infrastructure", "defense contracting"]):
            proximity_ncf = 4
            if "defense" in desc_lower or "military" in desc_lower:
                 proximity_ncf = 5
    elif "technology" in sector_lower:
        proximity_ncf = 2 # Can vary wildly, default to lower unless specified
        if any(k in desc_lower for k in ["cybersecurity", "critical infrastructure support", "cloud infrastructure for government/healthcare", "data privacy for sensitive sectors"]):
            proximity_ncf = 4
        if "ai risk management" in desc_lower or "safe superintelligence" in desc_lower:
            proximity_ncf = 5
    elif any(s in sector_lower for s in ["business & professional services", "retail"]):
        proximity_ncf = 2 # Generally lower NCF unless supporting critical functions
        if "supply chain risk" in desc_lower or "financial compliance" in desc_lower:
            proximity_ncf = 3
    else: # Media, Hospitality, some general creative/entertainment
        proximity_ncf = 1
        
    # Override for Robotics if not already set and description implies it, can sometimes increase NCF
    if kind_of_agent != "Robotics agent (real-world)" and any(k in desc_lower for k in ["autonomous vehicle", "robotics", "autonomous driving company", "physical world", "in-home robot", "drones"]):
        kind_of_agent = "Robotics agent (real-world)"
        if proximity_ncf < 3 and any(k in desc_lower for k in ["logistics", "delivery", "inspection of infrastructure", "security robot"]):
            proximity_ncf = 3 # Robotics in these areas have higher NCF

    # Final check: if description mentions "national critical functions" or similar, elevate NCF
    if "national critical functions" in desc_lower or "critical national infrastructure" in desc_lower:
        proximity_ncf = 5

    return {
        "Organization": org_name,
        "Sector": current_sector,
        "Agent_Type_Text": current_agent_type_text, # This is the "Function"
        "Description": description_summary,
        "Kind_of_Agent": kind_of_agent, # This is for color-coding
        "Economic_Value": economic_value,
        "Proximity_NCF": proximity_ncf,
        "Full_Description_Tooltip": full_description
    }


def load_all_data():
    """
    Loads ALL AI use cases by parsing the provided text.
    This is an extensive list generated by applying heuristics.
    Accuracy of automated classification and scoring may vary.
    """
    all_entries = []

    # --- Automotive & Logistics ---
    current_sector = "Automotive & Logistics"
    # Customer Agents
    current_agent_type = "Customer Agents"
    all_entries.append(parse_and_classify_entry("Continental", "is using Google's data and AI technologies to develop automotive solutions that are safe, efficient, and user-focused. One of the initial outcomes of this partnership is the integration of Google Cloud's conversational AI technologies into Continental's Smart Cockpit HPC, an in-vehicle speech-command solution.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("General Motors", "OnStar has been augmented with new AI features, including a virtual assistant powered by Google Cloud’s conversational AI technologies that are better able to recognize the speaker’s intent.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("MercedesBenz (CLA Nav)", "is providing conversational search and navigation in the new CLA series cars using Google Cloud’s industry-tuned Automotive AI Agent.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Mercedes Benz (e-commerce)", "is infusing e-commerce capabilities into its online storefront with a gen AI-powered smart sales assistant.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("PODS", "worked with the advertising agency Tombras to create the “World’s Smartest Billboard” using Gemini — a campaign on its trucks that could adapt to each neighborhood in New York City, changing in real-time based on data. It hit all 299 neighborhoods in just 29 hours, creating more than 6,000 unique headlines.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("UPS Capital", "launched DeliveryDefense Address Confidence, which uses machine learning and UPS data to provide a confidence score for shippers to help them determine the likelihood of a successful delivery.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Volkswagen of America", "built a virtual assistant in the myVW app, where drivers can explore their owners’ manuals and ask questions, such as, “How do I change a flat tire?” or “What does this digital cockpit indicator light mean?” Users can also use Gemini’s multimodal capabilities to see helpful information and context on indicator lights simply by pointing their smartphone cameras at the dashboard.", current_sector, current_agent_type))
    
    # Employee Agents
    current_agent_type = "Employee Agents"
    all_entries.append(parse_and_classify_entry("704 Apps", "creates applications serving the last-mile transportation segment, connecting thousands of drivers and passengers every day. During trips, the audio content of conversations between car occupants is sent to Gemini, which measures the emotional “temperature.\" Specific words such as “robbery”, “assault”, “kidnapping”, among others, can be classified as hostile by the tool, generating alerts to anticipate risky situations before they happen.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Oxa", "a developer of software for autonomous vehicles, uses Gemini for Google Workspace to build campaign templates for metrics reporting, write social posts in order to make marketing processes more efficient, create job descriptions, and proofread content across all teams, saving time and resources.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Rivian", "uses Google Workspace with Gemini to enhance communication and collaboration across tech and marketing teams, resulting in faster, higher quality work.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Toyota (Factory ML)", "implemented an AI platform using Google Cloud's AI infrastructure to enable factory workers to develop and deploy machine learning models. This led to a reduction of over 10,000 man-hours per year and increased efficiency and productivity.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Uber (Employee Productivity)", "is using AI agents to help employees be more productive, save time, and be even more effective at work. For customer service representatives, the company launched new tools that summarize communications with users and can even surface context from previous interactions, so front-line staff can be more helpful and effective.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Uber (Workspace Gemini)", "also uses Google Workspace with Gemini to save time on repetitive tasks, free up developers for higher-value work, reduce their agency spending, and to enhance employee retention.", current_sector, current_agent_type))

    # Code Agents
    current_agent_type = "Code Agents"
    all_entries.append(parse_and_classify_entry("Renault Group’s Ampere", "an EV and software subsidiary created in 2023, is using an enterprise version of Gemini Code Assist, built for teams of developers and able to understand a company’s code base, standards, and conventions.", current_sector, current_agent_type))

    # Data Agents
    current_agent_type = "Data Agents"
    all_entries.append(parse_and_classify_entry("BMW Group (SORDI.ai)", "in collaboration with Monkeyway, developed the AI solution SORDI.ai to optimize industrial planning processes and supply chains with gen AI. This involves scanning assets and using Vertex AI to create 3D models that act as digital twins that perform thousands of simulations to optimize distribution efficiency.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Dematic", "is using the multimodal features in Vertex AI and Gemini to build end-to-end fulfillment solutions for both ecommerce and omnichannel retailers.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Geotab", "a global leader in telematics, uses BigQuery and Vertex AI to analyze billions of data points per day from over 4.6 million vehicles. This enables real-time insights for fleet optimization, driver safety, transportation decarbonization, and macro-scale transportation analytics to drive safer and more sustainable cities.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Kinaxis", "is building data-driven supply chain solutions to address logistics use cases including scenario modeling, planning, operations management, and automation.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Nuro", "an autonomous driving company, uses vector search in AlloyDB to enable their vehicles to accurately classify objects encountered on the road.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Picterra", "which calls itself a search engine for the physical world, adopted Google Kubernetes Engine to power its platform, providing the ability to quickly scale to meet the demands of geospatial AI workloads. With GKE, Picterra can model the terrain of entire countries quickly, even at ultra-high resolutions.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Prewave", "a supply chain risk intelligence platform, utilizes Google Cloud's AI services to provide end-to-end risk monitoring and ESG risk detection for businesses. This enables companies to gain transparency deep into their supply chains, ensuring resilience, sustainability, and compliance with regulations like the European CSDDD.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("TruckHouse", "specializes in expedition vehicles and speeds inventory tracking with Gemini in Sheets so they can spend more time in the great outdoors.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("UPS (Digital Twin)", "is building a digital twin of its entire distribution network, so both workers and customers can see where their packages are at any time.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Woven (Toyota Mobility)", "– Toyota's investment in the future of mobility — is partnering with Google to leverage vast amounts of data and AI to enable autonomous driving, supported by thousands of ML workloads on Google Cloud’s AI Hypercomputer. This has resulted in 50% total-cost-of-ownership savings to support automated driving.", current_sector, current_agent_type))

    # --- Business & Professional Services ---
    current_sector = "Business & Professional Services"
    # Customer Agents
    current_agent_type = "Customer Agents"
    all_entries.append(parse_and_classify_entry("Accenture (Retailer VA)", "is transforming customer support at a major retailer by offering convenient self-service options through virtual assistants, enhancing the overall customer experience.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Capgemini (Ecommerce Agents)", "is using Google Cloud to build AI agents that help optimize the ecommerce experience by helping retailers accept customer orders through new revenue channels and accelerate the order-to-cash process for digital stores.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Deloitte (Care Finder)", "offers a “Care Finder” agent, built with Google Cloud, as part of its Agent Fleet. The agent helps care seekers find in-network providers — often in less than a minute — significantly faster than the average call time of five to eight minutes.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Ferret.ai", "uses AI to offer insights about the backgrounds of people in a user's personal and professional network, providing a curated relationship intelligence and monitoring solution for its users — increasingly important services in a world of growing reputational risks.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Intuit (TurboTax Autofill)", "the makers of TurboTax, integrated Google Cloud’s visual recognition platform, Doc AI, and Gemini models into Intuit’s proprietary GenOS. This will expand the capabilities of Intuit’s “done-for-you” autofill of tax returns across the ten most common U.S. tax forms (variations of the 1099 and 1040 forms), helping users save time and boosting accuracy.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Stax AI (Retirement Planning)", "which aims to revolutionize retirement planning with AI, uses MongoDB Atlas and Vertex AI to automate its manual processes and transform massive volumes of trust accounting data in minutes.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Sutherland (Client-facing Teams)", "a leading digital transformation company, is focused on bringing together human expertise and AI, including boosting its client-facing teams by automatically surfacing suggested responses and automating insights in real time.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Wagestream (Internal Inquiries)", "a financial wellbeing platform for employee benefits, is using Gemini models to handle more than 80% of its internal customer inquiries, including questions about payment dates, balances, and more.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("WealthAPI (Financial Insights)", "the leading provider of wealth management interfaces in Germany, uses Gemini and DataStax Astra DB to deliver next-gen financial insights in real time to millions of customers for personalized guidance at scale.", current_sector, current_agent_type))

    # Employee Agents
    current_agent_type = "Employee Agents"
    all_entries.append(parse_and_classify_entry("Allegis Group (Recruitment)", "a global leader in talent solutions, partnered with TEKsystems to implement AI models to streamline its recruitment process, including automating tasks such as updating candidate profiles, generating job descriptions, and analyzing recruiter-candidate interactions. The implementation resulted in significant improvements in recruiter efficiency and a reduction in technical debt.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("BCG (Sales Optimization)", "uses Google Cloud to provide a sales optimization tool that improves the effectiveness and impact of insurance advisors.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Cintas (Knowledge Center)", "is using Vertex AI Search to develop an internal knowledge center for customer service and sales teams to easily find key information.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Beyond (Project Kickoff)", "is a technology consultancy that guides their clients through transformational journeys to unlock the potential of AI and cloud-based technology. Google Workspace with Gemini helps them reduce the time from project brief to project kickoff from months to weeks, and the time for first drafts of RFI responses from days to minutes.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Dun & Bradstreet (Email Gen & Search)", "a business research and intelligence service, built an email-generation tool with Gemini that helps sellers create tailored, personalized communications to prospects and customers for its research services. The company also developed intelligent search capabilities to help users with complex queries like, \"Find me all the companies in this area with a high ESG rating.\"", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Cognizant (Legal Contracts)", "used Vertex AI and Gemini built an AI agent to help legal teams draft contracts, assign risk scores and make recommendations for ways to optimize operational impact.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Equifax (Workspace Transition)", "adopted Google Workspace, launching a strategic change management campaign to ensure a smooth transition across more than 20 countries in one weekend. Workspace’s suite of Gemini-powered tools for communication, collaboration, and productivity offered a comprehensive and user-friendly solution that could be easily embraced by Equifax employees at all levels.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Finnt (Corporate Finance Automation)", "part of the Google for Startups Cloud AI Accelerator, provides AI automation solutions for corporate finance teams, helping to cut accounting procedures time by 90%, boost accuracy, and unlock unique insights.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Flashpoint (Workforce Productivity)", "is improving efficiency and productivity across its workforce, using Google Workspace to communicate and collaborate more effectively, maximize ROI, and increase employee satisfaction, so they can dedicate more time to keeping customers secure.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Fluna (Legal Agreement Automation)", "a Brazilian digital services company, has automated the analysis and drafting of legal agreements using Vertex AI, Document AI, and Gemini 1.5 Pro, achieving an accuracy of 92% in data extraction while ensuring security and reliability for sensitive information.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("FreshFields (Legal AI Products)", "a global law firm, will roll out Gemini with Google Workspace across its practice and will also create groundbreaking AI products and bespoke AI agents to transform processes in the highly regulated legal industry.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Joe the Architect (Email Management)", "a 25-person architecture firm, catches up on long email chains with Gemini in Gmail to keep track of client needs across dozens of conversations.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("KPMG (Law Firm & Banking AI)", "is building Google AI into their newly formed KPMG Law firm, as well as driving AI transformation within the banking industry, and the company is also implementing Agentspace to enhance its own workplace operations.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("L+R (Design Agency Workflow)", "a design and technology agency, leverages Gemini for Google Workspace Workspace to elevate performance and precision, streamlining workflows and empowering its team to achieve more impactful results.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Monks (Ad Campaign Efficiency)", "used Google Gemini to help Hatch build a personalized ad campaign. The campaign delivered an 80% improved click-through rate, 46% more engaged site visitors, and a 31% improved cost-per-purchase over other campaigns. On top of this, by using AI the team was able to deliver the campaign much more efficiently, reducing time to investment by 50% and costs by 97%.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Own Your Brand (Enrollment Management)", "founder Lauren Magenta uses Google Workspace to run her business and Gemini for Google Workspace is transforming how she manages enrollment. Gemini helps her quickly draft personalized emails to potential clients in her own voice.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Randstad (Work Culture Transformation)", "a large HR services and talent provider, is using Gemini for Workspace across its organization to transform its work culture, leading to a more culturally diverse and inclusive workplace that’s seen a double-digit reduction in sick days.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Sulamérica (Insurance Operations)", "adopted Google Workspace a decade ago to make collaboration among employees more agile, intuitive, and fluid. The insurance company recently started using Gemini in Workspace, making it available to 1,250 employees to increase operational efficiency, security, and productivity.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("UKG (HR Conversational Agent)", "an HR and workforce management solutions provider, enhances the workplace experience with UKG Bryte AI, a trusted conversational agent built with Google Cloud that enables HR administrators and people managers to request information about company policies, business insights, and more.", current_sector, current_agent_type))

    # Creative Agents
    current_agent_type = "Creative Agents"
    all_entries.append(parse_and_classify_entry("Agoda (Travel Visuals)", "is a digital travel platform that helps travelers see the world for less... They’re now testing Imagen and Veo on Vertex AI to create visuals, allowing Agoda teams to generate unique images of travel destinations which would then be used to generate videos.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Kraft Heinz (Campaign Creation)", "is using Google’s media generation models, Imagen and Veo, on Vertex AI, speeding up campaign creations from eight weeks to eight hours.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Quom (Financial Inclusion Agents)", "a financial inclusion specialist in Mexico, has developed AI-powered conversational agents that optimize and personalize user and customer support.", current_sector, current_agent_type)) # Could also be customer agent
    all_entries.append(parse_and_classify_entry("Salesrun (Retail Sales Optimization)", "the world’s first dedicated sales activity suite, sees Google Cloud gen AI as an alternative for analyzing information related to purchasing habits, enabling the optimization of cash flow and boosting sales for its retail customers.", current_sector, current_agent_type)) # Could also be data agent
    all_entries.append(parse_and_classify_entry("Thoughtworks (Internal/External Comms)", "is a global technology consultancy that helps businesses use technology to solve problems and innovate. They use Google Workspace with Gemini to improve internal and external communication across their company, including in non-native languages — from emails to documents and blogs.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Yazi (Marketing & Dev)", "turns to Google Workspace with Gemini to accelerate marketing efforts so they can launch products faster; their dev teams also use it to write and deploy more code.", current_sector, current_agent_type))

    # Code Agents
    current_agent_type = "Code Agents"
    all_entries.append(parse_and_classify_entry("Capgemini (Code Assist)", "has been using Code Assist to improve software engineering productivity, quality, security, and developer experience, with early results showing workload gains for coding and more stable code quality.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Tata Consultancy Services (TCS) (Persona-based AI Agents)", "helps build persona-based AI agents on Google Cloud, contextualized with enterprise knowledge to accelerate software development.", current_sector, current_agent_type))

    # Data Agents
    current_agent_type = "Data Agents"
    all_entries.append(parse_and_classify_entry("The Colombian Security Council (Chemical Emergency Chatbot)", "developed a generative AI-based chatbot to improve data analysis and its chemical emergency management processes, allowing for quick responses to urgent situations.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Contraktor (Contract Analysis)", "developed a project to analyze contracts with AI. As a result, the company achieved a reduction of up to 75% in the time taken to analyze and review a contract, with the possibility of both reading and extracting relevant data from the documents.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Gamuda Berhad (Bot Unify for Construction)", "a Malaysian infrastructure and property management company, has developed Bot Unify, a platform that democratizes generative AI to allow users access to Gemini models and RAG frameworks to provide faster information and insights during construction projects.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Habi (Real Estate Document Automation)", "a Colombian real estate company, has implemented AI solutions to streamline and automate the management and verification of physical and digital documents. This improved validation operations and increased the efficiency and adaptability of employees.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("HCLTech (Insight for Manufacturing Quality)", "an industry-leading global technology company, launched HCLTech Insight — a manufacturing quality AI agent that helps predict and eliminate different types of defects on manufacturing using Vertex AI, Google Cloud’s Cortex Framework, and the Manufacturing Data Engine platform.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("IPRally (Patent Document Search)", "built a custom machine-learning platform that uses natural language processing on the text of more than 120 million global patent documents, creating an accurate, easily searchable database that adds more than 200,000 new sources a week.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Ipsos (Market Research Data Analysis)", "built a data analysis tool for its teams of market researchers, eliminating the need for time-consuming requests to data analysts. The tool is powered by Gemini 1.5 Pro and Flash models, as well as Grounding with Google Search, to enhance real-world accuracy from contemporaneous search information.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Juganu (Smart Store Digital Twins)", "a SaaS provider for smart cities and smart stores, is working with Google Cloud to automate and digitize the physical store. The company has begun developing digital twins that give retailers virtual eyes in the store to help automate routine tasks, improve efficiency, and deliver better customer experiences.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Nowports (Logistics Market Prediction)", "is harnessing the power of AI to revolutionize logistics and stand out from the competition. By analyzing key operational information, they aim to accurately predict market behavior, optimizing their entire supply chain.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Servicios Orienta (Wellness Data Analysis)", "a Mexican personal wellness and organizational efficiency company, has adopted AI-based solutions to analyze large volumes of data, interpret results, and provide recommendations that enhance the customer experience.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Workday (Accessible Data Insights)", "is using natural language processing in Vertex AI Search and Conversation to make data insights more accessible for technical and non-technical users alike.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Zenpli (Digital Identity Onboarding)", "a digital identity partner for other businesses, leverages the multimodal capabilities of the models available in Vertex AI to provide its clients with a radically enhanced experience: a 90% faster onboarding process with contracts, a 50% reduction in costs thanks to AI-powered automation, and superior data quality that ensures regulatory compliance.", current_sector, current_agent_type))
    
    # --- Financial Services ---
    current_sector = "Financial Services"
    # Customer Agents
    current_agent_type = "Customer Agents"
    all_entries.append(parse_and_classify_entry("Albo (Neobank Customer Service)", "is revolutionizing customer service and financial education in Mexico through AI. The neobank has managed to optimize its processes to provide faster and more efficient responses, as well as offering educational tools to users with limited access to traditional financial services.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Apex Fintech Solutions (Investor Education)", "is leveraging Google Cloud to power seamless access, frictionless investing, and investor education at scale. Using BigQuery, Looker, Google Kubernetes Engine, Apex is enhancing accessibility to financial insights while laying the groundwork for AI-driven innovation.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Banco Covalto (Credit Approval)", "in Mexico is transforming its operations with gen AI to streamline processes and enhance customer experience, reducing credit approval response times by more than 90%.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Bud Financial (Financial LLM)", "uses its Financial LLM, powered by Gemini models, to provide personalized answers to customer queries and automate banking tasks, such as moving money between accounts to avoid overdrafts.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Contabilizei (The Concierge AI)", "is improving customer service in Brazilian financial services with “The Concierge,” its AI solution powered by Vertex AI. Using tools like Vertex AI Search and Model Garden, the platform delivers fast, personalized responses.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Discover Financial (Virtual Assistant)", "has created the Discover Virtual Assistant, powered by generative AI, that can assist customers directly and provide additional information to Discover service agents, delivering smoother, more efficient, and more satisfying interactions to customers around the world — in whatever channel they prefer.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Figure (Home Equity Chatbots)", "a fintech offering home equity lines of credit, leverages Gemini’s multimodal models to create AI-powered chatbots that help streamline, simplify, and accelerate lending experiences for both consumers and employees.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Fundwell (Business Funding Match)", "helps businesses secure the funding they need to grow with speed and confidence. Utilizing Google Cloud, Fundwell simplifies the customer journey by analyzing financial health with AI to match businesses with their ideal funding solution.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("ING Bank (Employee Chatbot for Customer Queries)", "aims to offer a superior customer experience and has developed a gen AI chatbot for workers to enhance self-service capabilities and improve answer quality on customer queries.", current_sector, current_agent_type)) # Employee tool for customer service
    all_entries.append(parse_and_classify_entry("Safe Rate (AI Mortgage Agent)", "a digital mortgage lender, is using Gemini models to create an AI mortgage agent that includes gen AI chat features like “Beat this Rate” and “Refinance Me;” these help borrowers quickly compare different rates and get personalized quotes in under 30 seconds.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Scotiabank (Personalized Banking Chatbot)", "is using Gemini and Vertex AI to create a more personal and predictive banking experience for its clients, including powering its award winning chatbot, which continues to elevate the bank's digital offerings and highlights the value of AI technology to enhance the digital client experience.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("SEB (Wealth Management Agent)", "a Nordic corporate bank, has support from Bain & Company to develop an AI agent for the wealth management division. The agent, built with Google Cloud, enhances end-customer conversations with suggested responses and generates call summaries, helping to increase efficiency by 15%.", current_sector, current_agent_type)) # Employee tool for customer service
    all_entries.append(parse_and_classify_entry("United Wholesale Mortgage (Underwriter Productivity)", "is transforming the mortgage experience with Vertex AI, Gemini, and BigQuery, already more than doubling underwriter productivity in just nine months, resulting in shorter loan close times for 50,000 brokers and their clients.", current_sector, current_agent_type)) # Primarily employee productivity impacting customers
    all_entries.append(parse_and_classify_entry("Wayfair (Product Catalog Enrichment)", "automates its product catalog enrichment and now updates product attributes 5x faster, achieving significant operational cost savings.", current_sector, current_agent_type)) # More data/employee agent

    # Employee Agents
    current_agent_type = "Employee Agents"
    all_entries.append(parse_and_classify_entry("ATB Financial (Workspace Gemini)", "a leading financial institution in Alberta, Canada, has successfully deployed Google Workspace with Gemini to its more than 5,000 team members, allowing them to automate routine tasks, access information quickly, and collaborate more effectively, all while ensuring data is secure and trustworthy.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Banco BV (Agentspace)", "implemented Agentspace, enabling its employees to use gen AI technologies for research, assistance, and operations across several of its critical systems, in a secure and compliant manner.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Banco Rendimento (WhatsApp Transfers)", "a currency exchange market, is using Vertex AI and other solutions to create a service that enables sending international transfers through WhatsApp, delivering 24/7 service without requiring a representative to complete the transaction.", current_sector, current_agent_type)) # Customer facing automation
    all_entries.append(parse_and_classify_entry("Banestes (Workspace for Credit Analysis)", "a Brazilian bank, used Gemini in Google Workspace to streamline work dynamics, such as accelerating credit analysis by simplifying balance sheet reviews and boosting productivity in marketing and legal departments.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Bank of New York Mellon (Employee VA)", "built a virtual assistant to help employees find relevant information and answers to their questions.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Citi (Gen AI for Dev & Document Processing)", "uses Vertex AI to deliver gen AI capabilities across the company, fueling generative AI initiatives related to developer toolkits, document processing, and digitization capabilities to empower customer servicing teams.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Cotality (Real Estate Insights)", "is using Gemini to provide data-driven insights for more than 1.5 million property professionals across the entire real estate management ecosystem. Cotality (formerly known as CoreLogic) has incorporated AI features and automations into its industry solutions such as MLSTouch for real estate agents, TOTAL for Mobile for the home appraiser, and the newly launched Araya, its property data and insights platform. It's also using Gemini and Vertex AI to bring operational efficiency to the company's internal operations.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Commerzbank (Client Call Documentation)", "a leading German bank, implemented an AI agent powered by Gemini 1.5 Pro to automate the documentation of client calls, freeing up its financial advisors from tedious manual processes; a significant reduction in processing time allowed advisors to focus on higher-value activities like building client relationships and providing personalized advice.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("DBS (Customer Call Handling)", "a leading Asian financial services group, is reducing customer call handling times by 20% with Customer Engagement Suite.", current_sector, current_agent_type)) # Customer facing impact
    all_entries.append(parse_and_classify_entry("Deutsche Bank (DB Lumina Research Tool)", "has created DB Lumina, an AI-powered research tool that accelerates the time it takes financial analysts to create research reports and notes. Work that used to take hours or even days can now be completed in a matter of minutes, all while maintaining data privacy requirements for the highly regulated financial sector.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Discover Financial (Contact Center Agent Assist)", "helps its 10,000 contact center representatives to search and synthesize information across detailed policies and procedures during calls.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("FinQuery (Workspace Productivity)", "a fintech company, is using Gemini for Google Workspace as a valuable productivity and collaboration tool to help in brainstorming sessions, draft emails 20% faster, manage complex cross-organizational project plans, and aid engineering teams with debugging code and evaluating new monitoring tools.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Five Sigma (Claims Handling Automation)", "created an AI engine which frees up human claims handlers to focus on areas where a human touch is valuable, like complex decision-making and empathic customer service. This has led to an 80% reduction in errors, a 25% increase in adjustor’s productivity, and a 10% reduction in claims cycle processing time.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Generali (Salesperson Policy Access)", "utilizes Vertex AI and Google Cloud solutions to enable salespeople to access policy information instantly through natural language queries.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("HDFC ERGO (1Up App for Agents)", "India's leading non-life insurance company, built a pair of insurance \"superapps\" for the Indian market. On the 1Up app, the insurer leverages Vertex AI to give insurance agents context-sensitive \"nudges\" through different scenarios to facilitate the customer onboarding experience.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("HDFC ERGO (Personalized Offerings)", "also runs advanced data insight from BigQuery through Vertex AI to drive highly personalized offerings for consumers in specific geographical locations.", current_sector, current_agent_type)) # Data agent for customer impact
    all_entries.append(parse_and_classify_entry("Hiscox (Lead Underwriting Model)", "used BigQuery and Vertex AI to create the first AI-enhanced lead underwriting model for insurers, automating and accelerating the quoting for complex risks from three days down to a few minutes.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Loadsure (Claims Processing Automation)", "utilizes Google Cloud's Document AI and Gemini AI to automate insurance claims processing, extracting data from various documents and classifying them with high accuracy. This has led to faster processing times, increased accuracy, and improved customer satisfaction by settling claims in near real-time.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Multimodal (Financial Workflow Automation)", "part of the Google for Startups Cloud AI Accelerator, automates complex financial services workflows with multimodal AI agents that can process documents, query databases, power chatbots, make decisions, and generate reports.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("OSTTRA (Workspace Proposal & Interview Gen)", "chose Google Workspace to boost teamwork, and Gemini is now helping automate tasks like writing proposals and generating interview questions, using features like “Help me write” to save employees time and increase productivity.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Pinnacol Assurance (Repetitive Task Automation)", "Colorado’s largest worker’s compensation carrier, leans on Gemini to accelerate repetitive tasks, such as creating questions for client interviews and digging deeper into insurance claims, with 96% of surveyed employees reporting time savings", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("ROSHN Group (RoshnAI Internal Assistant)", "one of Saudi Arabia’s leading property developers has built RoshnAI, an internal assistant that leverages a combination of AI model that include Gemini 1.5 Pro and Flash to generate valuable insights from ROSHN's internal data sources for its employees.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Symphony (Finance Team Collaboration)", "the communications platform for the financial services industry, uses Vertex AI to help finance and trading teams collaborate across multiple asset classes.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Tributei (Tax Assessment Automation)", "was founded in 2019 to simplify the complex tax assessment processes for Brazil’s state VAT. ML resources help Tributei simplify not only tax assessments but also tax management tasks, with performance improved by 400%. This initiative has already helped 19,000 companies automate and audit VAT-related transactions, spotting more than BRL 15 million in tax overcharges.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("The Trumble Insurance Agency (Workspace Creativity)", "is using Gemini for Google Workspace to significantly improve its creativity and the value that it delivers to its clients with enhanced efficiency, productivity, and creativity.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("wealth.com (Ester Chat Agent for Estate Planning)", "built a platform that simplifies estate planning while equipping financial advisors with powerful tools to visualize and manage complex plans. Its new AI-powered Ester chat agent helps accurately and securely extract information from complex and lengthy planning documents, like trusts and wills.", current_sector, current_agent_type))

    # Code Agents
    current_agent_type = "Code Agents"
    all_entries.append(parse_and_classify_entry("CME Group (Developer Productivity)", "which operates the Chicago Mercantile Exchange, says most developers using Gemini Code Assist report a productivity gain of at least 10.5 hours a month.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Commerzbank (Developer Efficiency with Code Assist)", "is enhancing developer efficiency through Code Assist's robust security and compliance features.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Regnology (Ticket-to-Code Writer)", "a provider of regulatory reporting services, built its Ticket-to-Code Writer tool with Gemini 1.5 Pro to automate the conversion of bug tickets into actionable code, significantly streamlining the software development process.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("ROSHN Group (Code & Cloud Assist)", "is using Gemini Code Assist and Cloud Assist to increase the productivity of its engineers who are working on its unique real estate shopping website and app; shortly after launch, the organization was able to register 45,000 new users and conduct 9,400 completed purchases digitally.", current_sector, current_agent_type))

    # Data Agents
    current_agent_type = "Data Agents"
    all_entries.append(parse_and_classify_entry("CERC (Financial Market Infrastructure)", "Brazil’s first and largest cloud-native financial market infrastructure, built its IT on Google Cloud from the outset, allowing CERC to be more agile, flexible, and secure. CERC now processes 100,000 transactions per second with its infrastructure on Google Cloud.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Ci Banco (Document Management System)", "leverages Google Cloud technologies across more than 50 projects, including a document management system powered by Vertex AI. This system has optimized the document review process for their trust authorization procedures, reducing the time from one week to less than two hours.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Citadel Securities (Market Data Modeling)", "a top financial institution, is now able to facilitate market data modeling and training, with a 20% price and performance improvement using Google Cloud TPUs.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("CME Group (Cloud Trading Platform)", "is building a first-of-its-kind cloud-based commodities trading platform with AI tools built-in, offering CME’s trading customers access to deeper insights and smarter trades as well as rapid experimentation on new trading strategies that won’t interrupt existing trade flows.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Digits (Next-gen Accounting Software)", "developing next-gen accounting software for startups and small businesses. Using AI-driven bookkeeping, expense management, and financial analysis, Digits enables business owners to achieve financial clarity and focus on growth.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Dojo (Payment Data Engagement)", "is enabling millions of secure, reliable, and ultra-fast payment experiences daily, empowering businesses to serve more customers. Dojo is leveraging Google Cloud gen AI services like Looker and Gemini models to explore innovative use cases that offer more intuitive, natural ways to engage with payment data.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Generali Italia (ML Model Evaluation Pipeline)", "Italy's largest insurance provider, used Vertex AI to build a model evaluation pipeline that helps ML teams quickly evaluate performance and deploy models.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Hiperstream (Data Flow Performance)", "is using Gemini to analyze specific information and automatically categorize it, resulting in a 200% increase in the performance of data flows and communications for its financial and B2B customers.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Intesa Sanpaolo (Democratic Data Lab)", "built its Democratic Data Lab using data analytics and AI to enable its risk management team to keep up with the rapid changes and complexity of modern financial markets. By democratizing access to data, the Democratic Data Lab is empowering other departments across the bank to have more oversight and control of risks.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Kredito (Risk Assessment Model)", "a Chilean fintech pioneer in online lending, created an AI-based risk assessment model that improved the prediction of payment behaviors and helped clients access working capital more quickly.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Macquarie (Data Cleaning & Gen AI Insights)", "in Australia has been using predictive AI to clean and unify 100% of its data, so teams can then draw insights using gen AI tools in Vertex AI, removing roadblocks and reducing the noise to drive better results for employees and customers.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("MSCI (Climate Risk Datasets)", "a leading publisher of market indices and data, uses machine learning with Vertex AI, BigQuery, and Cloud Run to enrich its datasets to help clients gain insights into around 1 million asset locations to help manage climate-related risks.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Snowdrop (Transactional Data Enrichment)", "leverages Google Cloud's AI and geospatial data, including Google Places and Vertex AI, to enrich transactional data for financial institutions. This automation has led to a 40% improvement in data accuracy, a 15% increase in merchant-to-transaction matching, and the ability to process over 2.1 billion transactions monthly while scaling globally.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("SURA Investments (Customer Needs Analysis)", "the largest asset manager in Latin America, developed an AI-based analysis model for employees that allows them to better understand customer needs and improve customer experience and satisfaction.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Syte (Property Data Platform)", "AI-driven property platform allows the retrieval of all relevant characteristic data on properties and its development, expansion, and conversion potential in real-time, making it easy to identify sites and buildings for re-densification.", current_sector, current_agent_type))

    # Security Agents
    current_agent_type = "Security Agents"
    all_entries.append(parse_and_classify_entry("Airwallex (Fraud Detection)", "an Australian multinational fintech company, detects and manages fraud in real time in a scalable, always-available environment, powered by Vertex AI, Google Kubernetes Engine, and GitLab.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Apex Fintech Services (Threat Detection Writing)", "is using Gemini in Security to accelerate the writing of complex threat detections from hours to a matter of seconds.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("BBVA (Google SecOps Threat Response)", "uses AI in Google SecOps to detect, investigate, and respond to security threats with more accuracy, speed, and scale. The platform now surfaces critical security data in seconds, when it previously took minutes or even hours, and delivers highly automated responses.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Bradesco (Anti Money Laundering AI)", "one of the largest financial institutions in Latin America, has been using Google Cloud AI to detect suspicious activity and combat money laundering more effectively and efficiently — and was one of the early adopters worldwide of Google Cloud’s Anti Money Laundering AI.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Charles Schwab (Google SecOps Integration)", "has integrated its own intelligence into the AI-powered Google SecOps, so analysts can better prioritize work and respond to threats.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Cloudwalk (Anti-fraud & Credit Analysis)", "a Brazilian fintech unicorn that currently serves more than one million customers with payment solutions, uses Google Cloud infrastructure and AI services to build anti-fraud and credit analysis models. This allowed the fintech to close 2023 with a profit of $22.3 million, showing 200% growth in its commercial base.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Credem (Online User Security)", "a 114-year-old Italian financial institution, uses AI to enhance security for online users, offer products tailored to customer needs, and predict software malfunctions, achieving significant results in a short time.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Dun & Bradstreet (Security Command Center)", "is using Security Command Center to centralize monitoring of AI security threats alongside their other cloud security findings.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Fiserv (Gemini in Security Operations)", "a developer of financial services technology, can now summarize threats, find answers, and detect, validate, and respond to security events faster with the Gemini in Security Operations platform.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Resistant AI (Fraud Combat in Documentation)", "is building AI-powered solutions to combat fraud in financial services documentation and workflows with the help of Google Cloud. These solutions can expedite background checks, reduce fraud losses, and speed up underwriting and claims processing processes.", current_sector, current_agent_type))

    # --- Healthcare & Life Sciences ---
    current_sector = "Healthcare & Life Sciences"
    # Customer Agents
    current_agent_type = "Customer Agents"
    all_entries.append(parse_and_classify_entry("Bennie Health (Employee Health Benefits Platform)", "uses Vertex AI to power its innovative employee health benefits platform, providing actionable insights and streamlining data management in order to enhance efficiency and decision-making for employees and HR teams.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Clivi (Personalized Patient Monitoring)", "a Mexican health startup, has created a gen AI platform with Google Cloud that enables personalized and continuous monitoring of its patients to offer tailored responses, improve the volume and capacity of care, and reduce complications.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Family Vision Care of Ponca City (Patient Email Explanations)", "uses Gemini in Gmail to easily explain medical terms in patient emails and to improve accessibility.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Freenome (Early Cancer Detection Tests)", "is creating diagnostic tests that will help detect life-threatening diseases like cancer in the earliest, most-treatable stages — combining the latest in science and AI with the ease of a standard blood draw.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Genial Care (Autism Care Records)", "a Latin American healthcare network, is a reference in innovative care for children with Autism Spectrum Disorder and their families. By investing in Vertex AI, the company has improved the quality of records of sessions involving atypical children and their families, allowing caregivers to fully monitor the work carried out.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Orby (Digital Brain for Rehabilitation)", "is combining AI and neurotechnology, applying complex mathematical models, Google Cloud’s IT resources, and Gemini to create a “digital brain.” This solution supports patients’ rehabilitation, helping them to recover lost motor skills and reduce their pain.", current_sector, current_agent_type))

    # Employee Agents
    current_agent_type = "Employee Agents"
    all_entries.append(parse_and_classify_entry("American Addiction Centers (Employee Onboarding)", "was able to reduce employee onboarding from three days to 12 hours using Gemini for Google Workspace, and is now exploring how to streamline tasks like generating safety checklists for medical staff, saving valuable time and improving patient care.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Asepha (Autonomous AI Pharmacists)", "part of the Google for Startups Cloud AI Accelerator, is building fully autonomous AI pharmacists to help automate manual work.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Bayer (Radiology Platform)", "is building a radiology platform that will assist radiologists with data analysis, intelligent search, and document creation that meet healthcare requirements needed for regulatory approval.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("BenchSci (Biological Research Solutions)", "develops generative AI solutions empowering scientists to understand complex connections in biological research, saving them time and financial resources and ultimately bringing new medicine to patients faster.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Better Habits (Wellness Workshop Comms)", "uses Google Workspace with Gemini to reduce the time spent developing communication plans, allowing them to focus on delivering high-quality wellness workshops.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Certify OS (Medical Provider Credentialing)", "is automating credentialing, licensing, and monitoring of medical providers for healthcare networks, relieving the burden of time-consuming and often siloed information.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Click Therapeutics (Clinical Trial Insights)", "develops prescription digital therapeutics designed to treat disease. Its Clinical Operations team leverages Gemini for Google Workspace to transform complex operations data into actionable insights so they can quickly pinpoint ways to streamline the patient experience in clinical trials.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Mark Cuban’s Cost Plus Drugs (Gmail & Document Automation)", "widely uses Gemini for Google Workspace, estimating that employees are saving an average five hours per week just with AI capabilities in Gmail. Gemini is also streamlining time-consuming, manual processes through uses like AI-generated transcriptions and auto-formatting of pharmaceutical lab results or FDA compliance documentation.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Covered California (Document Automation)", "the state’s healthcare marketplace, is using Document AI to help improve the consumer and employee experience by automating parts of the documentation and verification process when residents apply for coverage.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Cradle (Protein Design for Drug Discovery)", "a biotech startup, is using Google Cloud's generative AI technology to design proteins for drug discovery, food production, and chemical manufacturing. By leveraging TPUs and Google's security infrastructure, the company accelerates R&D processes for pharmaceutical and chemical companies while protecting sensitive intellectual property.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("CytoReason (Computational Disease Models)", "uses AI to create computational disease models that map human diseases, tissue by tissue and cell by cell, to help pharma companies shorten clinical trials and reduce the high costs of drug development. CytoReason has been able to reduce query time from two minutes to 10 seconds.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Dasa (Physician Test Result Assistance)", "the largest medical diagnostics company in Brazil, is helping physicians detect relevant findings in test results more quickly.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("DaVita (Kidney Care AI Models)", "is developing dozens of AI models to transform kidney care, including analyzing medical records, uncovering critical patient insights, and reducing errors. AI enables physicians to focus on personalized care, resulting in significant improvements in healthcare delivery.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Hackensack Meridian Health (Clinical Decision Tool)", "has developed a clinical decision-making tool that analyzes large patient data sets to identify patterns and trends. These insights can be used to help providers make better decisions about patient care.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("HCA Healthcare (Cati AI Caregiver Assistant)", "is testing Cati, a virtual AI caregiver assistant that helps to ensure continuity of care when one caregiver shift ends and another begins. The healthcare network operator is also using gen AI to improve workflows on time-consuming tasks, such as clinical documentation, so physicians and nurses can focus more on patient care.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Hemominas (Blood Donor Chatbot)", "Brazil's largest blood bank, partnered with Xertica to develop an omnichannel chatbot for donor search and scheduling, streamlining processes and enhancing efficiency. The AI solution has the potential to save half-a-million lives annually by attracting more donors and optimizing blood supply management.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Highmark Health (Intelligence System)", "is building an intelligence system equipped with AI to deliver valuable analytics and insights to healthcare workers, patients, and members, powered by Google Cloud’s Healthcare Data Engine.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("PwC (Oncology Clinic Admin Work)", "uses AI agent technology, powered by Google Cloud, to help oncology clinics to streamline administrative work so that doctors can better optimize the time they spend with patients.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Sami Saúde (Workspace for Care Providers)", "uses Gemini for Google Workspace to automate repetitive tasks, empowering care providers and accelerating access to care. This has resulted in a 13% increase in productivity, 100% of patient summaries being generated by AI, and more accurate diagnoses for improved patient outcomes.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Seattle Children's Hospital (Pathway Assistance Search)", "is pioneering a new approach to clinical care with its Pathway Assistance solution, which makes thousands of pages of clinical guidelines instantly searchable by pediatricians.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Straloo (Digital Rehabilitation Diagnostics)", "uses Gemini to innovate the diagnostic approach in its digital rehabilitation platform, helping doctors and physical therapists prescribe appropriate treatments for those suffering from knee and back pain.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Ubie (Physician Assistance Tools)", "a healthcare-focused startup founded in Japan, is using Gemini models — fine-tuned on Vertex AI — to power its AI-powered physician assistance tools.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Ufonia (Automated Clinical Consultations)", "helps physicians deliver care by using Google Cloud’s full AI stack alongside its own clinical evidence to automate routine clinical consultations with patients, transforming the experience for both patients and clinicians.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("WellSky (Documentation Time Reduction)", "is integrating Google Cloud's healthcare and Vertex AI capabilities to reduce the time spent completing documentation outside work hours.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Wipro (Healthcare Contract Adjustment)", "is supporting a national healthcare provider in using Google Cloud’s AI agent technology to develop and adjust contracts, helping to optimize and accelerate a historically complex and time-consuming task while improving accuracy.", current_sector, current_agent_type))
    
    # Data Agents
    current_agent_type = "Data Agents"
    all_entries.append(parse_and_classify_entry("Amigo Tech (Amigo Intelligence Platform)", "launched Amigo Intelligence, a platform based on Google AI technologies that automates medical processes, reduces costs, and improves the efficiency of clinics and practices. The solution includes tools like anamnesis automation, advanced exam analysis, and a medical AI chatbot, transforming healthcare management.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Apollo Hospitals (TB & Breast Cancer Screening Models)", "in India partnered with Google Health to build screening models for tuberculosis and breast cancer, helping an extremely limited population of radiologists cover more patients at risk, scaling to 3 million screenings in a matter of years.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("ARC Innovation at Sheba Medical Center (Ovarian Cancer Decisions)", "is using Google Cloud's AI tools, including Looker Studio and BigQuery ML, to create healthcare solutions that improve critical clinical decisions during the treatment of ovarian cancer.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Auransa (AI Drug Discovery Pipeline)", "an emerging clinical-stage biopharma company, has created a proprietary AI platform to derive a differentiated pipeline of novel drugs.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Autoscience (AI for Scientific Research)", "a startup building AI agents to aid in scientific research, is using Google Cloud infrastructure and resources through the Google for Startups Cloud Program as it begins to build and market its products.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Bayer (Flu Outbreak Prediction)", "built a data agent that uses gen AI in BigQuery to predict flu outbreaks. It combines Google Search trends and internal data for real-time, location-specific healthcare planning.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Bayer and Google (Early Drug Discovery TPUs)", "also announced a collaboration to drive early drug discovery that will apply AI-specialized Tensor Processing Units (TPUs) to help accelerate and scale Bayer’s quantum chemistry calculations.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Beep Saúde (Last-mile Dynamic Routing)", "the largest home health company in Brazil, implemented an AI-powered last-mile dynamic routing system with Google Maps to optimize its operations and manage a 10% cancellation volume. The company also uses AI to speed up the processing of medical orders, aiming to reduce costs and increase efficiency to boost its expansion plans in Brazil.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Bliss Health (Digital Broker Channel)", "is transforming the insurance market with a digital channel for brokers, integrated with Google Cloud and technologies like Dialogflow and Gemini Pro. The solution has reduced its service-level agreement from four hours to seconds in transactional queries, improved operational efficiency, and eliminated bureaucracy, helping to speed up business closure.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("CerebraAI (Stroke Detection)", "part of the Google for Startups Cloud AI Accelerator, is developing AI solutions that are essential in emergency medicine, including a gen AI tool for rapid stroke detection in non-contrast CT scans.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Chopo/Grupo Proa (Patient Data Integration)", "a Mexican medical diagnostics company, leverages generative AI to integrate patient and physician data, obtaining a complete view that optimizes decision-making. This initiative has enabled a considerable reduction in acquisition costs and an increase in sales.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Elanco (Animal Health Gen AI Framework)", "a leader in animal health, has implemented a gen AI framework supporting critical business processes, such as Pharmacovigilance, Customer Orders, and Clinical Insights. The framework, powered by Vertex AI and Gemini, has resulted in an estimated ROI of $1.9 million since launching last year.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Fairtility (IVF Outcome Enhancement)", "is using Google Cloud's AI capabilities to enhance IVF outcomes worldwide. By leveraging AI and machine learning within Google Cloud, Fairtility analyzes embryo images and related data to identify embryos with the highest potential for successful implantation, increasing the likelihood of pregnancy for patients undergoing IVF.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Ginkgo Bioworks (AI for Biological Engineering)", "is building a next-generation AI platform for biological engineering and biosecurity, including pioneering new AI models for biological engineering applications that are powered by Vertex AI.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Mayo Clinic (Clinical Data Search for Researchers)", "has given thousands of its scientific researchers access to 50 petabytes worth of clinical data through Vertex AI Search, accelerating information retrieval across multiple languages.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Mendel (Clinical AI for Patient Journeys)", "has built a clinical AI system designed to consolidate the longstanding silos in medical data into a knowledge base of holistic patient journeys, boosting patient recruitment for new therapies and clinical trials.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("The National Institutes of Health (NIH STRIDES)", "the U.S. government’s healthcare and research agency, uses Google Cloud as part of STRIDES, the Science and Technology Research Infrastructure for Discovery, Experimentation, and Sustainability. The initiative provides easy access to high-value NIH datasets and a wide range of Google Cloud services, including compute resources, data storage and analytics, and cutting-edge AI and ML capabilities to accelerate biomedical research.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Neomed (Cardiovascular Diagnosis Reports)", "a Brazilian healthcare startup, works in the diagnosis of cardiovascular diseases, assisting clinics and hospitals in the management of data and reports of graphical exams. Its AI-based solution reduces the time for electrocardiogram reports to around two minutes.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Nextnet (Life Sciences Research Insights)", "uses Gemini and Vertex AI to uncover novel insights and knowledge for life sciences and pharmaceutical research, enabling researchers to analyze biomedical data and identify hidden relationships in scientific literature.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Ordaōs (AI Drug Discovery GKE)", "an AI-driven drug discovery leader, relies on its cloud computing capabilities to design, process, and analyze data for millions of protein structures, notably using Google Kubernetes Engine to achieve increased flexibility and easier scalability to take on new, larger AI projects.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Probrain (Personalized Auditory Stimulation)", "offers personalized auditory stimulation training. By implementing cloud-based gen AI solutions, it’s modernized services and reduced costs by approximately 89%. For the end consumer, this also resulted in savings of almost 50%.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Red Interclinica (Hospital Data Insights)", "the Chilean hospital network, uses AI to make better decisions through data transformed into insights, as well as making medical care more accessible for its patients, while also reducing costs and generating more value for the organization.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Schrödinger (Drug Discovery Cloud GPUs)", "uses Cloud GPUs to power AI models working on advanced drug discovery.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Superluminal Medicines (Dynamic Protein Models)", "uses Google Cloud's computing power to analyze multiple protein structures and integrate them into dynamic protein models for drug discovery, allowing for a more accurate representation of protein behavior and the design of more precise drug interventions.", current_sector, current_agent_type))

    # Security Agents
    current_agent_type = "Security Agents"
    all_entries.append(parse_and_classify_entry("apree health (Zero Trust Security)", "uses Google Workspace to implement a Zero Trust security solution with granular access controls and device management, centralizing its data access and protecting sensitive patient data while quickly migrating nearly 1,000 users from its previous collaboration solution.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Pfizer (Cybersecurity Data Aggregation)", "can now aggregate cybersecurity data sources, cutting analysis times from days to seconds.", current_sector, current_agent_type))

    # --- Hospitality & Travel ---
    current_sector = "Hospitality & Travel"
    # Customer Agents
    current_agent_type = "Customer Agents"
    all_entries.append(parse_and_classify_entry("Alaska Airlines (Conversational Travel Agent)", "is developing natural language search, providing travelers with a conversational experience powered by AI that’s akin to interacting with a knowledgeable travel agent. This chatbot aims to streamline travel booking, enhance customer experience, and reinforce brand identity.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Gymshark (Personalized Fitness Experiences)", "a leading UK fitness community and gymwear brand, is using BigQuery, Looker, Dataflow, and Vertex AI to build a unified data platform that enhances customer insights and delivers personalized fitness experiences at scale.’", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("HomeToGo (AI Sunny Travel Assistant)", "a vacation-rental app, created AI Sunny, a new AI-powered travel assistant that supports guests while booking, and has plans to build it into Super AI Sunny, an end-to-end smart travel companion.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Hotelplan Suisse (Travel Expertise Chatbot)", "built a chatbot trained on the business’s travel expertise to answer customer inquiries in real-time, and, following that success, it plans to use gen AI to create travel content.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("IHG Hotels & Resorts (Vacation Planning Chatbot)", "is building a gen AI-powered chatbot to help guests easily plan their next vacation directly in the IHG One Rewards mobile app.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Mustard (Personalized Sports Coaching App)", "uses proprietary computer vision and AI technology to unlock exceptional, personalized coaching experiences for every golfer and baseball pitcher who wants to level up, all with the ease of a straightforward mobile app.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Mystifly (Mystic Chatbot for Travel)", "is a Singapore-based travel tech company that has developed Mystic, a chatbot built on Google Cloud's conversational and generative AI platforms; it offers users self-serve options that reduce the need for direct agent support, improving efficiency and customer satisfaction.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("The Papa John’s (Predictive Ordering & Chatbot)", "pizza chain is using BigQuery, Vertex AI, and Gemini models to build predictive tools that can better anticipate customers orders in the app, as well as an enhanced loyalty program and more personalized marketing offers. There are also plans to build an AI-powered chatbot to help handle orders.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Priceline (Trip Intelligence AI Tools)", "Trip Intelligence suite features one of the travel industry’s most comprehensive array of AI tools, including more than 30 new features to dramatically streamline the travel planning and booking process.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Sabre Travel AI (Personalized Travel Offers)", "has developed an AI agent that personalizes offers, optimizes revenue management, and streamlines operations for travel companies; this has led to improved customer experiences and increased revenue while fostering growth for Sabre's partners.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Six Flags (Digital Assistant for Park Planning)", "theme parks has built an industry-first digital assistant who can answer guests’ questions and help them plan their whole day. Six Flags will also apply Google Cloud's capabilities in AI, analytics, and infrastructure to offer improved operations, personalization, and customer experiences across Six Flags' diverse portfolio of parks.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Studiosus Reisen (Real-time Reservations)", "a German travel company, worked with happtiq and Solid Cloud to migrate its 40-year old on-premise system and SAP workloads to Google Cloud to enable real-time reservations, increasing its conversion rates by 40%.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Technogym (Technogym Coach AI Trainer)", "leverages Vertex AI and Model Garden to power Technogym Coach, an AI-driven virtual trainer that creates hyper-personalized fitness programs. This increased user engagement and motivation, improved fitness outcomes, and delivered a more personalized and effective training experience.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("trivago (Smart AI Search for Hotels)", "new “Smart AI Search” is an advanced free-text search functionality, powered by Vertex AI Search, that allows users to search for hotels using natural language, making it easier and more personalized to find the ideal accommodations.", current_sector, current_agent_type))

    # Employee Agents
    current_agent_type = "Employee Agents"
    all_entries.append(parse_and_classify_entry("Attache (Workspace for Guest Stays)", "leverages Gemini for Google Workspace to streamline various tasks, such as analyzing historical data, which helped achieve an 80% reduction in calls from new arrivals, leading to happier customers and smoother stays.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("loveholidays (Customer Service Cost Savings)", "saved 20% of their customer service cost per year after deploying Customer Engagement Suite.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Sweets and Meats BBQ (Event Finding in Sheets)", "finds local events for its food trucks with help from Gemini in Sheets, easily generating a weekly schedule in seconds.", current_sector, current_agent_type))

    # Creative Agents
    current_agent_type = "Creative Agents"
    all_entries.append(parse_and_classify_entry("Curb Free with Cory Lee (Content Brainstorming)", "a popular \"wheelchair travel site,\" shares accessible travel guides, and brainstorms new content ideas with Gemini in Docs to keep giving readers fresh and valuable info.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Japan Airlines (AI Video Tourism Spots)", "partnered with Pencil, a generative AI platform, to create new tourism spots that will broadcast in-flight and via YouTube Ads; JAL has been working with Jellyfish and Pencil, both owned by the Brandtech Group, to experiment with AI video using Google’s Veo 2.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Radisson Hotel Group (Personalized Advertising)", "personalized its advertising at scale, in collaboration with Accenture, using Vertex AI and Gemini models. By training them on extensive datasets stored in BigQuery, its ad teams saw productivity rise around 50% while revenue increased from AI-powered campaigns by more than 20%.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Three Fold Noodles + Dumpling (Social Media Posts)", "drafts social media posts with Gemini in Docs to stay active online without compromising on quality time in the kitchen.", current_sector, current_agent_type))

    # Data Agents
    current_agent_type = "Data Agents"
    all_entries.append(parse_and_classify_entry("BrushBuck Wildlife Tours (Animal Movement Tracking)", "tracks seasonal animal movements with help from Gemini in Sheets so every visitor has a chance to marvel at Wyoming's wildlife.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Fitz's Bottling Company (Inventory Formatting)", "has been selling root beer since 1947 and now uses Gemini in Sheets to quickly pull together and format inventory information, helping them continue the success of the world's first root beer microbrewery.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Hog Island Oyster (Sales Analysis)", "simplifies sales analysis with Gemini in Sheets, creating reports on oyster sales by type, size, and quantity with a single prompt.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Latam Airlines (Data Management & Governance)", "is leveraging Google Cloud AI to automate data management and governance, enhancing customer experience. By using generative AI, the airline optimized processes like table classification and metadata management, resulting in reduced time and costs.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Studiosus Reisen (Security Alert Filtering)", "worked with happtiq to use Vertex AI to build a custom AI model to automatically classify and filter security alerts, reducing the manual effort to active security concerns for travelers by 75%", current_sector, current_agent_type))

    # --- Manufacturing, Industrial & Electronics ---
    current_sector = "Manufacturing, Industrial & Electronics"
    # Customer Agents
    current_agent_type = "Customer Agents"
    all_entries.append(parse_and_classify_entry("Motorola (Moto AI Smartphone Features)", "Moto AI leverages Gemini and Imagen to help smartphone users unlock new levels of productivity, creativity, and enjoyment with features such as conversation summaries, notification digests, image creation, and natural language search — all with reliable responses grounded in Google Search.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Oppo/OnePlus (Gemini in Phones)", "is incorporating Gemini models and Google Cloud AI into its phones to deliver innovative customer experiences, including news and audio recording summaries, AI toolbox, and more.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Samsung (Galaxy S24 AI Features)", "is deploying Gemini Pro and Imagen 2 to its Galaxy S24 smartphones so users can take advantage of amazing features like text summarization, organization, and magical image editing.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Samsung (Ballie Home Robot)", "is using Google’s generative AI technology for Ballie — its exciting new home companion robot. Ballie will be able to engage in natural, conversational interactions to help users manage home environments, including adjusting lighting, greeting people at the door, personalizing schedules, setting reminders, and more.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("ScottsMiracle-Gro (Gardening Advice Agent)", "built an AI agent on Vertex AI to provide tailored gardening advice and product recommendations for consumers.", current_sector, current_agent_type))

    # Employee Agents
    current_agent_type = "Employee Agents"
    all_entries.append(parse_and_classify_entry("AES (Energy Safety Audits)", "a global energy company, uses gen AI agents built with Vertex AI and Anthropic’s Claude models to automate and streamline its energy safety audits. This has resulted in a 99% reduction in audit costs, a time reduction from 14 days to one hour, and an increase of 10-20% in accuracy.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Copel (SAP ERP Natural Language Query)", "a major Brazilian electric utility company, has developed an AI agent with Gemini Pro 1.5 that interacts with the company's on-premises SAP ERP system, allowing employees to ask a variety of questions using natural language.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Enpal (Solar Panel Sales Automation)", "working with Google Cloud partner dida, automated part of its solar panels sales process. By automating the generation of quotes for prospective solar panel customers, including assessing roof size and the number of panels required, Enpal reduced the time required by 87.5%, from 120 minutes to 15 minutes.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Honeywell (Product Lifecycle Management)", "an almost 120-year-old manufacturing company, has already incorporated Gemini into building automation products and is now applying AI to transform how its engineers manage product lifecycles.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Hydro Ottawa (Workspace for Employee Efficiency)", "uses Gemini for Google Workspace to help employees automate daily tasks and collaborate more efficiently. This has resulted in better and more cost-effective services for its customers.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Plenitude (Customer Onboarding Automation)", "leverages Google Cloud's Optical Character Recognition and Gemini Flash models to automate customer onboarding, extracting data from energy bills and verifying IDs with Document AI. This has resulted in faster onboarding, reduced fraud, and significant time savings in ID verification.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Robert Bosch (Marketing Process Streamlining)", "the world's largest automotive supplier, revolutionizes marketing through gen AI-powered solutions, streamlining processes, optimizing resource allocation, and maximizing efficiency across 100+ decentralized departments.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Suzano (SAP Data Query with Natural Language)", "the world's largest pulp manufacturer and a leader in sustainable bioeconomics, worked with Google Cloud and Sauter to develop an AI agent powered by Gemini Pro to translate natural language questions into SQL code to query SAP Materials data on BigQuery. This has resulted in a 95% reduction in the time required for queries among the 50,000 employees using the data.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Trimble (Workspace for Productivity)", "a maker of software and hardware for products ranging from satellites to drones and monitors of many kinds, is leveraging Gemini for Google Workspace's advanced capabilities so employees can enhance productivity; the company has streamlined workflows, including efficient document search, concise summaries, and code generation, all within a secure and collaborative environment.", current_sector, current_agent_type))

    # Creative Agents
    current_agent_type = "Creative Agents"
    all_entries.append(parse_and_classify_entry("Ace Sign Co. (Design Mock-ups)", "uses Gemini in Slides to mock-up designs in seconds, not hours, giving them more time and flexibility to dream big on each design — as they’ve been doing since 1887.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Cottrell Boatbuilding (Social Post Writing)", "writes high-quality social posts with help from Gemini in Docs, winning back time to focus on the craft they've honed for 40+ years.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Empresas Lipigas (Proposal Creation for Bulk Clients)", "a leading gas sales and distribution company in Chile, is using Google Cloud's AI to build a cloud-based model that will streamline the creation of proposals for their bulk clients, resulting in faster response times and taking into account the specific needs of each project and current regulations.", current_sector, current_agent_type))

    # Code Agents
    current_agent_type = "Code Agents"
    all_entries.append(parse_and_classify_entry("Broadcom (Enterprise Gemini Code Assist)", "a leading provider of semiconductors and security solutions, is using an enterprise version of Gemini Code Assist, built for teams of developers and agents and able to understand a company’s code base, standards, and conventions.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Far Eastern New Century (FENC) (AI Assistants for Ops Efficiency)", "worked with Microfusion to streamline cross-border operations using Google Cloud VMware Engine to deliver 99% system availability and 20% higher scalability and build AI assistants with Vertex AI and Gemini that have increased FENC’s operational efficiency by 30% to 40%.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Sumitomo Rubber Industries (Cloud Workstations with Code Assist)", "worked with Kyocera to deploy Cloud Workstations, which now natively includes gen AI capabilities through Gemini Code Assist, to drastically reduce development tasks from months to minutes — accelerating software development and time to market.", current_sector, current_agent_type))

    # Data Agents
    current_agent_type = "Data Agents"
    all_entries.append(parse_and_classify_entry("Bayer Crop Science (Climate FieldView Platform)", "has developed Climate FieldView, a comprehensive agricultural platform with more than 250 layers of data and billions of data points; AI-powered recommendations allow farmers to design and monitor their fields for greater yields and efficient fertilization, with the added benefit of reduced carbon emissions.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Capital Energy (AI for Energy Management)", "a 100% renewable electricity company, is using Vertex AI and Fortinet technologies to apply AI to energy management. The company has accelerated decision-making, maximized the value of its assets, and reduced operating costs — all while strengthening enterprise security — to take sustainable energy to new heights.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Casa Dos Ventos (Wind Energy Document & Image Analysis)", "a Brazilian wind energy company, is using Vertex AI to automate processes like document analysis and image data extraction, as well as accelerating information searches in large document repositories and providing its employees with a platform that provides fast and relevant answers when consulted. In addition, Casa dos Ventos has automated the creation of project instruction files.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("COI Energy (Equitable Green Energy Capacity Identification)", "is facilitating equitable green energy by leveraging advanced AI technologies to identify underutilized energy capacity, what it calls “kW for Good,” which businesses can then provide to low-income households. This offers businesses tax deductions while creating a more climate-friendly economy for all.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Elia Group (eCO2grid for CO2 Intensity Forecasting)", "an energy transmission provider in Northern Europe, is using Vertex AI to build an \"eCO2grid\" that measures and forecasts the CO2 intensity of its electricity generation, with the aim of reducing greenhouse emissions.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Guardian Bikes (Factory Data Query in Sheets)", "specializes in kid's bikes with safer brakes, and uses Gemini in Sheets to easily query and organize the massive amounts of data its factory produces.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Ingrid Capacity (Energy Market Forecasting)", "an alternative energy supplier, uses AI combined with scenario modeling to forecast energy markets and infrastructure build-up, improving the precision of its predictions. This AI-powered forecasting has increased the total output of its asset trading operations.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Physical Intelligence (General-purpose AI for Robots)", "a startup developing general-purpose AI for robots, recently partnered with Google Cloud to support its foundational model development, using Google Cloud’s secure and scalable AI infrastructure.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Solestial (Solar Cell Production Tracking)", "optimizes production of their space-stable solar cells by tracking manufacturing data with Gemini in Sheets — bringing the future of energy a step closer to liftoff.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Southern California Edison (Geospatial AI for Infrastructure)", "is using geospatial capabilities and AI to improve infrastructure planning and monitoring, generate new insights, and create regional resilience for communities facing climate challenges today and tomorrow.", current_sector, current_agent_type))
    all_entries.append(parse_and_classify_entry("Zebra Technologies (On-device AI for Mobile Computing)", "maker of industry-specialized mobile computing devices, is using Gemini to deliver on-device AI capabilities that drive better work and customer experiences, including advanced analytics and AI-driven insights for retail workers so they can make in-the-moment decisions to prevent low stock or inventory shrinkage.", current_sector, current_agent_type))
    
    # Security Agents
    current_agent_type = "Security Agents"
    all_entries.append(parse_and_classify_entry("TSMC (Mission-critical Workload Data Protection)", "one of the world’s leading chip producers, protects its data for mission-critical workloads.", current_sector, current_agent_type)) # Description is vague, assuming security focus
    all_entries.append(parse_and_classify_entry("Vestas (AI for Wind Turbine Security)", "a global leader in sustainable energy solutions, is using AI to enhance the security of its wind turbines, ensuring they are protected against potential threats and vulnerabilities.", current_sector, current_agent_type)) # Description is vague, assuming security focus

    if not all_entries: # Fallback if parsing somehow fails or is empty
        # Use the small sample from before as a absolute fallback
        return pd.DataFrame([
            {
                "Organization": "MercedesBenz (Nav)", "Sector": "Automotive & Logistics", "Agent_Type_Text": "Customer Agents",
                "Description": "Conversational search and navigation in cars.",
                "Kind_of_Agent": "Chatbot / LLM", "Economic_Value": 3, "Proximity_NCF": 3,
                "Full_Description_Tooltip": "MercedesBenz is providing conversational search and navigation in the new CLA series cars using Google Cloud’s industry-tuned Automotive AI Agent."
            },
            {
                "Organization": "Nuro", "Sector": "Automotive & Logistics", "Agent_Type_Text": "Data Agents",
                "Description": "Vector search for autonomous vehicles to classify objects.",
                "Kind_of_Agent": "Robotics agent (real-world)", "Economic_Value": 4, "Proximity_NCF": 4,
                "Full_Description_Tooltip": "Nuro, an autonomous driving company, uses vector search in AlloyDB to enable their vehicles to accurately classify objects encountered on the road."
            },
             {
                "Organization": "Airwallex", "Sector": "Financial Services", "Agent_Type_Text": "Security Agents",
                "Description": "Detects and manages fraud in real time.",
                "Kind_of_Agent": "Execution agent (computer)", "Economic_Value": 4, "Proximity_NCF": 4,
                "Full_Description_Tooltip": "Airwallex... detects and manages fraud in real time in a scalable, always-available environment..."
            },
        ])

    return pd.DataFrame(all_entries)


def get_color_map():
    """Returns a color map for the 'Kind_of_Agent'."""
    return {
        'Chatbot / LLM': 'blue',
        'Info-retrieval agent (computer)': 'green',
        'Execution agent (computer)': 'red',
        'Robotics agent (real-world)': 'purple'
    }

# %% Main App Logic
def run_ai_explorer_app():
    st.set_page_config(layout="wide", page_title="AI Use Case Explorer")
    st.title("AI Use Case Explorer (Comprehensive Data Attempt)")
    st.markdown("""
    This application visualizes AI use cases based on an attempt to parse and classify **all** entries from the provided text.
    Due to the automated nature of this extensive parsing, variations in classification or scoring accuracy may exist.
    The visualizations help explore AI integration by function, sector, and consequentiality, relevant to your work on Societal Resilience of Frontier AI.
    """)

    df_full = load_all_data()
    
    if df_full.empty:
        st.error("No data was loaded. Please check the data source and parsing logic.")
        return

    color_map = get_color_map()

    # Define the order for categorical axes
    sectors_list = sorted(df_full['Sector'].unique())
    kind_of_agent_list = ['Chatbot / LLM', 'Info-retrieval agent (computer)', 'Execution agent (computer)', 'Robotics agent (real-world)']
    agent_type_text_list = ['Customer Agents', 'Employee Agents', 'Creative Agents', 'Code Agents', 'Data Agents', 'Security Agents']

    # Ensure columns are categorical with the defined order for consistent plotting
    df_full['Kind_of_Agent'] = pd.Categorical(df_full['Kind_of_Agent'], categories=kind_of_agent_list, ordered=True)
    df_full['Sector'] = pd.Categorical(df_full['Sector'], categories=sectors_list, ordered=True)
    df_full['Agent_Type_Text'] = pd.Categorical(df_full['Agent_Type_Text'], categories=agent_type_text_list, ordered=True)

    # --- Sidebar for Filters ---
    st.sidebar.header("Filters")
    selected_sector_fig1 = st.sidebar.selectbox(
        "Filter by Sector for 'Function Plot':",
        options=["All Sectors"] + sectors_list,
        key="sector_filter_fig1"
    )

    # --- Figure 1: AI Use Cases by Function (and Sector/Kind of Agent) ---
    st.header("AI Use Cases: Function Plot")
    
    df_fig1_display = df_full.copy()
    y_axis_fig1_label = "Sector"
    plot_title_fig1 = "AI Agents by Function Across All Sectors (Color: Kind of Agent)"
    y_column_fig1 = 'Sector'
    y_axis_order_fig1 = sectors_list


    if selected_sector_fig1 != "All Sectors":
        df_fig1_display = df_full[df_full['Sector'] == selected_sector_fig1].copy()
        if not df_fig1_display.empty: # Check if filter results in empty dataframe
            y_axis_fig1_label = "Kind of Agent"
            y_column_fig1 = 'Kind_of_Agent'
            y_axis_order_fig1 = kind_of_agent_list
            plot_title_fig1 = f"AI Agents by Function for {selected_sector_fig1} (Color: Kind of Agent)"
        else: # If filter is empty, revert to all data to avoid error
            st.warning(f"No data found for sector '{selected_sector_fig1}' in the 'Function Plot'. Displaying all sectors instead.")
            df_fig1_display = df_full.copy() # Revert to full data
            selected_sector_fig1 = "All Sectors" # Reset filter display text
            # Y-axis remains Sector for all data view
            y_axis_fig1_label = "Sector"
            y_column_fig1 = 'Sector'
            y_axis_order_fig1 = sectors_list
            plot_title_fig1 = "AI Agents by Function Across All Sectors (Color: Kind of Agent)"


    st.markdown(f"Displaying AI agents by **Function (X-axis)**. Color indicates the **Kind of Agent**. Y-axis shows **{y_axis_fig1_label}**.")

    if not df_fig1_display.empty:
        fig1 = px.scatter(
            df_fig1_display,
            x='Agent_Type_Text', 
            y=y_column_fig1,    
            color='Kind_of_Agent',
            color_discrete_map=color_map,
            hover_name='Organization',
            hover_data={ # Customize hover data for clarity
                'Sector': True,
                'Agent_Type_Text': False, # X-axis, already clear
                y_column_fig1: False, # Y-axis, already clear
                'Kind_of_Agent': False, # Color, already clear
                'Full_Description_Tooltip': False, # Shown explicitly below
                'Description':True,
            },
            custom_data=['Full_Description_Tooltip', 'Organization', 'Sector', 'Kind_of_Agent', 'Description'],
            category_orders={
                "Agent_Type_Text": agent_type_text_list,
                 y_column_fig1: y_axis_order_fig1,
                "Kind_of_Agent": kind_of_agent_list
            },
            title=plot_title_fig1
        )

        fig1.update_traces(
            marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')),
            hovertemplate=("<b>%{hovertext}</b><br>" + # Organization from hover_name
                           "Sector: %{customdata[2]}<br>" + 
                           "Function: %{x}<br>" +
                           f"{y_axis_fig1_label}: %{{y}}<br>" + 
                           "Kind of Agent: %{customdata[3]}<br>" +
                           "<i>Desc: %{customdata[4]}</i><br>" +
                           "<extra></extra>") 
        )

        fig1.update_layout(
            height=700, # Increased height for potentially more data points
            xaxis_title="Function (Original Agent Type)",
            yaxis_title=y_axis_fig1_label,
            legend_title="Kind of Agent"
        )
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No data to display for the selected criteria in the 'Function Plot'.")
    
    st.markdown("""
    **Note on Clickability**: Hover tooltips provide details. For interactive filtering or detail views triggered by clicks,
    more advanced Streamlit features or libraries like `streamlit-plotly-events` would be used.
    """)

    # --- Figure 2: Consequentiality ---
    st.header("AI Use Cases: Consequentiality Analysis")
    st.markdown("""
    Visualizing use cases by estimated **Economic Value Created** and **Proximity to National Critical Functions**.
    Scales are 1 (Low) to 5 (High). Hover for details. This plot always shows all data.
    """)
    
    if not df_full.empty:
        fig2 = px.scatter(
            df_full, 
            x='Economic_Value',
            y='Proximity_NCF',
            color='Kind_of_Agent',
            color_discrete_map=color_map,
            size='Economic_Value', 
            hover_name='Organization',
             hover_data={ # Customize hover data
                'Sector': True,
                'Agent_Type_Text': True, 
                'Kind_of_Agent': False, # From color
                'Description':True,
                'Economic_Value': False, # From X
                'Proximity_NCF': False, # From Y
                'Full_Description_Tooltip': False, # Shown explicitly
            },
            custom_data=['Full_Description_Tooltip', 'Organization', 'Sector', 'Agent_Type_Text', 'Description', 'Kind_of_Agent'],
            title="Consequentiality of AI Use Cases (All Sectors)"
        )
        
        fig2.update_traces(
            hovertemplate=("<b>%{hovertext}</b><br>" + 
                           "Sector: %{customdata[2]}<br>" + 
                           "Function: %{customdata[3]}<br>" + 
                           "Kind of Agent: %{customdata[5]}<br>" + 
                           "Economic Value: %{x}<br>" +
                           "Proximity to NCF: %{y}<br>" +
                           "<i>Desc: %{customdata[4]}</i><br>" +
                           "<extra></extra>")
        )

        fig2.update_layout(
            height=700, # Increased height
            xaxis_title="Economic Value Created (1-Low to 5-High)",
            yaxis_title="Proximity to National Critical Functions (1-Low to 5-High)",
            legend_title="Kind of Agent",
            xaxis=dict(tickmode='linear', tick0=1, dtick=1, range=[0.5, 5.5]),
            yaxis=dict(tickmode='linear', tick0=1, dtick=1, range=[0.5, 5.5])
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data to display for the 'Consequentiality Plot'.")


    # Displaying sample data table for reference
    st.subheader("Data Table (Excerpt of Processed Entries)")
    st.dataframe(df_full[['Organization', 'Sector', 'Agent_Type_Text', 'Kind_of_Agent', 'Economic_Value', 'Proximity_NCF', 'Description']].head(50)) # Show head for brevity
    st.markdown(f"Total entries processed and displayed: {len(df_full)}")


# %% Execution
if __name__ == "__main__":
    run_ai_explorer_app()
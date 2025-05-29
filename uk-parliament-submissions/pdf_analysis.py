def analyze_paragraph_batch(self, paragraphs: List[Dict], question_set: Dict) -> Dict:
        """Analyze a batch of paragraphs using Claude via model_completions.py"""
        # Prepare context
        context = "\n\n".join([
            f"[Source: {p['source']}, Page {p['page']}]\n{p['text']}"
            for p in paragraphs
        ])
        
        # System prompt
        system_prompt = """You are analyzing UK Parliament evidence on AI risks in finance.
        
Focus ONLY on content about AI agents or general-purpose AI as defined:
AI agent = Software program that can interact with its environment, collect data, 
and use the data for executing self-determined actions that impact the environment, 
to meet predetermined, underspecified goals.

Return your response as valid JSON only."""
        
        # User message
        user_message = f"""Analyze these paragraphs for the following questions:
{json.dumps(question_set, indent=2)}

For EACH relevant finding:
1. Provide the EXACT quote from the document
2. Include source document and page number
3. Categorize by question number

Context:
{context}

Returnimport os
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple
import PyPDF2
from collections import defaultdict
import re
from datetime import datetime
import sys

# Import the model_completions script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from model_completions import get_completion

class AIFinanceRiskAnalyzer:
    """Analyzes PDFs for AI agent risks in finance using Claude via model_completions.py"""
    
    def __init__(self, pdf_folder: str):
        self.pdf_folder = Path(pdf_folder)
        self.results = defaultdict(list)
        self.ai_agent_keywords = [
            "AI agent", "AI agents", "autonomous AI", "general-purpose AI",
            "GPAI", "frontier AI", "computer-use", "self-determined",
            "autonomous system", "AI execution", "AI tooling"
        ]
        
    def extract_full_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract all text from PDF for initial filtering"""
        full_text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    full_text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
        return full_text
        
    def pdf_contains_required_terms(self, pdf_path: Path) -> bool:
        """Check if PDF contains both 'agent' and 'stability'"""
        full_text = self.extract_full_text_from_pdf(pdf_path).lower()
        contains_agent = 'agent' in full_text
        contains_stability = 'stability' in full_text
        return contains_agent and contains_stability
        
    def extract_paragraphs_from_pdf(self, pdf_path: Path) -> List[Dict]:
        """Extract text from PDF, returning paragraphs with metadata"""
        paragraphs = []
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    # Split into paragraphs
                    paras = text.split('\n\n')
                    for para in paras:
                        if len(para.strip()) > 50:  # Filter short fragments
                            paragraphs.append({
                                'text': para.strip(),
                                'source': pdf_path.name,
                                'page': page_num + 1
                            })
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
        return paragraphs
    
    def is_relevant_paragraph(self, text: str) -> bool:
        """Check if paragraph mentions AI agents or general-purpose AI"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.ai_agent_keywords)
    
    def analyze_paragraph_batch(self, paragraphs: List[Dict], question_set: Dict) -> Dict:
        """Analyze a batch of paragraphs using Claude via model_completions.py"""
        # Prepare context
        context = "\n\n".join([
            f"[Source: {p['source']}, Page {p['page']}]\n{p['text']}"
            for p in paragraphs
        ])
        
        prompt = f"""You are analyzing UK Parliament evidence on AI risks in finance.
        
Focus ONLY on content about AI agents or general-purpose AI as defined:
AI agent = Software program that can interact with its environment, collect data, 
and use the data for executing self-determined actions that impact the environment, 
to meet predetermined, underspecified goals.

Analyze these paragraphs for the following questions:
{json.dumps(question_set, indent=2)}

For EACH relevant finding:
1. Provide the EXACT quote from the document
2. Include source document and page number
3. Categorize by question number

Context:
{context}

Return response as JSON with structure:
{{
    "findings": [
        {{
            "question_num": 1,
            "quote": "exact quote here",
            "source": "filename.pdf",
            "page": 1,
            "summary": "brief summary"
        }}
    ]
}}"""
        
        try:
            # Use model_completions.py function
            response = get_completion(
                prompt=prompt,
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0
            )
            
            # Parse JSON response
            # Extract JSON from response if it's wrapped in other text
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"findings": []}
            return result
            
        except Exception as e:
            print(f"Error in Claude analysis: {e}")
            return {"findings": []}
    
    def process_pdfs(self):
        """Main processing loop"""
        questions = {
            1: "Which scenarios are described as likely risks to financial stability from AI agents?",
            2: "What data sources and evidence would we need to track and measure these risks?",
            3: "What are the most consequential general-purpose AI capabilities & tools currently in finance?",
            4: "What AI capabilities are expected in finance over the next ten years?",
            5: "What are the most significant vulnerabilities and systems affected?"
        }
        
        # First, filter PDFs that contain both 'agent' and 'stability'
        print("Filtering PDFs for 'agent' AND 'stability'...")
        pdf_files = list(self.pdf_folder.glob("*.pdf"))
        relevant_pdfs = []
        
        for pdf_path in pdf_files:
            if self.pdf_contains_required_terms(pdf_path):
                relevant_pdfs.append(pdf_path)
                print(f"✓ Relevant: {pdf_path.name}")
            else:
                print(f"✗ Skipping: {pdf_path.name} (missing required terms)")
        
        print(f"\nFound {len(relevant_pdfs)} relevant PDFs out of {len(pdf_files)} total")
        
        # Collect all relevant paragraphs from filtered PDFs
        all_relevant_paragraphs = []
        
        print("\nExtracting relevant paragraphs from filtered PDFs...")
        for pdf_path in relevant_pdfs:
            print(f"Processing: {pdf_path.name}")
            paragraphs = self.extract_paragraphs_from_pdf(pdf_path)
            
            # Filter for relevant paragraphs (AI agent mentions)
            relevant = [p for p in paragraphs if self.is_relevant_paragraph(p['text'])]
            all_relevant_paragraphs.extend(relevant)
        
        print(f"\nFound {len(all_relevant_paragraphs)} relevant paragraphs")
        
        # Process in batches to respect context window
        batch_size = 10  # Adjust based on paragraph length
        
        for i in range(0, len(all_relevant_paragraphs), batch_size):
            batch = all_relevant_paragraphs[i:i+batch_size]
            print(f"Analyzing batch {i//batch_size + 1}/{(len(all_relevant_paragraphs)-1)//batch_size + 1}")
            
            results = self.analyze_paragraph_batch(batch, questions)
            
            # Store results by question
            for finding in results.get('findings', []):
                self.results[finding['question_num']].append(finding)
            
            # Rate limiting
            time.sleep(1)
    
    def cluster_and_summarize(self):
        """Cluster findings by theme and create summaries"""
        clustered_results = {}
        
        for question_num, findings in self.results.items():
            if not findings:
                continue
                
            # System prompt
            system_prompt = "You are a research analyst specializing in AI risks in finance. Return your response as valid JSON only."
            
            # User message
            user_message = f"""Group these findings into thematic clusters and provide a summary for each cluster.

Findings for Question {question_num}:
{json.dumps(findings, indent=2)}

Return as JSON:
{{
    "clusters": [
        {{
            "theme": "cluster theme",
            "summary": "comprehensive summary",
            "finding_indices": [0, 1, 2],
            "key_quotes": ["most important quote 1", "quote 2"]
        }}
    ]
}}"""
            
            try:
                # Prepare conversation history
                conversation_history = [{"user": user_message}]
                
                response, token_usage = get_claude_completion(
                    system_prompt=system_prompt,
                    conversation_history=conversation_history,
                    anthropic_client=self.anthropic_client,
                    max_tokens=2000,
                    temperature=0
                )
                
                if response:
                    # Extract JSON from response
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        clustered_results[question_num] = json.loads(json_match.group())
                
            except Exception as e:
                print(f"Error clustering question {question_num}: {e}")
        
        return clustered_results
    
    def generate_report(self):
        """Generate final analysis report"""
        clustered = self.cluster_and_summarize()
        
        # Count relevant PDFs
        pdf_files = list(self.pdf_folder.glob("*.pdf"))
        relevant_pdfs = [p for p in pdf_files if self.pdf_contains_required_terms(p)]
        
        report = {
            "analysis_date": datetime.now().isoformat(),
            "total_documents": len(pdf_files),
            "relevant_documents": len(relevant_pdfs),
            "total_findings": sum(len(findings) for findings in self.results.values()),
            "filter_criteria": "PDFs containing both 'agent' AND 'stability'",
            "questions": {}
        }
        
        for q_num, clusters in clustered.items():
            report["questions"][q_num] = {
                "clusters": clusters,
                "raw_findings": self.results[q_num]
            }
        
        # Save report
        with open('ai_finance_risk_analysis.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown summary
        self.generate_markdown_summary(report)
        
        return report
    
    def generate_markdown_summary(self, report: Dict):
        """Create a readable markdown summary"""
        md_content = f"""# AI Agent Risks in Finance - Analysis Report
Generated: {report['analysis_date']}
Total Documents: {report['total_documents']}
Documents Analyzed (containing 'agent' AND 'stability'): {report['relevant_documents']}
Total Relevant Findings: {report['total_findings']}

## Executive Summary

This analysis reviewed UK Parliament evidence submissions to identify risks from AI agents 
and general-purpose AI systems in finance, focusing on scenarios that could lead to 
financial instability comparable to the 2008 crisis within the next 3 years.

Filter applied: Only analyzed PDFs containing both 'agent' and 'stability' terms.

"""
        
        question_titles = {
            1: "Likely Risk Scenarios",
            2: "Data Sources for Risk Tracking",
            3: "Current AI Capabilities in Finance",
            4: "Future AI Capabilities (10 years)",
            5: "Vulnerabilities and Affected Systems"
        }
        
        for q_num in sorted(report['questions'].keys()):
            q_data = report['questions'][q_num]
            md_content += f"\n## Question {q_num}: {question_titles.get(int(q_num), 'Unknown')}\n\n"
            
            if 'clusters' in q_data and q_data['clusters'].get('clusters'):
                for cluster in q_data['clusters']['clusters']:
                    md_content += f"### {cluster['theme']}\n\n"
                    md_content += f"{cluster['summary']}\n\n"
                    md_content += "**Key Quotes:**\n"
                    for quote in cluster.get('key_quotes', []):
                        md_content += f"- \"{quote}\"\n"
                    md_content += "\n"
        
        with open('ai_finance_risk_summary.md', 'w') as f:
            f.write(md_content)


# Usage example
if __name__ == "__main__":
    # Configuration
    PDF_FOLDER = "2025-05-UKParliament-Evidence"
    API_KEY = os.getenv("ANTHROPIC_API_KEY")  # Get from environment or specify directly
    
    # Run analysis
    analyzer = AIFinanceRiskAnalyzer(PDF_FOLDER, API_KEY)
    
    print("Starting AI Finance Risk Analysis...")
    print("=" * 50)
    
    # Process all PDFs
    analyzer.process_pdfs()
    
    # Generate final report
    print("\nGenerating final report...")
    report = analyzer.generate_report()
    
    print("\nAnalysis complete!")
    print(f"Results saved to:")
    print("- ai_finance_risk_analysis.json (full data)")
    print("- ai_finance_risk_summary.md (readable summary)")
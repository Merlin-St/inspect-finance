# %%
from inspect_ai.analysis.beta import evals_df, samples_df, messages_df
import pandas as pd

# Get all evaluation data without filtering
evals = evals_df("logs")
samples = samples_df("logs")
all_messages = messages_df("logs")

# Print available data stats
print(f"Found {len(evals)} evaluations")
print(f"Found {len(samples)} samples")
print(f"Found {len(all_messages)} messages")

# Extract system prompts
system_prompts = all_messages[all_messages['role'] == 'system']
if not system_prompts.empty:
    print("\nSYSTEM PROMPT:")
    print(system_prompts['content'].iloc[0])
    print("-" * 80)

# Group messages by sample_id
sample_groups = {}
for _, msg in all_messages.iterrows():
    if msg['sample_id'] not in sample_groups:
        sample_groups[msg['sample_id']] = []
    sample_groups[msg['sample_id']].append(msg)

# Analyze the first 3 samples
print("\nSAMPLE ANALYSIS:")
displayed = 0
for sample_id, sample_data in samples.iterrows():
    if displayed >= 3:
        break
        
    # Skip samples without required data
    if 'input' not in sample_data or pd.isna(sample_data['input']):
        continue
        
    # Get messages for this sample
    messages = sample_groups.get(sample_data['sample_id'], [])
    
    # Extract user question
    user_msgs = [msg for msg in messages if msg['role'] == 'user']
    question = user_msgs[0]['content'] if user_msgs else sample_data.get('input', 'No question found')
    
    # Extract assistant's response
    assistant_msgs = [msg for msg in messages if msg['role'] == 'assistant']
    response = None
    for msg in assistant_msgs:
        if 'content' in msg and pd.notna(msg['content']) and msg['content']:
            response = msg['content']
            break
    
    # Extract target answer and score
    target = sample_data.get('target', 'No target found')
    score = sample_data.get('score_model_graded_fact', 'No score found')
    
    # Display sample information
    print(f"\nSAMPLE #{displayed+1}:")
    print(f"Question: {question}")
    print(f"Target: {target}")
    print(f"Model Response: {response if response else 'No response found'}")
    print(f"Score: {score}")
    print("-" * 80)
    
    displayed += 1

# If we couldn't find model responses in the messages, try direct log access
if displayed == 0:
    import json
    import glob
    
    print("\nAttempting to read responses directly from log files:")
    log_files = glob.glob("logs/*.eval")
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                log_data = json.load(f)
                
                if 'results' in log_data and isinstance(log_data['results'], list):
                    for i, result in enumerate(log_data['results'][:3]):
                        print(f"\nSAMPLE #{i+1} from {log_file}:")
                        print(f"Question: {result.get('sample', {}).get('input', 'N/A')}")
                        print(f"Target: {result.get('sample', {}).get('target', 'N/A')}")
                        print(f"Response: {result.get('response', 'N/A')}")
                        print(f"Score: {result.get('score', 'N/A')}")
                        print("-" * 80)
                    
                    # If we found results, don't check other log files
                    if log_data['results']:
                        break
        except Exception as e:
            print(f"Error reading {log_file}: {e}")
# %%

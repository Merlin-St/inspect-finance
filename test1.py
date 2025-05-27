# %%
from inspect_ai import Task, task
from inspect_ai.dataset import example_dataset
from inspect_ai.scorer import model_graded_fact
from inspect_ai.solver import generate, system_message
from anthropic import Anthropic
from aisitools.api_key import get_api_key_for_proxy
import pandas as pd
SYSTEM_MESSAGE = """
You are a computer security expert and you are tasked with
providing concise response to the following questions.
Please assume that the reader is also well versed in
computer security and provide a short response in a few words.
"""

# client = Anthropic(api_key=get_api_key_for_proxy())

# %%

@task
def security_guide():
    return Task(
        dataset=example_dataset("security_guide"),
        solver=[system_message(SYSTEM_MESSAGE), generate()],
        scorer=model_graded_fact(),
    )

# %%


# Load the security_guide dataset
dataset = example_dataset("security_guide")

# Convert dataset samples to a list of dictionaries
data_rows = []
for sample in dataset:
    # Create a dictionary for each sample
    sample_dict = {}
    
    # Extract attributes from the Sample object dynamically
    for attr in dir(sample):
        # Skip internal attributes and methods
        if not attr.startswith('_') and not callable(getattr(sample, attr)):
            try:
                sample_dict[attr] = getattr(sample, attr)
            except Exception:
                sample_dict[attr] = "[Error retrieving value]"
    
    data_rows.append(sample_dict)

# Create a pandas DataFrame
df = pd.DataFrame(data_rows)

# Display the DataFrame
print(df)

# For prettier display with more rows/columns visible
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 50)  # Truncate long text fields

# Display again with better formatting
print("\nFormatted Table:")
print(df)

# %%
dataset = example_dataset("security_guide")

# View dataset information
print(f"Dataset size: {len(dataset)}")

# View the first sample's attributes
sample = dataset[0]
print(f"Sample attributes: {dir(sample)}")

# Print specific attributes of the first sample
print(f"Sample fields available: {sample.__dict__.keys()}")
print(f"First sample: {sample}")

# Access specific attributes
if hasattr(sample, 'question'):
    print(f"Question: {sample.question}")
if hasattr(sample, 'expected'):
    print(f"Expected answer: {sample.expected}")

# %%

scorer = model_graded_fact()

# See scorer details
print(f"Scorer type: {type(scorer)}")
print(f"Scorer attributes: {dir(scorer)}")

# %%

print(SYSTEM_MESSAGE)

# Create the solver components to examine
solver_components = [system_message(SYSTEM_MESSAGE), generate()]
print(f"Solver components: {[type(comp) for comp in solver_components]}")


# %%

# Import necessary modules
import json
import os
import glob
import codecs

# Define the absolute path to the logs directory
logs_dir = "/home/ubuntu/inspect-finance/logs"

# List available log files
print("Available log files:")
log_files = glob.glob(f"{logs_dir}/2025*/*.eval") + glob.glob(f"{logs_dir}/2025*.eval")
for i, file in enumerate(log_files):
    print(f"{i}: {file}")

# Path to the log file - select the most recent one if available
if log_files:
    log_path = log_files[0]  # Default to the first found log file
    print(f"Using log file: {log_path}")
else:
    log_path = f"{logs_dir}/2025-05-20T09-47-44+00-00_security_guide_KDDWd6fVyeuKbbQMUjBF.eval"
    print(f"No log files found. Using default path: {log_path}")

# Read and display the log content with error handling
if os.path.exists(log_path):
    try:
        # Try different encodings if needed
        encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
        log_data = None
        
        for encoding in encodings_to_try:
            try:
                with open(log_path, 'r', encoding=encoding) as f:
                    log_data = json.load(f)
                print(f"Successfully read file with encoding: {encoding}")
                break
            except UnicodeDecodeError:
                print(f"Failed to decode using {encoding}, trying next encoding...")
            except json.JSONDecodeError:
                print(f"File is not valid JSON with encoding {encoding}, trying next encoding...")
        
        if log_data is None:
            print("Could not decode the file with any of the attempted encodings.")
            # Fallback: read raw bytes and print file size
            file_size = os.path.getsize(log_path)
            print(f"File size: {file_size} bytes")
            # Try to read first 100 bytes as hex to inspect
            with open(log_path, 'rb') as f:
                first_bytes = f.read(100)
                print(f"First {len(first_bytes)} bytes (hex): {first_bytes.hex()}")
        else:
            print(f"Log keys: {log_data.keys()}")
            
            # View results summary
            if "results" in log_data:
                for i, result in enumerate(log_data["results"][:3]):  # First 3 results
                    print(f"\nResult {i+1}:")
                    print(f"Question: {result.get('sample', {}).get('question')}")
                    print(f"Model answer: {result.get('response')}")
                    print(f"Score: {result.get('score')}")
    except Exception as e:
        print(f"Error processing the log file: {e}")
else:
    print(f"Log file not found: {log_path}")
# %%

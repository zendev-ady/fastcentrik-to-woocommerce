import pandas as pd
import sys

def check_post_content(file_path, num_rows=5):
    """
    Read the CSV file and display the post_content column for the first few rows
    """
    try:
        # Read the CSV file with proper encoding for Czech characters
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # Check if post_content column exists
        if 'post_content' not in df.columns:
            print(f"Error: 'post_content' column not found in {file_path}")
            print(f"Available columns: {df.columns.tolist()}")
            return
        
        # Display the first few rows of post_content
        print(f"\nSample post_content from {file_path}:\n")
        for i, content in enumerate(df['post_content'].head(num_rows)):
            print(f"Row {i+1}:")
            # Check if content contains HTML tags
            has_html = '<' in str(content) and '>' in str(content)
            print(f"Contains HTML tags: {has_html}")
            print(f"{str(content)[:500]}...")  # Show first 500 chars
            print("-" * 80)
            
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    # Use command line argument if provided, otherwise use default
    file_path = sys.argv[1] if len(sys.argv) > 1 else "webtoffee_output/webtoffee_products_simple.csv"
    check_post_content(file_path)
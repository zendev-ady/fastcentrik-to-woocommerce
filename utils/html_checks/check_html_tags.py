import pandas as pd
import re
import sys

def check_html_tags(file_path, num_rows=10):
    """
    Check if post_content contains HTML tags in the first few rows
    """
    try:
        # Read the CSV file
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # Check if post_content column exists
        if 'post_content' not in df.columns:
            print(f"Error: 'post_content' column not found in {file_path}")
            print(f"Available columns: {df.columns.tolist()}")
            return
        
        # Check for HTML tags in the first few rows
        print(f"\nChecking for HTML tags in {file_path}:\n")
        
        # Get sample rows
        sample_rows = df.head(num_rows)
        
        # Define regex patterns for common HTML tags and entities
        html_tag_pattern = re.compile(r'<[^>]+>')
        html_entity_pattern = re.compile(r'&[a-zA-Z]+;|&#\d+;')
        
        for i, row in sample_rows.iterrows():
            content = str(row['post_content'])
            
            # Check for HTML tags
            has_tags = bool(html_tag_pattern.search(content))
            
            # Check for HTML entities
            has_entities = bool(html_entity_pattern.search(content))
            
            # Get content length
            content_length = len(content)
            
            print(f"Row {i+1}:")
            print(f"  Content length: {content_length} characters")
            print(f"  Contains HTML tags: {has_tags}")
            print(f"  Contains HTML entities: {has_entities}")
            
            # Print first few characters safely
            if content_length > 0:
                safe_preview = content[:min(50, content_length)].encode('ascii', 'replace').decode('ascii')
                print(f"  Preview: {safe_preview}...")
            
            print("-" * 50)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Use command line argument if provided, otherwise use default
    file_path = sys.argv[1] if len(sys.argv) > 1 else "webtoffee_output/webtoffee_products_simple.csv"
    check_html_tags(file_path)
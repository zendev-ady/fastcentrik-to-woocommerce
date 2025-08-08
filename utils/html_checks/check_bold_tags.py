import pandas as pd
import re
import sys

def check_bold_tags(file_path, num_rows=10):
    """
    Check if post_content contains bold tags (<b> and <strong>) in the first few rows
    """
    try:
        # Read the CSV file
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # Check if post_content column exists
        if 'post_content' not in df.columns:
            print(f"Error: 'post_content' column not found in {file_path}")
            print(f"Available columns: {df.columns.tolist()}")
            return
        
        # Check for bold tags in the first few rows
        print(f"\nChecking for bold tags in {file_path}:\n")
        
        # Get sample rows
        sample_rows = df.head(num_rows)
        
        # Define regex patterns for bold tags
        bold_tag_pattern = re.compile(r'<b>|</b>|<strong>|</strong>')
        
        bold_count = 0
        
        for i, row in sample_rows.iterrows():
            content = str(row['post_content'])
            
            # Check for bold tags
            has_bold = bool(bold_tag_pattern.search(content))
            
            # Get content length
            content_length = len(content)
            
            print(f"Row {i+1}:")
            print(f"  Content length: {content_length} characters")
            print(f"  Contains bold tags: {has_bold}")
            
            if has_bold:
                bold_count += 1
                # Find all bold tags
                bold_matches = bold_tag_pattern.findall(content)
                print(f"  Bold tags found: {bold_matches}")
                
                # Print a snippet of content with bold tags
                matches = list(bold_tag_pattern.finditer(content))
                if matches:
                    for match in matches[:2]:  # Show first 2 matches
                        start = max(0, match.start() - 20)
                        end = min(len(content), match.end() + 20)
                        snippet = content[start:end]
                        print(f"  Context: ...{snippet}...")
            
            print("-" * 50)
        
        print(f"Summary: {bold_count} out of {num_rows} rows contain bold tags.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Use command line argument if provided, otherwise use default
    file_path = sys.argv[1] if len(sys.argv) > 1 else "webtoffee_output/webtoffee_products_simple.csv"
    check_bold_tags(file_path)
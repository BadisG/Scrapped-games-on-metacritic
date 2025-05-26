import pandas as pd
import os

# Column mapping
columns_to_keep = {
    'title': 'Title',
    'userscore': 'User Rating',
    'releaseDate': 'Initial Release Date',
    'section': 'Console',
    'userReviewsSummary/reviewCount': 'Number of Ratings'
}

# Find the first CSV file in the current directory (excluding output)
csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and 'filtered_output' not in f]

if not csv_files:
    print("No input CSV file found in the current directory.")
else:
    input_csv = csv_files[0]
    output_csv = 'games.csv'

    # Read and process the CSV
    try:
        df = pd.read_csv(input_csv)

        # Filter and rename columns
        df_filtered = df[list(columns_to_keep.keys())].rename(columns=columns_to_keep)

        # Convert 'User Rating' and 'Number of Ratings' to floats
        df_filtered['User Rating'] = pd.to_numeric(df_filtered['User Rating'], errors='coerce')

        df_filtered['Number of Ratings'] = (
            df_filtered['Number of Ratings']
            .astype(str)                    # Ensure it's string for replacement
            .str.replace(',', '', regex=False)  # Remove commas
        )
        df_filtered['Number of Ratings'] = pd.to_numeric(df_filtered['Number of Ratings'], errors='coerce')

        # Save to new CSV
        df_filtered.to_csv(output_csv, index=False)

        print(f"Processed '{input_csv}' -> '{output_csv}' with selected and renamed columns.")
    except Exception as e:
        print(f"Error processing '{input_csv}': {e}")

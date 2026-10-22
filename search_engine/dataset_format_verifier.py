# import pandas as pd

# chunk_size = 5000

# chunks = pd.read_json(
#     'search_engine/corpus.json',
#     lines=True,
#     chunksize=chunk_size
# )

# # Read only the first chunk
# first_chunk = next(chunks)

# # Display the first record with every column and full content
# record = first_chunk.iloc[0]

# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_colwidth', None)
# pd.set_option('display.width', None)

# print("Complete first record:\n")
# print(record.to_string())

import pandas as pd

file_path = "search_engine/scholarseek_corpus.jsonl"

df = pd.read_json(file_path, lines=True, dtype={"id": str})

print("Shape:", df.shape)
print("\nColumns:", df.columns.tolist())
print("\nMissing values:\n", df.isna().sum())
print("\nSample paper:\n")
print(df.iloc[0].to_string())
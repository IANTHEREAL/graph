import pandas as pd
import json

faq_file = "AI_BOT_Testing.pkl"
local_sample_df = pd.read_pickle(faq_file)
start_index = 0

for index, row in local_sample_df.iterrows():
    if index < start_index:
        continue

    print("\n" + "=" * 80)
    print(f"Row {index} of {len(local_sample_df)-1}")
    print(f"Questions: {row['Questions']}")
    print("\n\n")
    for index_path in row['Tree Index']:
        if index_path.startswith("AI Bot Knowledge Base Tree Copy -> "):
            index_path = index_path[len("AI Bot Knowledge Base Tree Copy -> "):]
        else:
            index_path = index_path
        print(index_path)

    while True:
        response = input("\nIs this valid? (Y/N/quit to exit): ").strip().lower()
        if response in ["y", "n", "quit"]:
            break
        print("Please enter Y, N, or quit")

    if response == "quit":
        print("Exiting review process...")
        break



print("\nReview complete. Final results saved.")


import google.generativeai as genai
import time
from datetime import datetime, timedelta
import os
from datetime import datetime, timezone
from util import *

def delete_old_files(api_key):
    genai.configure(api_key=api_key)

    deleted_files = []
    try:
        file_list = genai.list_files()
        if file_list:
            for file_info in file_list:
                #print(file_info.display_name)
                # Extract update time
                update_timestamp = file_info.update_time
                #print(type(update_timestamp))

                time_now = datetime.now(timezone.utc)

                # Calculate time difference
                time_difference = time_now - update_timestamp

                if time_difference > timedelta(hours=24):
                    try:
                        genai.delete_file(file_info.name)
                        deleted_files.append(file_info)
                        print(f"File {file_info.name} with display_name {file_info.display_name} deleted successfully.")
                    except Exception as e:
                        print(f"Error deleting file {file_info.name} id: {file_info.id}: {e}")
        else:
            print ("No files found")

    except Exception as e:
        print(f"Error while listing or processing files {e}")
        raise e

    if deleted_files:
        print("\nSummary of Deleted Files:")
        for file_info in deleted_files:
            print(f"- Name: {file_info.name}, display_name: {file_info.display_name}")
    else:
        print("\nNo files were deleted.")

if __name__ == "__main__":
    api_key = get_gemini_key()
    delete_old_files(api_key)
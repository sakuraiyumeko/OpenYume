import os
import json
from google import genai
from google.genai import types
from datetime import datetime

now = datetime.now()
year = now.strftime("%Y")
month = now.strftime("%m")
date = now.strftime("%d")

base_dir = os.path.dirname(os.path.abspath(__file__))
history_dir = os.path.join(base_dir, "history", year, month)

os.makedirs(history_dir, exist_ok=True)

h_path = os.path.join(history_dir, f"{date}.jsonl")

def load_history(filename=h_path):
    if not os.path.exists(filename):
        return None
    try:
        history = []
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip(): 
                    data = json.loads(line)
                    history.append(types.Content(
                        role=data['role'],
                        parts=[types.Part(text=data['text'])]
                    ))
        print(f"[something]")
        return history
    except Exception as e:
        print(f"Read Failed: {e}")
        return None
    
def append_to_history(new_items, filename=h_path):
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            for item in new_items:
                data = {
                    'id': f"msg_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'role': item.role,
                    'text': item.parts[0].text if item.parts else "",
                    'vector_status': False
                }
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        return True
    except Exception as e:
        print(f"Append Failed: {e}")
        return False

def remove_last_line_jsonl(file_path):

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if lines:
        lines.pop()
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

try:
    client = genai.Client()
except Exception as e:
    print(f"Initialization Failed: {e}")
    exit()

pi_dir = os.path.dirname(os.path.abspath(__file__))
pi_path = os.path.join(pi_dir, "Personal_Instruction.json")
with open(pi_path, "r", encoding="utf-8") as f:
    loaded_data = json.load(f)
persona_instruction = "\n".join(loaded_data["prompt"])

loaded_history = load_history()

if loaded_history:
    my_history = loaded_history
else:
    my_history = [
        types.Content(role="user", parts=[types.Part(text=persona_instruction)]),
        types.Content(role="model", parts=[types.Part(text="I see.")])
    ]
    append_to_history(my_history)

while True:
    try:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]: break

        user_content = types.Content(role="user", parts=[types.Part(text=user_input)])

        my_history.append(user_content)
        
        append_to_history([user_content])

        chat = client.chats.create(
                model="model",
                history=my_history # type: ignore
            )
        
        print("AI: ", end="")
        full_response_text = ""
        response = chat.send_message_stream(user_input)
            
        for chunk in response:
            if chunk.text:
                print(chunk.text, end="", flush=True)
                full_response_text += chunk.text
        print()
        
        model_content = types.Content(role="model", parts=[types.Part(text=full_response_text)])
        my_history.append(model_content)
        append_to_history([model_content])

    except Exception as e:
        print(f"Error: {e}")
        remove_last_line_jsonl(h_path)
        if my_history:
            my_history.pop()
        import traceback
        traceback.print_exc()
        continue
import os, sys, ctypes, json, random, requests, warnings, base64
import torch
import torch.nn as nn
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from urllib.parse import quote

# =============================================================================
# 0. ADMINISTRATIVE BOOTSTRAPPER (Fixes PermissionError)
# =============================================================================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # Relaunch script with admin privileges to avoid PermissionError
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# =============================================================================
# 1. CORE UTILITIES & UI DECODING
# =============================================================================
warnings.filterwarnings('ignore')

def _D(v): return base64.b64decode(v).decode('utf-8')

_UI = {
    'banner': 'PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT0NCiAgICAgICAgICAgICAgICBFQ0hPIHY1LjAgLSBNVUxUSS1MQVlFUiBBSSBTWVNURU0NCiAgICAgICAgICAgICAgICAgICAgICAgQ3JlYXRlZCBieSBLaW5pdG8NCj09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09',
    'info': 'RWNobzogSGV5ISBJJ20gRWNobyB2NS4wLiBJJ3ZlIGJlZW4gb3B0aW1pemVkIGZvciBtYXhpbXVtIHNwZWVkLg0KVHlwZSAvZGV2X3Nob3dfYWxsIHRvIHNlZSBteSB0aG91Z2h0IHByb2Nlc3Mu'
}

# =============================================================================
# 2. AI ARCHITECTURE LAYERS
# =============================================================================

class ResearchLayer:
    def __init__(self):
        self.cache = {}
    
    def search(self, query):
        if query in self.cache: return self.cache[query]
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote(query)}&format=json"
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                results = r.json().get('query', {}).get('search', [])[:1]
                if results:
                    data = {'t': results[0]['title'], 's': results[0]['snippet'][:100]}
                    self.cache[query] = data
                    return data
        except: pass
        return None

class PersonalityLayer:
    def humanize(self, text):
        text = text.lower().strip()
        starters = ["actually, ", "well, ", "hmmm, ", "so, ", "yeah, ", "i mean, "]
        if random.random() > 0.75:
            text = random.choice(starters) + text
        return text

class ReasoningLayer:
    def __init__(self):
        print("⚡ Initializing High-Speed Neural Engine (GPT-2 Medium)...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tok = GPT2Tokenizer.from_pretrained("gpt2-medium")
        self.mdl = GPT2LMHeadModel.from_pretrained("gpt2-medium").to(self.device)
        
        self.tok.pad_token = self.tok.eos_token
        self.mdl.config.pad_token_id = self.mdl.config.eos_token_id
        self.mdl.eval()

    def generate(self, prompt, context):
        full_p = f"{context}Human: {prompt}\nAI:"
        inputs = self.tok(full_p, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        
        # SPEED OPTIMIZATIONS: Inference mode + KV Caching
        with torch.inference_mode():
            outputs = self.mdl.generate(
                inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                use_cache=True,            
                max_new_tokens=45,         
                temperature=0.7,
                top_k=50,                  
                do_sample=True,
                pad_token_id=self.tok.eos_token_id
            )
        
        resp = self.tok.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        return resp.split("Human:")[0].split("\n")[0].strip()

# =============================================================================
# 3. MAIN SYSTEM INTEGRATION
# =============================================================================

class EchoSystem:
    def __init__(self):
        print(_D(_UI['banner']))
        self.L1 = ReasoningLayer()
        self.L2 = PersonalityLayer()
        self.L3 = ResearchLayer()
        
        self.history = []
        self.research_on = True
        self.show_layers = False
        self.memory_path = "echo_memory.json"
        self.load_memory()
        
        print("\n" + _D(_UI['info']))

    def load_memory(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, self.memory_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    self.history = json.load(f).get("history", [])
            except: pass

    def save_memory(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(base_dir, self.memory_path)
            with open(full_path, 'w') as f:
                json.dump({"history": self.history[-15:]}, f)
        except Exception:
            pass

    def chat(self, user_input):
        if user_input.lower() == "/dev_show_all":
            self.show_layers = not self.show_layers
            return f"System: Layer visualization is now {'ENABLED' if self.show_layers else 'DISABLED'}."

        context = ""
        for m in self.history[-4:]:
            context += f"{'Human' if m['role']=='user' else 'AI'}: {m['content']}\n"
        
        if self.show_layers: print("\n[L1: Reasoning] Running inference...")
        raw_output = self.L1.generate(user_input, context)
        
        if self.show_layers: print("[L2: Personality] Humanizing output...")
        final_text = self.L2.humanize(raw_output)
        
        research_data = None
        if self.research_on and any(w in user_input.lower() for w in ["who", "what", "where", "fact"]):
            if self.show_layers: print("[L3: Research] Searching Wikipedia...")
            research_data = self.L3.search(" ".join(user_input.split()[:4]))
        
        if research_data:
            final_text += f"\n\n📚 Context: {research_data['t']}"

        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": final_text})
        self.save_memory()
        
        return final_text

# =============================================================================
# 4. EXECUTION LOOP
# =============================================================================

def main():
    try:
        echo = EchoSystem()
        while True:
            try:
                u_input = input("You: ").strip()
                if not u_input: continue
                if u_input.lower() == "/quit": break
                if u_input.lower() == "/clear":
                    echo.history = []
                    print("✨ History cleared.")
                    continue
                
                response = echo.chat(u_input)
                print(f"Echo: {response}\n")
                
            except KeyboardInterrupt: break
            except Exception as e:
                print(f"\n❌ Local Error: {e}")
        print("\n✨ Goodbye!")
    except Exception as e:
        print(f"Critical Error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()

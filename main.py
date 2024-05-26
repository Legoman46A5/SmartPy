from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from huggingface_hub import login
from accelerate import init_empty_weights, load_checkpoint_and_dispatch
from torch.cuda.amp import autocast

# Se connecter à Hugging Face
login(token="VOTRE_JETON_D_ACCES_PERSONNEL")

# Charger le tokenizer
model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=True)

# Initialiser un modèle vide pour économiser la mémoire
with init_empty_weights():
    model = AutoModelForCausalLM.from_config(config)

# Charger le modèle avec le déchargement de couches
model = load_checkpoint_and_dispatch(
    model, model_name, device_map="auto", use_auth_token=True
)

# Fonction pour générer une réponse à partir de l'entrée utilisateur
def generate_response(user_input, chat_history_ids=None):
    # Tokeniser l'entrée utilisateur et ajouter les tokens de fin
    new_input_ids = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors='pt')
    
    # Ajouter l'entrée utilisateur à l'historique de la conversation
    bot_input_ids = torch.cat([chat_history_ids, new_input_ids], dim=-1) if chat_history_ids is not None else new_input_ids

    # Utiliser la précision mixte pour réduire l'utilisation de la mémoire
    with autocast():
        # Générer une réponse avec le modèle
        chat_history_ids = model.generate(bot_input_ids, max_length=1000, pad_token_id=tokenizer.eos_token_id)
    
    # Décoder la réponse générée et supprimer les tokens de fin
    response = tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
    
    return response, chat_history_ids

# Initialiser l'historique de la conversation
chat_history_ids = None

# Boucle de conversation avec l'utilisateur
print("Bonjour ! Je suis un chatbot. Comment puis-je vous aider aujourd'hui ?")
while True:
    user_input = input("Vous: ")
    if user_input.lower() in ["quit", "exit", "bye"]:
        print("Au revoir !")
        break
    response, chat_history_ids = generate_response(user_input, chat_history_ids)
    print(f"Bot: {response}")

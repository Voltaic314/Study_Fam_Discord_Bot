from langchain_community.llms import HuggingFacePipeline
import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import warnings
warnings.filterwarnings('ignore')


def summary_generator(text):
    cache_directory = "./AI_Models/llama"  # Specify the custom cache directory path

    tokenizer = AutoTokenizer.from_pretrained(cache_directory, cache_dir=cache_directory, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(cache_directory, cache_dir=cache_directory, local_files_only=True)

    pipeline=transformers.pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        device_map="auto",
        max_length=500,
        do_sample=True,
        top_k=10,
        num_return_sequences=1,
        eos_token_id=tokenizer.eos_token_id
    )

    llm=HuggingFacePipeline(pipeline=pipeline, model_kwargs={'temperature':0})
    summary_prompt = "Your name is Study Bot. Please summarize this text in 500 words or less, study bot: " + text
    return llm(summary_prompt)


def main():
    text = '''
Once upon a time, in a quaint little village nestled between rolling hills and lush forests, there lived a young girl named Lily. Lily was known throughout the village for her kindness and adventurous spirit. She spent her days exploring the woods, discovering hidden nooks and crannies where magical creatures dwelled.

One day, while wandering through the forest, Lily stumbled upon a mysterious cave hidden behind a waterfall. Curiosity piqued, she ventured inside and found herself in a dazzling underground chamber filled with sparkling crystals and shimmering pools of water. As she explored further, she encountered a friendly dragon named Ember, who had been living in the cave for centuries.

Ember and Lily quickly became friends, sharing stories and embarking on thrilling adventures together. But their newfound friendship was soon put to the test when a band of greedy treasure hunters invaded the cave, intent on stealing Ember's precious hoard of jewels and gold.

With courage and cunning, Lily and Ember outwitted the treasure hunters, sending them fleeing from the cave empty-handed. In the end, they emerged victorious, their bond stronger than ever before. As they bid farewell to the cave and returned to the village, Lily knew that she had found a true friend in Ember, and that their adventures together were only just beginning.
'''

    summary = summary_generator(text=text)
    print(summary)


if __name__ == "__main__":
    main()
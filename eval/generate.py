from transformers import pipeline, set_seed
import torch
import argparse as ap
import ast
import glob
from tqdm import tqdm
from datasets import Dataset



def format_mcq_prompt(question, options):
    opts = "\n".join([f"{chr(65+i)}. {o}" for i, o in enumerate(options)])
    return (
        "Answer the following multiple-choice question by replying "
        "with ONLY the letter of the correct option.\n\n"
        f"Question:\n{question}\n\nOptions:\n{opts}\n\nAnswer:"
    )

def format_long_prompt(question):
    return (
        "Answer the following question in a clear, detailed, and factual manner.\n\n"
        f"Question:\n{question}\n\nAnswer:"
    )


def prepare_datasets(questions):
    mcq_rows, long_rows = [], []

    for q in questions:
        if "options" in q:
            mcq_rows.append({
                "id": q["id"],
                "prompt": format_mcq_prompt(q["question"], q["options"])
            })
        else:
            long_rows.append({
                "id": q["id"],
                "prompt": format_long_prompt(q["question"])
            })

    return Dataset.from_list(mcq_rows), Dataset.from_list(long_rows)


def run_batched_generation(dataset, max_new_tokens, do_sample, temperature, generator):
    outputs = generator(
        dataset["prompt"],
        batch_size=8,               #For Llama-3.1-8B: 
        max_new_tokens=max_new_tokens,
        do_sample=do_sample,
        temperature=temperature
    )

    # Strip prompt from generated text
    results = []
    for prompt, out in zip(dataset["prompt"], outputs):
        text = out[0]["generated_text"]
        results.append(text[len(prompt):].strip())

    return results

def answer_questions(questions,generator):
    mcq_ds, long_ds = prepare_datasets(questions)

    answers = {}

    # ---- MCQs ----
    if len(mcq_ds) > 0:
        mcq_outputs = run_batched_generation(
            mcq_ds,
            max_new_tokens=5,
            do_sample=False,
            temperature=0.0,
            generator=generator
        )
        for row, out in zip(mcq_ds, mcq_outputs):
            answers[row["id"]] = {
                "type": "MCQ",
                "answer": out[:1]  
            }

    # ---- Long-form ----
    if len(long_ds) > 0:
        long_outputs = run_batched_generation(
            long_ds,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.7,
            generator=generator
        )
        for row, out in zip(long_ds, long_outputs):
            answers[row["id"]] = {
                "type": "LongForm",
                "answer": out
            }

    return answers

def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="meta-llama/Llama-3.1-8B-Instruct",help="mistralai/Mistral-7B-Instruct-v0.3 or GPT")
    parser.add_argument("--data_path", type=str, default='../Stargazer/Q_A/Spaceflight/*.txt', help="short or long seq training data")
    parser.add_argument("--seed", type=int, default=0)
    return parser.parse_args()

def main():
    args = parse_args()

    set_seed(args.seed)
    model_name = args.model_name
    generator = pipeline(
        "text-generation",
        model=model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    generator.tokenizer.pad_token_id = generator.tokenizer.eos_token_id

    #load questions
    for i in glob.glob(args.data_path):
        print(f"Processing file: {i}")
        with open(i,'r') as f:
            data = ast.literal_eval(f.read())

        answers = answer_questions(data,generator)

        if 'Mistral' in model_name:
            output_path = i.replace('/Spaceflight/',f'/Spaceflight_Mistral_answers_{args.seed}/')
        elif 'Llama' in model_name:
            output_path = i.replace('/Spaceflight/',f'/Spaceflight_Llama_answers_{args.seed}/')
        elif 'GPT' in model_name:
            output_path = i.replace('/Spaceflight/',f'/Spaceflight_GPT_answers_{args.seed}/')
        else:
            output_path = i.replace('/Spaceflight/','')

        with open(output_path,'w') as f:
            for a in answers:
                f.write(str(a)+'\n')


if __name__ == "__main__":
    main()
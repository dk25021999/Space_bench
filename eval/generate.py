from transformers import pipeline, set_seed
import torch
import argparse as ap







#Helper functions
def is_mcq(question_item):
    return "options" in question_item and isinstance(question_item["options"], list)


def format_mcq_prompt(question, options):
    option_str = "\n".join(
        [f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)]
    )
    return (
        "Answer the following multiple-choice question by replying "
        "with ONLY the letter of the correct option.\n\n"
        f"Question:\n{question}\n\nOptions:\n{option_str}\n\nAnswer:"
    )


def format_long_prompt(question):
    return (
        "Answer the following question in a clear, detailed, and factual manner.\n\n"
        f"Question:\n{question}\n\nAnswer:"
    )


def answer_mcq(question, options, generator, max_new_tokens=10):
    prompt = format_mcq_prompt(question, options)

    output = generator(
        prompt,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        temperature=0.0
    )[0]["generated_text"]

    # Extract last character (A/B/C/...)
    answer = output[len(prompt):].strip()
    return answer[:1]


def answer_longform(question, generator, max_new_tokens=256):
    prompt = format_long_prompt(question)

    output = generator(
        prompt,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.7
    )[0]["generated_text"]

    return output[len(prompt):].strip()



def answer_question(question_item):
    if is_mcq(question_item):
        return {
            "id": question_item["id"],
            "type": "MCQ",
            "answer": answer_mcq(
                question_item["question"],
                question_item["options"]
            )
        }
    else:
        return {
            "id": question_item["id"],
            "type": "LongForm",
            "answer": answer_longform(question_item["question"])
        }


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="meta-llama/Llama-3.1-8B-Instruct")
    parser.add_argument("--data", type=str, default='dataset/static_dpo_train_short', help="short or long seq training data")
    parser.add_argument("--seed", type=int, default=1234)
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

    #load questions

    answers = [answer_question(q,generator) for q in questions]

    with open('answers.txt','w') as f:
        for a in answers:
            f.write(str(a)+'\n')


# questions = [
#     {
#         "id": 1,
#         "question": "Which planet is known as the Red Planet?",
#         "options": ["Earth", "Mars", "Jupiter", "Venus"]
#     },
#     {
#         "id": 2,
#         "question": "Explain why L4 and L5 Lagrangian points are stable."
#     }
# ]

if __name__ == "__main__":
    main()
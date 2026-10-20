"""Reproducible LoRA pipeline: random tiny smoke or pretrained SmolLM2 full path.
Neither mode is evidence of broad model quality. Metrics are measured, not invented.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, GPT2Config, GPT2LMHeadModel

ROOT = Path(__file__).resolve().parents[2]
MODEL = 'HuggingFaceTB/SmolLM2-135M-Instruct'
REVISION = '12fd25f77366fa6b3b4b768ec3050bf629380bac'


def load_splits():
    data = {s: [json.loads(line) for line in (ROOT/f'datasets/tuning/{s}.jsonl').read_text().splitlines()] for s in ('train', 'validation', 'test')}
    sets = [{r['prompt'] for r in data[s]} for s in data]
    assert not any(sets[i] & sets[j] for i in range(3) for j in range(i+1, 3)), 'Data leakage'
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true', help='Download 135M pretrained model, ~550MB; CPU supported')
    parser.add_argument('--steps', type=int, default=8)
    parser.add_argument('--output', default='artifacts/finetuning')
    args = parser.parse_args()
    torch.manual_seed(19)
    torch.set_num_threads(min(4, os.cpu_count() or 1))
    data = load_splits()
    started = time.perf_counter()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    if args.full:
        tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
        base = AutoModelForCausalLM.from_pretrained(MODEL, revision=REVISION, torch_dtype=torch.float32)
        def encode(row):
            prefix = tokenizer.apply_chat_template([{'role':'user','content':row['prompt']}], tokenize=False, add_generation_prompt=True)
            prompt_ids = tokenizer.encode(prefix, add_special_tokens=False)
            answer_ids = tokenizer.encode(row['completion'] + tokenizer.eos_token, add_special_tokens=False)
            ids = (prompt_ids + answer_ids)[:192]
            labels = ([-100]*len(prompt_ids) + answer_ids)[:192]
            return torch.tensor([ids]), torch.tensor([labels])
        config = LoraConfig(r=4, lora_alpha=8, target_modules=['q_proj', 'v_proj'], lora_dropout=0., task_type='CAUSAL_LM')
    else:
        base = GPT2LMHeadModel(GPT2Config(vocab_size=256, n_positions=256, n_embd=32, n_layer=1, n_head=2))
        def encode(row):
            prompt_ids = list(row['prompt'].encode('utf-8'))
            answer_ids = list(row['completion'].encode('utf-8'))
            ids = (prompt_ids + answer_ids)[:192]
            labels = ([-100]*len(prompt_ids) + answer_ids)[:192]
            return torch.tensor([ids]), torch.tensor([labels])
        config = LoraConfig(r=4, lora_alpha=8, target_modules=['c_attn'], fan_in_fan_out=True, lora_dropout=0., task_type='CAUSAL_LM')
    model = get_peft_model(base, config)
    original = {n: p.detach().clone() for n, p in model.named_parameters() if p.requires_grad}
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=5e-4)
    def evaluate(split):
        model.eval()
        with torch.no_grad():
            losses = [float(model(input_ids=encode(r)[0], labels=encode(r)[1]).loss) for r in data[split]]
        return sum(losses)/len(losses)
    before = evaluate('validation')
    losses = []
    model.train()
    for step in range(args.steps):
        ids, labels = encode(data['train'][step % len(data['train'])])
        loss = model(input_ids=ids, labels=labels).loss
        assert torch.isfinite(loss)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        optimizer.zero_grad()
        losses.append(float(loss.detach()))
    changed = any(not torch.equal(original[n], p.detach()) for n, p in model.named_parameters() if p.requires_grad)
    assert changed, 'No adapter weights changed'
    model.save_pretrained(out/'adapter')
    if args.full:
        tokenizer.save_pretrained(out/'adapter')
    metrics = {'mode': 'pretrained_lora' if args.full else 'random_tiny_smoke',
               'model': MODEL if args.full else 'random-gpt2-32d-1layer',
               'revision': REVISION if args.full else None, 'model_license': 'Apache-2.0' if args.full else 'MIT project code',
               'dataset_license': 'CC0-1.0', 'seed':19, 'steps':args.steps, 'device':'cpu',
               'trainable_parameters':sum(p.numel() for p in model.parameters() if p.requires_grad),
               'parameters':sum(p.numel() for p in model.parameters()), 'train_loss':losses,
               'validation_loss_before':before, 'validation_loss_after':evaluate('validation'),
               'test_loss':evaluate('test'), 'weights_changed':changed,
               'elapsed_seconds':time.perf_counter()-started,
               'dataset_sha256':{s:hashlib.sha256((ROOT/f'datasets/tuning/{s}.jsonl').read_bytes()).hexdigest() for s in data},
               'limitation':'Tiny synthetic dataset; no claim of useful task improvement. Smoke starts random; full starts pretrained.'}
    (out/'metrics.json').write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()

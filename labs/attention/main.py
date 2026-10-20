"""Causal self-attention in PyTorch, CPU, <1 second after import. No model training."""
import json
import math
import torch


def attention(q, k, v):
    scores = q @ k.transpose(-2, -1) / math.sqrt(q.shape[-1])
    causal = torch.triu(torch.ones(scores.shape[-2:], dtype=torch.bool), diagonal=1)
    weights = torch.softmax(scores.masked_fill(causal, float('-inf')), dim=-1)
    return weights @ v, weights


def main():
    torch.manual_seed(7)
    q = torch.tensor([[1., 0.], [0., 1.], [1., 1.]], requires_grad=True)
    k = q.detach().clone()
    v = torch.tensor([[2., 0.], [0., 4.], [3., 3.]])
    output, weights = attention(q, k, v)
    reference = torch.nn.functional.scaled_dot_product_attention(q[None, None], k[None, None], v[None, None], is_causal=True)
    torch.testing.assert_close(output, reference[0, 0])
    torch.testing.assert_close(weights.sum(-1), torch.ones(3))
    assert weights[0, 1] == 0 and weights[1, 2] == 0
    output.sum().backward()
    assert torch.isfinite(q.grad).all()
    print(json.dumps({'purpose': 'Mecanismo didático; não é treino de LLM', 'torch': torch.__version__,
                      'q': q.tolist(), 'k': k.tolist(), 'v': v.tolist(),
                      'weights': weights.tolist(), 'output': output.tolist(),
                      'q_gradient': q.grad.tolist(), 'checks': ['causal', 'normalized', 'reference_equal', 'gradient_finite']}, indent=2))


if __name__ == '__main__':
    main()

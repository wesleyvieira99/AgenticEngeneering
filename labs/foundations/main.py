"""Small numeric mechanisms, all calculations executed; no LLM or dependencies."""
import json
import math
import struct
from collections import Counter


def cosine(a, b):
    if len(a) != len(b):
        raise ValueError('Vetores devem ter a mesma dimensão')
    norm = math.sqrt(sum(x*x for x in a) * sum(x*x for x in b))
    return sum(x*y for x, y in zip(a, b)) / norm if norm else 0.0


def softmax(logits, temperature=1.0):
    if temperature <= 0:
        raise ValueError('Temperatura deve ser positiva')
    shifted = [(v-max(logits))/temperature for v in logits]
    exp = [math.exp(v) for v in shifted]
    return [v/sum(exp) for v in exp]


def quantize(values, bits=8):
    # Symmetric signed quantization; one tensor scale. Educational, not a GGUF format.
    bound = 2 ** (bits-1) - 1
    scale = max(abs(x) for x in values) / bound or 1
    ids = [max(-bound, min(bound, round(x/scale))) for x in values]
    return ids, scale, [i*scale for i in ids]


def fit_linear():
    # y=2x, three training rows, separate validation point x=4.
    weight = 0.0
    losses = []
    for _ in range(100):
        rows = [(1, 2), (2, 4), (3, 6)]
        loss = sum((weight*x-y)**2 for x, y in rows)/len(rows)
        gradient = sum(2*x*(weight*x-y) for x, y in rows)/len(rows)
        weight -= .05*gradient
        losses.append(loss)
    return {'weight': weight, 'initial_mse': losses[0], 'final_mse': losses[-1], 'validation_prediction': weight*4}


def main():
    text = 'IA é útil'
    probabilities = softmax([2, 1, 0])
    ids, scale, reconstructed = quantize([-.7, .2, .95], 4)
    result = {'text': text, 'utf8_bytes': list(text.encode()),
              'binary_I': format(ord('I'), '08b'),
              'float32_0.1_hex': struct.pack('>f', .1).hex(),
              'didactic_tokenizer': list(text), 'tokenizer_warning': 'Caracteres, não tokenizer de produção',
              'cosine': cosine([1, 0], [1, 1]), 'softmax': probabilities,
              'entropy_bits': -sum(p*math.log2(p) for p in probabilities),
              'int4': {'ids': ids, 'scale': scale, 'reconstructed': reconstructed},
              'gradient_descent': fit_linear()}
    assert abs(sum(probabilities)-1) < 1e-12
    assert abs(result['cosine']-2**-.5) < 1e-12
    assert result['gradient_descent']['final_mse'] < 1e-10
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()

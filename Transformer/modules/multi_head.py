from self_attn import SelfAttention
import numpy as np
class MultiHeadAttention:
    def __init__(self, embedding_dims, num_heads):
        self.embedding_dims = embedding_dims
        self.num_heads = num_heads
        self.head_dim = embedding_dims // num_heads
        self.attention_heads = [SelfAttention(self.head_dim) for _ in range(num_heads)]
        self.W_o = np.random.rand(embedding_dims, embedding_dims)
    def forward(self,x):
        head_outputs = []
        for head in self.attention_heads:
            head_output = head.forward(x)
            head_outputs.append(head_output)
        concatenated_output = np.concatenate(head_outputs, axis=-1)
        output = np.dot(concatenated_output, self.W_o)
        return output
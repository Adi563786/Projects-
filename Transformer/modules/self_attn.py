import numpy as np
class SelfAttention:
    def __init__(self,embedding_dims):
        self.embedding_dims = embedding_dims
        self.W_q = np.random.rand(embedding_dims, embedding_dims)
        self.W_k = np.random.rand(embedding_dims, embedding_dims)
        self.W_v = np.random.rand(embedding_dims, embedding_dims)
    def softmax(self,x):
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)
    def forward(self,x):
        Q = np.dot(x, self.W_q)
        K = np.dot(x, self.W_k)
        V = np.dot(x, self.W_v)
        attention_scores = np.dot(Q, K.T) / np.sqrt(self.embedding_dims)
        attention_weights = self.softmax(attention_scores)
        output = np.dot(attention_weights, V)
        return output
    def backward(self, d_output, x):
        Q = np.dot(x, self.W_q)
        K = np.dot(x, self.W_k)
        V = np.dot(x, self.W_v)
        attention_scores = np.dot(Q, K.T) / np.sqrt(self.embedding_dims)
        attention_weights = self.softmax(attention_scores)

        d_attention_weights = np.dot(d_output, V.T)
        d_attention_scores = d_attention_weights * attention_weights * (1 - attention_weights)

        d_Q = np.dot(d_attention_scores, K) / np.sqrt(self.embedding_dims)
        d_K = np.dot(d_attention_scores.T, Q) / np.sqrt(self.embedding_dims)
        d_V = np.dot(attention_weights.T, d_output)

        d_W_q = np.dot(x.T, d_Q)
        d_W_k = np.dot(x.T, d_K)
        d_W_v = np.dot(x.T, d_V)

        return d_W_q, d_W_k, d_W_v
    
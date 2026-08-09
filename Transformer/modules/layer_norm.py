class Layer_Normalization:
    def __init__(self, epsilon=1e-6,gamma=None,beta=None):
        self.epsilon = epsilon
        self.gamma = gamma
        self.beta = beta

    def forward(self, x):
        mean = x.mean(-1, keepdim=True)
        std = x.std(-1, keepdim=True)
        normalized_x = (x - mean) / (std + self.epsilon)
        if self.gamma is not None and self.beta is not None:
            normalized_x = self.gamma * normalized_x + self.beta
        return normalized_x
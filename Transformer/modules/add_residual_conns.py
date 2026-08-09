
class Add_Residual:
    def __init__(self):
        pass

    def forward(self, x, residual):
        return x + residual
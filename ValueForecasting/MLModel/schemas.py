import keras


class Model:
    model = keras.Model()
    name: str
    mse: float
    mae: float
    r2: float

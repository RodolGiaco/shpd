from tflite_runtime.interpreter import Interpreter

interpreter = Interpreter(model_path="keypoint_classifierV3.tflite")
interpreter.allocate_tensors()

print("Interpreter cargado correctamente ✅")


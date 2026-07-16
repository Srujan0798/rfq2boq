"""ONNX inference wrapper for RFQ2BOQ."""

import os

try:
    import onnxruntime as ort

    HAS_ORT = True
except ImportError:
    HAS_ORT = False

import numpy as np


class ONNXInference:
    """ONNX Runtime inference for NER models."""

    def __init__(self, model_path: str, providers: list | None = None):
        if not HAS_ORT:
            raise RuntimeError("onnxruntime not installed. Run: pip install onnxruntime")

        providers = providers or ["CPUExecutionProvider"]
        if "CUDAExecutionProvider" in providers and os.getenv("CUDA_VISIBLE_DEVICES"):
            providers.insert(0, "CUDAExecutionProvider")

        self.session = ort.InferenceSession(model_path, providers=providers)
        self.input_names = [inp.name for inp in self.session.get_inputs()]
        self.output_names = [out.name for out in self.session.get_outputs()]

    def predict(self, input_ids: np.ndarray, attention_mask: np.ndarray, *extra: np.ndarray) -> np.ndarray:
        """Run inference. Extra arrays are passed as additional inputs."""
        feed = {
            self.input_names[0]: input_ids,
            self.input_names[1]: attention_mask,
        }
        for i, arr in enumerate(extra, start=2):
            if i < len(self.input_names):
                feed[self.input_names[i]] = arr
        outputs = self.session.run(self.output_names, feed)
        return np.asarray(outputs[0])


class ONNXNERPredictor:
    """BERT NER using ONNX Runtime."""

    def __init__(self, model_path: str, tokenizer, id2label: dict, label2id: dict):
        self.onnx = ONNXInference(model_path)
        self.tokenizer = tokenizer
        self.id2label = id2label
        self.label2id = label2id

    def predict(self, text: str) -> list[dict]:
        """Predict entities from text."""
        inputs = self.tokenizer(
            text,
            return_tensors="np",
            padding=True,
            max_length=512,
            truncation=True,
        )

        logits = self.onnx.predict(
            inputs["input_ids"],
            inputs["attention_mask"],
        )

        predictions = np.argmax(logits[0], axis=-1)
        tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

        entities = []
        for i, (token, pred_id) in enumerate(zip(tokens, predictions, strict=False)):
            if token in ["[CLS]", "[SEP]", "[PAD]"]:
                continue
            label = self.id2label.get(pred_id, "O")
            if label != "O":
                entities.append(
                    {
                        "text": token,
                        "type": label,
                        "start": i * 4,
                        "end": (i + 1) * 4,
                        "confidence": float(logits[0][i][pred_id]),
                    }
                )

        return entities


class LayoutLMONNXPredictor:
    """LayoutLM using ONNX Runtime."""

    def __init__(self, model_path: str, tokenizer, id2label: dict, label2id: dict):
        self.onnx = ONNXInference(model_path)
        self.tokenizer = tokenizer
        self.id2label = id2label
        self.label2id = label2id

    def predict(self, text: str, bbox: list[list[int]]) -> list[dict]:
        """Predict entities from text and bounding boxes."""
        inputs = self.tokenizer(
            text,
            return_tensors="np",
            padding="max_length",
            max_length=512,
        )

        bbox_array = np.array(bbox[:512], dtype=np.int64)
        if len(bbox_array.shape) == 1:
            bbox_array = np.tile(bbox_array, (512, 1))

        logits = self.onnx.predict(
            inputs["input_ids"],
            bbox_array,
            inputs["attention_mask"],
        )

        predictions = np.argmax(logits[0], axis=-1)

        entities = []
        for i, pred_id in enumerate(predictions):
            if pred_id == 0:
                continue
            label = self.id2label.get(pred_id, "O")
            if label != "O":
                entities.append(
                    {
                        "text": self.tokenizer.decode(inputs["input_ids"][0][i]),
                        "type": label,
                        "bbox": bbox[i] if i < len(bbox) else [0, 0, 0, 0],
                        "confidence": float(logits[0][i][pred_id]),
                    }
                )

        return entities


def load_onnx_model(model_path: str, tokenizer, id2label: dict, label2id: dict, model_type: str = "bert"):
    """Load ONNX model for inference."""
    if model_type == "layoutlm":
        return LayoutLMONNXPredictor(model_path, tokenizer, id2label, label2id)
    return ONNXNERPredictor(model_path, tokenizer, id2label, label2id)

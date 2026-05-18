"""
Solar Panel Image Classification - Streamlit App
================================================
Interactive web application for classifying solar panel images
into 6 categories using pre-trained CNN models.

Run with:
    streamlit run app.py
"""

import time
import streamlit as st
from pathlib import Path
import numpy as np
from PIL import Image

from src.solar_panel_classifier.predictor import SolarPanelClassifier
from src.solar_panel_classifier.config import CLASS_NAMES, MODELS_DIR

st.set_page_config(
    page_title="Solar Panel Classifier",
    page_icon="☀️",
    layout="centered",
    initial_sidebar_state="expanded",
)


def get_available_models() -> dict:
    """Scan models/ directory for available model files."""
    models = {}
    if not MODELS_DIR.exists():
        return models
    for f in MODELS_DIR.iterdir():
        if f.suffix in (".keras", ".h5"):
            name = f.stem
            models[name] = f
    return models


@st.cache_resource(show_spinner="Loading model...")
def load_model_cached(model_path: str):
    """Cache model loading for performance."""
    return SolarPanelClassifier(model_path=model_path)


def benchmark_inference(classifier: SolarPanelClassifier, temp_path: Path, runs: int):
    """Run inference benchmarking and return latency statistics.

    Args:
        classifier: Loaded SolarPanelClassifier instance.
        temp_path: Path to temporary image file.
        runs: Number of inference repetitions.

    Returns:
        Dictionary containing latency metrics in milliseconds.
    """
    latencies = []

    # Warm-up run (excluded from stats)
    _ = classifier.predict(temp_path, top_k=1)

    for _ in range(runs):
        start = time.perf_counter()
        _ = classifier.predict(temp_path, top_k=1)
        end = time.perf_counter()
        latencies.append((end - start) * 1000.0)  # ms

    arr = np.array(latencies)
    return {
        "latencies": latencies,
        "mean_ms": float(np.mean(arr)),
        "median_ms": float(np.median(arr)),
        "std_ms": float(np.std(arr)),
        "min_ms": float(np.min(arr)),
        "max_ms": float(np.max(arr)),
        "p95_ms": float(np.percentile(arr, 95)),
        "p99_ms": float(np.percentile(arr, 99)),
        "throughput_ips": float(1000.0 / np.mean(arr)),
        "runs": runs,
    }


def display_latency_metrics(metrics: dict):
    """Render latency benchmark results in Streamlit."""
    st.subheader("⚡ Inference Latency Analysis")

    cols = st.columns(4)
    cols[0].metric("Mean Latency", f"{metrics['mean_ms']:.2f} ms")
    cols[1].metric("Median Latency", f"{metrics['median_ms']:.2f} ms")
    cols[2].metric("Throughput", f"{metrics['throughput_ips']:.2f} img/s")
    cols[3].metric("Runs", f"{metrics['runs']}")

    cols2 = st.columns(4)
    cols2[0].metric("Min", f"{metrics['min_ms']:.2f} ms")
    cols2[1].metric("Max", f"{metrics['max_ms']:.2f} ms")
    cols2[2].metric("P95", f"{metrics['p95_ms']:.2f} ms")
    cols2[3].metric("P99", f"{metrics['p99_ms']:.2f} ms")

    # Distribution chart
    st.caption("Latency Distribution (ms)")
    hist, bins = np.histogram(metrics["latencies"], bins=10)
    bin_labels = [f"{bins[i]:.1f}-{bins[i+1]:.1f}" for i in range(len(bins)-1)]
    chart_data = {"Range (ms)": bin_labels, "Count": hist.tolist()}
    st.bar_chart(chart_data, x="Range (ms)", y="Count")

    # Raw data expander
    with st.expander("📋 Raw Latency Data"):
        st.write(f"**Standard Deviation:** {metrics['std_ms']:.3f} ms")
        st.line_chart(metrics["latencies"])
        st.caption("Per-run latency (ms). First run after warm-up is on the left.")


def main():
    st.title("☀️ Solar Panel Condition Classifier")
    st.markdown(
        """
        Upload an image of a solar panel to classify its condition.

        **Supported classes:**
        - 🐦 Bird-drop
        - ✨ Clean
        - 🌫️ Dusty
        - ⚡ Electrical-damage
        - 🔧 Physical-Damage
        - ❄️ Snow-Covered
        """
    )

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        available = get_available_models()
        if not available:
            st.error("No models found in `models/` directory.")
            st.stop()

        model_options = list(available.keys())
        selected_model_name = st.selectbox("Select Model", model_options)
        selected_model_path = str(available[selected_model_name])

        top_k = st.slider("Top-K Predictions", min_value=1, max_value=6, value=3)

        st.divider()
        st.subheader("⚡ Benchmark")
        enable_benchmark = st.checkbox("Enable Latency Benchmark", value=False)
        benchmark_runs = st.slider(
            "Benchmark Runs",
            min_value=1,
            max_value=50,
            value=10,
            disabled=not enable_benchmark,
            help="Number of repeated inferences to measure stable latency.",
        )

        st.divider()
        st.markdown(
            """
            **About**

            This app uses deep learning (CNN) models trained on
            solar panel images to detect various conditions that
            affect panel performance.
            """
        )

    # Load model
    try:
        classifier = load_model_cached(selected_model_path)
    except Exception as e:
        st.error(f"Failed to load model: {e}")
        st.stop()

    # File uploader
    uploaded_file = st.file_uploader(
        "📤 Upload an image",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        accept_multiple_files=False,
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file).convert("RGB")

        # Show uploaded image (full width, centered)
        st.image(image, caption="Uploaded Image", use_container_width=True)

        # Run inference
        with st.spinner("Analyzing..."):
            temp_path = Path("_temp_uploaded_image.jpg")
            image.save(temp_path)

            try:
                # Standard prediction with timing (single run)
                t0 = time.perf_counter()
                predictions = classifier.predict(temp_path, top_k=top_k)
                t1 = time.perf_counter()
                single_latency_ms = (t1 - t0) * 1000.0

                # Benchmark mode
                benchmark_metrics = None
                if enable_benchmark:
                    with st.spinner(
                        f"Running benchmark ({benchmark_runs} inferences)..."
                    ):
                        benchmark_metrics = benchmark_inference(
                            classifier, temp_path, benchmark_runs
                        )
            finally:
                if temp_path.exists():
                    temp_path.unlink()

        # Prediction Results section — placed BELOW the uploaded image
        st.subheader("🔍 Prediction Results")

        # Top prediction highlight
        top_class, top_conf = predictions[0]
        st.metric(
            label="Predicted Condition",
            value=top_class,
            delta=f"{top_conf:.2%} confidence",
        )

        # Bar chart of all top-k
        labels = [p[0] for p in predictions]
        scores = [p[1] for p in predictions]
        chart_data = {"Class": labels, "Confidence": scores}
        st.bar_chart(chart_data, x="Class", y="Confidence")

        # Detailed scores section — also BELOW the uploaded image
        st.subheader("📊 Detailed Scores")
        for cls, conf in predictions:
            st.progress(float(conf), text=f"{cls}: {conf:.2%}")

        # Single-run latency badge
        st.caption(f"⏱️ Single inference latency: **{single_latency_ms:.2f} ms**")

        # Benchmark results — full width below everything else
        if enable_benchmark and benchmark_metrics is not None:
            st.divider()
            display_latency_metrics(benchmark_metrics)

    # Sample info
    with st.expander("ℹ️ Model Information"):
        st.write(f"**Model file:** `{selected_model_name}`")
        st.write(f"**Classes:** {', '.join(CLASS_NAMES)}")
        st.write(f"**Input size:** 224 × 224")
        if "efficientnet" in selected_model_name.lower():
            st.write("**Architecture:** EfficientNetB0 (Transfer Learning + Fine-tuning)")
        elif "mobilenet" in selected_model_name.lower():
            st.write("**Architecture:** MobileNetV2 (Transfer Learning)")


if __name__ == "__main__":
    main()

"""Collect GPU information (optional — requires GPUtil)."""


def collect() -> list[dict]:
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        return [
            {
                "id": gpu.id,
                "name": gpu.name,
                "load_percent": round(gpu.load * 100, 1),
                "memory_used_mb": round(gpu.memoryUsed, 1),
                "memory_total_mb": round(gpu.memoryTotal, 1),
                "memory_percent": round(gpu.memoryUtil * 100, 1),
                "temp_celsius": gpu.temperature,
                "driver": gpu.driver,
            }
            for gpu in gpus
        ]
    except ImportError:
        return []
    except Exception:
        return []

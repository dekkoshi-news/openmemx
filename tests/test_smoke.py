
def test_import():
    try:
        import openmemx
        print(f"OpenMemX version: {openmemx.__version__}")
        assert openmemx.__version__ == "1.0.0"
    except ImportError as e:
        print(f"Failed to import openmemx: {e}")
        assert False, "Could not import openmemx"

def test_memory_engine_import():
    try:
        from openmemx import MemoryEngine
        assert MemoryEngine is not None
    except ImportError as e:
        assert False, f"Could not import MemoryEngine: {e}"

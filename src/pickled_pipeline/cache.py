import os
import json
import pickle
import hashlib
import inspect
from functools import wraps


def _default_checkpoint_name(func):
    qualified_name = f"{func.__module__}.{func.__qualname__}"
    return qualified_name.replace("<", "").replace(">", "")


class Cache:
    def __init__(self, cache_dir="pipeline_cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.manifest_path = os.path.join(
            self.cache_dir,
            "cache_manifest.json",
        )
        # Load existing manifest or initialize a new one
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, "r") as f:
                self.checkpoint_order = json.load(f)
        else:
            self.checkpoint_order = []

    def checkpoint(self, name=None, exclude_args=None):
        if exclude_args is None:
            exclude_args = []

        def decorator(func):
            checkpoint_name = name or _default_checkpoint_name(func)
            signature = inspect.signature(func)
            varkw_name = None
            for param_name, param in signature.parameters.items():
                if param.kind == param.VAR_KEYWORD:
                    varkw_name = param_name
                    break

            @wraps(func)
            def wrapper(*args, **kwargs):
                # Map arguments to their names, including varargs and
                # keyword-only args.
                bound = signature.bind(*args, **kwargs)
                bound.apply_defaults()
                bound_args = bound.arguments

                normalized_items = []
                normalized_varkw = None
                if varkw_name and varkw_name in bound_args:
                    varkw = dict(bound_args[varkw_name])
                    for arg in exclude_args:
                        varkw.pop(arg, None)
                    normalized_varkw = tuple(sorted(varkw.items()))

                for arg_name, value in bound_args.items():
                    if arg_name in exclude_args:
                        continue
                    if arg_name == varkw_name:
                        value = normalized_varkw
                    normalized_items.append((arg_name, value))

                # Create a unique key based on the checkpoint name and filtered
                # arguments.
                key_input = (checkpoint_name, tuple(normalized_items))
                key_payload = pickle.dumps(key_input)
                key_hash = hashlib.md5(key_payload).hexdigest()
                cache_filename = f"{checkpoint_name}__{key_hash}.pkl"
                cache_path = os.path.join(self.cache_dir, cache_filename)

                if os.path.exists(cache_path):
                    with open(cache_path, "rb") as f:
                        result = pickle.load(f)
                    print(f"[{checkpoint_name}] Loaded result from cache.")
                else:
                    result = func(*args, **kwargs)
                    with open(cache_path, "wb") as f:
                        pickle.dump(result, f)
                    message = (
                        f"[{checkpoint_name}] Computed result and saved to "
                        "cache."
                    )
                    print(message)

                # Record the checkpoint name if not already recorded
                if checkpoint_name not in self.checkpoint_order:
                    self.checkpoint_order.append(checkpoint_name)
                    with open(self.manifest_path, "w") as f:
                        json.dump(self.checkpoint_order, f)
                return result

            return wrapper

        return decorator

    def truncate_cache(self, starting_from_checkpoint_name):
        if not os.path.exists(self.manifest_path):
            print("No manifest file found. Cannot determine checkpoint order.")
            return False
        with open(self.manifest_path, "r") as f:
            checkpoint_order = json.load(f)
        if starting_from_checkpoint_name not in checkpoint_order:
            message = (
                f"Checkpoint '{starting_from_checkpoint_name}' not found in "
                "manifest."
            )
            print(message)
            return False
        delete_flag = False
        for checkpoint_name in checkpoint_order:
            if checkpoint_name == starting_from_checkpoint_name:
                delete_flag = True
            if delete_flag:
                # Delete all cache files associated with this checkpoint
                files_to_delete = [
                    fname
                    for fname in os.listdir(self.cache_dir)
                    if fname.startswith(f"{checkpoint_name}__")
                    and fname.endswith(".pkl")
                ]
                for filename in files_to_delete:
                    file_path = os.path.join(self.cache_dir, filename)
                    os.remove(file_path)
                    print(f"Removed cache file '{filename}'")
        # Update the manifest by removing truncated checkpoints
        index = checkpoint_order.index(starting_from_checkpoint_name)
        checkpoint_order = checkpoint_order[:index]
        with open(self.manifest_path, "w") as f:
            json.dump(checkpoint_order, f)
        self.checkpoint_order = checkpoint_order
        print(
            f"Cache truncated from checkpoint "
            f"'{starting_from_checkpoint_name}' onward."
        )
        return True

    def clear_cache(self):
        # Remove all files except the manifest
        for filename in os.listdir(self.cache_dir):
            if filename == "cache_manifest.json":
                continue
            file_path = os.path.join(self.cache_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        # Clear the manifest
        self.checkpoint_order = []
        with open(self.manifest_path, "w") as f:
            json.dump(self.checkpoint_order, f)
        print("Cache directory cleared.")

    def list_checkpoints(self):
        # Return a copy of the checkpoint order
        return list(self.checkpoint_order)

from __future__ import annotations

import json
import hashlib
import inspect
import os
import pickle
import tempfile
from collections.abc import Callable, Iterable
from functools import wraps
from typing import Any, ParamSpec, TypeVar, cast


P = ParamSpec("P")
R = TypeVar("R")
CACHE_MANIFEST_FILENAME = "cache_manifest.json"


def _default_checkpoint_name(func: Callable[..., Any]) -> str:
    qualified_name = f"{func.__module__}.{func.__qualname__}"
    return qualified_name.replace("<", "").replace(">", "")


class Cache:
    def __init__(self, cache_dir: str | os.PathLike[str] = "pipeline_cache"):
        self.cache_dir = os.fspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.manifest_path = os.path.join(
            self.cache_dir,
            CACHE_MANIFEST_FILENAME,
        )
        self.checkpoint_order = self._load_manifest()

    def checkpoint(
        self,
        name: str | None = None,
        exclude_args: Iterable[str] | None = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        if exclude_args is None:
            exclude_args = []
        excluded_arg_names = set(exclude_args)

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            checkpoint_name = name or _default_checkpoint_name(func)
            signature = inspect.signature(func)
            varkw_name: str | None = None
            for param_name, param in signature.parameters.items():
                if param.kind == param.VAR_KEYWORD:
                    varkw_name = param_name
                    break

            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                # Map arguments to their names, including varargs and
                # keyword-only args.
                bound = signature.bind(*args, **kwargs)
                bound.apply_defaults()
                bound_args = bound.arguments

                normalized_items: list[tuple[str, Any]] = []
                normalized_varkw: tuple[tuple[str, Any], ...] | None = None
                if varkw_name and varkw_name in bound_args:
                    varkw = dict(bound_args[varkw_name])
                    for arg in excluded_arg_names:
                        varkw.pop(arg, None)
                    normalized_varkw = tuple(sorted(varkw.items()))

                for arg_name, value in bound_args.items():
                    if arg_name in excluded_arg_names:
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
                    try:
                        with open(cache_path, "rb") as f:
                            result = pickle.load(f)
                    except (EOFError, pickle.UnpicklingError):
                        os.remove(cache_path)
                        result = self._compute_and_store(
                            func,
                            args,
                            kwargs,
                            checkpoint_name,
                            cache_path,
                        )
                    else:
                        print(f"[{checkpoint_name}] Loaded result from cache.")
                else:
                    result = self._compute_and_store(
                        func,
                        args,
                        kwargs,
                        checkpoint_name,
                        cache_path,
                    )

                self._record_checkpoint(checkpoint_name)
                return cast(R, result)

            return wrapper

        return decorator

    def truncate_cache(self, starting_from_checkpoint_name: str) -> bool:
        if not os.path.exists(self.manifest_path):
            print("No manifest file found. Cannot determine checkpoint order.")
            return False
        checkpoint_order = self._load_manifest()
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
                    if self._filename_belongs_to_checkpoint(
                        fname,
                        checkpoint_name,
                    )
                ]
                for filename in files_to_delete:
                    file_path = os.path.join(self.cache_dir, filename)
                    os.remove(file_path)
                    print(f"Removed cache file '{filename}'")
        # Update the manifest by removing truncated checkpoints
        index = checkpoint_order.index(starting_from_checkpoint_name)
        checkpoint_order = checkpoint_order[:index]
        self._write_manifest(checkpoint_order)
        self.checkpoint_order = checkpoint_order
        print(
            f"Cache truncated from checkpoint "
            f"'{starting_from_checkpoint_name}' onward."
        )
        return True

    def clear_cache(self) -> None:
        # Remove all files except the manifest
        for filename in os.listdir(self.cache_dir):
            if filename == CACHE_MANIFEST_FILENAME:
                continue
            file_path = os.path.join(self.cache_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        # Clear the manifest
        self.checkpoint_order = []
        self._write_manifest(self.checkpoint_order)
        print("Cache directory cleared.")

    def list_checkpoints(self) -> list[str]:
        # Return a copy of the checkpoint order
        return list(self.checkpoint_order)

    def _compute_and_store(
        self,
        func: Callable[..., R],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        checkpoint_name: str,
        cache_path: str,
    ) -> R:
        result = func(*args, **kwargs)
        self._atomic_pickle_dump(result, cache_path)
        print(f"[{checkpoint_name}] Computed result and saved to cache.")
        return result

    def _record_checkpoint(self, checkpoint_name: str) -> None:
        checkpoint_order = self._load_manifest()
        if checkpoint_name not in checkpoint_order:
            checkpoint_order.append(checkpoint_name)
            self._write_manifest(checkpoint_order)
        self.checkpoint_order = checkpoint_order

    def _load_manifest(self) -> list[str]:
        if not os.path.exists(self.manifest_path):
            return []
        with open(self.manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        if not isinstance(manifest, list) or not all(
            isinstance(item, str) for item in manifest
        ):
            raise ValueError("Cache manifest must be a JSON list of strings.")
        return manifest

    def _write_manifest(self, checkpoint_order: list[str]) -> None:
        self._atomic_json_dump(checkpoint_order, self.manifest_path)

    def _atomic_pickle_dump(self, value: Any, final_path: str) -> None:
        temp_path = self._temporary_path(".pkl")
        try:
            with open(temp_path, "wb") as f:
                pickle.dump(value, f)
            os.replace(temp_path, final_path)
        except Exception:
            self._remove_if_exists(temp_path)
            raise

    def _atomic_json_dump(self, value: Any, final_path: str) -> None:
        temp_path = self._temporary_path(".json")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(value, f)
            os.replace(temp_path, final_path)
        except Exception:
            self._remove_if_exists(temp_path)
            raise

    def _temporary_path(self, suffix: str) -> str:
        fd, temp_path = tempfile.mkstemp(
            prefix=".pickled-pipeline-",
            suffix=suffix,
            dir=self.cache_dir,
        )
        os.close(fd)
        return temp_path

    def _filename_belongs_to_checkpoint(
        self,
        filename: str,
        checkpoint_name: str,
    ) -> bool:
        return self._checkpoint_name_from_filename(filename) == checkpoint_name

    def _checkpoint_name_from_filename(self, filename: str) -> str | None:
        if not filename.endswith(".pkl"):
            return None
        stem = filename.removesuffix(".pkl")
        checkpoint_name, separator, key_hash = stem.rpartition("__")
        if separator != "__":
            return None
        if len(key_hash) != 32 or not all(
            character in "0123456789abcdef" for character in key_hash
        ):
            return None
        return checkpoint_name

    def _remove_if_exists(self, path: str) -> None:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

"""
Headless data widgets — pure-Python replacements for the Orange data
category widgets, without any Qt dependency.
"""

from __future__ import annotations

import math
from typing import Any, Optional

import numpy as np
import sklearn.model_selection as skl

from Orange.data import Table
from Orange.data.pandas_compat import table_from_frame

from ..headless_widget import HeadlessWidget
from ..schemas import SignalDesc


# ======================================================================
# File Loader
# ======================================================================

class HLFileLoader(HeadlessWidget):
    """
    Load an Orange Table from a file path.

    Supported formats:
      - Orange native: .csv, .tsv, .tab, .xlsx, .xls, .pkl (auto-detected)
      - Extended via pandas: .parquet, .json, .feather, .orc
      - Built-in datasets: "iris", "titanic", "housing", etc.

    Settings
    --------
    file_path : str
        Path to data file, or name of a built-in Orange dataset.
    """

    # Extensions handled by pandas instead of Orange
    _PANDAS_EXTENSIONS = {".parquet", ".json", ".feather", ".orc"}

    def get_input_signals(self) -> list[SignalDesc]:
        return []  # root node — no inputs

    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self._settings = {"file_path": ""}
        self.data: Optional[Table] = None

    def receive(self, input_name: str, value: Any) -> None:
        pass  # no inputs

    def handle_new_signals(self) -> None:
        import os
        import pandas as pd
        from Orange.data.pandas_compat import table_from_frame

        path = self._settings.get("file_path", "")
        if not path:
            self.data = None
            self.send("Data", self.data)
            return

        ext = os.path.splitext(path)[1].lower() if os.path.isfile(path) else ""

        if ext in self._PANDAS_EXTENSIONS:
            # Use pandas for formats Orange doesn't support natively
            if ext == ".parquet":
                df = pd.read_parquet(path)
            elif ext == ".json":
                df = pd.read_json(path)
            elif ext == ".feather":
                df = pd.read_feather(path)
            elif ext == ".orc":
                df = pd.read_orc(path)
            else:
                df = pd.read_csv(path)
            self.data = table_from_frame(df)
        else:
            # Orange native loader (handles csv, tsv, xlsx, xls, pkl,
            # and built-in dataset names like "iris")
            self.data = Table(path)

        self.send("Data", self.data)


class HLViewer(HeadlessWidget):
    """
    A pure passthrough widget used to hold data on the backend for frontend visualisation
    nodes (like Scatter Plot, Data Table, Histogram) that don't modify data themselves.
    """
    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={"default": True})]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None

    def receive(self, input_name: str, value: Any) -> None:
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self) -> None:
        if self.data is None:
            self.send("Data", None)
        else:
            self.send("Data", self.data)


# ======================================================================
# Data Sampler
# ======================================================================

class HLDataSampler(HeadlessWidget):
    """
    Headless version of ``OWDataSampler``.

    Randomly draws a subset of data points from the input dataset.
    Core logic extracted from
    ``Orange.widgets.data.owdatasampler.OWDataSampler``.
    """

    # Sampling type constants
    FixedProportion, FixedSize, CrossValidation, Bootstrap = range(4)

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(
                name="Data Sample",
                type="Orange.data.Table",
                flags={"default": True},
            ),
            SignalDesc(
                name="Remaining Data",
                type="Orange.data.Table",
                flags={},
            ),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings = {
            "sampling_type": self.FixedProportion,
            "sampleSizePercentage": 70,
            "sampleSizeNumber": 1,
            "number_of_folds": 10,
            "selectedFold": 1,
            "use_seed": True,
            "replacement": False,
            "stratify": False,
        }

    def receive(self, input_name: str, value: Any) -> None:
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self) -> None:
        if self.data is None or len(self.data) == 0:
            self.send("Data Sample", None)
            self.send("Remaining Data", None)
            return

        s = self._settings
        rnd = 42 if s["use_seed"] else None
        sampling_type = s["sampling_type"]
        data_length = len(self.data)
        stratified = (
            s["stratify"]
            and self.data.domain.has_discrete_class
        )

        if sampling_type == self.FixedProportion:
            size = int(math.ceil(s["sampleSizePercentage"] / 100 * data_length))
            indices = self._sample_n(data_length, size, stratified, False, rnd)

        elif sampling_type == self.FixedSize:
            size = min(s["sampleSizeNumber"], data_length)
            repl = s["replacement"]
            indices = self._sample_n(data_length, size, stratified, repl, rnd)

        elif sampling_type == self.CrossValidation:
            n_folds = s["number_of_folds"]
            sel_fold = s["selectedFold"]
            indices = self._cross_val(data_length, n_folds, sel_fold, stratified, rnd)

        elif sampling_type == self.Bootstrap:
            indices = self._bootstrap(data_length, rnd)

        else:
            self.send("Data Sample", None)
            self.send("Remaining Data", None)
            return

        remaining_idx, sample_idx = indices
        self.send("Data Sample", self.data[sample_idx])
        self.send("Remaining Data", self.data[remaining_idx])

    # ---- sampling helpers (mirroring owdatasampler logic) ----

    @staticmethod
    def _sample_n(data_length, n, stratified, replace, random_state):
        if replace:
            rgen = np.random.RandomState(random_state)
            sample = rgen.randint(0, data_length, n)
            mask = np.ones(data_length)
            mask[sample] = 0
            others = np.nonzero(mask)[0]
            return others, sample
        if n == 0 or n >= data_length:
            rgen = np.random.RandomState(random_state)
            shuffled = np.arange(data_length)
            rgen.shuffle(shuffled)
            empty = np.array([], dtype=int)
            return (shuffled, empty) if n == 0 else (empty, shuffled)
        splitter = skl.ShuffleSplit(
            n_splits=1, test_size=n, random_state=random_state,
        )
        ind = splitter.split(np.zeros(data_length))
        return next(iter(ind))

    def _cross_val(self, data_length, n_folds, sel_fold, stratified, random_state):
        if stratified and self.data.domain.has_discrete_class:
            splitter = skl.StratifiedKFold(
                n_folds, shuffle=True, random_state=random_state,
            )
            splits = list(splitter.split(self.data.X, self.data.Y))
        else:
            splitter = skl.KFold(
                n_folds, shuffle=True, random_state=random_state,
            )
            splits = list(splitter.split(np.zeros(data_length)))
        sample, remaining = splits[sel_fold - 1]
        return remaining, sample

    @staticmethod
    def _bootstrap(data_length, random_state):
        rgen = np.random.RandomState(random_state)
        sample = rgen.randint(0, data_length, data_length)
        sample.sort()
        in_sample = np.ones(data_length, dtype=bool)
        in_sample[sample] = False
        remaining = np.flatnonzero(in_sample)
        return remaining, sample


# ======================================================================
# Select Columns (simplified)
# ======================================================================

class HLSelectColumns(HeadlessWidget):
    """
    Headless column selector.

    Settings
    --------
    kept_attributes : list[str]
        Names of columns to keep as features.
    target : str | None
        Name of the target column.
    metas : list[str]
        Names of columns to move to metas.
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings = {
            "kept_attributes": [],  # empty → keep all
            "target": None,
            "metas": [],
        }

    def receive(self, input_name, value):
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self):
        from Orange.data import Domain

        if self.data is None:
            self.send("Data", None)
            return

        s = self._settings
        domain = self.data.domain

        # Determine attributes
        if s["kept_attributes"]:
            attrs = [domain[n] for n in s["kept_attributes"] if n in domain]
        else:
            attrs = list(domain.attributes)

        # Determine class var
        target_name = s.get("target")
        if target_name and target_name in domain:
            class_vars = [domain[target_name]]
            attrs = [a for a in attrs if a.name != target_name]
        else:
            class_vars = list(domain.class_vars)

        # Determine metas
        meta_names = s.get("metas", [])
        if meta_names:
            meta_vars = [domain[n] for n in meta_names if n in domain]
            attrs = [a for a in attrs if a.name not in meta_names]
        else:
            meta_vars = list(domain.metas)

        new_domain = Domain(attrs, class_vars, meta_vars)
        self.send("Data", self.data.transform(new_domain))


# ======================================================================
# Select Rows (simplified filter)
# ======================================================================

class HLSelectRows(HeadlessWidget):
    """
    Headless row filter.

    Settings
    --------
    filters : list[dict]
        Each dict: ``{"column": str, "op": "=="|"!="|">"|"<", "value": Any}``
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Matching Data", type="Orange.data.Table", flags={"default": True}),
            SignalDesc(name="Unmatched Data", type="Orange.data.Table", flags={}),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings: dict[str, Any] = {"filters": []}

    def receive(self, input_name, value):
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self):
        if self.data is None:
            self.send("Matching Data", None)
            self.send("Unmatched Data", None)
            return

        filters = self._settings.get("filters", [])
        if not filters:
            self.send("Matching Data", self.data)
            self.send("Unmatched Data", None)
            return

        from Orange.data.pandas_compat import table_to_frame
        df = table_to_frame(self.data, include_metas=True)

        mask = np.ones(len(df), dtype=bool)
        _ops = {
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            ">":  lambda a, b: a > b,
            "<":  lambda a, b: a < b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
        }

        for f in filters:
            col, op, val = f["column"], f["op"], f["value"]
            if col in df.columns:
                op_fn = _ops.get(op)
                if op_fn is not None:
                    mask &= op_fn(df[col], val).values

        matching_idx = np.flatnonzero(mask)
        unmatched_idx = np.flatnonzero(~mask)

        self.send("Matching Data", self.data[matching_idx] if len(matching_idx) else None)
        self.send("Unmatched Data", self.data[unmatched_idx] if len(unmatched_idx) else None)


# ======================================================================
# Merge Data
# ======================================================================

class HLMergeData(HeadlessWidget):
    """
    Headless version of ``OWMergeData``.

    Merges two tables by matching rows on a key column,
    similar to a SQL JOIN.

    Settings
    --------
    merge_type : str
        One of ``"inner"``, ``"left"``, ``"right"``, ``"outer"``.
    key_attribute_1 : str
        Column name in the primary (Data) table to join on.
    key_attribute_2 : str
        Column name in the extra (Extra Data) table to join on.
        If empty, uses the same name as ``key_attribute_1``.
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Data", type="Orange.data.Table", flags={}),
            SignalDesc(name="Extra Data", type="Orange.data.Table", flags={}),
        ]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Data", type="Orange.data.Table", flags={"default": True}),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self.extra_data: Optional[Table] = None
        self._settings: dict[str, Any] = {
            "merge_type": "inner",
            "key_attribute_1": "",
            "key_attribute_2": "",
        }

    def receive(self, input_name: str, value: Any) -> None:
        if input_name == "Data":
            self.data = value
        elif input_name == "Extra Data":
            self.extra_data = value

    def handle_new_signals(self) -> None:
        import pandas as pd
        from Orange.data.pandas_compat import table_to_frame, table_from_frame

        if self.data is None or self.extra_data is None:
            self.send("Data", self.data)
            return

        s = self._settings
        key1 = s.get("key_attribute_1", "")
        key2 = s.get("key_attribute_2", "") or key1

        if not key1:
            # No key specified — send primary data unchanged
            self.send("Data", self.data)
            return

        df1 = table_to_frame(self.data, include_metas=True)
        df2 = table_to_frame(self.extra_data, include_metas=True)

        how = s.get("merge_type", "inner")
        if how not in ("inner", "left", "right", "outer"):
            how = "inner"

        merged = pd.merge(df1, df2, left_on=key1, right_on=key2,
                          how=how, suffixes=("", "_extra"))

        result = table_from_frame(merged)
        self.send("Data", result)


# ======================================================================
# Concatenate
# ======================================================================

class HLConcatenate(HeadlessWidget):
    """
    Headless version of ``OWConcatenate``.

    Appends rows from the Extra Data table onto the primary Data table.

    Settings
    --------
    merge_type : str
        ``"union"`` keeps all columns (fills missing with NaN).
        ``"intersection"`` keeps only columns common to both tables.
    append_source_column : bool
        If True, adds a meta column indicating which table each row came from.
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Data", type="Orange.data.Table", flags={}),
            SignalDesc(name="Extra Data", type="Orange.data.Table", flags={}),
        ]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Data", type="Orange.data.Table", flags={"default": True}),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self.extra_data: Optional[Table] = None
        self._settings: dict[str, Any] = {
            "merge_type": "union",
            "append_source_column": False,
        }

    def receive(self, input_name: str, value: Any) -> None:
        if input_name == "Data":
            self.data = value
        elif input_name == "Extra Data":
            self.extra_data = value

    def handle_new_signals(self) -> None:
        import pandas as pd
        from Orange.data.pandas_compat import table_to_frame, table_from_frame

        if self.data is None and self.extra_data is None:
            self.send("Data", None)
            return
        if self.data is None:
            self.send("Data", self.extra_data)
            return
        if self.extra_data is None:
            self.send("Data", self.data)
            return

        s = self._settings
        join_type = s.get("merge_type", "union")

        df1 = table_to_frame(self.data, include_metas=True)
        df2 = table_to_frame(self.extra_data, include_metas=True)

        if s.get("append_source_column", False):
            df1["Source"] = "Data"
            df2["Source"] = "Extra Data"

        if join_type == "intersection":
            common = list(set(df1.columns) & set(df2.columns))
            df1 = df1[common]
            df2 = df2[common]

        merged = pd.concat([df1, df2], ignore_index=True)
        result = table_from_frame(merged)
        self.send("Data", result)


# ======================================================================
# Save Data
# ======================================================================

class HLSaveData(HeadlessWidget):
    """
    Headless version of ``OWSave``.

    Exports data to a file on disk.

    Settings
    --------
    file_path : str
        Output file path (including extension).
        Supported extensions: ``.csv``, ``.tsv``, ``.xlsx``, ``.parquet``,
        ``.json``, ``.tab``.
    """

    _PANDAS_EXTENSIONS = {".parquet", ".json", ".xlsx"}

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={"default": True})]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings: dict[str, Any] = {"file_path": ""}

    def receive(self, input_name: str, value: Any) -> None:
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self) -> None:
        import os
        import logging
        log = logging.getLogger(__name__)

        # Always pass data through
        self.send("Data", self.data)

        if self.data is None:
            return

        path = self._settings.get("file_path", "")
        if not path:
            return

        ext = os.path.splitext(path)[1].lower()

        try:
            if ext in self._PANDAS_EXTENSIONS:
                import pandas as pd
                from Orange.data.pandas_compat import table_to_frame
                df = table_to_frame(self.data, include_metas=True)
                if ext == ".parquet":
                    df.to_parquet(path, index=False)
                elif ext == ".json":
                    df.to_json(path, orient="records", indent=2)
                elif ext == ".xlsx":
                    df.to_excel(path, index=False)
            else:
                # Use Orange's native saver for .csv, .tsv, .tab
                Table.save(self.data, path)
            log.info("Data saved to %s (%d rows)", path, len(self.data))
        except Exception as exc:
            log.error("Failed to save data to %s: %s", path, exc)
            raise


# ======================================================================
# Edit Domain
# ======================================================================

class HLEditDomain(HeadlessWidget):
    """
    Headless version of ``OWEditDomain``.

    Changes variable types (e.g., numeric → discrete, or feature → target).

    Settings
    --------
    retype : dict[str, str]
        Mapping ``{column_name: new_type}`` where new_type is one of
        ``"continuous"``, ``"discrete"``, ``"string"``.
    rename : dict[str, str]
        Mapping ``{old_name: new_name}`` for renaming columns.
    set_target : str | None
        Name of the column to designate as the class (target) variable.
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={"default": True})]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings: dict[str, Any] = {
            "retype": {},
            "rename": {},
            "set_target": None,
        }

    def receive(self, input_name: str, value: Any) -> None:
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self) -> None:
        from Orange.data import Domain, ContinuousVariable, DiscreteVariable, StringVariable
        import pandas as pd
        from Orange.data.pandas_compat import table_to_frame, table_from_frame

        if self.data is None:
            self.send("Data", None)
            return

        s = self._settings
        retype = s.get("retype", {})
        rename = s.get("rename", {})
        target_name = s.get("set_target", None)

        if not retype and not rename and not target_name:
            # Nothing to change
            self.send("Data", self.data)
            return

        # Convert to dataframe, apply type changes, convert back
        df = table_to_frame(self.data, include_metas=True)

        # Apply renames
        if rename:
            df = df.rename(columns=rename)
            # Also update the target name if it was renamed
            if target_name and target_name in rename:
                target_name = rename[target_name]

        # Apply type conversions
        for col, new_type in retype.items():
            actual_col = rename.get(col, col)
            if actual_col not in df.columns:
                continue
            if new_type == "continuous":
                df[actual_col] = pd.to_numeric(df[actual_col], errors="coerce")
            elif new_type == "discrete":
                df[actual_col] = df[actual_col].astype(str)
            elif new_type == "string":
                df[actual_col] = df[actual_col].astype(str)

        result = table_from_frame(df)

        # If set_target is specified, restructure the domain
        if target_name and target_name in [v.name for v in result.domain.variables + result.domain.metas]:
            domain = result.domain
            all_vars = list(domain.attributes) + list(domain.class_vars) + list(domain.metas)
            target_var = None
            for v in all_vars:
                if v.name == target_name:
                    target_var = v
                    break
            if target_var is not None:
                new_attrs = [v for v in domain.attributes if v.name != target_name]
                new_metas = [v for v in domain.metas if v.name != target_name]
                new_domain = Domain(new_attrs, [target_var], new_metas)
                result = result.transform(new_domain)

        self.send("Data", result)

